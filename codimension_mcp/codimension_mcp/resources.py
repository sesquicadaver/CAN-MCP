# -*- coding: utf-8 -*-
"""MCP resources exposing cached project analysis context."""

from __future__ import annotations

import os
from collections.abc import Callable
from os.path import realpath

from codimension_core import build_call_graph, build_import_graph
from codimension_core.summaries import build_dependency_summary, build_symbol_summary
from mcp.server.fastmcp import FastMCP

from .diagrams import read_diagram_html
from .schemas import WorkspaceState
from .serializers import dumps_graph, dumps_payload


def _resolve_project_path(project_root: str, path: str) -> str:
    if os.path.isabs(path):
        return realpath(path)
    return realpath(os.path.join(project_root, path))


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


def read_project_tree(state: WorkspaceState) -> str:
    if state.project is None:
        return dumps_payload({"status": "error", "error": "Call open_project(path) first"})
    return dumps_payload({"files": state.project.get_project_tree()})


def read_dependency_summary(state: WorkspaceState) -> str:
    if state.project is None:
        return dumps_payload({"status": "error", "error": "Call open_project(path) first"})
    return dumps_payload(build_dependency_summary(state.project))


def read_symbol_summary(state: WorkspaceState) -> str:
    if state.project is None:
        return dumps_payload({"status": "error", "error": "Call open_project(path) first"})
    return dumps_payload(build_symbol_summary(state.project))


def read_file_dependency_summary(state: WorkspaceState, path: str) -> str:
    if state.project is None:
        return dumps_payload({"status": "error", "error": "Call open_project(path) first"})
    try:
        abs_path = _resolve_project_path(state.project.root, path)
        return dumps_payload(build_dependency_summary(state.project, abs_path))
    except ValueError as exc:
        return dumps_payload({"status": "error", "error": str(exc)})


def read_file_symbol_summary(state: WorkspaceState, path: str) -> str:
    if state.project is None:
        return dumps_payload({"status": "error", "error": "Call open_project(path) first"})
    try:
        abs_path = _resolve_project_path(state.project.root, path)
        return dumps_payload(build_symbol_summary(state.project, abs_path))
    except ValueError as exc:
        return dumps_payload({"status": "error", "error": str(exc)})


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

    @mcp.resource(
        "codimension://project/tree",
        name="project_tree",
        description="Relative paths of Python files in the open project.",
        mime_type="application/json",
    )
    def project_tree_resource() -> str:
        return read_project_tree(get_state())

    @mcp.resource(
        "codimension://deps/summary",
        name="dependency_summary",
        description="Classified import summary (system/project/unresolved) for the open project.",
        mime_type="application/json",
    )
    def dependency_summary_resource() -> str:
        return read_dependency_summary(get_state())

    @mcp.resource(
        "codimension://symbols/summary",
        name="symbol_summary",
        description="Symbol counts by type for the open project.",
        mime_type="application/json",
    )
    def symbol_summary_resource() -> str:
        return read_symbol_summary(get_state())

    @mcp.resource(
        "codimension://deps/file/{path}",
        name="dependency_file_summary",
        description="Classified import summary for one project file (relative path).",
        mime_type="application/json",
    )
    def dependency_file_resource(path: str) -> str:
        return read_file_dependency_summary(get_state(), path)

    @mcp.resource(
        "codimension://symbols/file/{path}",
        name="symbol_file_summary",
        description="Symbol counts for one project file (relative path).",
        mime_type="application/json",
    )
    def symbol_file_resource(path: str) -> str:
        return read_file_symbol_summary(get_state(), path)
