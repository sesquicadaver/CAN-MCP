# -*- coding: utf-8 -*-
"""Tests for headless import diagram model."""

from __future__ import annotations

from codimension_core.import_diagram import build_import_diagram_model
from codimension_core.project import Project


def test_build_import_diagram_model(tmp_path):
    project_dir = tmp_path / "proj"
    project_dir.mkdir()
    (project_dir / "a.py").write_text("import os\n", encoding="utf-8")
    (project_dir / "b.py").write_text("import a\n", encoding="utf-8")
    project = Project.open(str(project_dir))
    project.analyze_all()

    model = build_import_diagram_model(project)
    assert model.modules
    assert "digraph ImportsDiagram" in model.to_graphviz()
