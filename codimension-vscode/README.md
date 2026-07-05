# codimension-vscode

VS Code / Cursor companion extension scaffold for [Codimension MCP](../codimension_mcp/README.md).

## Scope (0.4.0)

- Command palette entry pointing to MCP setup docs
- **Codimension: Show Diagram (HTML WebView)** — opens `.codimension/diagrams/*.html` from `render_diagram`
- **Auto-open** when diagram HTML is created (setting `codimension.autoOpenDiagrams`, default on)

## Build

```bash
cd codimension-vscode
npm install
npm run compile
```

## MCP integration

Configure the analysis server in Cursor/VS Code MCP settings:

```json
{
  "mcpServers": {
    "codimension": {
      "command": "codimension-mcp",
      "args": ["--workspace", "${workspaceFolder}"]
    }
  }
}
```

See [CODIMENSION-EVO.md](../CODIMENSION-EVO.md) for architecture.
