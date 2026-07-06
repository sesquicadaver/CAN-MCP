# -*- coding: utf-8 -*-
"""Tests for MCP impact analysis resources."""

from __future__ import annotations

import json

from codimension_mcp.resources import (
    decode_impact_key,
    encode_impact_key,
    read_impact_diagram,
    read_impact_graph,
)
from codimension_mcp.schemas import WorkspaceState
from codimension_mcp.tools import analyze_project, open_project


def test_impact_key_roundtrip():
    assert encode_impact_key("leaf") == "leaf"
    assert decode_impact_key("leaf") == "leaf"
    assert encode_impact_key("pkg/mod.py") == "pkg__path__mod.py"
    assert decode_impact_key("pkg__path__mod.py") == "pkg/mod.py"
    assert encode_impact_key("main.py:function:run") == "main.py__function__run"
    assert decode_impact_key("main.py__function__run") == "main.py:function:run"


def test_impact_mcp_resources(tmp_path):
    project_dir = tmp_path / "proj"
    project_dir.mkdir()
    (project_dir / "chain.py").write_text(
        "def leaf():\n    return 1\n\ndef middle():\n    return leaf()\n\ndef top():\n    return middle()\n",
        encoding="utf-8",
    )

    state = WorkspaceState()
    open_project(state, str(project_dir))
    analyze_project(state)

    graph = json.loads(read_impact_graph(state, "leaf"))
    assert graph["graph_ir_version"] == 1
    assert graph["meta"]["kind"] == "impact_analysis"
    assert graph["meta"]["impacted_count"] >= 2

    html = read_impact_diagram(state, "leaf")
    assert html.startswith("<!DOCTYPE html>")
    assert "<svg" in html
