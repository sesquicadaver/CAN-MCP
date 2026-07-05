# -*- coding: utf-8 -*-
"""Tests for codimension_mcp tool layer."""

from __future__ import annotations

import json
from pathlib import Path

from codimension_mcp.diagrams import read_diagram_html
from codimension_mcp.resources import read_call_graph, read_import_graph, read_workspace_status
from codimension_mcp.schemas import WorkspaceState
from codimension_mcp.tools import (
    analyze_project,
    explain_symbol_tool,
    find_dead_code_tool,
    get_import_graph_tool,
    get_cache_stats_tool,
    get_project_tree,
    get_symbols_tool,
    open_project,
    render_diagram_tool,
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


def test_mcp_resources_closed_and_open(tmp_path):
    project_dir = tmp_path / "proj"
    project_dir.mkdir()
    (project_dir / "main.py").write_text("def f():\n    pass\n", encoding="utf-8")

    state = WorkspaceState()
    closed = json.loads(read_workspace_status(state))
    assert closed["status"] == "closed"

    open_project(state, str(project_dir))
    analyze_project(state)

    opened = json.loads(read_workspace_status(state))
    assert opened["status"] == "open"
    assert opened["python_files"] == 1

    imports = json.loads(read_import_graph(state))
    assert imports["meta"]["kind"] == "import_graph"

    calls = json.loads(read_call_graph(state))
    assert calls["meta"]["kind"] == "call_graph"


def test_render_diagram_and_html_resource(tmp_path):
    project_dir = tmp_path / "proj"
    project_dir.mkdir()
    (project_dir / "a.py").write_text("import os\n", encoding="utf-8")
    (project_dir / "b.py").write_text("import a\n", encoding="utf-8")

    state = WorkspaceState()
    open_project(state, str(project_dir))
    analyze_project(state)

    payload = json.loads(render_diagram_tool(state, "import"))
    assert payload["status"] == "ok"
    assert payload["html_path"].endswith(".html")
    assert Path(payload["html_path"]).is_file()

    html = read_diagram_html(state, "import")
    assert html.startswith("<!DOCTYPE html>")
    assert "<svg" in html


def test_mcp_cache_stats(tmp_path):
    project_dir = tmp_path / "proj"
    project_dir.mkdir()
    (project_dir / "main.py").write_text("x = 1\n", encoding="utf-8")

    state = WorkspaceState()
    open_project(state, str(project_dir))
    analyze_project(state)
    get_import_graph_tool(state)
    get_import_graph_tool(state)

    stats = json.loads(get_cache_stats_tool(state))
    assert stats["import_graph_hits"] >= 1
    assert "module_cache" in stats
