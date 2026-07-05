# -*- coding: utf-8 -*-
"""Tests for codimension_core impact_analysis."""

from __future__ import annotations

from codimension_core.callgraph import impact_analysis
from codimension_core.project import Project


def test_impact_analysis_transitive_callers(tmp_path):
    project_dir = tmp_path / "proj"
    project_dir.mkdir()
    (project_dir / "chain.py").write_text(
        "def leaf():\n    return 1\n\ndef middle():\n    return leaf()\n\ndef top():\n    return middle()\n",
        encoding="utf-8",
    )
    project = Project.open(str(project_dir))
    project.analyze_all()

    graph = impact_analysis(project, "leaf")
    impacted_ids = {node.id for node in graph.nodes}
    assert graph.meta["impacted_count"] >= 2
    assert any("middle" in node_id for node_id in impacted_ids)
    assert any("top" in node_id for node_id in impacted_ids)
    assert graph.edges


def test_impact_analysis_file_importers(tmp_path):
    project_dir = tmp_path / "proj"
    project_dir.mkdir()
    (project_dir / "lib.py").write_text("VALUE = 1\n", encoding="utf-8")
    (project_dir / "app.py").write_text("import lib\n\ndef run():\n    return lib.VALUE\n", encoding="utf-8")
    project = Project.open(str(project_dir))
    project.analyze_all()

    graph = impact_analysis(project, "lib.py")
    impacted_ids = {node.id for node in graph.nodes}
    assert "file:lib.py" in impacted_ids
    assert "file:app.py" in impacted_ids
