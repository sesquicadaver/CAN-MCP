# -*- coding: utf-8 -*-
"""Tests for codimension_mcp tool layer."""

from __future__ import annotations

import json

from codimension_mcp.schemas import WorkspaceState
from codimension_mcp.tools import (
    analyze_project,
    explain_symbol_tool,
    find_dead_code_tool,
    get_import_graph_tool,
    get_project_tree,
    get_symbols_tool,
    open_project,
)


def test_open_project_and_tree(tmp_path):
    project_dir = tmp_path / "proj"
    project_dir.mkdir()
    (project_dir / "main.py").write_text("def f():\n    pass\n", encoding="utf-8")

    state = WorkspaceState()
    payload = json.loads(open_project(state, str(project_dir)))
    assert payload["status"] == "ok"
    assert payload["python_files"] == 1

    tree = json.loads(get_project_tree(state))
    assert tree["files"] == ["main.py"]


def test_mcp_tools_return_graph_ir(tmp_path):
    project_dir = tmp_path / "proj"
    project_dir.mkdir()
    (project_dir / "a.py").write_text("import os\n", encoding="utf-8")
    (project_dir / "b.py").write_text("import a\n", encoding="utf-8")

    state = WorkspaceState()
    open_project(state, str(project_dir))
    analyze_project(state)

    symbols = json.loads(get_symbols_tool(state))
    assert symbols["graph_ir_version"] == 1
    assert symbols["nodes"]

    imports = json.loads(get_import_graph_tool(state))
    assert imports["edges"]


def test_mcp_dead_code_and_explain_tools(tmp_path):
    project_dir = tmp_path / "proj"
    project_dir.mkdir()
    (project_dir / "main.py").write_text(
        "def greet():\n    return 1\n\ndef orphan():\n    pass\n",
        encoding="utf-8",
    )

    state = WorkspaceState()
    open_project(state, str(project_dir))
    analyze_project(state)

    dead = json.loads(find_dead_code_tool(state))
    assert dead["meta"]["kind"] == "dead_code"

    explain = json.loads(explain_symbol_tool(state, "main.py:function:greet"))
    assert explain["meta"]["kind"] == "explain_symbol"
    assert "sections" in explain["meta"]
