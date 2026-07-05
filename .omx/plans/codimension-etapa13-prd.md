# PRD: Etapa 13 — CI + VS Code auto-open

## US-001: GitHub Actions CI
- Job `analysis`: pytest core+mcp, ruff, mypy on codimension_core + codimension_mcp
- Job `ide`: ruff + mypy on codimension + cdmplugins, smoke import (PyQt5 on ubuntu)
- Job `vscode`: npm ci + compile

## US-002: VS Code auto-open
- Setting `codimension.autoOpenDiagrams` (default true)
- Watcher on `.codimension/diagrams/*.html` → `showDiagramPanel`

## Verification
```bash
python -m pytest tests/test_codimension_core*.py tests/test_codimension_mcp.py -q
cd codimension-vscode && npm run compile
```
