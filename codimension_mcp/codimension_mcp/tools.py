# -*- coding: utf-8 -*-
"""MCP tool implementations backed by codimension_core."""

from __future__ import annotations

import os

from codimension_core import (
    analyze_dead_code,
    analyze_file,
    analyze_file_diagnostics,
    build_import_graph,
    explain_symbol,
    find_usages,
    get_control_flow,
    get_symbols,
)
from codimension_core.callgraph import build_call_graph, find_callees, find_callers, impact_analysis
from codimension_core.errors import AnalysisError, NotImplementedYetError, ProjectNotOpenError
from codimension_core.project import Project

from .schemas import WorkspaceState
from .serializers import dumps_graph, dumps_payload


def _resolve_path(project: Project, path: str) -> str:
    if os.path.isabs(path):
        return os.path.realpath(path)
    return os.path.realpath(os.path.join(project.root, path))


def open_project(state: WorkspaceState, path: str) -> str:
    """Open a workspace directory."""
    project = Project.open(path)
    state.workspace = project.root
    state.project = project
    state.analyzed_files = 0
    return dumps_payload(
        {
            "status": "ok",
            "workspace": project.root,
            "python_files": len(project.python_files),
        }
    )


def analyze_project(state: WorkspaceState) -> str:
    """Warm caches for all project files."""
    project = _require_project(state)
    state.analyzed_files = project.analyze_all()
    return dumps_payload({"status": "ok", "analyzed_files": state.analyzed_files})


def analyze_file_tool(state: WorkspaceState, path: str) -> str:
    """Analyze one file and return symbol Graph IR."""
    project = _require_project(state)
    graph = analyze_file(project, _resolve_path(project, path))
    return dumps_graph(graph)


def get_project_tree(state: WorkspaceState) -> str:
    """Return relative python file paths."""
    project = _require_project(state)
    return dumps_payload({"files": project.get_project_tree()})


def get_symbols_tool(state: WorkspaceState, path: str | None = None) -> str:
    """Return symbol Graph IR for one file or whole project."""
    project = _require_project(state)
    resolved = _resolve_path(project, path) if path else None
    return dumps_graph(get_symbols(project, resolved))


def get_import_graph_tool(state: WorkspaceState) -> str:
    """Return import dependency Graph IR."""
    project = _require_project(state)
    return dumps_graph(build_import_graph(project))


def get_call_graph_tool(state: WorkspaceState, symbol: str | None = None) -> str:
    """Return static call graph."""
    project = _require_project(state)
    return dumps_graph(build_call_graph(project, symbol))


def get_control_flow_tool(state: WorkspaceState, function_id: str) -> str:
    """Return CFG Graph IR for a function id."""
    project = _require_project(state)
    return dumps_graph(get_control_flow(project, function_id))


def find_callers_tool(state: WorkspaceState, symbol: str) -> str:
    """Find callers of a symbol."""
    project = _require_project(state)
    return dumps_graph(find_callers(project, symbol))


def find_callees_tool(state: WorkspaceState, symbol: str) -> str:
    """Find callees of a symbol."""
    project = _require_project(state)
    return dumps_graph(find_callees(project, symbol))


def impact_analysis_tool(state: WorkspaceState, target: str) -> str:
    """Impact analysis for a path or symbol."""
    project = _require_project(state)
    return dumps_graph(impact_analysis(project, target))


def find_usages_tool(state: WorkspaceState, symbol: str) -> str:
    """Find usages of a symbol via jedi."""
    project = _require_project(state)
    return dumps_graph(find_usages(project, symbol))


def get_diagnostics_tool(state: WorkspaceState, path: str) -> str:
    """Return pyflakes/radon diagnostics for one file."""
    project = _require_project(state)
    return dumps_graph(analyze_file_diagnostics(project, _resolve_path(project, path)))


def find_dead_code_tool(state: WorkspaceState, path: str | None = None) -> str:
    """Run vulture dead-code analysis on the project or one path."""
    project = _require_project(state)
    resolved = _resolve_path(project, path) if path else None
    return dumps_graph(analyze_dead_code(project, resolved))


def explain_symbol_tool(state: WorkspaceState, symbol: str) -> str:
    """Return structured explanation context for a symbol."""
    project = _require_project(state)
    return dumps_graph(explain_symbol(project, symbol))


def _require_project(state: WorkspaceState) -> Project:
    if state.project is None:
        raise ProjectNotOpenError("Call open_project(path) first")
    return state.project


def format_tool_error(exc: Exception) -> str:
    """Convert core exceptions into MCP-friendly JSON errors."""
    if isinstance(exc, NotImplementedYetError):
        return dumps_payload({"status": "not_implemented", "error": str(exc)})
    if isinstance(exc, AnalysisError):
        return dumps_payload({"status": "error", "error": str(exc)})
    return dumps_payload({"status": "error", "error": f"{type(exc).__name__}: {exc}"})
