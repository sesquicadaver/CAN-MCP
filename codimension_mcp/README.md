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

## Discovery

Start with the catalog — no need to guess URIs or tool names:

- **Resource:** `codimension://catalog`
- **Tool:** `list_mcp_catalog`

```shell
# After codimension-mcp is running, agents should read the catalog first.
```

## Tools

<!-- catalog:tools -->
| Tool | Purpose |
| ---- | ------- |
| `list_mcp_catalog` | Return MCP catalog. |
| `open_project` | Open a Python project directory for analysis. |
| `analyze_project` | Warm caches for all Python files. |
| `analyze_file` | Symbol Graph IR for one file. |
| `get_project_tree` | Relative Python file paths. |
| `get_symbols` | Symbol Graph IR (optional path). |
| `get_import_graph` | Import dependency Graph IR. |
| `get_call_graph` | Static call graph (optional symbol filter). |
| `get_control_flow` | CFG for file.py:function:name. |
| `find_callers` | Find callers of a symbol. |
| `find_callees` | Find callees of a symbol. |
| `find_usages` | Jedi usage search. |
| `impact_analysis` | Transitive blast radius for symbol or file. |
| `explain_symbol` | Structured symbol context bundle. |
| `lookup_symbol` | Reverse index lookup by name. |
| `find_dead_code` | Vulture dead-code scan. |
| `get_diagnostics` | pyflakes/radon diagnostics per file. |
| `get_import_diagram` | Graphviz DOT import diagram model. |
| `get_cache_stats` | Incremental cache counters. |
| `get_dependency_summary` | Classified imports (optional path). |
| `get_symbol_summary` | Symbol counts by type (optional path). |
| `render_diagram` | HTML/SVG diagram. |
<!-- /catalog:tools -->

## Resources

<!-- catalog:resources -->
| URI | MIME | Content |
| --- | ---- | ------- |
| `codimension://catalog` | application/json | **Start here** — mcp capability catalog |
| `codimension://workspace/status` | application/json | Workspace status |
| `codimension://project/tree` | application/json | Python file list |
| `codimension://deps/summary` | application/json | Import classification |
| `codimension://deps/file/{path}` | application/json | File import summary |
| `codimension://symbols/summary` | application/json | Symbol counts |
| `codimension://symbols/file/{path}` | application/json | File symbol counts |
| `codimension://graph/import` | application/json | Import Graph IR |
| `codimension://graph/call` | application/json | Call Graph IR |
| `codimension://graph/control_flow/{function_key}` | application/json | CFG Graph IR |
| `codimension://graph/impact/{target_key}` | application/json | Impact Graph IR |
| `codimension://diagram/import` | text/html | Import diagram HTML |
| `codimension://diagram/call` | text/html | Call graph HTML |
| `codimension://diagram/control_flow/{function_key}` | text/html | CFG HTML |
| `codimension://diagram/impact/{target_key}` | text/html | Impact diagram HTML |
| `codimension://cache/stats` | application/json | Cache statistics |
<!-- /catalog:resources -->

## Prompts

<!-- catalog:prompts -->
| Name | Args | Workflow |
| ---- | ---- | -------- |
| `refactor_symbol` | `symbol` | explain → impact → usages → plan |
| `review_dead_code` | — | vulture → verify → deletion plan |
| `review_imports` | — | import graph → cycles → fixes |
| `analyze_module` | `path` | symbols → CFG → callers → summary |
| `audit_dependencies` | — | deps/symbols summary → graph → fixes |
| `assess_change_impact` | `target` | impact graph/diagram → callers → test plan |
<!-- /catalog:prompts -->

## VS Code extension

Commands `Codimension: Copy MCP Server Config` and `Codimension: List MCP Resource URIs` in `codimension-vscode/`.

## Cursor WebView

After `render_diagram("import")`, open the returned `html_path` in Cursor Simple Browser.

Resources `codimension://diagram/import` and `codimension://diagram/call` return `text/html` directly.

## Cursor config

Copy the sample and adjust the workspace path. Full guide: [doc/MCP-CURSOR-HOWTO.md](../doc/MCP-CURSOR-HOWTO.md).

```shell
./scripts/install-cursor-mcp.sh
# or manually copy .cursor/mcp.json.example → .cursor/mcp.json
```

```json
{
  "mcpServers": {
    "codimension": {
      "command": "codimension-mcp",
      "args": ["--workspace", "${workspaceFolder}"]
    }
  }
}
```

**Function resource keys:** encode `file.py:function:name` as `file.py__function__name` in URIs.  
**Impact targets:** bare symbol (`leaf`), file (`lib.py`), or encoded path (`pkg__path__mod.py`).  
**Source of truth:** `codimension_mcp/catalog.py`. Run `python scripts/generate_mcp_catalog_artifacts.py` after catalog changes (VS Code URIs + README tables).

## Legacy IDE

PyQt GUI (`codimension/`, `cdmplugins/`) is maintenance-only. See [doc/LEGACY-IDE.md](../doc/LEGACY-IDE.md).
