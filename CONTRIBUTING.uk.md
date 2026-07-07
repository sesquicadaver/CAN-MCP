# Участь у CAN-MCP

> **Мови:** [English](CONTRIBUTING.md) · [Українська](CONTRIBUTING.uk.md)

## Порядок дій

1. Fork і гілка: `git checkout -b feature/your-feature`
2. Середовище розробки:

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install --upgrade pip
pip install -r requirements-dev.txt
pip install -e ./codimension_core -e ./codimension_mcp
```

3. Запустіть `./scripts/test-analysis.sh`
4. Оновлюйте [doc/uk/plugins/living-specification.md](doc/uk/plugins/living-specification.md) та [doc/en/plugins/living-specification.md](doc/en/plugins/living-specification.md) при винесенні модулів
5. Документація двомовна: `doc/en/` та `doc/uk/`
6. Відкрийте Pull Request

## CI

[`.github/workflows/ci.yml`](.github/workflows/ci.yml) — ruff, mypy (core), pytest, узгодженість MCP catalog, pip-audit.

## Стандарти

- **Область:** лише `codimension_core`, `codimension_mcp`, `codimension-vscode`, MCP docs, headless tests
- **Lint:** ruff (E, F, W, I) на core + mcp
- **Types:** mypy на `codimension_core`
- **License:** GPL v3
- **Docs:** оновлюйте обидві мовні копії при зміні документації для користувача
