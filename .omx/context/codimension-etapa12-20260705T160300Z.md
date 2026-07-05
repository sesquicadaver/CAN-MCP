# Etapa 12 — Import diagram MCP/WebView parity

**Task:** Unify MCP `render_diagram("import")` with full `build_import_diagram_model`, add HTML/DOT resource, vscode hygiene.

**Desired outcome:**
- `render_diagram("import")` writes HTML from full import diagram model (classes/docstrings options via defaults).
- MCP resource `codimension://diagram/import-model` (or extend existing) serves HTML/DOT.
- Tests pass; versions bumped; `.gitignore` for vscode build artifacts.

**Known facts:**
- `get_import_diagram` returns Graphviz DOT from full model.
- `render_diagram("import")` uses `build_import_graph()` (simplified IR) — gap identified post etapa 11.
- VS Code WebView command exists but no `.gitignore`.

**Constraints:** No Carantine imports; test in venv; minimal diff; Ukrainian docs optional.

**Touchpoints:** `codimension_mcp/diagrams.py`, `resources.py`, `graph_render.py` or `import_diagram.py`, tests, vscode `.gitignore`, pyproject versions.
