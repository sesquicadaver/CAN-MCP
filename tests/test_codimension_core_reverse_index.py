# -*- coding: utf-8 -*-
"""Tests for reverse symbol index."""

from __future__ import annotations

from codimension_core.project import Project
from codimension_core.reverse_index import lookup_symbol


def test_lookup_symbol_finds_function(tmp_path):
    project_dir = tmp_path / "proj"
    project_dir.mkdir()
    (project_dir / "main.py").write_text("def helper():\n    pass\n", encoding="utf-8")
    project = Project.open(str(project_dir))
    project.analyze_all()

    graph = lookup_symbol(project, "helper")
    assert graph.meta["count"] == 1
    assert graph.nodes[0].name == "helper"
