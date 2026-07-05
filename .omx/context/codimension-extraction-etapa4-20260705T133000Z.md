# Context: Codimension extraction etapa 4

**Task:** Etapa 4 — analyzer extraction + resolved import dependency graph.

**Desired outcome:**
- `codimension_core.analyzer` — pyflakes + radon (з `ierrors.py`)
- `build_import_graph` використовує `ImportResolution`
- IDE `ierrors.py` — wrapper; legacy → Carantine
- MCP tool `get_diagnostics(path)`
- Тести green, ruff clean

**Constraints:** Carantine для legacy, venv-only, мінімальний diff.

**Touchpoints:** `analyzer.py`, `dependency_graph.py`, `ierrors.py`, MCP server, tests, docs.

**Acceptance:** pytest для analyzer + resolved graph; commit+push.
