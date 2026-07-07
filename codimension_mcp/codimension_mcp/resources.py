# -*- coding: utf-8 -*-
"""MCP resources exposing cached project analysis context."""

from __future__ import annotations

from collections.abc import Callable

from codimension_core import build_call_graph, build_import_graph
from codimension_core.errors import AnalysisError, PathOutsideProjectError
from codimension_core.paths import resolve_project_path
from codimension_core.project import Project
from codimension_core.summaries import build_dependency_summary, build_symbol_summary
from mcp.server.fastmcp import FastMCP

from .catalog import read_mcp_catalog
from .diagrams import read_diagram_html
from .schemas import WorkspaceState
from .serializers import dumps_graph, dumps_payload


def _resolve_project_path(project: Project, path: str) -> str:
    return resolve_project_path(project, path)


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
        abs_path = _resolve_project_path(state.project, path)
        return dumps_payload(build_dependency_summary(state.project, abs_path))
    except PathOutsideProjectError as exc:
        return dumps_payload({"status": "error", "error": str(exc), "error_code": "path_outside_project"})
    except ValueError as exc:
        return dumps_payload({"status": "error", "error": str(exc)})


def read_file_symbol_summary(state: WorkspaceState, path: str) -> str:
    if state.project is None:
        return dumps_payload({"status": "error", "error": "Call open_project(path) first"})
    try:
        abs_path = _resolve_project_path(state.project, path)
        return dumps_payload(build_symbol_summary(state.project, abs_path))
    except PathOutsideProjectError as exc:
        return dumps_payload({"status": "error", "error": str(exc), "error_code": "path_outside_project"})
    except ValueError as exc:
        return dumps_payload({"status": "error", "error": str(exc)})


def encode_function_key(function_id: str) -> str:
    """Encode file.py:function:name for use in MCP resource URI path segments."""
    if ":function:" in function_id:
        file_part, name = function_id.split(":function:", 1)
        return f"{file_part.replace('/', '__path__')}__function__{name}"
    if ":class:" in function_id:
        file_part, name = function_id.split(":class:", 1)
        return f"{file_part.replace('/', '__path__')}__class__{name}"
    return function_id.replace("/", "__path__")


def decode_function_key(function_key: str) -> str:
    """Decode MCP resource function key back to a symbol id."""
    if "__function__" in function_key:
        file_part, name = function_key.split("__function__", 1)
        file_path = file_part.replace("__path__", "/")
        return f"{file_path}:function:{name}"
    if "__class__" in function_key:
        file_part, name = function_key.split("__class__", 1)
        file_path = file_part.replace("__path__", "/")
        return f"{file_path}:class:{name}"
    raise ValueError(f"Invalid function key: {function_key}")


def encode_impact_key(target: str) -> str:
    """Encode impact target (symbol id, file path, or bare name) for resource URIs."""
    if ":function:" in target or ":class:" in target:
        return encode_function_key(target)
    return target.replace("/", "__path__")


def decode_impact_key(target_key: str) -> str:
    """Decode impact resource key back to an impact_analysis target."""
    if "__function__" in target_key or "__class__" in target_key:
        return decode_function_key(target_key)
    return target_key.replace("__path__", "/")


def read_impact_graph(state: WorkspaceState, target_key: str) -> str:
    if state.project is None:
        return dumps_payload({"status": "error", "error": "Call open_project(path) first"})
    try:
        from codimension_core.callgraph import impact_analysis

        target = decode_impact_key(target_key)
        return dumps_graph(impact_analysis(state.project, target))
    except (ValueError, AnalysisError) as exc:
        return dumps_payload({"status": "error", "error": str(exc)})


def read_impact_diagram(state: WorkspaceState, target_key: str) -> str:
    if state.project is None:
        return dumps_payload({"status": "error", "error": "Call open_project(path) first"})
    try:
        target = decode_impact_key(target_key)
        return read_diagram_html(state, "impact", target)
    except ValueError as exc:
        return dumps_payload({"status": "error", "error": str(exc)})


def read_control_flow_graph(state: WorkspaceState, function_key: str) -> str:
    if state.project is None:
        return dumps_payload({"status": "error", "error": "Call open_project(path) first"})
    try:
        function_id = decode_function_key(function_key)
        from codimension_core.cfg import get_control_flow

        return dumps_graph(get_control_flow(state.project, function_id))
    except (ValueError, AnalysisError) as exc:
        return dumps_payload({"status": "error", "error": str(exc)})


def read_control_flow_diagram(state: WorkspaceState, function_key: str) -> str:
    if state.project is None:
        return dumps_payload({"status": "error", "error": "Call open_project(path) first"})
    try:
        function_id = decode_function_key(function_key)
        return read_diagram_html(state, "control_flow", function_id)
    except ValueError as exc:
        return dumps_payload({"status": "error", "error": str(exc)})


def register_resources(mcp: FastMCP, get_state: Callable[[], WorkspaceState]) -> None:
    """Register codimension:// resources on the MCP server."""

    @mcp.resource(
        "codimension://catalog",
        name="mcp_catalog",
        description="Machine-readable list of all Codimension MCP tools, resources, and prompts.",
        mime_type="application/json",
    )
    def mcp_catalog_resource() -> str:
        return read_mcp_catalog()

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

    @mcp.resource(
        "codimension://graph/control_flow/{function_key}",
        name="control_flow_graph",
        description="CFG Graph IR for a function (key: main.py__function__name).",
        mime_type="application/json",
    )
    def control_flow_graph_resource(function_key: str) -> str:
        return read_control_flow_graph(get_state(), function_key)

    @mcp.resource(
        "codimension://diagram/control_flow/{function_key}",
        name="control_flow_diagram",
        description="CFG HTML diagram for a function (key: main.py__function__name).",
        mime_type="text/html",
    )
    def control_flow_diagram_resource(function_key: str) -> str:
        return read_control_flow_diagram(get_state(), function_key)

    @mcp.resource(
        "codimension://graph/impact/{target_key}",
        name="impact_graph",
        description="Impact analysis Graph IR for symbol, file, or bare name.",
        mime_type="application/json",
    )
    def impact_graph_resource(target_key: str) -> str:
        return read_impact_graph(get_state(), target_key)

    @mcp.resource(
        "codimension://diagram/impact/{target_key}",
        name="impact_diagram",
        description="Impact analysis HTML diagram for symbol, file, or bare name.",
        mime_type="text/html",
    )
    def impact_diagram_resource(target_key: str) -> str:
        return read_impact_diagram(get_state(), target_key)
