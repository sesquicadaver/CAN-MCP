# -*- coding: utf-8 -*-
"""Diagram export for Cursor WebView and MCP resources."""

from __future__ import annotations

import os
from os.path import join

from codimension_core import build_import_graph
from codimension_core.callgraph import build_call_graph, impact_analysis
from codimension_core.cfg import get_control_flow
from codimension_core.errors import AnalysisError
from codimension_core.graph_ir import GraphIR
from codimension_core.graph_render import graph_to_html, graph_to_mermaid

from .schemas import WorkspaceState
from .serializers import dumps_payload

DIAGRAM_KINDS = frozenset({"import", "call", "control_flow", "impact"})


def _require_project(state: WorkspaceState):
    if state.project is None:
        raise AnalysisError("Call open_project(path) first")
    return state.project


def _build_graph(state: WorkspaceState, kind: str, target: str | None) -> GraphIR:
    project = _require_project(state)
    if kind == "import":
        return build_import_graph(project)
    if kind == "call":
        return build_call_graph(project, target)
    if kind == "control_flow":
        if not target:
            raise AnalysisError("control_flow diagram requires target function_id")
        return get_control_flow(project, target)
    if kind == "impact":
        if not target:
            raise AnalysisError("impact diagram requires target path or symbol")
        return impact_analysis(project, target)
    raise AnalysisError(f"Unknown diagram kind: {kind}. Use: {', '.join(sorted(DIAGRAM_KINDS))}")


def _diagram_output_dir(project_root: str) -> str:
    output_dir = join(project_root, ".codimension", "diagrams")
    os.makedirs(output_dir, exist_ok=True)
    return output_dir


def render_diagram(state: WorkspaceState, kind: str, target: str | None = None) -> str:
    """Build graph, write HTML, return JSON payload with paths and mermaid."""
    if kind not in DIAGRAM_KINDS:
        raise AnalysisError(f"Unknown diagram kind: {kind}")
    project = _require_project(state)
    graph = _build_graph(state, kind, target)
    title = f"Codimension {kind} diagram"
    if target:
        title = f"{title}: {target}"
    html_body = graph_to_html(graph, title)
    mermaid = graph_to_mermaid(graph)
    suffix = target.replace("/", "_").replace(":", "_") if target else "project"
    file_name = f"{kind}-{suffix}.html"
    output_dir = _diagram_output_dir(project.root)
    html_path = join(output_dir, file_name)
    with open(html_path, "w", encoding="utf-8") as handle:
        handle.write(html_body)
    return dumps_payload(
        {
            "status": "ok",
            "kind": kind,
            "target": target,
            "html_path": html_path,
            "mermaid": mermaid,
            "nodes": len(graph.nodes),
            "edges": len(graph.edges),
            "webview_hint": f"Open {html_path} in Cursor Simple Browser or file preview",
        }
    )


def read_diagram_html(state: WorkspaceState, kind: str, target: str | None = None) -> str:
    """Return HTML for MCP resource consumers."""
    if kind not in DIAGRAM_KINDS:
        return dumps_payload({"status": "error", "error": f"Unknown diagram kind: {kind}"})
    try:
        graph = _build_graph(state, kind, target)
    except AnalysisError as exc:
        return dumps_payload({"status": "error", "error": str(exc)})
    title = f"Codimension {kind} diagram"
    if target:
        title = f"{title}: {target}"
    return graph_to_html(graph, title)
