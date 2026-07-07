# -*- coding: utf-8 -*-
"""Static inter-procedural call graph (AST-based, project scope)."""

from __future__ import annotations

import ast
from dataclasses import dataclass, field
from os.path import basename, realpath

from .graph_ir import GraphEdge, GraphIR, GraphNode, enrich_graph_meta, standard_symbol_extra
from .project import Project
from .symbol_registry import resolve_symbol_reference
from .symbols import symbol_id


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
    class_methods: dict[str, dict[str, str]] = field(default_factory=dict)
    file_to_module: dict[str, str] = field(default_factory=dict)
    module_to_file: dict[str, str] = field(default_factory=dict)
    edges: list[tuple[str, str, int, str, float]] = field(default_factory=list)


def _rel_file(project: Project, file_path: str) -> str:
    return project.to_relative_path(file_path)


def _file_to_module_name(rel_file: str) -> str:
    path = rel_file.replace("\\", "/")
    if path.endswith("/__init__.py"):
        return path[: -len("/__init__.py")].replace("/", ".")
    if path.endswith("__init__.py"):
        return path[: -len("__init__.py")].rstrip("/.").replace("/", ".")
    if path.endswith(".py"):
        return path[:-3].replace("/", ".")
    return path.replace("/", ".")



def _build_module_maps(project: Project) -> tuple[dict[str, str], dict[str, str]]:
    file_to_module: dict[str, str] = {}
    module_to_file: dict[str, str] = {}
    for abs_path in project.python_files:
        rel = _rel_file(project, abs_path)
        module = _file_to_module_name(rel)
        file_to_module[rel] = module
        if module not in module_to_file:
            module_to_file[module] = abs_path
    return file_to_module, module_to_file


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


def _build_class_methods(spans: list[_FunctionSpan]) -> dict[str, str]:
    methods: dict[str, str] = {}
    for span in spans:
        if "." in span.qualname:
            methods[span.qualname.split(".")[-1]] = span.qualname
    return methods


def _resolve_relative_module(current_module: str, module: str | None, level: int) -> str:
    if level == 0:
        return module or ""
    parts = current_module.split(".") if current_module else []
    if level > len(parts):
        base_parts: list[str] = []
    else:
        base_parts = parts[:-level] if level else parts
    if module:
        return ".".join(base_parts + module.split("."))
    return ".".join(base_parts)


def _build_import_map_brief(info: object) -> dict[str, str]:
    mapping: dict[str, str] = {}
    for import_obj in getattr(info, "imports", []):
        module = import_obj.name or ""
        if import_obj.what:
            for what in import_obj.what:
                alias = what.alias or what.name
                if module.startswith("."):
                    mapping[alias] = f"{module.lstrip('.')}.{what.name}" if module != "." else what.name
                else:
                    mapping[alias] = f"{module}.{what.name}" if module else what.name
        else:
            alias = import_obj.alias or module.split(".")[0]
            mapping[alias] = module
    return mapping


def _build_import_map_ast(
    project: Project,
    rel_path: str,
    tree: ast.AST,
    file_to_module: dict[str, str],
) -> dict[str, str]:
    mapping: dict[str, str] = {}
    current_module = file_to_module.get(rel_path, "")
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                name = alias.asname or alias.name.split(".")[0]
                mapping[name] = alias.name
        elif isinstance(node, ast.ImportFrom):
            module_name = _resolve_relative_module(current_module, node.module, node.level)
            for alias in node.names:
                if alias.name == "*":
                    continue
                local = alias.asname or alias.name
                mapping[local] = f"{module_name}.{alias.name}" if module_name else alias.name
    return mapping


def _merge_import_maps(*maps: dict[str, str]) -> dict[str, str]:
    merged: dict[str, str] = {}
    for item in maps:
        merged.update(item)
    return merged


def _resolve_import_target(project: Project, index: _CallGraphIndex, qualified: str) -> str | None:
    parts = qualified.split(".")
    for split_at in range(len(parts), 0, -1):
        module_name = ".".join(parts[:split_at])
        remainder = ".".join(parts[split_at:])
        abs_path = index.module_to_file.get(module_name)
        if abs_path is None:
            continue
        if not remainder:
            return symbol_id(project, abs_path, "module", module_name.split(".")[-1])
        return symbol_id(project, abs_path, "function", remainder)
    return None


def _function_for_line(spans: list[_FunctionSpan], line: int) -> _FunctionSpan | None:
    matches = [span for span in spans if span.line_start <= line <= span.line_end]
    if not matches:
        return None
    return max(matches, key=lambda span: span.line_start)


def _resolve_method_callee(
    span: _FunctionSpan,
    attr_name: str,
    index: _CallGraphIndex,
) -> str | None:
    if "." not in span.qualname:
        return None
    class_name = span.qualname.rsplit(".", 1)[0]
    method_qual = f"{class_name}.{attr_name}"
    for fn_id, fn_span in index.functions.items():
        if fn_span.qualname == method_qual:
            return fn_id
    return None


def _callee_symbol_id(
    project: Project,
    rel_path: str,
    abs_path: str,
    callee_name: str,
    index: _CallGraphIndex,
    *,
    receiver: str | None = None,
    span: _FunctionSpan | None = None,
) -> tuple[str | None, float]:
    if receiver == "self" and span is not None:
        resolved = _resolve_method_callee(span, callee_name, index)
        if resolved:
            return resolved, 0.85

    local = index.local_names.get(rel_path, {})
    if callee_name in local:
        return symbol_id(project, abs_path, "function", local[callee_name]), 0.9

    import_map = index.import_map.get(rel_path, {})
    if callee_name in import_map:
        imported = import_map[callee_name]
        if imported.startswith("."):
            current_module = index.file_to_module.get(rel_path, "")
            resolved_module = _resolve_relative_module(current_module, imported.lstrip("."), 1)
            imported = f"{resolved_module}.{callee_name}" if resolved_module else callee_name
        resolved = _resolve_import_target(project, index, imported)
        if resolved:
            return resolved, 0.8
        return f"external:function:{imported}", 0.5

    for path in project.python_files:
        rel = _rel_file(project, path)
        module = index.file_to_module.get(rel, "")
        if module.endswith(f".{callee_name}") or rel.endswith(f"/{callee_name}.py"):
            return symbol_id(project, path, "module", callee_name), 0.6
    return f"external:function:{callee_name}", 0.3


def _extract_calls(
    tree: ast.AST,
    spans: list[_FunctionSpan],
    rel_path: str,
    abs_path: str,
    project: Project,
    index: _CallGraphIndex,
) -> None:
    for node in ast.walk(tree):
        if not isinstance(node, ast.Call):
            continue
        span = _function_for_line(spans, node.lineno)
        if span is None:
            continue
        caller_id = symbol_id(project, abs_path, "function", span.qualname)
        callee_name, label, receiver = _call_target_name(node)
        if not callee_name:
            continue
        callee_id, confidence = _callee_symbol_id(
            project,
            rel_path,
            abs_path,
            callee_name,
            index,
            receiver=receiver,
            span=span,
        )
        if callee_id is None:
            continue
        index.edges.append((caller_id, callee_id, node.lineno, label, confidence))


def _call_target_name(node: ast.Call) -> tuple[str | None, str, str | None]:
    func = node.func
    if isinstance(func, ast.Name):
        return func.id, func.id, None
    if isinstance(func, ast.Attribute):
        value_name = ""
        receiver: str | None = None
        if isinstance(func.value, ast.Name):
            value_name = func.value.id
            receiver = value_name
        label = f"{value_name}.{func.attr}" if value_name else func.attr
        return func.attr, label, receiver
    return None, "", None


def _build_index(project: Project) -> _CallGraphIndex:
    index = _CallGraphIndex()
    file_to_module, module_to_file = _build_module_maps(project)
    index.file_to_module = file_to_module
    index.module_to_file = module_to_file

    for file_path in project.python_files:
        rel_path = _rel_file(project, file_path)
        info = project.cache.get(file_path)
        spans = _collect_function_spans(info, file_path)
        index.local_names[rel_path] = {span.qualname.split(".")[-1]: span.qualname for span in spans}
        index.class_methods[rel_path] = _build_class_methods(spans)
        with open(file_path, encoding="utf-8", errors="replace") as handle:
            source = handle.read()
        try:
            tree = ast.parse(source, filename=file_path)
        except SyntaxError:
            tree = None
        brief_map = _build_import_map_brief(info)
        ast_map = _build_import_map_ast(project, rel_path, tree, file_to_module) if tree is not None else {}
        index.import_map[rel_path] = _merge_import_maps(brief_map, ast_map)
        for span in spans:
            symbol = symbol_id(project, file_path, "function", span.qualname)
            index.functions[symbol] = span
        if tree is not None:
            _extract_calls(tree, spans, rel_path, file_path, project, index)
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
                extra=standard_symbol_extra(qualname=span.qualname, provenance="ast", confidence=0.7),
            )
        )

    for caller_id, callee_id, line_no, label, confidence in index.edges:
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
                        extra={"provenance": "ast", "confidence": confidence},
                    )
                )
    return graph


def _get_call_index(project: Project) -> _CallGraphIndex:
    return project.analysis_cache.get_or_build_call_index(
        project.python_files,
        lambda: _build_index(project),
        refresh=lambda: project.analysis_cache.refresh_signatures(project.python_files, project.cache),
    )


def build_call_graph(project: Project, symbol: str | None = None) -> GraphIR:
    """Build a static call graph for the open project."""
    project.require_open()
    index = _get_call_index(project)
    graph = _index_to_graph(index, symbol)
    return enrich_graph_meta(graph, project_root=project.root)


def find_callers(project: Project, symbol: str) -> GraphIR:
    """Return call edges where the given symbol is the callee."""
    project.require_open()
    resolved = resolve_symbol_reference(project, symbol)
    index = _get_call_index(project)
    graph = GraphIR(meta={"kind": "callers", "symbol": symbol, "resolved_symbol": resolved})
    for caller_id, callee_id, line_no, label, _confidence in index.edges:
        if callee_id == resolved or resolved in callee_id:
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
    return enrich_graph_meta(graph, project_root=project.root)


def find_callees(project: Project, symbol: str) -> GraphIR:
    """Return call edges where the given symbol is the caller."""
    project.require_open()
    resolved = resolve_symbol_reference(project, symbol)
    index = _get_call_index(project)
    graph = GraphIR(meta={"kind": "callees", "symbol": symbol, "resolved_symbol": resolved})
    for caller_id, callee_id, line_no, label, _confidence in index.edges:
        if caller_id == resolved or resolved in caller_id:
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
    return enrich_graph_meta(graph, project_root=project.root)


def _matches_callee(callee_id: str, target: str, resolved: str | None = None) -> bool:
    if resolved and callee_id == resolved:
        return True
    return target in callee_id or callee_id.endswith(f":function:{target}")


def _resolve_target_file(project: Project, target: str) -> str | None:
    if target.startswith("/"):
        resolved = realpath(target)
        return resolved if project.is_project_path(resolved) else None
    for path in project.python_files:
        rel = project.to_relative_path(path)
        if basename(path) == target or rel == target or rel.endswith("/" + target):
            return path
    return None


def _collect_transitive_callers(
    index: _CallGraphIndex,
    seed_callee_ids: set[str],
) -> tuple[set[str], list[tuple[str, str, str]]]:
    """Walk reverse call edges from seed callees; return callers and impact edges."""
    reverse: dict[str, list[tuple[str, int, str]]] = {}
    for caller_id, callee_id, line_no, label, _confidence in index.edges:
        reverse.setdefault(callee_id, []).append((caller_id, line_no, label))

    impacted: set[str] = set()
    edges_out: list[tuple[str, str, str]] = []
    queue = [callee_id for callee_id in seed_callee_ids if callee_id]
    visited_callees: set[str] = set(queue)
    while queue:
        callee_id = queue.pop(0)
        for caller_id, line_no, label in reverse.get(callee_id, []):
            edges_out.append((caller_id, callee_id, f"{label}:{line_no}"))
            if caller_id not in impacted:
                impacted.add(caller_id)
            if caller_id not in visited_callees:
                visited_callees.add(caller_id)
                queue.append(caller_id)
    return impacted, edges_out


def _add_impact_node(
    graph: GraphIR,
    node_id: str,
    index: _CallGraphIndex,
    fallback_file: str,
) -> None:
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
                extra={"impact": True},
            )
        )
        return
    if node_id.startswith("file:"):
        graph.add_node(
            GraphNode(
                id=node_id,
                type="file",
                name=node_id.split(":", 1)[1],
                file=fallback_file,
                line_start=0,
                line_end=0,
                extra={"impact": True},
            )
        )
        return
    graph.add_node(
        GraphNode(
            id=node_id,
            type="impact",
            name=node_id,
            file=fallback_file,
            line_start=0,
            line_end=0,
        )
    )


def impact_analysis(project: Project, target: str) -> GraphIR:
    """Estimate blast radius using transitive callers and import dependents."""
    project.require_open()
    from .dependency_graph import build_import_graph

    call_index = _get_call_index(project)
    import_graph = build_import_graph(project)
    graph = GraphIR(meta={"kind": "impact_analysis", "target": target})
    impacted: set[str] = set()
    fallback_file = target if target.endswith(".py") else ""

    resolved_symbol: str | None = None
    is_symbol_target = ":function:" in target or ":class:" in target
    if is_symbol_target:
        try:
            resolved_symbol = resolve_symbol_reference(project, target)
        except Exception:
            resolved_symbol = None

    if is_symbol_target and resolved_symbol:
        seed_ids = {resolved_symbol}
        seed_ids |= {
            callee_id
            for _caller_id, callee_id, _line_no, _label, _confidence in call_index.edges
            if callee_id == resolved_symbol
        }
        callers, call_edges = _collect_transitive_callers(call_index, seed_ids)
        impacted |= callers
        impacted |= seed_ids
        for caller_id, callee_id, label in call_edges:
            graph.add_edge(
                GraphEdge(from_id=caller_id, to_id=callee_id, type="impacted_by_call", label=label)
            )
    elif target.endswith(".py") or ("/" in target and not is_symbol_target) or "\\" in target:
        target_file = _resolve_target_file(project, target)
        if target_file:
            fallback_file = target_file
            file_id = f"file:{basename(target_file)}"
            impacted.add(file_id)
            for edge in import_graph.edges:
                if edge.to_id == file_id:
                    impacted.add(edge.from_id)
                    graph.add_edge(
                        GraphEdge(
                            from_id=edge.from_id,
                            to_id=file_id,
                            type="impacted_by_import",
                            label=edge.label,
                        )
                    )
            seed_ids = {
                symbol
                for symbol, span in call_index.functions.items()
                if span.file_path == target_file
            }
            callers, call_edges = _collect_transitive_callers(call_index, seed_ids)
            impacted |= callers
            for caller_id, callee_id, label in call_edges:
                graph.add_edge(
                    GraphEdge(from_id=caller_id, to_id=callee_id, type="impacted_by_call", label=label)
                )
    elif not is_symbol_target:
        seed_ids = {
            callee_id
            for _caller_id, callee_id, _line_no, _label, _confidence in call_index.edges
            if _matches_callee(callee_id, target, resolved_symbol)
        }
        seed_ids |= {
            symbol
            for symbol in call_index.functions
            if _matches_callee(symbol, target, resolved_symbol)
        }
        callers, call_edges = _collect_transitive_callers(call_index, seed_ids)
        impacted |= callers
        impacted |= seed_ids
        for caller_id, callee_id, label in call_edges:
            graph.add_edge(
                GraphEdge(from_id=caller_id, to_id=callee_id, type="impacted_by_call", label=label)
            )

    graph.meta["impacted_count"] = len(impacted)
    if resolved_symbol:
        graph.meta["resolved_symbol"] = resolved_symbol
    for node_id in sorted(impacted):
        _add_impact_node(graph, node_id, call_index, fallback_file)
    return enrich_graph_meta(graph, project_root=project.root)
