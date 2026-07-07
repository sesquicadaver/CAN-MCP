# -*- coding: utf-8 -*-
"""Import graph edge classification (extra.kind)."""

from __future__ import annotations

from codimension_core import Project
from codimension_core.dependency_graph import build_import_graph


def _edge_kinds(graph) -> set[tuple[str, str]]:
    return {
        (edge.from_id, edge.extra.get("kind", ""))
        for edge in graph.edges
        if edge.type == "imports"
    }


def test_resolved_import_graph_classifies_stdlib_project_third_party(tmp_path):
    project_dir = tmp_path / "proj"
    project_dir.mkdir()
    (project_dir / "helper.py").write_text("VALUE = 1\n", encoding="utf-8")
    (project_dir / "main.py").write_text(
        "import os\nfrom helper import VALUE\nimport definitely_not_installed_pkg\n",
        encoding="utf-8",
    )

    project = Project.open(str(project_dir))
    graph = build_import_graph(project, resolved=True)
    kinds = {kind for _from_id, kind in _edge_kinds(graph)}
    assert "stdlib" in kinds
    assert "project" in kinds
    assert "third_party" in kinds or "unresolved" in kinds


def test_brief_import_graph_sets_edge_kind(tmp_path):
    project_dir = tmp_path / "proj"
    project_dir.mkdir()
    (project_dir / "helper.py").write_text("VALUE = 1\n", encoding="utf-8")
    (project_dir / "main.py").write_text("import helper\nimport json\n", encoding="utf-8")

    project = Project.open(str(project_dir))
    graph = build_import_graph(project, resolved=False)
    project_edges = [edge for edge in graph.edges if edge.extra.get("kind") == "project"]
    stdlib_edges = [edge for edge in graph.edges if edge.extra.get("kind") == "stdlib"]
    assert project_edges
    assert stdlib_edges
