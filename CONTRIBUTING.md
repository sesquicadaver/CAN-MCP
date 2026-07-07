# Contributing to CAN-MCP

> **Languages:** [English](CONTRIBUTING.md) · [Українська](CONTRIBUTING.uk.md)

## Workflow

1. Fork and branch: `git checkout -b feature/your-feature`
2. Install dev env:

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install --upgrade pip
pip install -r requirements-dev.txt
pip install -e ./codimension_core -e ./codimension_mcp
```

3. Run merge gate: `./scripts/test-analysis.sh`
4. Update [doc/en/plugins/living-specification.md](doc/en/plugins/living-specification.md) and [doc/uk/plugins/living-specification.md](doc/uk/plugins/living-specification.md) when adding extracted modules
5. Keep documentation bilingual (EN + UK) under `doc/en/` and `doc/uk/`
6. Open a Pull Request

## CI

[`.github/workflows/ci.yml`](.github/workflows/ci.yml) — ruff, mypy (core), pytest, MCP catalog parity, pip-audit.

## Standards

- **Scope:** only `codimension_core`, `codimension_mcp`, `codimension-vscode`, MCP docs, and headless tests
- **Lint:** ruff (E, F, W, I) on core + mcp
- **Types:** mypy on `codimension_core`
- **License:** GPL v3
- **Docs:** update both language copies when changing user-facing documentation
