# CAN-MCP — Codimension headless analysis for AI agents

[![CI](https://github.com/sesquicadaver/CAN-MCP/actions/workflows/ci.yml/badge.svg)](https://github.com/sesquicadaver/CAN-MCP/actions/workflows/ci.yml)
[![Python](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/)
[![License](https://img.shields.io/badge/license-GPL%20v3-green.svg)](LICENSE)

Headless Python code analysis exposed via **MCP** (Model Context Protocol) for Cursor and other AI clients.

## Packages

| Package | Role |
| ------- | ---- |
| [`codimension_core`](codimension_core/) | Headless analysis (symbols, imports, call graph, CFG, diagnostics) |
| [`codimension_mcp`](codimension_mcp/) | MCP server — 22 tools, 16 resources, 6 prompts |
| [`codimension-vscode`](codimension-vscode/) | VS Code extension (optional MCP UI) |

Architecture map: [doc/CODIMENSION-CORE-MAP.md](doc/CODIMENSION-CORE-MAP.md)

## Quick start

```bash
git clone https://github.com/sesquicadaver/CAN-MCP.git
cd CAN-MCP
python3 -m venv .venv
source .venv/bin/activate
pip install --upgrade pip
pip install -e ./codimension_core -e ./codimension_mcp
pip install pyflakes radon jedi vulture
./scripts/install-cursor-mcp.sh   # writes .cursor/mcp.json
./scripts/test-analysis.sh        # merge gate (ruff, mypy, pytest)
```

Cursor: reload MCP server **codimension** after install. Full guide: [doc/MCP-CURSOR-HOWTO.md](doc/MCP-CURSOR-HOWTO.md).

<!-- catalog:root-mcp -->
**MCP discovery:** read `codimension://catalog` or call tool `list_mcp_catalog`.

| Kind | Count |
| ---- | ----- |
| Tools | 22 |
| Resources | 17 |
| Prompts | 6 |

Key resources: `codimension://graph/import`, `codimension://graph/call`, `codimension://graph/impact/{target_key}`, `codimension://cache/stats`.

Full catalog: [codimension_mcp/README.md](codimension_mcp/README.md). **Cursor HOWTO:** [doc/MCP-CURSOR-HOWTO.md](doc/MCP-CURSOR-HOWTO.md). Cursor: `./scripts/install-cursor-mcp.sh` або `.cursor/mcp.json` (local). VS Code extension: [codimension-vscode/](codimension-vscode/).
<!-- /catalog:root-mcp -->

## Development

```bash
./scripts/test-analysis.sh
./scripts/verify-mcp-catalog.sh
```

Living spec (TZ → module → tests): [doc/plugins/living-specification.md](doc/plugins/living-specification.md).

## License

GPL v3 — see [LICENSE](LICENSE). Fork lineage from [SergeySatskiy/codimension](https://github.com/SergeySatskiy/codimension); this repository contains **only** the headless MCP stack.
