# Etapa 13 — CI pipeline + VS Code auto-open diagrams

**Task:** Add GitHub Actions CI for analysis packages; auto-open WebView when MCP writes diagram HTML.

**Desired outcome:**
- `.github/workflows/ci.yml` with jobs: analysis (core+mcp pytest/ruff/mypy), ide (ruff/mypy/smoke), vscode (npm compile).
- `codimension.autoOpenDiagrams` setting + FileSystemWatcher on `.codimension/diagrams/*.html`.

**Constraints:** Core tests must not require PyQt; full `pytest tests/` optional/separate job if flaky.

**Touchpoints:** `.github/workflows/ci.yml`, `codimension-vscode/src/*`, `package.json`, living-spec, versions.
