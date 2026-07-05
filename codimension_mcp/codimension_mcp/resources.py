# -*- coding: utf-8 -*-
"""MCP resources exposing cached project analysis context."""

from __future__ import annotations

from collections.abc import Callable

from codimension_core import build_call_graph, build_import_graph
from mcp.server.fastmcp import FastMCP

from .diagrams import read_diagram_html
from .schemas import WorkspaceState
from .serializers import dumps_graph, dumps_payload


def read_workspace_status(state: WorkspaceState) -> str:
    """Return workspace status JSON for MCP resource consumers."""
    if state.project is None:
        return dumps_payload({"status": "closed", "workspace": state.workspace or None})
    return dumps_payload(
        {
            "status": "open",
            "workspace": state.project.root,
            "python_files": len(state.project.python_files),
            "analyzed_files": state.analyzed_files,
            "tool_calls": dict(state.tool_calls),
        }
    )


def read_import_graph(state: WorkspaceState) -> str:
    if state.project is None:
        return dumps_payload({"status": "error", "error": "Call open_project(path) first"})
    return dumps_graph(build_import_graph(state.project))


def read_call_graph(state: WorkspaceState) -> str:
    if state.project is None:
        return dumps_payload({"status": "error", "error": "Call open_project(path) first"})
    return dumps_graph(build_call_graph(state.project))


def read_cache_stats(state: WorkspaceState) -> str:
    if state.project is None:
        return dumps_payload({"status": "closed"})
    return dumps_payload(state.project.get_cache_stats())


def register_resources(mcp: FastMCP, get_state: Callable[[], WorkspaceState]) -> None:
    """Register codimension:// resources on the MCP server."""

    @mcp.resource(
        "codimension://workspace/status",
        name="workspace_status",
        description="Open workspace path, python file count, and analysis counters.",
        mime_type="application/json",
    )
    def workspace_status() -> str:
        return read_workspace_status(get_state())

    @mcp.resource(
        "codimension://graph/import",
        name="import_graph",
        description="Resolved import dependency graph for the open project.",
        mime_type="application/json",
    )
    def import_graph_resource() -> str:
        return read_import_graph(get_state())

    @mcp.resource(
        "codimension://graph/call",
        name="call_graph",
        description="Static call graph for the open project.",
        mime_type="application/json",
    )
    def call_graph_resource() -> str:
        return read_call_graph(get_state())

    @mcp.resource(
        "codimension://diagram/import",
        name="diagram_import",
        description="HTML import diagram from full ImportDiagramModel (classes/imports resolution).",
        mime_type="text/html",
    )
    def diagram_import_resource() -> str:
        return read_diagram_html(get_state(), "import")

    @mcp.resource(
        "codimension://diagram/call",
        name="diagram_call",
        description="HTML/SVG call graph for Cursor WebView.",
        mime_type="text/html",
    )
    def diagram_call_resource() -> str:
        return read_diagram_html(get_state(), "call")

    @mcp.resource(
        "codimension://cache/stats",
        name="cache_stats",
        description="Incremental analysis cache statistics.",
        mime_type="application/json",
    )
    def cache_stats_resource() -> str:
        return read_cache_stats(get_state())
