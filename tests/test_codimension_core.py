# -*- coding: utf-8 -*-
"""Tests for codimension_core scaffold."""

from __future__ import annotations

import json

import pytest

from codimension_core import (
    Project,
    analyze_file,
    build_import_graph,
    get_control_flow,
    get_symbols,
    graph_ir,
)
from codimension_core.callgraph import build_call_graph
from codimension_core.cfg import get_control_flow_from_source
from codimension_core.errors import NotImplementedYetError
from codimension_core.symbols import analyze_source


def test_graph_ir_roundtrip():
    graph = graph_ir.GraphIR(meta={"kind": "test"})
    graph.add_node(
        graph_ir.GraphNode(
            id="a.py:function:foo",
            type="function",
            name="foo",
            file="a.py",
            line_start=1,
            line_end=3,
        )
    )
    payload = graph.to_dict()
    assert payload["graph_ir_version"] == 1
    assert payload["nodes"][0]["id"] == "a.py:function:foo"


def test_analyze_source_symbols():
    source = "def hello():\n    return 1\n"
    graph = analyze_source(source, "sample.py")
    types = {node.type for node in graph.nodes}
    assert "module" in types
    assert "function" in types
    assert any(node.name == "hello" for node in graph.nodes)


def test_project_scan_excludes_venv(tmp_path):
    project_dir = tmp_path / "proj"
    project_dir.mkdir()
    (project_dir / "main.py").write_text("x = 1\n", encoding="utf-8")
    venv_dir = project_dir / ".venv" / "bin"
    venv_dir.mkdir(parents=True)
    python_bin = venv_dir / "python"
    python_bin.write_text("#!/bin/sh\n", encoding="utf-8")
    python_bin.chmod(0o755)
    (project_dir / ".venv" / "lib").mkdir(parents=True)
    (project_dir / ".venv" / "lib" / "site.py").write_text("pass\n", encoding="utf-8")

    project = Project.open(str(project_dir))
    rel_paths = project.get_project_tree()
    assert rel_paths == ["main.py"]


def test_import_graph_internal_edge(tmp_path):
    project_dir = tmp_path / "proj"
    project_dir.mkdir()
    (project_dir / "helper.py").write_text("VALUE = 1\n", encoding="utf-8")
    (project_dir / "main.py").write_text("import helper\n", encoding="utf-8")

    project = Project.open(str(project_dir))
    graph = build_import_graph(project)
    edges = {(edge.from_id, edge.to_id, edge.type) for edge in graph.edges}
    assert ("file:main.py", "file:helper.py", "imports") in edges


def test_project_open_analyze_and_symbols(tmp_path):
    project_dir = tmp_path / "proj"
    project_dir.mkdir()
    main = project_dir / "main.py"
    main.write_text("def run():\n    pass\n", encoding="utf-8")

    project = Project.open(str(project_dir))
    assert project.analyze_all() == 1
    graph = analyze_file(project, str(main))
    assert graph.nodes
    all_symbols = get_symbols(project)
    assert len(all_symbols.nodes) >= len(graph.nodes)


def test_control_flow_from_source():
    source = "def run():\n    if True:\n        return 1\n    return 0\n"
    graph = get_control_flow_from_source(source, "run", "sample.py")
    assert graph.nodes
    assert graph.edges
    assert graph.meta["function_id"] == "sample.py:function:run"


def test_get_control_flow_in_project(tmp_path):
    project_dir = tmp_path / "proj"
    project_dir.mkdir()
    main = project_dir / "main.py"
    main.write_text("def run():\n    return 1\n", encoding="utf-8")
    project = Project.open(str(project_dir))
    graph = get_control_flow(project, "main.py:function:run")
    assert graph.nodes


def test_call_graph_not_implemented(tmp_path):
    (tmp_path / "a.py").write_text("pass\n", encoding="utf-8")
    project = Project.open(str(tmp_path))
    with pytest.raises(NotImplementedYetError):
        build_call_graph(project)


def test_tools_json_payload_shape(tmp_path):
    project_dir = tmp_path / "proj"
    project_dir.mkdir()
    (project_dir / "main.py").write_text("x = 1\n", encoding="utf-8")
    project = Project.open(str(project_dir))
    payload = json.loads(json.dumps(get_symbols(project).to_dict()))
    assert "nodes" in payload
    assert "edges" in payload
