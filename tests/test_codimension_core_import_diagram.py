# -*- coding: utf-8 -*-
"""Tests for headless import diagram model."""

from __future__ import annotations

from codimension_core.import_diagram import ImportDiagramOptions, build_import_diagram_model
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


def test_import_diagram_includes_classes_and_docstrings(tmp_path):
    project_dir = tmp_path / "proj"
    project_dir.mkdir()
    (project_dir / "mod.py").write_text(
        '"""Module doc."""\n\nclass Foo:\n    pass\n\ndef bar():\n    pass\n',
        encoding="utf-8",
    )
    project = Project.open(str(project_dir))
    project.analyze_all()

    options = ImportDiagramOptions(include_classes=True, include_funcs=True, include_docs=True)
    model = build_import_diagram_model(project, options=options)
    dot = model.to_graphviz()
    assert "Foo" in dot
    assert "bar" in dot
    assert model.docstrings


def test_import_diagram_model_to_graph_ir(tmp_path):
    from codimension_core.import_diagram import import_diagram_model_to_graph_ir

    project_dir = tmp_path / "proj"
    project_dir.mkdir()
    (project_dir / "mod.py").write_text("import os\n", encoding="utf-8")
    project = Project.open(str(project_dir))
    project.analyze_all()

    model = build_import_diagram_model(project)
    graph = import_diagram_model_to_graph_ir(model)
    assert graph.meta["kind"] == "import_diagram"
    assert graph.meta["graphviz"]
    assert graph.nodes
    assert graph.edges or len(model.connections) == 0
