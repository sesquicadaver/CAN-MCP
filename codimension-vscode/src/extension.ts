import * as vscode from "vscode";

export function activate(context: vscode.ExtensionContext): void {
  const disposable = vscode.commands.registerCommand("codimension.openMcpDocs", () => {
    vscode.window.showInformationMessage(
      "Configure codimension-mcp in MCP settings. See codimension_mcp/README.md in the repository.",
    );
  });
  context.subscriptions.push(disposable);
}

export function deactivate(): void {}
