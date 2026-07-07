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

    assert payload["graph_ir_version"] == graph_ir.GRAPH_IR_VERSION
    node = payload["nodes"][0]
    for key in ("id", "type", "name", "file", "line_start", "line_end", "uri"):
        assert key in node

    edge = payload["edges"][0]
    assert edge["from"] == "a"
    assert edge["to"] == "b"
    assert edge["type"] == "calls"
    assert "provenance" in edge


def test_symbol_graph_meta_contract(tmp_path):
    from codimension_core import Project, get_symbols

    project_dir = tmp_path / "proj"
    project_dir.mkdir()
    (project_dir / "main.py").write_text("def run():\n    pass\n", encoding="utf-8")
    project = Project.open(str(project_dir))
    payload = get_symbols(project).to_dict()

    assert payload["meta"]["schema_id"] == "codimension.graph.symbols.v1"
    assert "symbols" in payload["meta"]["capabilities"]
    function_nodes = [node for node in payload["nodes"] if node["type"] == "function"]
    assert function_nodes
    extra = function_nodes[0].get("extra", {})
    assert extra.get("language") == "py"
    assert extra.get("provenance") == "brief_ast"
    assert "qualname" in extra
