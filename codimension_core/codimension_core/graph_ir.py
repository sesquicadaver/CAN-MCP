# -*- coding: utf-8 -*-
"""Graph IR v1 — stable JSON interchange between core and MCP."""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any

GRAPH_IR_VERSION = 1


@dataclass
class GraphNode:
    """One node in the analysis graph."""

    id: str
    type: str
    name: str
    file: str
    line_start: int
    line_end: int
    extra: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        payload = asdict(self)
        if not payload["extra"]:
            del payload["extra"]
        return payload


@dataclass
class GraphEdge:
    """Directed edge between graph nodes."""

    from_id: str
    to_id: str
    type: str
    label: str = ""

    def to_dict(self) -> dict[str, Any]:
        payload = {
            "from": self.from_id,
            "to": self.to_id,
            "type": self.type,
        }
        if self.label:
            payload["label"] = self.label
        return payload


@dataclass
class GraphIR:
    """Versioned graph document."""

    nodes: list[GraphNode] = field(default_factory=list)
    edges: list[GraphEdge] = field(default_factory=list)
    version: int = GRAPH_IR_VERSION
    meta: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "graph_ir_version": self.version,
            "meta": self.meta,
            "nodes": [node.to_dict() for node in self.nodes],
            "edges": [edge.to_dict() for edge in self.edges],
        }

    def add_node(self, node: GraphNode) -> None:
        if any(existing.id == node.id for existing in self.nodes):
            return
        self.nodes.append(node)

    def add_edge(self, edge: GraphEdge) -> None:
        self.edges.append(edge)
