# codimension-mcp

> **Мови:** [English](README.md) · [Українська](README.uk.md)

MCP-сервер для headless аналізу Codimension (CAN-MCP).

## Встановлення

```shell
pip install -e ./codimension_core
pip install -e ./codimension_mcp
```

## Запуск

```shell
codimension-mcp --workspace /path/to/project
```

## Discovery

Почніть із catalog:

- **Resource:** `codimension://catalog`
- **Tool:** `list_mcp_catalog`

## Tools / Resources / Prompts

Автогенеровані таблиці catalog — у [README.md](README.md) (English, оновлюються скриптом `generate_mcp_catalog_artifacts.py`).

## Розширення VS Code

Команди `Codimension: Copy MCP Server Config` та `Codimension: List MCP Resource URIs` у `codimension-vscode/`.

## Cursor WebView

Після `render_diagram("import")` відкрийте `html_path` у Cursor Simple Browser.

## Конфіг Cursor

- [doc/uk/MCP-CURSOR-HOWTO.md](../doc/uk/MCP-CURSOR-HOWTO.md)
- [doc/en/MCP-CURSOR-HOWTO.md](../doc/en/MCP-CURSOR-HOWTO.md)

```shell
./scripts/install-cursor-mcp.sh
```

**Ключі URI:** `file.py:function:name` → `file.py__function__name`.  
**Source of truth:** `codimension_mcp/catalog.py`.
