# -*- coding: utf-8 -*-
"""Structured symbol explanation context for MCP/LLM consumers."""

from __future__ import annotations

from .analyzer import analyze_file_diagnostics
from .callgraph import find_callees, find_callers
from .cfg import get_control_flow
from .graph_ir import GraphIR, GraphNode
from .imports import resolve_imports_for_file
from .project import Project
from .symbols import analyze_file, find_usages, get_symbols, parse_symbol_query


def explain_symbol(project: Project, symbol: str) -> GraphIR:
    """Build structured explanation context as Graph IR + meta payload."""
    project.require_open()
    file_hint, name = parse_symbol_query(symbol)

    target_file = None
    if file_hint:
        for path in project.python_files:
            if path.endswith("/" + file_hint) or path.endswith("\\" + file_hint):
                target_file = path
                break

    sections: dict[str, object] = {"symbol": symbol, "name": name, "file_hint": file_hint}
    graph = GraphIR(meta={"kind": "explain_symbol", **sections})

    if target_file:
        sections["symbols"] = analyze_file(project, target_file).to_dict()
        sections["imports"] = resolve_imports_for_file(project, target_file).to_dict()
        try:
            sections["diagnostics"] = analyze_file_diagnostics(project, target_file).to_dict()
        except (ImportError, RuntimeError, AttributeError):
            sections["diagnostics"] = {}
        function_id = symbol if ":function:" in symbol else f"{file_hint}:function:{name}"
        try:
            sections["control_flow"] = get_control_flow(project, function_id).to_dict()
        except (ValueError, OSError):
            sections["control_flow"] = {}
    else:
        sections["symbols"] = get_symbols(project).to_dict()

    try:
        sections["usages"] = find_usages(project, symbol).to_dict()
    except (ImportError, RuntimeError):
        sections["usages"] = {}
    sections["callers"] = find_callers(project, name).to_dict()
    sections["callees"] = find_callees(project, name).to_dict()

    graph.meta["sections"] = sections
    graph.add_node(
        GraphNode(
            id=f"explain:{symbol}",
            type="explain_context",
            name=name,
            file=target_file or "",
            line_start=0,
            line_end=0,
            extra={"sections": list(sections.keys())},
        )
    )
    return graph
