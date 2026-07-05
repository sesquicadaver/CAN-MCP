import * as vscode from "vscode";

const DIAGRAM_DIR = ".codimension/diagrams";
let activePanel: vscode.WebviewPanel | undefined;

function basename(fsPath: string): string {
  const parts = fsPath.split(/[/\\]/);
  return parts[parts.length - 1] || fsPath;
}

function autoOpenEnabled(): boolean {
  return vscode.workspace.getConfiguration("codimension").get<boolean>("autoOpenDiagrams", true);
}

async function listDiagramHtmlFiles(root: vscode.Uri): Promise<vscode.Uri[]> {
  const diagramDir = vscode.Uri.joinPath(root, ...DIAGRAM_DIR.split("/"));
  try {
    const entries = await vscode.workspace.fs.readDirectory(diagramDir);
    return entries
      .filter(([name, type]) => type === vscode.FileType.File && name.endsWith(".html"))
      .map(([name]) => vscode.Uri.joinPath(diagramDir, name))
      .sort((a, b) => a.fsPath.localeCompare(b.fsPath));
  } catch {
    return [];
  }
}

async function pickDiagramFile(root: vscode.Uri): Promise<vscode.Uri | undefined> {
  const files = await listDiagramHtmlFiles(root);
  if (files.length === 0) {
    return undefined;
  }
  if (files.length === 1) {
    return files[0];
  }
  const picked = await vscode.window.showQuickPick(
    files.map((uri) => ({
      label: basename(uri.fsPath),
      description: uri.fsPath,
      uri,
    })),
    { placeHolder: "Select a Codimension diagram HTML file" },
  );
  return picked?.uri;
}

function resolveTargetUri(htmlPath: string | undefined, root: vscode.Uri): vscode.Uri | undefined {
  if (htmlPath) {
    return vscode.Uri.file(htmlPath);
  }
  return undefined;
}

async function readHtml(uri: vscode.Uri): Promise<string | undefined> {
  try {
    const raw = await vscode.workspace.fs.readFile(uri);
    return new TextDecoder("utf-8").decode(raw);
  } catch (err) {
    const message = err instanceof Error ? err.message : String(err);
    vscode.window.showErrorMessage(`Cannot read diagram file: ${message}`);
    return undefined;
  }
}

function renderPanel(targetUri: vscode.Uri, root: vscode.Uri, html: string): void {
  const title = `Codimension: ${basename(targetUri.fsPath)}`;
  if (activePanel) {
    activePanel.title = title;
    activePanel.webview.html = html;
    activePanel.reveal(vscode.ViewColumn.One);
    return;
  }

  activePanel = vscode.window.createWebviewPanel(
    "codimensionDiagram",
    title,
    vscode.ViewColumn.One,
    {
      enableScripts: true,
      retainContextWhenHidden: true,
      localResourceRoots: [vscode.Uri.joinPath(root, ".codimension")],
    },
  );
  activePanel.webview.html = html;
  activePanel.webview.onDidReceiveMessage((message: { command?: string; href?: string }) => {
    if (message.command === "openExternal" && message.href) {
      void vscode.env.openExternal(vscode.Uri.parse(message.href));
    }
  });
  activePanel.onDidDispose(() => {
    activePanel = undefined;
  });
}

export async function showDiagramPanel(htmlPath?: string): Promise<void> {
  const folders = vscode.workspace.workspaceFolders;
  if (!folders?.length) {
    vscode.window.showWarningMessage("Open a workspace folder to view Codimension diagrams.");
    return;
  }

  let targetUri = resolveTargetUri(htmlPath, folders[0].uri);
  if (!targetUri) {
    targetUri = await pickDiagramFile(folders[0].uri);
  }

  if (!targetUri) {
    vscode.window.showInformationMessage(
      `No diagram HTML found. Run MCP render_diagram first; output is written to ${DIAGRAM_DIR}/`,
    );
    return;
  }

  const root =
    folders.find((folder) => targetUri!.fsPath.startsWith(folder.uri.fsPath))?.uri ?? folders[0].uri;
  const html = await readHtml(targetUri);
  if (!html) {
    return;
  }
  renderPanel(targetUri, root, html);
}

function registerFolderWatcher(context: vscode.ExtensionContext, root: vscode.Uri): void {
  const pattern = new vscode.RelativePattern(root, `${DIAGRAM_DIR}/*.html`);
  const watcher = vscode.workspace.createFileSystemWatcher(pattern);

  watcher.onDidCreate((uri) => {
    if (!autoOpenEnabled()) {
      return;
    }
    void showDiagramPanel(uri.fsPath);
  });

  context.subscriptions.push(watcher);
}

export function watchDiagramOutput(context: vscode.ExtensionContext): void {
  for (const folder of vscode.workspace.workspaceFolders ?? []) {
    registerFolderWatcher(context, folder.uri);
  }

  context.subscriptions.push(
    vscode.workspace.onDidChangeWorkspaceFolders((event) => {
      for (const folder of event.added) {
        registerFolderWatcher(context, folder.uri);
      }
    }),
  );
}
