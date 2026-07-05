# -*- coding: utf-8 -*-
"""Static inter-procedural call graph (AST-based, project scope)."""

from __future__ import annotations

import ast
from dataclasses import dataclass, field
from os.path import basename, realpath

from .graph_ir import GraphEdge, GraphIR, GraphNode
from .project import Project
from .symbols import _symbol_id


@dataclass
class _FunctionSpan:
    qualname: str
    file_path: str
    line_start: int
    line_end: int


@dataclass
class _CallGraphIndex:
    functions: dict[str, _FunctionSpan] = field(default_factory=dict)
    local_names: dict[str, dict[str, str]] = field(default_factory=dict)
    import_map: dict[str, dict[str, str]] = field(default_factory=dict)
    edges: list[tuple[str, str, int, str]] = field(default_factory=list)


def _collect_function_spans(info: object, file_path: str, prefix: str = "") -> list[_FunctionSpan]:
    spans: list[_FunctionSpan] = []
    for fn in getattr(info, "functions", []):
        name = f"{prefix}{fn.name}" if not prefix else f"{prefix}.{fn.name}"
        spans.append(
            _FunctionSpan(
                qualname=name,
                file_path=file_path,
                line_start=fn.line,
                line_end=getattr(fn, "colonLine", fn.line),
            )
        )
        for nested in getattr(fn, "functions", []):
            spans.append(
                _FunctionSpan(
                    qualname=f"{name}.{nested.name}",
                    file_path=file_path,
                    line_start=nested.line,
                    line_end=getattr(nested, "colonLine", nested.line),
                )
            )
    for cls in getattr(info, "classes", []):
        cls_prefix = f"{prefix}{cls.name}" if not prefix else f"{prefix}.{cls.name}"
        for method in getattr(cls, "functions", []):
            spans.append(
                _FunctionSpan(
                    qualname=f"{cls_prefix}.{method.name}",
                    file_path=file_path,
                    line_start=method.line,
                    line_end=getattr(method, "colonLine", method.line),
                )
            )
    return spans


def _build_import_map(info: object) -> dict[str, str]:
    mapping: dict[str, str] = {}
    for import_obj in getattr(info, "imports", []):
        if import_obj.what:
            module = import_obj.name
            for what in import_obj.what:
                alias = what.alias or what.name
                mapping[alias] = f"{module}.{what.name}" if module else what.name
        else:
            alias = import_obj.alias or import_obj.name.split(".")[0]
            mapping[alias] = import_obj.name
    return mapping


def _function_for_line(spans: list[_FunctionSpan], line: int) -> _FunctionSpan | None:
    matches = [span for span in spans if span.line_start <= line <= span.line_end]
    if not matches:
        return None
    return max(matches, key=lambda span: span.line_start)


def _callee_symbol_id(project: Project, caller_file: str, callee_name: str, index: _CallGraphIndex) -> str | None:
    local = index.local_names.get(caller_file, {})
    if callee_name in local:
        target = local[callee_name]
        return _symbol_id(caller_file, "function", target)

    import_map = index.import_map.get(caller_file, {})
    if callee_name in import_map:
        imported = import_map[callee_name]
        top = imported.split(".")[0]
        for path in project.python_files:
            if basename(path) == f"{top}.py":
                return _symbol_id(path, "function", imported.split(".")[-1])
        return f"external:function:{imported}"

    for path in project.python_files:
        if basename(path) == f"{callee_name}.py":
            return _symbol_id(path, "module", callee_name)
    return f"external:function:{callee_name}"


def _extract_calls(
    tree: ast.AST,
    spans: list[_FunctionSpan],
    caller_file: str,
    project: Project,
    index: _CallGraphIndex,
) -> None:
    for node in ast.walk(tree):
        if not isinstance(node, ast.Call):
            continue
        span = _function_for_line(spans, node.lineno)
        if span is None:
            continue
        caller_id = _symbol_id(caller_file, "function", span.qualname)
        callee_name, label = _call_target_name(node)
        if not callee_name:
            continue
        callee_id = _callee_symbol_id(project, caller_file, callee_name, index)
        if callee_id is None:
            continue
        index.edges.append((caller_id, callee_id, node.lineno, label))


def _call_target_name(node: ast.Call) -> tuple[str | None, str]:
    func = node.func
    if isinstance(func, ast.Name):
        return func.id, func.id
    if isinstance(func, ast.Attribute):
        value_name = ""
        if isinstance(func.value, ast.Name):
            value_name = func.value.id
        label = f"{value_name}.{func.attr}" if value_name else func.attr
        return func.attr, label
    return None, ""


def _build_index(project: Project) -> _CallGraphIndex:
    index = _CallGraphIndex()
    for file_path in project.python_files:
        info = project.cache.get(file_path)
        spans = _collect_function_spans(info, file_path)
        index.local_names[file_path] = {span.qualname.split(".")[-1]: span.qualname for span in spans}
        index.import_map[file_path] = _build_import_map(info)
        for span in spans:
            symbol = _symbol_id(file_path, "function", span.qualname)
            index.functions[symbol] = span
        with open(file_path, encoding="utf-8", errors="replace") as handle:
            source = handle.read()
        try:
            tree = ast.parse(source, filename=file_path)
        except SyntaxError:
            continue
        _extract_calls(tree, spans, file_path, project, index)
    return index


def _index_to_graph(index: _CallGraphIndex, symbol_filter: str | None = None) -> GraphIR:
    graph = GraphIR(meta={"kind": "call_graph"})
    for symbol, span in index.functions.items():
        if symbol_filter and symbol_filter not in symbol and span.qualname != symbol_filter:
            continue
        graph.add_node(
            GraphNode(
                id=symbol,
                type="function",
                name=span.qualname,
                file=span.file_path,
                line_start=span.line_start,
                line_end=span.line_end,
            )
        )

    for caller_id, callee_id, line_no, label in index.edges:
        if symbol_filter and symbol_filter not in (caller_id, callee_id):
            if not (
                caller_id.endswith(f":function:{symbol_filter}")
                or callee_id.endswith(f":function:{symbol_filter}")
            ):
                continue
        if caller_id.startswith("external:"):
            graph.add_node(
                GraphNode(
                    id=caller_id,
                    type="external_function",
                    name=caller_id.split(":", 2)[-1],
                    file="",
                    line_start=0,
                    line_end=0,
                )
            )
        if callee_id.startswith("external:"):
            graph.add_node(
                GraphNode(
                    id=callee_id,
                    type="external_function",
                    name=callee_id.split(":", 2)[-1],
                    file="",
                    line_start=0,
                    line_end=0,
                )
            )
        if caller_id in index.functions or caller_id.startswith("external:"):
            if callee_id in index.functions or callee_id.startswith("external:"):
                graph.add_edge(
                    GraphEdge(
                        from_id=caller_id,
                        to_id=callee_id,
                        type="calls",
                        label=f"{label}:{line_no}",
                    )
                )
    return graph


def build_call_graph(project: Project, symbol: str | None = None) -> GraphIR:
    """Build a static call graph for the open project."""
    project.require_open()
    index = _build_index(project)
    return _index_to_graph(index, symbol)


def find_callers(project: Project, symbol: str) -> GraphIR:
    """Return call edges where the given symbol is the callee."""
    project.require_open()
    index = _build_index(project)
    graph = GraphIR(meta={"kind": "callers", "symbol": symbol})
    for caller_id, callee_id, line_no, label in index.edges:
        if symbol in callee_id or callee_id.endswith(f":function:{symbol}"):
            graph.add_edge(
                GraphEdge(from_id=caller_id, to_id=callee_id, type="calls", label=f"{label}:{line_no}")
            )
            for node_id in (caller_id, callee_id):
                if node_id in index.functions:
                    span = index.functions[node_id]
                    graph.add_node(
                        GraphNode(
                            id=node_id,
                            type="function",
                            name=span.qualname,
                            file=span.file_path,
                            line_start=span.line_start,
                            line_end=span.line_end,
                        )
                    )
    return graph


def find_callees(project: Project, symbol: str) -> GraphIR:
    """Return call edges where the given symbol is the caller."""
    project.require_open()
    index = _build_index(project)
    graph = GraphIR(meta={"kind": "callees", "symbol": symbol})
    for caller_id, callee_id, line_no, label in index.edges:
        if symbol in caller_id or caller_id.endswith(f":function:{symbol}"):
            graph.add_edge(
                GraphEdge(from_id=caller_id, to_id=callee_id, type="calls", label=f"{label}:{line_no}")
            )
            for node_id in (caller_id, callee_id):
                if node_id in index.functions:
                    span = index.functions[node_id]
                    graph.add_node(
                        GraphNode(
                            id=node_id,
                            type="function",
                            name=span.qualname,
                            file=span.file_path,
                            line_start=span.line_start,
                            line_end=span.line_end,
                        )
                    )
    return graph


def impact_analysis(project: Project, target: str) -> GraphIR:
    """Estimate blast radius using reverse call edges and import dependents."""
    project.require_open()
    from .dependency_graph import build_import_graph

    call_index = _build_index(project)
    import_graph = build_import_graph(project)
    graph = GraphIR(meta={"kind": "impact_analysis", "target": target})

    impacted: set[str] = set()
    if target.endswith(".py"):
        target_file = realpath(target) if target.startswith("/") else None
        if target_file is None:
            for path in project.python_files:
                if basename(path) == target or path.endswith("/" + target):
                    target_file = path
                    break
        if target_file:
            impacted.add(f"file:{basename(target_file)}")
            for edge in import_graph.edges:
                if edge.to_id == f"file:{basename(target_file)}":
                    impacted.add(edge.from_id)
    else:
        for caller_id, callee_id, line_no, label in call_index.edges:
            if target in callee_id or callee_id.endswith(f":function:{target}"):
                impacted.add(caller_id)
                graph.add_edge(
                    GraphEdge(from_id=caller_id, to_id=callee_id, type="impacted_by_call", label=label)
                )

    for node_id in sorted(impacted):
        graph.add_node(
            GraphNode(
                id=node_id,
                type="impact",
                name=node_id,
                file=target,
                line_start=0,
                line_end=0,
            )
        )
    return graph
