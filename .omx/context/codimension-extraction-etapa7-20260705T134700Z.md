# Context: Codimension extraction etapa 7

**Task:** CODIMENSION-EVO etapa 7 — Cursor WebView для діаграм.

**Outcome:**
- `codimension_core.graph_render` — Graph IR → Mermaid + self-contained SVG HTML
- MCP tool `render_diagram(kind, target?)` writes `.codimension/diagrams/*.html`
- MCP resource `codimension://diagram/{kind}` returns text/html
- Tests, docs, core 0.7.0 / mcp 0.3.0

**Constraints:** No PyQt; offline HTML (inline SVG, no CDN); headless only.

**Touchpoints:** `graph_render.py`, `codimension_mcp/diagrams.py`, `tools.py`, `server.py`, `resources.py`.
