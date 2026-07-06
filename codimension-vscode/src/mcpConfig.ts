import * as vscode from "vscode";

import { MCP_RESOURCE_URIS } from "./mcpResourceUris.generated";

export function buildMcpServerConfig(workspacePath: string): string {
  const config = {
    mcpServers: {
      codimension: {
        command: "codimension-mcp",
        args: ["--workspace", workspacePath],
      },
    },
  };
  return JSON.stringify(config, null, 2);
}

export async function copyMcpConfigToClipboard(): Promise<void> {
  const folder = vscode.workspace.workspaceFolders?.[0];
  if (!folder) {
    vscode.window.showWarningMessage("Open a workspace folder to copy Codimension MCP config.");
    return;
  }
  const json = buildMcpServerConfig(folder.uri.fsPath);
  await vscode.env.clipboard.writeText(json);
  vscode.window.showInformationMessage(
    "Codimension MCP config copied. Paste into Cursor MCP settings or .cursor/mcp.json.",
  );
}

export function listMcpResourceUris(): string {
  return MCP_RESOURCE_URIS.join("\n");
}

export async function showMcpResources(): Promise<void> {
  const uris = listMcpResourceUris();
  const doc = await vscode.workspace.openTextDocument({
    content: `# Codimension MCP resources\n\nStart with codimension://catalog or list_mcp_catalog.\n\n${uris}\n\nSee codimension_mcp/README.md for tools and prompts.\n`,
    language: "markdown",
  });
  await vscode.window.showTextDocument(doc, vscode.ViewColumn.Beside);
}
