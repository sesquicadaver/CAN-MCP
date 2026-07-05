# Context: Codimension extraction etapa 3

**Task:** Продовжити CODIMENSION-EVO extraction після etapa 1→2 (imports + callgraph).

**Desired outcome:**
- `depsdiagram` делегує classification у `codimension_core.imports`
- `find_usages` у core + MCP tool
- Тести + docs оновлені
- Carantine без змін (legacy importutils лишається до повного від’єднання)

**Known facts:**
- `8815628` — importutils extraction + static callgraph done
- `classify_resolution` вже є в `codimension_core/imports.py`
- IDE wrapper `codimension/utils/importutils.py` делегує в core

**Constraints:**
- GPL v3, venv-only testing
- Код поза MCP → Carantine спочатку
- Мінімальний diff, існуючі патерни

**Touchpoints:**
- `codimension/diagram/depsdiagram.py`
- `codimension_core/symbols.py`, `imports.py`
- `codimension_mcp/tools.py`, `server.py`
- `tests/`, `doc/CODIMENSION-CORE-MAP.md`

**Acceptance:**
- pytest green for new/changed tests
- ruff clean on touched files
- MCP `find_usages` returns Graph IR
