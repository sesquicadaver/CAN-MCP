# -*- coding: utf-8 -*-
"""Import dependency graph — brief and resolved modes."""

from __future__ import annotations

import sys
from os.path import basename, realpath

from .graph_ir import GraphEdge, GraphIR, GraphNode
from .imports import build_import_context, classify_resolution, get_import_resolutions
from .project import Project


def build_import_graph(project: Project, *, resolved: bool = True) -> GraphIR:
    """Build import graph; resolved=True uses ImportResolution."""
    project.require_open()

    def builder() -> GraphIR:
        if resolved:
            return _build_resolved_import_graph(project)
        return _build_brief_import_graph(project)

    return project.analysis_cache.get_or_build_import_graph(project.python_files, builder)


def _build_brief_import_graph(project: Project) -> GraphIR:
    graph = GraphIR(meta={"kind": "import_graph", "resolved": False})
    file_by_stem: dict[str, str] = {}
    for path in project.python_files:
        stem = basename(path)[:-3]
        file_by_stem[stem] = path
        _add_file_node(graph, path)

    for path in project.python_files:
        info = project.cache.get(path)
        source_id = f"file:{basename(path)}"
        for import_obj in getattr(info, "imports", []):
            module_name = _import_module_name(import_obj)
            if not module_name:
                continue
            top_level = module_name.split(".")[0]
            target_path = file_by_stem.get(top_level)
            if target_path is None:
                target_id = f"module:{module_name}"
                graph.add_node(
                    GraphNode(
                        id=target_id,
                        type="external_module",
                        name=module_name,
                        file="",
                        line_start=0,
                        line_end=0,
                    )
                )
            else:
                target_id = f"file:{basename(target_path)}"
            graph.add_edge(
                GraphEdge(
                    from_id=source_id,
                    to_id=target_id,
                    type="imports",
                    label=_import_label(import_obj),
                )
            )
    return graph


def _build_resolved_import_graph(project: Project) -> GraphIR:
    graph = GraphIR(meta={"kind": "import_graph", "resolved": True})
    path_by_base: dict[str, str] = {}
    for path in project.python_files:
        _add_file_node(graph, path)
        path_by_base[basename(path)] = path

    for path in project.python_files:
        info = project.cache.get(path)
        context = build_import_context(project, path)
        source_id = f"file:{basename(path)}"
        for resolution in get_import_resolutions(context, path, info.imports):
            bucket = classify_resolution(resolution, path, project, sys.path)
            if bucket == "other":
                bucket = "unresolved"
            target_id = _resolution_target_id(resolution, project, path_by_base, graph, bucket)
            graph.add_edge(
                GraphEdge(
                    from_id=source_id,
                    to_id=target_id,
                    type="imports",
                    label=resolution.getVisibleName(),
                )
            )
    return graph


def _add_file_node(graph: GraphIR, path: str) -> None:
    graph.add_node(
        GraphNode(
            id=f"file:{basename(path)}",
            type="file",
            name=basename(path),
            file=path,
            line_start=1,
            line_end=1,
        )
    )


def _resolution_target_id(
    resolution: object,
    project: Project,
    path_by_base: dict[str, str],
    graph: GraphIR,
    classification: str,
) -> str:
    if resolution.builtIn:
        node_id = f"builtin:{resolution.importObj.name}"
        graph.add_node(
            GraphNode(
                id=node_id,
                type="builtin_module",
                name=resolution.importObj.name,
                file="",
                line_start=0,
                line_end=0,
                extra={"classification": classification},
            )
        )
        return node_id
    if resolution.path:
        resolved = realpath(resolution.path)
        base = basename(resolved)
        if base.endswith(".py") and project.is_project_path(resolved):
            node_id = f"file:{base}"
            if node_id not in {node.id for node in graph.nodes}:
                _add_file_node(graph, resolved)
        else:
            node_id = f"resolved:{resolved}"
            graph.add_node(
                GraphNode(
                    id=node_id,
                    type="resolved_module",
                    name=base,
                    file=resolved,
                    line_start=0,
                    line_end=0,
                    extra={"classification": classification},
                )
            )
        return node_id
    node_id = f"unresolved:{resolution.getVisibleName()}:{resolution.importObj.line}"
    graph.add_node(
        GraphNode(
            id=node_id,
            type="unresolved_import",
            name=resolution.getVisibleName(),
            file="",
            line_start=resolution.importObj.line,
            line_end=resolution.importObj.line,
            extra={"error": resolution.errMessage or "", "classification": classification},
        )
    )
    return node_id


def _import_module_name(import_obj: object) -> str:
    if getattr(import_obj, "what", None):
        return getattr(import_obj, "name", "") or ""
    return getattr(import_obj, "name", "") or ""


def _import_label(import_obj: object) -> str:
    if getattr(import_obj, "what", None):
        items = import_obj.what
        if len(items) == 1:
            return items[0].name
        return ", ".join(item.name for item in items)
    return getattr(import_obj, "name", "") or "import"
