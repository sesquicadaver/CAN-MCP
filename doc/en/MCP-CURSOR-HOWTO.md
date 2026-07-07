# Codimension MCP × Cursor — Complete HOWTO

> **Languages:** [English](../en/MCP-CURSOR-HOWTO.md) | [Українська](../uk/MCP-CURSOR-HOWTO.md)

Practical guide for connecting **codimension-mcp** to Cursor and working with **23 tools**, **17 resources**, and **6 prompts**.

**Source of truth:** `codimension_mcp/catalog.py`  
**Short catalog:** [codimension_mcp/README.md](../../codimension_mcp/README.md)  
**Local config (not in git):** `.cursor/mcp.json` — generated for this checkout

---

## Contents

1. [Architecture](#1-architecture)
2. [Installation](#2-installation)
3. [Connecting to Cursor](#3-connecting-to-cursor)
4. [Verifying the connection](#4-verifying-the-connection)
5. [Basic workflow](#5-basic-workflow)
6. [Data formats](#6-data-formats)
7. [Tools — reference with examples](#7-tools--reference-with-examples)
8. [Resources — reference with examples](#8-resources--reference-with-examples)
9. [Prompts — ready-made scenarios](#9-prompts--ready-made-scenarios)
10. [Diagrams and WebView](#10-diagrams-and-webview)
11. [End-to-end scenarios](#11-end-to-end-scenarios)
12. [Example prompts for Cursor Agent](#12-example-prompts-for-cursor-agent)
13. [Troubleshooting](#13-troubleshooting)
14. [Checklist](#14-checklist)

---

## 1. Architecture

```text
Cursor Agent (MCP host)
        │  JSON-RPC / stdio
        ▼
codimension-mcp          ← MCP server (codimension_mcp/)
        │
        ▼
codimension_core         ← headless analysis (no PyQt)
        │
        ├─ symbols, imports, callgraph, cfg
        ├─ diagnostics (pyflakes/radon)
        └─ Graph IR v1 → JSON
```

The legacy PyQt IDE is **not part of** CAN-MCP and is **not required** for MCP.

---

## 2. Installation

### 2.1. Clone and venv

```bash
git clone https://github.com/sesquicadaver/CAN-MCP.git
cd CAN-MCP

python3 -m venv .venv
source .venv/bin/activate          # Windows: .venv\Scripts\activate
pip install --upgrade pip
```

### 2.2. MCP packages

```bash
pip install -e ./codimension_core -e ./codimension_mcp
```

Or in one script (venv + MCP + `.cursor/mcp.json`):

```bash
./scripts/install-cursor-mcp.sh
```

### 2.3. Analysis dependencies (recommended)

```bash
pip install pyflakes radon jedi vulture
```

| Package | Purpose |
|---------|---------|
| `pyflakes` + `radon` | `get_diagnostics` |
| `jedi` | `find_usages` |
| `vulture` | `find_dead_code` |

### 2.4. Verification

```bash
which codimension-mcp
# → .../CAN-MCP/.venv/bin/codimension-mcp

codimension-mcp --help

# Full merge gate (same as CI):
./scripts/test-analysis.sh
```

---

## 3. Connecting to Cursor

### 3.1. Project config for this checkout

File **`.cursor/mcp.json`** (gitignored) is generated with absolute paths.  
Cursor expands `${workspaceFolder}` **only in project-level** `.cursor/mcp.json`, not in the global config.

**Recommended — use `CODIMENSION_WORKSPACE` env:**

```json
{
  "mcpServers": {
    "codimension": {
      "command": "/home/sesquicadaver/GITFOLDER/CAN-MCP/.venv/bin/codimension-mcp",
      "env": {
        "CODIMENSION_WORKSPACE": "${workspaceFolder}",
        "VIRTUAL_ENV": "/home/sesquicadaver/GITFOLDER/CAN-MCP/.venv",
        "PATH": "/home/sesquicadaver/GITFOLDER/CAN-MCP/.venv/bin:/usr/local/bin:/usr/bin:/bin"
      }
    }
  }
}
```

| Field | Value |
|-------|-------|
| `command` | Full path to `codimension-mcp` in the CAN-MCP venv |
| `env.CODIMENSION_WORKSPACE` | `${workspaceFolder}` — root of the **Python project open in Cursor** |

Alternative (also works in project config only):

```json
"args": ["--workspace", "${workspaceFolder}"]
```

Template without concrete paths: [`.cursor/mcp.json.example`](../../.cursor/mcp.json.example)

> **Important:** The server does **not** auto-open `$HOME`, the process cwd, or any implicit default.  
> It opens a workspace only when you set `CODIMENSION_WORKSPACE`, pass `--workspace`, or call `open_project`.

### 3.2. Global config

File: `~/.cursor/mcp.json` — same server entry, available in all workspaces.

**Do NOT use** `"args": ["--workspace", "${workspaceFolder}"]` in `~/.cursor/mcp.json`.  
Cursor **does not expand** `${workspaceFolder}` in the global config — the literal string is passed to the server, which causes `FileNotFoundError` (see [Troubleshooting](#13-troubleshooting)).

Safe global pattern:

```json
{
  "mcpServers": {
    "codimension": {
      "command": "/absolute/path/to/CAN-MCP/.venv/bin/codimension-mcp",
      "env": {
        "VIRTUAL_ENV": "/absolute/path/to/CAN-MCP/.venv",
        "PATH": "/absolute/path/to/CAN-MCP/.venv/bin:/usr/local/bin:/usr/bin:/bin"
      }
    }
  }
}
```

Then either:

- rely on the Agent calling `open_project(path)` per workspace, or
- set `CODIMENSION_WORKSPACE` to a **fixed absolute path** if you always analyze one project.

### 3.3. Two typical setups

**A. Analyzing CAN-MCP:**

- Cursor workspace = `/home/sesquicadaver/GITFOLDER/CAN-MCP`
- `CODIMENSION_WORKSPACE=${workspaceFolder}` → analyzes this repository

**B. Analyzing another project:**

- Cursor workspace = your Python project
- `command` → still points to the CAN-MCP venv
- `CODIMENSION_WORKSPACE` → `${workspaceFolder}` = the target project

### 3.4. Activation

1. Save `mcp.json`
2. Cursor Settings → **MCP** → server `codimension` → enable / Reload
3. Or restart Cursor

---

## 4. Verifying the connection

### 4.1. In Agent chat

```text
Use MCP codimension: call list_mcp_catalog and briefly summarize tools/resources/prompts.
```

Expected: **23 tools**, **17 resources**, **6 prompts**.

```text
Call get_project_tree via codimension MCP.
```

Expected: JSON with a `"files": ["...", ...]` array.

### 4.2. Resource without a tool

```text
Read MCP resource codimension://workspace/status
```

Expected:

```json
{
  "status": "open",
  "workspace": "/abs/path/to/project",
  "python_files": 27,
  "analyzed_files": 27,
  "tool_calls": { "open_project": 1 }
}
```

---

## 5. Basic workflow

```text
┌─────────────────────────────────────────────────────────┐
│ 1. open_project(path)     — if no --workspace / env set │
│ 2. analyze_project()      — warm caches                 │
│ 3. get_symbols()          — symbol overview             │
│ 4. … targeted analysis …                                │
└─────────────────────────────────────────────────────────┘
```

If `mcp.json` sets `CODIMENSION_WORKSPACE` or `"args": ["--workspace", "..."]`, step 1 runs at server startup.

**Discovery (always first for a new agent):**

- Tool: `list_mcp_catalog`
- Resource: `codimension://catalog`

---

## 6. Data formats

### 6.1. Graph IR v2 (default)

Most tools return Graph IR v2 (`node.uri`, `edge.provenance`). Legacy v1: `CODIMENSION_GRAPH_IR=1`.

```json
{
  "graph_ir_version": 2,
  "meta": {
    "kind": "symbols"
  },
  "nodes": [
    {
      "id": "codimension_core/project.py:function:open",
      "type": "function",
      "name": "open",
      "file": "codimension_core/project.py",
      "line_start": 52,
      "line_end": 60,
      "uri": "codimension://symbol/codimension_core__path__project.py__function__open"
    }
  ],
  "edges": []
}
```

### 6.2. Symbol ID (for tools)

| Type | Format | Example |
|------|--------|---------|
| Function | `file.py:function:name` | `codimension_core/project.py:function:open` |
| Class | `file.py:class:Name` | `codimension_core/project.py:class:Project` |

### 6.3. URI keys (for resources)

| Concept | Tool ID | URI key |
|---------|---------|---------|
| Function | `main.py:function:foo` | `main.py__function__foo` |
| Class | `pkg/mod.py:class:Bar` | `pkg/mod.py__class__Bar` |
| File (impact) | `lib/mod.py` | `lib__mod.py` |

**CFG resource example:**

```text
codimension://graph/control_flow/codimension_core__project.py__function__open
```

### 6.4. Errors

```json
{
  "status": "error",
  "error": "Call open_project(path) first"
}
```

---

## 7. Tools — reference with examples

### Discovery

#### `list_mcp_catalog`

```json
{}
```

**Response (fragment):**

```json
{
  "status": "ok",
  "catalog_version": "1.0",
  "tools": [{ "name": "open_project" }],
  "resources": [{ "uri": "codimension://catalog" }],
  "prompts": [{ "name": "refactor_symbol" }]
}
```

### Project

| Tool | Arguments | Example response |
|------|-----------|------------------|
| `open_project` | `{ "path": "/abs/project" }` | `{ "status": "ok", "python_files": 42 }` |
| `analyze_project` | `{}` | `{ "status": "ok", "analyzed_files": 42 }` |
| `invalidate_file` | `{ "path": "pkg/mod.py" }` | `{ "status": "ok", "invalidated": "pkg/mod.py" }` |
| `get_project_tree` | `{}` | `{ "files": ["main.py", "pkg/api.py"] }` |

### Symbols

| Tool | Arguments |
|------|-----------|
| `get_symbols` | `{}` or `{ "path": "pkg/mod.py" }` |
| `analyze_file` | `{ "path": "pkg/mod.py" }` |
| `lookup_symbol` | `{ "name": "Project" }` |
| `explain_symbol` | `{ "symbol": "pkg/mod.py:function:api" }` |

### Graphs

| Tool | Arguments |
|------|-----------|
| `get_import_graph` | `{}` |
| `get_call_graph` | `{}` or `{ "symbol": "main.py:function:main" }` |
| `get_control_flow` | `{ "function_id": "file.py:function:name" }` |
| `find_callers` / `find_callees` | `{ "symbol": "file.py:function:name" }` |
| `find_usages` | `{ "symbol": "file.py:class:Name" }` |
| `impact_analysis` | `{ "target": "file.py" }` or `{ "target": "file.py:function:name" }` |

### Code quality

| Tool | Arguments | Dependency |
|------|-----------|------------|
| `get_diagnostics` | `{ "path": "file.py" }` | pyflakes, radon |
| `find_dead_code` | `{}` or `{ "path": "file.py" }` | vulture |

### Summaries and diagrams

| Tool | Arguments |
|------|-----------|
| `get_dependency_summary` | `{}` or `{ "path": "file.py" }` |
| `get_symbol_summary` | `{}` or `{ "path": "file.py" }` |
| `get_import_diagram` | `{}` |
| `render_diagram` | `{ "kind": "import" }` / `"call"` / `"control_flow"` + `target` / `"impact"` + `target` |
| `get_cache_stats` | `{}` |

**`render_diagram` — example response:**

```json
{
  "status": "ok",
  "kind": "import",
  "html_path": "/project/.codimension/diagrams/import-project.html",
  "mermaid": "graph TD\n...",
  "nodes": 12,
  "edges": 8,
  "webview_hint": "Open ... in Cursor Simple Browser..."
}
```

---

## 8. Resources — reference with examples

### Static

| URI | MIME | Content |
|-----|------|---------|
| `codimension://catalog` | JSON | Full catalog |
| `codimension://workspace/status` | JSON | Workspace state |
| `codimension://project/tree` | JSON | List of `.py` files |
| `codimension://deps/summary` | JSON | Import classification |
| `codimension://symbols/summary` | JSON | Symbol counters |
| `codimension://graph/import` | JSON | Import Graph IR |
| `codimension://graph/call` | JSON | Call Graph IR |
| `codimension://diagram/import` | HTML | Import diagram |
| `codimension://diagram/call` | HTML | Call diagram |
| `codimension://cache/stats` | JSON | Cache statistics |

### Templated

| URI | Example |
|-----|---------|
| `codimension://deps/file/{path}` | `codimension://deps/file/main.py` |
| `codimension://symbols/file/{path}` | `codimension://symbols/file/pkg/api.py` |
| `codimension://graph/control_flow/{function_key}` | `.../main.py__function__api` |
| `codimension://diagram/control_flow/{function_key}` | HTML CFG |
| `codimension://graph/impact/{target_key}` | `.../codimension_core__project.py` |
| `codimension://diagram/impact/{target_key}` | HTML impact |
| `codimension://symbol/{symbol_key}` | `.../main.py__function__api` |

---

## 9. Prompts — ready-made scenarios

| Prompt | Arguments | Workflow |
|--------|-----------|----------|
| `refactor_symbol` | `symbol` | explain → impact → usages → plan |
| `review_dead_code` | — | vulture → verify → deletion plan |
| `review_imports` | — | import graph → cycles → fixes |
| `analyze_module` | `path` | symbols → CFG → callers → summary |
| `audit_dependencies` | — | deps/symbols summary → graph → fixes |
| `assess_change_impact` | `target` | impact graph/diagram → callers → test plan |

**In Cursor Agent:**

```text
Use MCP prompt refactor_symbol with symbol="pkg/api.py:function:fetch"
and follow the described workflow.
```

---

## 10. Diagrams and WebView

1. Agent calls `render_diagram("import")` (or `"call"`, `"control_flow"`, `"impact"`).
2. Response includes `html_path` (`.codimension/diagrams/*.html`).
3. Open in **Simple Browser** / HTML preview.

Or use resources: `codimension://diagram/import`, `codimension://diagram/call`.

**Valid `kind` values:** `import`, `call`, `control_flow`, `impact`.

---

## 11. End-to-end scenarios

### A. New project overview

```text
open_project → analyze_project → get_project_tree →
get_symbol_summary → get_dependency_summary → get_import_graph → find_dead_code
```

### B. Function refactor

```text
explain_symbol → impact_analysis → find_callers → find_usages → get_control_flow
```

Prompt: MCP prompt `refactor_symbol`.

### C. Pre-change file check

```text
impact_analysis → codimension://graph/impact/{key} → render_diagram(impact) → find_callers
```

Prompt: MCP prompt `assess_change_impact`.

### D. Import graph audit

```text
get_import_graph → get_import_diagram → render_diagram(import) → get_dependency_summary
```

Prompt: MCP prompt `review_imports`.

### E. Module deep-dive

```text
analyze_file → get_diagnostics → get_control_flow → find_callers / find_callees
```

Prompt: MCP prompt `analyze_module`.

---

## 12. Example prompts for Cursor Agent

```text
list_mcp_catalog → how many tools?
get_symbols for codimension_core/project.py
lookup_symbol name="open"
impact_analysis target="codimension_core/project.py"
```

```text
1. analyze_project
2. get_call_graph
3. For the top-3 functions by fan-in — find_callers
4. Table: function | callers count | files
```

---

## 13. Troubleshooting

| Symptom | Fix |
|---------|-----|
| `ImportError: codimension_core` / `build_call_graph` | `bash scripts/install-cursor-mcp.sh` or `pip install -e ./codimension_core -e ./codimension_mcp` |
| `Unknown tool: open_project` | Update CAN-MCP (stage 40+) |
| Cursor does not start MCP | Use an absolute path in `command` |
| `Call open_project first` | Call `open_project`, or set `CODIMENSION_WORKSPACE` / `--workspace` in project `mcp.json` |
| Yellow MCP status / slow startup / scanning `$HOME` | Workspace not set — server fell back to scanning home. Set `CODIMENSION_WORKSPACE` in **project** `.cursor/mcp.json`, or call `open_project` explicitly |
| `FileNotFoundError: .../${workspaceFolder}` | Literal `${workspaceFolder}` was passed — you used it in **global** `~/.cursor/mcp.json` where Cursor does not expand it. Move workspace config to project `.cursor/mcp.json` or use an absolute path |
| Empty diagnostics | `pip install pyflakes radon` |
| `find_usages` fails | `pip install jedi` |
| `find_dead_code` fails / `No module named vulture` | `pip install vulture` in venv; ensure `command` points to venv `codimension-mcp` (not system Python via symlink — fixed in core 0.20.5+) |
| CFG invalid `function_id` | Format `file.py:function:name` |

```bash
./scripts/test-analysis.sh
./scripts/verify-mcp-catalog.sh
```

---

## 14. Checklist

- [ ] Python 3.10+
- [ ] `pip install -e ./codimension_core -e ./codimension_mcp`
- [ ] `pip install pyflakes radon jedi vulture`
- [ ] `codimension-mcp --help` OK
- [ ] `.cursor/mcp.json` with absolute `command` and `CODIMENSION_WORKSPACE=${workspaceFolder}` (project config)
- [ ] No `${workspaceFolder}` in global `~/.cursor/mcp.json`
- [ ] Cursor MCP reloaded
- [ ] `list_mcp_catalog` → 23 / 17 / 6
- [ ] `get_project_tree` → file list
- [ ] `codimension://workspace/status` → `"status": "open"`

---

## Quick reference: all 23 tools

| # | Tool | Arguments |
|---|------|-----------|
| 1 | `list_mcp_catalog` | — |
| 2 | `open_project` | `path` |
| 3 | `analyze_project` | — |
| 4 | `invalidate_file` | `path` |
| 5 | `analyze_file` | `path` |
| 6 | `get_project_tree` | — |
| 7 | `get_symbols` | `path?` |
| 8 | `get_import_graph` | — |
| 9 | `get_call_graph` | `symbol?` |
| 10 | `get_control_flow` | `function_id` |
| 11 | `find_callers` | `symbol` |
| 12 | `find_callees` | `symbol` |
| 13 | `find_usages` | `symbol` |
| 14 | `impact_analysis` | `target` |
| 15 | `explain_symbol` | `symbol` |
| 16 | `lookup_symbol` | `name` |
| 17 | `find_dead_code` | `path?` |
| 18 | `get_diagnostics` | `path` |
| 19 | `get_import_diagram` | — |
| 20 | `get_cache_stats` | — |
| 21 | `get_dependency_summary` | `path?` |
| 22 | `get_symbol_summary` | `path?` |
| 23 | `render_diagram` | `kind`, `target?` |
