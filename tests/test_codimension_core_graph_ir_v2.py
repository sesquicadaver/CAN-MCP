# -*- coding: utf-8 -*-
"""Tests for Graph IR v2 opt-in serialization."""

from __future__ import annotations

from codimension_core import Project, get_symbols
from codimension_core.callgraph import build_call_graph
from codimension_core.graph_ir import (
    GRAPH_IR_VERSION,
    GRAPH_IR_VERSION_V2,
    GraphIR,
    decode_symbol_key,
    encode_symbol_key,
    enrich_graph_meta,
    symbol_node_uri,
)


def test_graph_ir_v1_default_no_uri(tmp_path, monkeypatch):
    monkeypatch.delenv("CODIMENSION_GRAPH_IR", raising=False)
    project_dir = tmp_path / "proj"
    project_dir.mkdir()
    (project_dir / "main.py").write_text("def run():\n    pass\n", encoding="utf-8")
    project = Project.open(str(project_dir))

    payload = get_symbols(project).to_dict()
    assert payload["graph_ir_version"] == GRAPH_IR_VERSION
    assert "uri" not in payload["nodes"][0]


def test_graph_ir_v2_opt_in_uri_and_provenance(tmp_path, monkeypatch):
    monkeypatch.setenv("CODIMENSION_GRAPH_IR", "2")
    project_dir = tmp_path / "proj"
    project_dir.mkdir()
    (project_dir / "main.py").write_text(
        "def helper():\n    return 1\n\ndef run():\n    return helper()\n",
        encoding="utf-8",
    )
    project = Project.open(str(project_dir))

    symbols = get_symbols(project).to_dict()
    assert symbols["graph_ir_version"] == GRAPH_IR_VERSION_V2
    function_nodes = [node for node in symbols["nodes"] if node["type"] == "function"]
    assert function_nodes
    assert function_nodes[0]["uri"].startswith("codimension://symbol/")

    calls = build_call_graph(project).to_dict()
    assert calls["graph_ir_version"] == GRAPH_IR_VERSION_V2
    assert calls["edges"]
    assert calls["edges"][0]["provenance"] == "ast"


def test_symbol_key_roundtrip_matches_uri_encoding():
    symbol_id = "pkg/mod.py:function:run"
    key = encode_symbol_key(symbol_id)
    assert decode_symbol_key(key) == symbol_id
    assert symbol_node_uri(symbol_id) == f"codimension://symbol/{key}"


def test_enriched_meta_has_schema_and_capabilities():
    graph = enrich_graph_meta(GraphIR(meta={"kind": "call_graph"}), project_root="/tmp/proj")
    payload = graph.to_dict()
    assert payload["meta"]["schema_id"] == "codimension.graph.calls.v1"
    assert "calls" in payload["meta"]["capabilities"]
    assert payload["meta"]["project_root"] == "/tmp/proj"
    assert "generated_at" in payload["meta"]
