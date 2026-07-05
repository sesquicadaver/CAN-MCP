# -*- coding: utf-8 -*-
"""Control-flow graph access via flow_ast fallback."""

from __future__ import annotations

from collections.abc import Sequence
from typing import cast

from .flow_ast import FUNCTION_FRAGMENT, getControlFlowFromFile, getControlFlowFromMemory
from .graph_ir import GraphEdge, GraphIR, GraphNode
from .project import Project


def get_control_flow(project: Project, function_id: str) -> GraphIR:
    """Return a CFG subgraph for ``file.py:function:name`` id."""
    project.require_open()
    file_path, fn_name = _parse_function_id(function_id, project)
    cached = project.analysis_cache.get_cfg(function_id, file_path)
    if cached is not None:
        return cached
    cflow = getControlFlowFromFile(file_path)
    fn_obj = _find_function(cast(Sequence[object], cflow.nsuite), fn_name)
    if fn_obj is None:
        raise ValueError(f"Function not found: {function_id}")
    graph = _function_to_graph(fn_obj, file_path, function_id)
    project.analysis_cache.store_cfg(function_id, file_path, graph)
    return graph


def get_control_flow_from_source(source: str, function_name: str, file_name: str = "<memory>") -> GraphIR:
    """Analyze in-memory source (tests)."""
    cflow = getControlFlowFromMemory(source)
    fn_obj = _find_function(cast(Sequence[object], cflow.nsuite), function_name)
    if fn_obj is None:
        raise ValueError(f"Function not found: {function_name}")
    function_id = f"{file_name}:function:{function_name}"
    return _function_to_graph(fn_obj, file_name, function_id)


def _parse_function_id(function_id: str, project: Project) -> tuple[str, str]:
    parts = function_id.split(":")
    if len(parts) < 3 or parts[1] != "function":
        raise ValueError("function_id must look like file.py:function:name")
    file_name = parts[0]
    fn_name = ":".join(parts[2:])
    for path in project.python_files:
        if path.endswith("/" + file_name) or path.endswith("\\" + file_name):
            return path, fn_name
    raise ValueError(f"File not found in project: {file_name}")


def _find_function(suite: Sequence[object], name: str) -> object | None:
    for node in suite:
        if getattr(node, "kind", None) == FUNCTION_FRAGMENT:
            fn_name = getattr(getattr(node, "name", None), "getContent", lambda: "")()
            if fn_name == name:
                return node
        nested = getattr(node, "nsuite", None)
        if nested:
            found = _find_function(cast(Sequence[object], nested), name)
            if found is not None:
                return found
    return None


def _line_range(node: object) -> tuple[int, int]:
    body = getattr(node, "body", None)
    if body is not None and hasattr(body, "getLineRange"):
        return cast(tuple[int, int], body.getLineRange())
    return (0, 0)


def _function_to_graph(fn_obj: object, file_path: str, function_id: str) -> GraphIR:
    start_line, end_line = _line_range(fn_obj)
    fn_name = getattr(getattr(fn_obj, "name", None), "getContent", lambda: "")()
    graph = GraphIR(meta={"kind": "control_flow", "function_id": function_id})
    root_id = f"{function_id}:entry"
    graph.add_node(
        GraphNode(
            id=root_id,
            type="cfg_entry",
            name=fn_name,
            file=file_path,
            line_start=start_line or 1,
            line_end=end_line or start_line or 1,
        )
    )
    _walk_cfg(getattr(fn_obj, "nsuite", []) or [], file_path, function_id, graph, root_id)
    return graph


def _walk_cfg(
    suite: list[object],
    file_path: str,
    function_id: str,
    graph: GraphIR,
    parent_id: str,
) -> None:
    for index, child in enumerate(suite):
        child_type = type(child).__name__
        start_line, end_line = _line_range(child)
        child_id = f"{function_id}:cfg:{child_type}:{index}:{start_line}"
        graph.add_node(
            GraphNode(
                id=child_id,
                type=f"cfg_{child_type.lower()}",
                name=child_type,
                file=file_path,
                line_start=start_line,
                line_end=end_line or start_line,
            )
        )
        graph.add_edge(GraphEdge(from_id=parent_id, to_id=child_id, type="cfg_flow"))
        nested = getattr(child, "nsuite", None)
        if nested:
            _walk_cfg(nested, file_path, function_id, graph, child_id)
