# -*- coding: utf-8 -*-
"""JSON serialization helpers for MCP tool responses."""

from __future__ import annotations

import json
from typing import Any

from codimension_core.graph_ir import GraphIR


def dumps_graph(graph: GraphIR) -> str:
    """Serialize Graph IR to indented JSON."""
    return json.dumps(graph.to_dict(), indent=2, sort_keys=True)


def dumps_payload(payload: dict[str, Any] | list[Any]) -> str:
    """Serialize generic payloads for MCP tools."""
    return json.dumps(payload, indent=2, sort_keys=True)
