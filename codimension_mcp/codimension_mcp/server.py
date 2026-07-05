# -*- coding: utf-8 -*-
"""Codimension MCP server entry point."""

from __future__ import annotations

import argparse
import sys

from mcp.server.fastmcp import FastMCP

from .prompts import register_prompts
from .resources import register_resources
from .schemas import WorkspaceState
from .tools import (
    analyze_file_tool,
    analyze_project,
    explain_symbol_tool,
    find_callees_tool,
    find_callers_tool,
    find_dead_code_tool,
    find_usages_tool,
    format_tool_error,
    get_cache_stats_tool,
    get_call_graph_tool,
    get_control_flow_tool,
    get_diagnostics_tool,
    get_import_graph_tool,
    get_project_tree,
    get_symbols_tool,
    impact_analysis_tool,
    open_project,
    render_diagram_tool,
)

mcp = FastMCP("codimension")
_state = WorkspaceState()

register_resources(mcp, lambda: _state)
register_prompts(mcp)


@mcp.tool()
def open_project_tool(path: str) -> str:
    """Open a Python project directory for analysis."""
    _state.record_tool("open_project")
    try:
        return open_project(_state, path)
    except Exception as exc:  # noqa: BLE001
        return format_tool_error(exc)


@mcp.tool()
def analyze_project_tool() -> str:
    """Analyze all Python files in the open project."""
    _state.record_tool("analyze_project")
    try:
        return analyze_project(_state)
    except Exception as exc:  # noqa: BLE001
        return format_tool_error(exc)


@mcp.tool()
def analyze_file(path: str) -> str:
    """Analyze one Python file and return symbol Graph IR."""
    _state.record_tool("analyze_file")
    try:
        return analyze_file_tool(_state, path)
    except Exception as exc:  # noqa: BLE001
        return format_tool_error(exc)


@mcp.tool()
def get_project_tree_tool() -> str:
    """Return relative paths of Python files in the open project."""
    _state.record_tool("get_project_tree")
    try:
        return get_project_tree(_state)
    except Exception as exc:  # noqa: BLE001
        return format_tool_error(exc)


@mcp.tool()
def get_symbols(path: str | None = None) -> str:
    """Return symbol Graph IR for one file or the whole project."""
    _state.record_tool("get_symbols")
    try:
        return get_symbols_tool(_state, path)
    except Exception as exc:  # noqa: BLE001
        return format_tool_error(exc)


@mcp.tool()
def get_import_graph() -> str:
    """Return import dependency Graph IR for the open project."""
    _state.record_tool("get_import_graph")
    try:
        return get_import_graph_tool(_state)
    except Exception as exc:  # noqa: BLE001
        return format_tool_error(exc)


@mcp.tool()
def get_call_graph(symbol: str | None = None) -> str:
    """Return static call graph for the open project."""
    _state.record_tool("get_call_graph")
    try:
        return get_call_graph_tool(_state, symbol)
    except Exception as exc:  # noqa: BLE001
        return format_tool_error(exc)


@mcp.tool()
def get_control_flow(function_id: str) -> str:
    """Return control-flow Graph IR for file.py:function:name."""
    _state.record_tool("get_control_flow")
    try:
        return get_control_flow_tool(_state, function_id)
    except Exception as exc:  # noqa: BLE001
        return format_tool_error(exc)


@mcp.tool()
def find_callers(symbol: str) -> str:
    """Find callers of a symbol."""
    _state.record_tool("find_callers")
    try:
        return find_callers_tool(_state, symbol)
    except Exception as exc:  # noqa: BLE001
        return format_tool_error(exc)


@mcp.tool()
def find_callees(symbol: str) -> str:
    """Find callees called by a symbol."""
    _state.record_tool("find_callees")
    try:
        return find_callees_tool(_state, symbol)
    except Exception as exc:  # noqa: BLE001
        return format_tool_error(exc)


@mcp.tool()
def get_diagnostics(path: str) -> str:
    """Return lint and complexity diagnostics for one Python file."""
    _state.record_tool("get_diagnostics")
    try:
        return get_diagnostics_tool(_state, path)
    except Exception as exc:  # noqa: BLE001
        return format_tool_error(exc)


@mcp.tool()
def find_usages(symbol: str) -> str:
    """Find usages of a symbol in the open project."""
    _state.record_tool("find_usages")
    try:
        return find_usages_tool(_state, symbol)
    except Exception as exc:  # noqa: BLE001
        return format_tool_error(exc)


@mcp.tool()
def find_dead_code(path: str | None = None) -> str:
    """Run vulture dead-code analysis on the project or one file/directory."""
    _state.record_tool("find_dead_code")
    try:
        return find_dead_code_tool(_state, path)
    except Exception as exc:  # noqa: BLE001
        return format_tool_error(exc)


@mcp.tool()
def explain_symbol(symbol: str) -> str:
    """Return structured explanation context (symbols, usages, callers, CFG) for a symbol."""
    _state.record_tool("explain_symbol")
    try:
        return explain_symbol_tool(_state, symbol)
    except Exception as exc:  # noqa: BLE001
        return format_tool_error(exc)


@mcp.tool()
def get_cache_stats() -> str:
    """Return incremental analysis cache hit/miss statistics."""
    _state.record_tool("get_cache_stats")
    try:
        return get_cache_stats_tool(_state)
    except Exception as exc:  # noqa: BLE001
        return format_tool_error(exc)


@mcp.tool()
def render_diagram(kind: str, target: str | None = None) -> str:
    """Render import/call/control_flow/impact graph as HTML for Cursor WebView."""
    _state.record_tool("render_diagram")
    try:
        return render_diagram_tool(_state, kind, target)
    except Exception as exc:  # noqa: BLE001
        return format_tool_error(exc)


@mcp.tool()
def impact_analysis(target: str) -> str:
    """Estimate change blast radius."""
    _state.record_tool("impact_analysis")
    try:
        return impact_analysis_tool(_state, target)
    except Exception as exc:  # noqa: BLE001
        return format_tool_error(exc)


def main() -> None:
    """CLI entry: codimension-mcp --workspace /path."""
    parser = argparse.ArgumentParser(description="Codimension MCP analysis server")
    parser.add_argument(
        "--workspace",
        help="Project root to open automatically at startup",
    )
    args, remaining = parser.parse_known_args()
    if args.workspace:
        open_project(_state, args.workspace)
    if remaining:
        sys.argv = [sys.argv[0], *remaining]
    mcp.run()


if __name__ == "__main__":
    main()
