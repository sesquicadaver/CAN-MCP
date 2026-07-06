# codimension-mcp

MCP server for Codimension code analysis. See [CODIMENSION-EVO.md](../CODIMENSION-EVO.md).

## Install

```shell
pip install -e ./codimension_core
pip install -e ./codimension_mcp
```

## Run

```shell
codimension-mcp --workspace /path/to/project
```

## Tools

| Tool | Purpose |
| ---- | ------- |
| `open_project` | Open workspace directory |
| `analyze_project` | Warm caches for all Python files |
| `analyze_file` | Symbol Graph IR for one file |
| `get_project_tree` | Relative Python file paths |
| `get_symbols` | Symbol index (file or project) |
| `get_import_graph` | Import dependency Graph IR |
| `get_call_graph` | Static call graph |
| `get_control_flow` | CFG for `file.py:function:name` |
| `find_callers` / `find_callees` | Call relationships |
| `find_usages` | Jedi usage search |
| `impact_analysis` | Transitive blast radius |
| `explain_symbol` | Structured symbol context |
| `lookup_symbol` | Reverse index lookup by name |
| `find_dead_code` | Vulture analysis |
| `get_diagnostics` | pyflakes/radon per file |
| `get_import_diagram` | Graphviz DOT + layout metadata |
| `get_cache_stats` | Incremental cache counters |
| `get_dependency_summary` | Classified imports (system/project/unresolved) |
| `get_symbol_summary` | Symbol counts by type |
| `render_diagram` | HTML/SVG for Cursor WebView |

## Resources

| URI | MIME | Content |
| --- | ---- | ------- |
| `codimension://workspace/status` | application/json | Open path, file counts |
| `codimension://project/tree` | application/json | Python file list |
| `codimension://deps/summary` | application/json | Classified import summary |
| `codimension://deps/file/{path}` | application/json | Per-file import summary |
| `codimension://symbols/summary` | application/json | Symbol counts by type |
| `codimension://symbols/file/{path}` | application/json | Per-file symbol counts |
| `codimension://graph/import` | application/json | Import Graph IR |
| `codimension://graph/call` | application/json | Call Graph IR |
| `codimension://diagram/import` | text/html | Import diagram HTML |
| `codimension://diagram/call` | text/html | Call graph HTML |
| `codimension://cache/stats` | application/json | Cache hit/miss stats |

## Prompts

| Name | Args | Workflow |
| ---- | ---- | -------- |
| `refactor_symbol` | `symbol` | explain → impact → usages → plan |
| `review_dead_code` | — | vulture → verify → deletion plan |
| `review_imports` | — | import graph → cycles → fixes |
| `analyze_module` | `path` | symbols → CFG → callers → summary |
| `audit_dependencies` | — | deps/symbols summary → graph → fixes |

## VS Code extension

Commands `Codimension: Copy MCP Server Config` and `Codimension: List MCP Resource URIs` in `codimension-vscode/`.

## Cursor WebView

After `render_diagram("import")`, open the returned `html_path` in Cursor Simple Browser.

Resources `codimension://diagram/import` and `codimension://diagram/call` return `text/html` directly.

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

## Legacy IDE

PyQt GUI (`codimension/`, `cdmplugins/`) is maintenance-only. See [doc/LEGACY-IDE.md](../doc/LEGACY-IDE.md).
