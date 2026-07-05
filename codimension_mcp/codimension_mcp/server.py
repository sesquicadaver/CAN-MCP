# -*- coding: utf-8 -*-
"""Codimension MCP server entry point."""

from __future__ import annotations

import argparse
import sys

from mcp.server.fastmcp import FastMCP

from .schemas import WorkspaceState
from .tools import (
    analyze_file_tool,
    analyze_project,
    find_callees_tool,
    find_callers_tool,
    find_usages_tool,
    format_tool_error,
    get_call_graph_tool,
    get_control_flow_tool,
    get_import_graph_tool,
    get_project_tree,
    get_symbols_tool,
    impact_analysis_tool,
    open_project,
)

mcp = FastMCP("codimension")
_state = WorkspaceState()


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
def find_usages(symbol: str) -> str:
    """Find usages of a symbol in the open project."""
    _state.record_tool("find_usages")
    try:
        return find_usages_tool(_state, symbol)
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
