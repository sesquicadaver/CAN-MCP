# -*- coding: utf-8 -*-
"""Parametrized regression tests over tests/fixtures/semantic_project."""

from __future__ import annotations

from pathlib import Path

import pytest

from codimension_core import Project
from codimension_core.callgraph import build_call_graph

FIXTURE_ROOT = Path(__file__).resolve().parent / "fixtures" / "semantic_project"


def _open_fixture() -> Project:
    return Project.open(str(FIXTURE_ROOT))


def _call_edge_pairs(graph) -> set[tuple[str, str]]:
    return {
        (edge.from_id, edge.to_id)
        for edge in graph.edges
        if edge.type == "calls"
    }


@pytest.mark.parametrize(
    ("caller_suffix", "callee_suffix"),
    [
        ("pkg/app.py:function:run", "pkg/utils.py:function:helper"),
        ("pkg/sibling/worker.py:function:Worker.run", "pkg/sibling/worker.py:function:Worker.process"),
    ],
)
def test_semantic_fixture_expected_call_edges(caller_suffix: str, callee_suffix: str):
    project = _open_fixture()
    graph = build_call_graph(project)
    pairs = _call_edge_pairs(graph)
    assert any(from_id.endswith(caller_suffix) and to_id.endswith(callee_suffix) for from_id, to_id in pairs)


def test_semantic_fixture_main_reaches_app_run():
    project = _open_fixture()
    graph = build_call_graph(project)
    pairs = _call_edge_pairs(graph)
    assert any(
        from_id.endswith("main.py:function:main") and to_id.endswith("pkg/app.py:function:run")
        for from_id, to_id in pairs
    )


def test_semantic_fixture_main_worker_run_resolves_to_worker_class():
    project = _open_fixture()
    graph = build_call_graph(project)
    pairs = _call_edge_pairs(graph)
    assert any(
        from_id.endswith("main.py:function:main")
        and to_id.endswith("pkg/sibling/worker.py:function:Worker.run")
        for from_id, to_id in pairs
    )
    worker_run_edges = [
        edge
        for edge in graph.edges
        if edge.type == "calls"
        and edge.from_id.endswith("main.py:function:main")
        and edge.label.startswith("worker.run:")
    ]
    assert worker_run_edges
    assert worker_run_edges[0].to_id.endswith("pkg/sibling/worker.py:function:Worker.run")
    assert worker_run_edges[0].extra.get("confidence", 0) >= 0.8


def test_semantic_fixture_import_helper_via_package():
    project = _open_fixture()
    graph = build_call_graph(project)
    pairs = _call_edge_pairs(graph)
    assert any(
        from_id.endswith("pkg/app.py:function:run") and to_id.endswith("pkg/utils.py:function:helper")
        for from_id, to_id in pairs
    )
