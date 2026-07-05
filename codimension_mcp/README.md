# codimension-mcp

MCP server for Codimension code analysis. See [CODIMENSION-EVO.md](../CODIMENSION-EVO.md).

## Install

```shell
pip install -e .
pip install -e ./codimension_core
pip install -e ./codimension_mcp
```

## Run

```shell
codimension-mcp --workspace /path/to/project
```

## Cursor WebView

After `render_diagram("import")`, open the returned `html_path` in Cursor Simple Browser.

MCP resources `codimension://diagram/import` and `codimension://diagram/call` return `text/html` directly.

## Cursor config

```json
{
  "mcpServers": {
    "codimension": {
      "command": "codimension-mcp",
      "args": ["--workspace", "/path/to/project"]
    }
  }
}
```
