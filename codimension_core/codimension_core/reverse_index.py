# -*- coding: utf-8 -*-
"""Reverse symbol index for fast name lookup across a project."""

from __future__ import annotations

from dataclasses import dataclass

from .graph_ir import GraphIR, GraphNode
from .project import Project
from .symbols import _symbol_id, get_symbols


@dataclass(frozen=True)
class SymbolDefinition:
    """One symbol definition site."""

    name: str
    kind: str
    file: str
    line: int
    symbol_id: str


def build_reverse_index(project: Project) -> dict[str, list[SymbolDefinition]]:
    """Build name → definitions map from project symbols."""
    project.require_open()
    index: dict[str, list[SymbolDefinition]] = {}
    graph = get_symbols(project)
    for node in graph.nodes:
        if node.type not in ("function", "class", "global", "module"):
            continue
        entry = SymbolDefinition(
            name=node.name,
            kind=node.type,
            file=node.file,
            line=node.line_start,
            symbol_id=node.id,
        )
        index.setdefault(node.name, []).append(entry)
        if node.type == "function" and "." in node.name:
            short_name = node.name.split(".")[-1]
            index.setdefault(short_name, []).append(entry)
    return index


def lookup_symbol(project: Project, name: str) -> GraphIR:
    """Return Graph IR nodes for all definitions matching a symbol name."""
    project.require_open()
    index = build_reverse_index(project)
    matches = index.get(name, [])
    graph = GraphIR(meta={"kind": "reverse_index", "name": name, "count": len(matches)})
    for item in matches:
        graph.add_node(
            GraphNode(
                id=item.symbol_id or _symbol_id(item.file, item.kind, item.name),
                type=item.kind,
                name=item.name,
                file=item.file,
                line_start=item.line,
                line_end=item.line,
            )
        )
    return graph
