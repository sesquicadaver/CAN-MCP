# -*- coding: utf-8 -*-
"""Tests for codimension_core explain_symbol."""

from __future__ import annotations

from codimension_core.explain import explain_symbol
from codimension_core.project import Project


def test_explain_symbol_with_file_hint(tmp_path):
    project_dir = tmp_path / "proj"
    project_dir.mkdir()
    main = project_dir / "main.py"
    main.write_text(
        "def greet():\n    return 'hi'\n\ndef unused():\n    pass\n",
        encoding="utf-8",
    )
    project = Project.open(str(project_dir))
    project.analyze_all()

    graph = explain_symbol(project, "main.py:function:greet")
    assert graph.meta["kind"] == "explain_symbol"
    sections = graph.meta["sections"]
    assert sections["name"] == "greet"
    assert "symbols" in sections
    assert "usages" in sections
    assert "callers" in sections
    assert "callees" in sections
    assert graph.nodes


def test_explain_symbol_without_file_hint(tmp_path):
    project_dir = tmp_path / "proj"
    project_dir.mkdir()
    (project_dir / "mod.py").write_text("VALUE = 1\n", encoding="utf-8")
    project = Project.open(str(project_dir))
    project.analyze_all()

    graph = explain_symbol(project, "VALUE")
    sections = graph.meta["sections"]
    assert sections["name"] == "VALUE"
    assert "symbols" in sections
