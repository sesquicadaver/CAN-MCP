# -*- coding: utf-8 -*-
"""Tests for Graph IR diagram rendering."""

from __future__ import annotations

from codimension_core.graph_ir import GraphEdge, GraphIR, GraphNode
from codimension_core.graph_render import graph_to_html, graph_to_mermaid


def test_graph_to_mermaid_basic():
    graph = GraphIR(meta={"kind": "import_graph"})
    graph.add_node(GraphNode(id="file:a.py", type="file", name="a.py", file="a.py", line_start=1, line_end=1))
    graph.add_node(GraphNode(id="file:b.py", type="file", name="b.py", file="b.py", line_start=1, line_end=1))
    graph.add_edge(GraphEdge(from_id="file:a.py", to_id="file:b.py", type="imports", label="import b"))
    mermaid = graph_to_mermaid(graph)
    assert "flowchart LR" in mermaid
    assert "n0" in mermaid
    assert "n1" in mermaid


def test_graph_to_html_contains_svg():
    graph = GraphIR(meta={"kind": "call_graph"})
    graph.add_node(
        GraphNode(id="main.py:function:f", type="function", name="f", file="main.py", line_start=1, line_end=3)
    )
    html = graph_to_html(graph, "Test diagram")
    assert "<!DOCTYPE html>" in html
    assert "<svg" in html
    assert "Test diagram" in html
