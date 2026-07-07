# codimension-vscode

> **Languages:** [English](README.md) · [Українська](README.uk.md)

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

Configure the analysis server in Cursor/VS Code MCP settings. See:

- [doc/en/MCP-CURSOR-HOWTO.md](../doc/en/MCP-CURSOR-HOWTO.md)
- [doc/uk/MCP-CURSOR-HOWTO.md](../doc/uk/MCP-CURSOR-HOWTO.md)
- [doc/en/CODIMENSION-CORE-MAP.md](../doc/en/CODIMENSION-CORE-MAP.md)
