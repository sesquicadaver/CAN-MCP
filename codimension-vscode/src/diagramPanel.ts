import * as vscode from "vscode";

const DIAGRAM_DIR = ".codimension/diagrams";

function workspaceRoot(): vscode.Uri | undefined {
  return vscode.workspace.workspaceFolders?.[0]?.uri;
}

function basename(fsPath: string): string {
  const parts = fsPath.split(/[/\\]/);
  return parts[parts.length - 1] || fsPath;
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

export async function showDiagramPanel(htmlPath?: string): Promise<void> {
  const root = workspaceRoot();
  if (!root) {
    vscode.window.showWarningMessage("Open a workspace folder to view Codimension diagrams.");
    return;
  }

  let targetUri: vscode.Uri | undefined;
  if (htmlPath) {
    targetUri = vscode.Uri.file(htmlPath);
  } else {
    targetUri = await pickDiagramFile(root);
  }

  if (!targetUri) {
    vscode.window.showInformationMessage(
      `No diagram HTML found. Run MCP render_diagram first; output is written to ${DIAGRAM_DIR}/`,
    );
    return;
  }

  let html: string;
  try {
    const raw = await vscode.workspace.fs.readFile(targetUri);
    html = new TextDecoder("utf-8").decode(raw);
  } catch (err) {
    const message = err instanceof Error ? err.message : String(err);
    vscode.window.showErrorMessage(`Cannot read diagram file: ${message}`);
    return;
  }

  const panel = vscode.window.createWebviewPanel(
    "codimensionDiagram",
    `Codimension: ${basename(targetUri.fsPath)}`,
    vscode.ViewColumn.One,
    {
      enableScripts: true,
      retainContextWhenHidden: true,
      localResourceRoots: [vscode.Uri.joinPath(root, ".codimension")],
    },
  );

  panel.webview.html = html;
  panel.webview.onDidReceiveMessage((message: { command?: string; href?: string }) => {
    if (message.command === "openExternal" && message.href) {
      void vscode.env.openExternal(vscode.Uri.parse(message.href));
    }
  });
}
