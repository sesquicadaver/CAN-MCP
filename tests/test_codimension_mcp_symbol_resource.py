# -*- coding: utf-8 -*-
"""Tests for codimension://symbol/{symbol_key} MCP resource."""

from __future__ import annotations

import json

from codimension_core.graph_ir import encode_symbol_key
from codimension_mcp.resources import read_symbol_node
from codimension_mcp.schemas import WorkspaceState
from codimension_mcp.tools import analyze_project, open_project


def test_symbol_resource_returns_matching_node(tmp_path):
    project_dir = tmp_path / "proj"
    project_dir.mkdir()
    (project_dir / "main.py").write_text("def run():\n    return 1\n", encoding="utf-8")

    state = WorkspaceState()
    open_project(state, str(project_dir))
    analyze_project(state)

    symbol_key = encode_symbol_key("main.py:function:run")
    payload = json.loads(read_symbol_node(state, symbol_key))
    assert payload["graph_ir_version"] == 1
    assert payload["meta"]["kind"] == "symbol"
    assert len(payload["nodes"]) == 1
    assert payload["nodes"][0]["id"] == "main.py:function:run"
    assert payload["nodes"][0]["name"] == "run"
