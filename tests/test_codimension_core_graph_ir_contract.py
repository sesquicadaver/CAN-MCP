# -*- coding: utf-8 -*-
"""Contract tests for Graph IR JSON shape."""

from __future__ import annotations

from codimension_core import graph_ir


def test_graph_ir_contract_fields():
    graph = graph_ir.GraphIR(meta={"kind": "contract"})
    graph.add_node(
        graph_ir.GraphNode(
            id="main.py:function:run",
            type="function",
            name="run",
            file="main.py",
            line_start=1,
            line_end=2,
        )
    )
    graph.add_edge(graph_ir.GraphEdge(from_id="a", to_id="b", type="calls", label="run:3"))
    payload = graph.to_dict()

    assert payload["graph_ir_version"] == 1
    assert "meta" in payload
    assert "nodes" in payload
    assert "edges" in payload

    node = payload["nodes"][0]
    for key in ("id", "type", "name", "file", "line_start", "line_end"):
        assert key in node

    edge = payload["edges"][0]
    assert edge["from"] == "a"
    assert edge["to"] == "b"
    assert edge["type"] == "calls"
