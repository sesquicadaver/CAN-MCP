# CAN-MCP — аналіз Codimension для AI-агентів

> **Мови:** [English](README.md) · [Українська](README.uk.md) · [Документація](doc/README.md)

[![CI](https://github.com/sesquicadaver/CAN-MCP/actions/workflows/ci.yml/badge.svg)](https://github.com/sesquicadaver/CAN-MCP/actions/workflows/ci.yml)
[![Python](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/)
[![License](https://img.shields.io/badge/license-GPL%20v3-green.svg)](LICENSE)

Аналіз Python-коду без PyQt IDE через **MCP** (Model Context Protocol) для Cursor та інших AI-клієнтів.

**Реліз:** `codimension-core` 1.0.0 · `codimension-mcp` 1.0.0 ([CHANGELOG.uk.md](CHANGELOG.uk.md) · [English](CHANGELOG.md))

## Пакети

| Пакет | Роль |
| ----- | ---- |
| [`codimension_core`](codimension_core/) | Аналіз без IDE: symbols, imports, call graph, CFG, diagnostics |
| [`codimension_mcp`](codimension_mcp/) | MCP-сервер — 23 tools, 17 resources, 6 prompts |
| [`codimension-vscode`](codimension-vscode/) | Розширення VS Code (опційний UI) |

Карта архітектури: [UK](doc/uk/CODIMENSION-CORE-MAP.md) · [EN](doc/en/CODIMENSION-CORE-MAP.md)

## Швидкий старт

```bash
git clone https://github.com/sesquicadaver/CAN-MCP.git
cd CAN-MCP
./scripts/dev-setup.sh   # venv, install, MCP config, тести
```

Ручне встановлення:

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install --upgrade pip
pip install -e "./codimension_core[analysis]" -e ./codimension_mcp
pip install -r requirements-dev.txt
./scripts/install-cursor-mcp.sh   # .cursor/mcp.json
./scripts/test-analysis.sh        # ruff, mypy, pytest
```

Після встановлення: Cursor → Settings → MCP → **codimension** → **Reload**.

- **Посібник (UK):** [doc/uk/MCP-CURSOR-HOWTO.md](doc/uk/MCP-CURSOR-HOWTO.md)
- **Guide (EN):** [doc/en/MCP-CURSOR-HOWTO.md](doc/en/MCP-CURSOR-HOWTO.md)

<!-- catalog:root-mcp -->
**Огляд MCP:** `codimension://catalog` або tool `list_mcp_catalog`.

| Kind | Count |
| ---- | ----- |
| Tools | 23 |
| Resources | 17 |
| Prompts | 6 |

Ключові resources: `codimension://graph/import`, `codimension://graph/call`, `codimension://graph/impact/{target_key}`, `codimension://cache/stats`.

Catalog: [codimension_mcp/README.uk.md](codimension_mcp/README.uk.md). Налаштування MCP: `./scripts/install-cursor-mcp.sh`. VS Code: [codimension-vscode/](codimension-vscode/).
<!-- /catalog:root-mcp -->

## Розробка

```bash
./scripts/dev-setup.sh
./scripts/test-analysis.sh
./scripts/verify-mcp-catalog.sh
```

Жива специфікація (модуль → тести):

- [UK](doc/uk/plugins/living-specification.md)
- [EN](doc/en/plugins/living-specification.md)

## Ліцензія

GPL v3 — [LICENSE](LICENSE). Форк [SergeySatskiy/codimension](https://github.com/SergeySatskiy/codimension); у репозиторії лише MCP-стек без PyQt IDE.

## Підтримка проєкту

Добровільні донати USDT — без частки, токенів, прав управління чи платної підтримки.

| Мережа | Адреса |
| ------ | ------ |
| USDT ERC-20 / Ethereum | 0xfa9821efd142228d53e1418fe335bb1cd8ff3c39 |
| USDT TRC-20 / Tron | TNnhueeGqujf6AAUhcgissoEkL7tdzmqQv |

Надсилайте USDT лише в відповідну мережу — інакше кошти можуть бути втрачені.

Дякуємо за підтримку.
