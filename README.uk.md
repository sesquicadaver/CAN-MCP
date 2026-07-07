# CAN-MCP — headless аналіз Codimension для AI-агентів

> **Мови:** [English](README.md) · [Українська](README.uk.md) · [Індекс документації](doc/README.md)

[![CI](https://github.com/sesquicadaver/CAN-MCP/actions/workflows/ci.yml/badge.svg)](https://github.com/sesquicadaver/CAN-MCP/actions/workflows/ci.yml)
[![Python](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/)
[![License](https://img.shields.io/badge/license-GPL%20v3-green.svg)](LICENSE)

Headless аналіз Python-коду через **MCP** (Model Context Protocol) для Cursor та інших AI-клієнтів.

**Реліз:** `codimension-core` 1.0.0 · `codimension-mcp` 1.0.0 ([CHANGELOG](CHANGELOG.uk.md) · [English](CHANGELOG.md))

## Пакети

| Пакет | Роль |
| ----- | ---- |
| [`codimension_core`](codimension_core/) | Headless аналіз (symbols, imports, call graph, CFG, diagnostics) |
| [`codimension_mcp`](codimension_mcp/) | MCP-сервер — 23 tools, 17 resources, 6 prompts |
| [`codimension-vscode`](codimension-vscode/) | Розширення VS Code (опційний MCP UI) |

Карта архітектури: [doc/uk/CODIMENSION-CORE-MAP.md](doc/uk/CODIMENSION-CORE-MAP.md) · [English](doc/en/CODIMENSION-CORE-MAP.md)

## Швидкий старт

```bash
git clone https://github.com/sesquicadaver/CAN-MCP.git
cd CAN-MCP
./scripts/dev-setup.sh   # venv, editable install, Cursor MCP, merge gate
```

Ручне встановлення:

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install --upgrade pip
pip install -e "./codimension_core[analysis]" -e ./codimension_mcp
pip install -r requirements-dev.txt
./scripts/install-cursor-mcp.sh   # створює .cursor/mcp.json
./scripts/test-analysis.sh        # merge gate (ruff, mypy, pytest)
```

Cursor: після встановлення перезавантажте MCP-сервер **codimension**.

- **Українська HOWTO:** [doc/uk/MCP-CURSOR-HOWTO.md](doc/uk/MCP-CURSOR-HOWTO.md)
- **English:** [doc/en/MCP-CURSOR-HOWTO.md](doc/en/MCP-CURSOR-HOWTO.md)

<!-- catalog:root-mcp -->
**MCP discovery:** читайте `codimension://catalog` або викличте tool `list_mcp_catalog`.

| Kind | Count |
| ---- | ----- |
| Tools | 23 |
| Resources | 17 |
| Prompts | 6 |

Ключові resources: `codimension://graph/import`, `codimension://graph/call`, `codimension://graph/impact/{target_key}`, `codimension://cache/stats`.

Повний catalog: [codimension_mcp/README.uk.md](codimension_mcp/README.uk.md). Cursor: `./scripts/install-cursor-mcp.sh` або `.cursor/mcp.json`. VS Code: [codimension-vscode/](codimension-vscode/).
<!-- /catalog:root-mcp -->

## Розробка

```bash
./scripts/dev-setup.sh
./scripts/test-analysis.sh
./scripts/verify-mcp-catalog.sh
```

Living spec (ТЗ → модуль → тести):

- [doc/uk/plugins/living-specification.md](doc/uk/plugins/living-specification.md)
- [English](doc/en/plugins/living-specification.md)

## Ліцензія

GPL v3 — див. [LICENSE](LICENSE). Форк від [SergeySatskiy/codimension](https://github.com/SergeySatskiy/codimension); репозиторій містить **лише** headless MCP stack.

## Підтримка проєкту

Якщо проєкт корисний, можна підтримати розробку добровільним донатом у USDT.

Донати не дають частки, токенів, governance, платної підтримки чи інвестиційного доходу.

### USDT

| Мережа | Адреса |
| ------ | ------ |
| USDT ERC-20 / Ethereum | 0xfa9821efd142228d53e1418fe335bb1cd8ff3c39 |
| USDT TRC-20 / Tron | TNnhueeGqujf6AAUhcgissoEkL7tdzmqQv |

Переконайтесь, що мережа відповідає типу адреси. Транзакції в неправильну мережу можуть бути втрачені назавжди.

Дякуємо за підтримку.
