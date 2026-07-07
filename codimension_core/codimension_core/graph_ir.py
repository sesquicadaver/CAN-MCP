# -*- coding: utf-8 -*-
"""Graph IR v1/v2 — stable JSON interchange between core and MCP."""

from __future__ import annotations

import os
from dataclasses import asdict, dataclass, field
from datetime import UTC, datetime
from typing import Any

GRAPH_IR_VERSION_V1 = 1
GRAPH_IR_VERSION = 2
GRAPH_IR_VERSION_V2 = 2

SCHEMA_BY_KIND: dict[str, str] = {
    "symbols": "codimension.graph.symbols.v1",
    "call_graph": "codimension.graph.calls.v1",
    "callers": "codimension.graph.calls.v1",
    "callees": "codimension.graph.calls.v1",
    "import_graph": "codimension.graph.imports.v1",
    "diagnostics": "codimension.graph.diagnostics.v1",
    "control_flow": "codimension.graph.cfg.v1",
    "dead_code": "codimension.graph.dead_code.v1",
    "usages": "codimension.graph.usages.v1",
    "impact_analysis": "codimension.graph.impact.v1",
    "reverse_index": "codimension.graph.symbols.v1",
    "symbol": "codimension.graph.symbol.v1",
}

CAPABILITIES_BY_KIND: dict[str, list[str]] = {
    "symbols": ["symbols"],
    "call_graph": ["calls"],
    "callers": ["calls"],
    "callees": ["calls"],
    "import_graph": ["imports"],
    "diagnostics": ["diagnostics"],
    "control_flow": ["cfg"],
    "dead_code": ["diagnostics"],
    "usages": ["symbols"],
    "impact_analysis": ["calls", "imports"],
    "reverse_index": ["symbols"],
    "symbol": ["symbols"],
}


def effective_graph_ir_version() -> int:
    """Return active Graph IR version (default v2; opt-out v1 via CODIMENSION_GRAPH_IR=1)."""
    env = os.environ.get("CODIMENSION_GRAPH_IR", "2").strip()
    if env == "1":
        return GRAPH_IR_VERSION_V1
    return GRAPH_IR_VERSION_V2


def encode_symbol_key(symbol_id: str) -> str:
    """Encode a symbol id for use in MCP resource URI path segments."""
    if ":function:" in symbol_id:
        file_part, name = symbol_id.split(":function:", 1)
        return f"{file_part.replace('/', '__path__')}__function__{name}"
    if ":class:" in symbol_id:
        file_part, name = symbol_id.split(":class:", 1)
        return f"{file_part.replace('/', '__path__')}__class__{name}"
    if ":global:" in symbol_id:
        file_part, name = symbol_id.split(":global:", 1)
        return f"{file_part.replace('/', '__path__')}__global__{name}"
    if ":module:" in symbol_id:
        file_part, name = symbol_id.split(":module:", 1)
        return f"{file_part.replace('/', '__path__')}__module__{name}"
    return symbol_id.replace("/", "__path__")


def decode_symbol_key(symbol_key: str) -> str:
    """Decode an MCP symbol key back to a canonical symbol id."""
    for marker, kind in (
        ("__function__", "function"),
        ("__class__", "class"),
        ("__global__", "global"),
        ("__module__", "module"),
    ):
        if marker in symbol_key:
            file_part, name = symbol_key.split(marker, 1)
            file_path = file_part.replace("__path__", "/")
            return f"{file_path}:{kind}:{name}"
    return symbol_key.replace("__path__", "/")


def symbol_node_uri(symbol_id: str) -> str:
    """Return stable MCP URI for a symbol node."""
    return f"codimension://symbol/{encode_symbol_key(symbol_id)}"


def standard_symbol_extra(
    *,
    qualname: str | None = None,
    namespace: str | None = None,
    provenance: str = "brief_ast",
    confidence: float = 1.0,
) -> dict[str, Any]:
    """Standard GraphNode.extra keys for symbol-like nodes."""
    extra: dict[str, Any] = {
        "language": "py",
        "provenance": provenance,
        "confidence": confidence,
    }
    if qualname:
        extra["qualname"] = qualname
    if namespace:
        extra["namespace"] = namespace
    return extra


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
    extra: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        payload: dict[str, Any] = {
            "from": self.from_id,
            "to": self.to_id,
            "type": self.type,
        }
        if self.label:
            payload["label"] = self.label
        if self.extra:
            payload["extra"] = self.extra
        return payload


@dataclass
class GraphIR:
    """Versioned graph document."""

    nodes: list[GraphNode] = field(default_factory=list)
    edges: list[GraphEdge] = field(default_factory=list)
    version: int = GRAPH_IR_VERSION_V2
    meta: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        version = effective_graph_ir_version()
        nodes_out: list[dict[str, Any]] = []
        for node in self.nodes:
            payload = node.to_dict()
            if version >= GRAPH_IR_VERSION_V2:
                payload["uri"] = symbol_node_uri(node.id)
            nodes_out.append(payload)

        edges_out: list[dict[str, Any]] = []
        for edge in self.edges:
            payload = edge.to_dict()
            if version >= GRAPH_IR_VERSION_V2:
                payload["provenance"] = edge.extra.get("provenance", "ast")
            edges_out.append(payload)

        return {
            "graph_ir_version": version,
            "meta": self.meta,
            "nodes": nodes_out,
            "edges": edges_out,
        }

    def add_node(self, node: GraphNode) -> None:
        if any(existing.id == node.id for existing in self.nodes):
            return
        self.nodes.append(node)

    def add_edge(self, edge: GraphEdge) -> None:
        self.edges.append(edge)


def enrich_graph_meta(
    graph: GraphIR,
    *,
    schema_id: str | None = None,
    project_root: str | None = None,
    capabilities: list[str] | None = None,
) -> GraphIR:
    """Attach standard meta fields without changing the default graph_ir_version."""
    kind = str(graph.meta.get("kind", ""))
    graph.meta.setdefault("schema_id", schema_id or SCHEMA_BY_KIND.get(kind, "codimension.graph.generic.v1"))
    graph.meta.setdefault("generated_at", datetime.now(UTC).replace(microsecond=0).isoformat())
    if project_root:
        graph.meta.setdefault("project_root", project_root)
    if capabilities is None:
        capabilities = CAPABILITIES_BY_KIND.get(kind, [])
    if capabilities:
        graph.meta.setdefault("capabilities", capabilities)
    return graph
