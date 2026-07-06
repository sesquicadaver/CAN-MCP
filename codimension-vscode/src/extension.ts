import * as vscode from "vscode";
import { showDiagramPanel, watchDiagramOutput } from "./diagramPanel";
import { copyMcpConfigToClipboard, showMcpResources } from "./mcpConfig";

export function activate(context: vscode.ExtensionContext): void {
  watchDiagramOutput(context);

  context.subscriptions.push(
    vscode.commands.registerCommand("codimension.openMcpDocs", () => {
      vscode.window.showInformationMessage(
        "Configure codimension-mcp in MCP settings. See codimension_mcp/README.md in the repository.",
      );
    }),
    vscode.commands.registerCommand("codimension.copyMcpConfig", () => copyMcpConfigToClipboard()),
    vscode.commands.registerCommand("codimension.showMcpResources", () => showMcpResources()),
    vscode.commands.registerCommand("codimension.showDiagram", async (htmlPath?: string) => {
      await showDiagramPanel(htmlPath);
    }),
  );
}

export function deactivate(): void {}
