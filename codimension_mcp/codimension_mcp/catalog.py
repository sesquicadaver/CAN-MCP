# -*- coding: utf-8 -*-
"""Machine-readable catalog of Codimension MCP tools, resources, and prompts."""

from __future__ import annotations

from codimension_mcp.serializers import dumps_payload

CATALOG_VERSION = "1.0"

TOOLS: list[dict[str, str | bool]] = [
    {"name": "open_project", "description": "Open a Python project directory for analysis.", "requires_project": False},
    {"name": "analyze_project", "description": "Warm caches for all Python files.", "requires_project": True},
    {
        "name": "invalidate_file",
        "description": "Drop cached analysis for one file after external edits.",
        "requires_project": True,
    },
    {"name": "analyze_file", "description": "Symbol Graph IR for one file.", "requires_project": True},
    {"name": "get_project_tree", "description": "Relative Python file paths.", "requires_project": True},
    {"name": "get_symbols", "description": "Symbol Graph IR (optional path).", "requires_project": True},
    {"name": "get_import_graph", "description": "Import dependency Graph IR.", "requires_project": True},
    {"name": "get_call_graph", "description": "Static call graph (optional symbol filter).", "requires_project": True},
    {"name": "get_control_flow", "description": "CFG for file.py:function:name.", "requires_project": True},
    {"name": "find_callers", "description": "Find callers of a symbol.", "requires_project": True},
    {"name": "find_callees", "description": "Find callees of a symbol.", "requires_project": True},
    {"name": "find_usages", "description": "Jedi usage search.", "requires_project": True},
    {"name": "impact_analysis", "description": "Transitive blast radius for symbol or file.", "requires_project": True},
    {"name": "explain_symbol", "description": "Structured symbol context bundle.", "requires_project": True},
    {"name": "lookup_symbol", "description": "Reverse index lookup by name.", "requires_project": True},
    {"name": "find_dead_code", "description": "Vulture dead-code scan.", "requires_project": True},
    {"name": "get_diagnostics", "description": "pyflakes/radon diagnostics per file.", "requires_project": True},
    {"name": "get_import_diagram", "description": "Graphviz DOT import diagram model.", "requires_project": True},
    {"name": "get_cache_stats", "description": "Incremental cache counters.", "requires_project": True},
    {"name": "get_dependency_summary", "description": "Classified imports (optional path).", "requires_project": True},
    {"name": "get_symbol_summary", "description": "Symbol counts by type (optional path).", "requires_project": True},
    {"name": "render_diagram", "description": "HTML/SVG diagram.", "requires_project": True},
    {"name": "list_mcp_catalog", "description": "Return MCP catalog.", "requires_project": False},
]

RESOURCES: list[dict[str, str]] = [
    {"uri": "codimension://catalog", "mime_type": "application/json", "description": "MCP capability catalog"},
    {"uri": "codimension://workspace/status", "mime_type": "application/json", "description": "Workspace status"},
    {"uri": "codimension://project/tree", "mime_type": "application/json", "description": "Python file list"},
    {"uri": "codimension://deps/summary", "mime_type": "application/json", "description": "Import classification"},
    {"uri": "codimension://deps/file/{path}", "mime_type": "application/json", "description": "File import summary"},
    {"uri": "codimension://symbols/summary", "mime_type": "application/json", "description": "Symbol counts"},
    {"uri": "codimension://symbols/file/{path}", "mime_type": "application/json", "description": "File symbol counts"},
    {"uri": "codimension://graph/import", "mime_type": "application/json", "description": "Import Graph IR"},
    {"uri": "codimension://graph/call", "mime_type": "application/json", "description": "Call Graph IR"},
    {
        "uri": "codimension://graph/control_flow/{function_key}",
        "mime_type": "application/json",
        "description": "CFG Graph IR",
    },
    {
        "uri": "codimension://graph/impact/{target_key}",
        "mime_type": "application/json",
        "description": "Impact Graph IR",
    },
    {"uri": "codimension://diagram/import", "mime_type": "text/html", "description": "Import diagram HTML"},
    {"uri": "codimension://diagram/call", "mime_type": "text/html", "description": "Call graph HTML"},
    {
        "uri": "codimension://diagram/control_flow/{function_key}",
        "mime_type": "text/html",
        "description": "CFG HTML",
    },
    {
        "uri": "codimension://diagram/impact/{target_key}",
        "mime_type": "text/html",
        "description": "Impact diagram HTML",
    },
    {
        "uri": "codimension://symbol/{symbol_key}",
        "mime_type": "application/json",
        "description": "Single symbol Graph IR node",
    },
    {"uri": "codimension://cache/stats", "mime_type": "application/json", "description": "Cache statistics"},
]

PROMPTS: list[dict[str, str]] = [
    {
        "name": "refactor_symbol",
        "args": "symbol",
        "description": "Safe refactor workflow",
        "workflow": "explain → impact → usages → plan",
    },
    {
        "name": "review_dead_code",
        "args": "",
        "description": "Review vulture findings",
        "workflow": "vulture → verify → deletion plan",
    },
    {
        "name": "review_imports",
        "args": "",
        "description": "Audit import graph",
        "workflow": "import graph → cycles → fixes",
    },
    {
        "name": "analyze_module",
        "args": "path",
        "description": "Deep-dive one module",
        "workflow": "symbols → CFG → callers → summary",
    },
    {
        "name": "audit_dependencies",
        "args": "",
        "description": "Dependency audit workflow",
        "workflow": "deps/symbols summary → graph → fixes",
    },
    {
        "name": "assess_change_impact",
        "args": "target",
        "description": "Blast-radius review before edits",
        "workflow": "impact graph/diagram → callers → test plan",
    },
]

ENCODING_NOTES = {
    "function_key": "file.py:function:name → file.py__function__name; pkg/mod.py → pkg__path__mod.py__function__name",
    "symbol_key": "same encoding as function_key for symbol ids",
    "impact_target": "pkg/mod.py → pkg__path__mod.py; symbols use function_key encoding",
    "diagram_kinds": "import, call, control_flow, impact",
    "graph_ir_v2": "set CODIMENSION_GRAPH_IR=2 for node.uri and edge.provenance fields",
}


def build_mcp_catalog() -> dict[str, object]:
    """Return structured catalog for agents and documentation."""
    return {
        "status": "ok",
        "catalog_version": CATALOG_VERSION,
        "server": "codimension-mcp",
        "discovery": "Read codimension://catalog or call list_mcp_catalog first.",
        "tools": TOOLS,
        "resources": RESOURCES,
        "prompts": PROMPTS,
        "encoding": ENCODING_NOTES,
    }


def read_mcp_catalog() -> str:
    """Serialize catalog as JSON for MCP tool/resource consumers."""
    return dumps_payload(build_mcp_catalog())


def catalog_resource_uris() -> list[str]:
    """Return registered MCP resource URI templates."""
    return [item["uri"] for item in RESOURCES]


def catalog_tool_names() -> list[str]:
    """Return registered MCP tool names."""
    return [str(item["name"]) for item in TOOLS]


def catalog_prompt_names() -> list[str]:
    """Return registered MCP prompt names."""
    return [item["name"] for item in PROMPTS]
