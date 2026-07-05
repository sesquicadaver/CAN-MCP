# PRD: Etapa 9 — IDE thin wrappers + Carantine cleanup

## Acceptance

1. `notused.py` uses `run_vulture` / `build_vulture_exclude_patterns` from core.
2. `core_bridge.core_project_from_ide()` shared by depsdiagram + notused.
3. Carantine legacy files removed where IDE fully delegates to core.
4. Carantine README updated; CODIMENSION-CORE-MAP marks extraction complete for wrapped modules.
5. Existing core/MCP tests still pass.
