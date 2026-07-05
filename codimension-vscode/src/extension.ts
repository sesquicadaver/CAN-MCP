import * as vscode from "vscode";
import { showDiagramPanel } from "./diagramPanel";

export function activate(context: vscode.ExtensionContext): void {
  context.subscriptions.push(
    vscode.commands.registerCommand("codimension.openMcpDocs", () => {
      vscode.window.showInformationMessage(
        "Configure codimension-mcp in MCP settings. See codimension_mcp/README.md in the repository.",
      );
    }),
    vscode.commands.registerCommand("codimension.showDiagram", async (htmlPath?: string) => {
      await showDiagramPanel(htmlPath);
    }),
  );
}

export function deactivate(): void {}
