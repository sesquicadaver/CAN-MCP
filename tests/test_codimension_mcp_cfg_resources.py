# -*- coding: utf-8 -*-
"""Tests for MCP function key encoding and CFG resources."""

from __future__ import annotations

import json

from codimension_mcp.resources import (
    decode_function_key,
    encode_function_key,
    read_control_flow_diagram,
    read_control_flow_graph,
)
from codimension_mcp.schemas import WorkspaceState
from codimension_mcp.tools import analyze_project, open_project


def test_function_key_roundtrip():
    function_id = "main.py:function:run"
    key = encode_function_key(function_id)
    assert key == "main.py__function__run"
    assert decode_function_key(key) == function_id


def test_control_flow_mcp_resources(tmp_path):
    project_dir = tmp_path / "proj"
    project_dir.mkdir()
    (project_dir / "main.py").write_text(
        "def run():\n    if True:\n        return 1\n    return 0\n",
        encoding="utf-8",
    )

    state = WorkspaceState()
    open_project(state, str(project_dir))
    analyze_project(state)

    key = encode_function_key("main.py:function:run")
    graph = json.loads(read_control_flow_graph(state, key))
    assert graph["graph_ir_version"] == 1
    assert graph["nodes"]

    html = read_control_flow_diagram(state, key)
    assert html.startswith("<!DOCTYPE html>")
    assert "<svg" in html
