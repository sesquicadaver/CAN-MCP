# PRD: Etapa 12 — Import diagram render parity

## User stories

### US-001: render_diagram import uses full model
- **Acceptance:** `render_diagram(state, "import")` builds via `build_import_diagram_model`, writes HTML under `.codimension/diagrams/import-project.html`, payload includes `graphviz` + `modules`.
- **Tests:** extend `tests/test_codimension_mcp.py`

### US-002: MCP resource for import diagram HTML
- **Acceptance:** Resource returns HTML from full import diagram model (reuse builder).
- **Tests:** resource read in MCP tests if feasible

### US-003: vscode gitignore
- **Acceptance:** `codimension-vscode/.gitignore` ignores `node_modules/`, `out/`

### US-004: Version bump + living spec
- core 0.11.0, mcp 0.7.0, vscode 0.3.0

## Verification
```bash
python -m pytest tests/test_codimension_core*.py tests/test_codimension_mcp.py -q
cd codimension-vscode && npm run compile
```
