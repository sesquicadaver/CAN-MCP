# -*- coding: utf-8 -*-
"""Import dependency graph builder (MVP — brief parser imports only)."""

from __future__ import annotations

from os.path import basename

from .graph_ir import GraphEdge, GraphIR, GraphNode
from .project import Project


def build_import_graph(project: Project) -> GraphIR:
    """Build import edges between project files using brief import statements."""
    project.require_open()
    graph = GraphIR(meta={"kind": "import_graph"})
    file_by_stem: dict[str, str] = {}
    for path in project.python_files:
        stem = basename(path)[:-3]
        file_by_stem[stem] = path
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
                graph.add_node(
                    GraphNode(
                        id=f"module:{module_name}",
                        type="external_module",
                        name=module_name,
                        file="",
                        line_start=0,
                        line_end=0,
                    )
                )
                target_id = f"module:{module_name}"
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
