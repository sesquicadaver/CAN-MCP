# Context: Codimension extraction etapa 9

**Task:** Thin IDE wrappers + Carantine cleanup after full core detachment.

**Outcome:**
- `codimension/analysis/core_bridge.py` — shared IDE→CoreProject adapter
- `notused.py` delegates vulture to `codimension_core.analyzer`
- `depsdiagram.py` uses core_bridge
- Remove fully detached Carantine legacy files
- Docs update

**Constraints:** Keep PyQt UI in notused.py; no Carantine imports in production code.
