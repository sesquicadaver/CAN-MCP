# codimension-vscode

VS Code / Cursor companion extension scaffold for [Codimension MCP](../codimension_mcp/README.md).

## Scope (0.1.0)

- Command palette entry pointing to MCP setup docs
- Future: WebView panels for Graph IR diagrams rendered by `render_diagram`

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
