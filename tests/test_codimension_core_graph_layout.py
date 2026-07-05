# -*- coding: utf-8 -*-
"""Tests for headless Graphviz layout parsing."""

from __future__ import annotations

import shutil

import pytest

from codimension_core.errors import AnalysisError
from codimension_core.graph_layout import (
    get_graph_from_plain_dot_data,
    layout_graph_from_dot,
    split_with_quotes_respect,
)

SAMPLE_PLAIN = """\
graph 1.0 10.0 10.0
node "a" 1 2 3 4 "A" solid box black white
node "b" 5 6 3 4 "B" solid box black white
edge "a" "b" 2 1 1 2 2 dashed black
stop
"""

SAMPLE_DOT = """\
digraph G {
  a -> b;
}
"""


def test_split_with_quotes_respect():
    parts = split_with_quotes_respect('edge "a" "b" 2 1 1 2 2 "hello world" dashed black')
    assert parts[0] == "edge"
    assert parts[8] == "hello world"


def test_get_graph_from_plain_dot_data():
    graph = get_graph_from_plain_dot_data(SAMPLE_PLAIN)
    assert graph.scale == 1.0
    assert len(graph.nodes) == 2
    assert len(graph.edges) == 1
    assert graph.nodes[0].name == "a"
    assert graph.edges[0].tail == "a"
    assert graph.edges[0].head == "b"


def test_layout_graph_normalize():
    graph = get_graph_from_plain_dot_data(SAMPLE_PLAIN)
    graph.normalize(72.0, 72.0)
    assert graph.width > 0
    assert graph.height > 0
    assert graph.nodes[0].posX >= graph.hSpace


@pytest.mark.skipif(shutil.which("dot") is None, reason="graphviz dot not installed")
def test_layout_graph_from_dot():
    graph = layout_graph_from_dot(SAMPLE_DOT)
    assert len(graph.nodes) >= 2
    assert graph.width > 0


def test_layout_graph_from_dot_without_dot(monkeypatch):
    monkeypatch.setattr("codimension_core.graph_layout.shutil.which", lambda _name: None)
    with pytest.raises(AnalysisError, match="dot"):
        layout_graph_from_dot(SAMPLE_DOT)
