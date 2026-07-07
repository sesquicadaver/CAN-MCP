# -*- coding: utf-8 -*-
"""Tests for codimension_mcp tool layer."""

from __future__ import annotations

import json
from pathlib import Path

from codimension_mcp.diagrams import read_diagram_html
from codimension_mcp.prompts import (
    PROMPT_BUILDERS,
    build_analyze_module_prompt,
    build_refactor_symbol_prompt,
    build_review_imports_prompt,
)
from codimension_mcp.resources import (
    read_cache_stats,
    read_call_graph,
    read_dependency_summary,
    read_file_dependency_summary,
    read_file_symbol_summary,
    read_import_graph,
    read_project_tree,
    read_symbol_summary,
    read_workspace_status,
)
from codimension_mcp.schemas import WorkspaceState
from codimension_mcp.tools import (
    analyze_project,
    explain_symbol_tool,
    find_dead_code_tool,
    get_cache_stats_tool,
    get_dependency_summary_tool,
    get_import_diagram_tool,
    get_import_graph_tool,
    get_project_tree,
    get_symbol_summary_tool,
    get_symbols_tool,
    lookup_symbol_tool,
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
    assert symbols["graph_ir_version"] == 2
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
    assert "graphviz" in payload
    assert "digraph ImportsDiagram" in payload["graphviz"]
    assert payload.get("modules", 0) >= 1

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


def test_mcp_lookup_symbol_and_import_diagram(tmp_path):
    project_dir = tmp_path / "proj"
    project_dir.mkdir()
    (project_dir / "main.py").write_text("def api():\n    return 1\n", encoding="utf-8")

    state = WorkspaceState()
    open_project(state, str(project_dir))
    analyze_project(state)

    lookup = json.loads(lookup_symbol_tool(state, "api"))
    assert lookup["meta"]["count"] == 1

    diagram = json.loads(get_import_diagram_tool(state))
    assert diagram["status"] == "ok"
    assert "digraph ImportsDiagram" in diagram["graphviz"]
    assert "layout" in diagram
    if "nodes" in diagram["layout"]:
        assert diagram["layout"]["nodes"] >= 1


def test_mcp_prompt_builders():
    assert "explain_symbol" in build_refactor_symbol_prompt("pkg/mod.py:function:foo")
    assert "project-relative canonical" in build_refactor_symbol_prompt("pkg/mod.py:function:foo")
    assert "find_dead_code" in PROMPT_BUILDERS["review_dead_code"]()
    assert "get_import_graph" in build_review_imports_prompt()
    assert "analyze_file" in build_analyze_module_prompt("pkg/mod.py")
    assert set(PROMPT_BUILDERS) == {
        "refactor_symbol",
        "review_dead_code",
        "review_imports",
        "analyze_module",
        "audit_dependencies",
        "assess_change_impact",
    }


def test_mcp_resources_tree_and_cache(tmp_path):
    project_dir = tmp_path / "proj"
    project_dir.mkdir()
    (project_dir / "main.py").write_text("x = 1\n", encoding="utf-8")

    state = WorkspaceState()
    closed_tree = json.loads(read_project_tree(state))
    assert closed_tree["status"] == "error"

    open_project(state, str(project_dir))
    analyze_project(state)
    get_import_graph_tool(state)

    tree = json.loads(read_project_tree(state))
    assert tree["files"] == ["main.py"]

    cache = json.loads(read_cache_stats(state))
    assert "module_cache" in cache
    assert cache.get("import_graph_hits", 0) >= 0


def test_mcp_summaries_tool_and_resource(tmp_path):
    project_dir = tmp_path / "proj"
    project_dir.mkdir()
    (project_dir / "main.py").write_text("import os\n\ndef f():\n    pass\n", encoding="utf-8")

    state = WorkspaceState()
    open_project(state, str(project_dir))
    analyze_project(state)

    deps_tool = json.loads(get_dependency_summary_tool(state))
    assert deps_tool["totals"]["system"] >= 1

    symbols_tool = json.loads(get_symbol_summary_tool(state))
    assert symbols_tool["counts"]["function"] >= 1

    deps_res = json.loads(read_dependency_summary(state))
    assert deps_res["totals"]["system"] >= 1

    symbols_res = json.loads(read_symbol_summary(state))
    assert symbols_res["total_symbols"] >= 1


def test_mcp_per_file_summary_resources(tmp_path):
    project_dir = tmp_path / "proj"
    project_dir.mkdir()
    (project_dir / "main.py").write_text("import os\n\ndef api():\n    return 1\n", encoding="utf-8")

    state = WorkspaceState()
    open_project(state, str(project_dir))
    analyze_project(state)

    deps = json.loads(read_file_dependency_summary(state, "main.py"))
    assert deps["scope"] == "file"
    assert deps["totals"]["system"] >= 1

    symbols = json.loads(read_file_symbol_summary(state, "main.py"))
    assert symbols["scope"] == "file"
    assert symbols["counts"]["function"] >= 1
