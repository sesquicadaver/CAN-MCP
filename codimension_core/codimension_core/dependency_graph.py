# -*- coding: utf-8 -*-
"""Import dependency graph — brief and resolved modes."""

from __future__ import annotations

import sys
from os.path import basename, realpath
from typing import cast

from .graph_ir import GraphEdge, GraphIR, GraphNode, enrich_graph_meta
from .imports import (
    ImportResolution,
    _is_stdlib_module_name,
    build_import_context,
    classify_resolution,
    get_import_resolutions,
)
from .parser_types import BriefImport, BriefModuleInfo
from .project import Project
from .symbols import build_module_to_file, file_node_id, resolve_module_to_file


def _import_edge_kind(classification: str) -> str:
    return {
        "system": "stdlib",
        "project": "project",
        "other": "third_party",
        "unresolved": "unresolved",
    }.get(classification, "unresolved")


def _brief_import_kind(module_name: str, target_path: str | None) -> str:
    if target_path:
        return "project"
    top_level = module_name.split(".")[0]
    if top_level in sys.builtin_module_names or _is_stdlib_module_name(module_name):
        return "stdlib"
    return "third_party"


def build_import_graph(project: Project, *, resolved: bool = True) -> GraphIR:
    """Build import graph; resolved=True uses ImportResolution."""
    project.require_open()

    def builder() -> GraphIR:
        if resolved:
            return _build_resolved_import_graph(project)
        return _build_brief_import_graph(project)

    return project.analysis_cache.get_or_build_import_graph(
        project.python_files,
        builder,
        refresh=lambda: project.analysis_cache.refresh_signatures(project.python_files, project.cache),
    )


def _build_brief_import_graph(project: Project) -> GraphIR:
    graph = GraphIR(meta={"kind": "import_graph", "resolved": False})
    module_to_file = build_module_to_file(project)
    for path in project.python_files:
        _add_file_node(graph, project, path)

    for path in project.python_files:
        info = cast(BriefModuleInfo, project.cache.get(path))
        source_id = file_node_id(project, path)
        for import_obj in info.imports:
            module_name = _import_module_name(import_obj)
            if not module_name:
                continue
            normalized = module_name.lstrip(".")
            target_path = resolve_module_to_file(normalized, module_to_file)
            if target_path is None:
                target_id = f"module:{normalized}"
                graph.add_node(
                    GraphNode(
                        id=target_id,
                        type="external_module",
                        name=normalized,
                        file="",
                        line_start=0,
                        line_end=0,
                    )
                )
            else:
                target_id = file_node_id(project, target_path)
            graph.add_edge(
                GraphEdge(
                    from_id=source_id,
                    to_id=target_id,
                    type="imports",
                    label=_import_label(import_obj),
                    extra={"kind": _brief_import_kind(module_name, target_path)},
                )
            )
    return enrich_graph_meta(graph, project_root=project.root)


def _build_resolved_import_graph(project: Project) -> GraphIR:
    graph = GraphIR(meta={"kind": "import_graph", "resolved": True})
    path_by_base: dict[str, str] = {}
    for path in project.python_files:
        _add_file_node(graph, project, path)
        path_by_base[basename(path)] = path

    for path in project.python_files:
        info = cast(BriefModuleInfo, project.cache.get(path))
        context = build_import_context(project, path)
        source_id = file_node_id(project, path)
        for resolution in get_import_resolutions(context, path, info.imports):
            bucket = classify_resolution(resolution, path, project, sys.path)
            target_bucket = "unresolved" if bucket == "other" else bucket
            target_id = _resolution_target_id(resolution, project, path_by_base, graph, target_bucket)
            graph.add_edge(
                GraphEdge(
                    from_id=source_id,
                    to_id=target_id,
                    type="imports",
                    label=resolution.getVisibleName(),
                    extra={"kind": _import_edge_kind(bucket)},
                )
            )
    return enrich_graph_meta(graph, project_root=project.root)


def _add_file_node(graph: GraphIR, project: Project, path: str) -> None:
    rel_path = project.to_relative_path(path)
    graph.add_node(
        GraphNode(
            id=file_node_id(project, path),
            type="file",
            name=basename(path),
            file=path,
            line_start=1,
            line_end=1,
            extra={"rel_path": rel_path},
        )
    )


def _resolution_target_id(
    resolution: ImportResolution,
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
            node_id = file_node_id(project, resolved)
            if node_id not in {node.id for node in graph.nodes}:
                _add_file_node(graph, project, resolved)
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


def _import_module_name(import_obj: BriefImport) -> str:
    if import_obj.what:
        return import_obj.name or ""
    return import_obj.name or ""


def _import_label(import_obj: BriefImport) -> str:
    if import_obj.what:
        items = import_obj.what
        if len(items) == 1:
            return items[0].name
        return ", ".join(item.name for item in items)
    return import_obj.name or "import"
