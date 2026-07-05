# -*- coding: utf-8 -*-
"""Tests for codimension_core analyzer extraction."""

from __future__ import annotations

import pytest

from codimension_core.analyzer import analyze_file_diagnostics, get_buffer_errors
from codimension_core.project import Project

pytest.importorskip("pyflakes")
pytest.importorskip("radon")


def test_get_buffer_errors_unused_import():
    source = "import os\n"
    errors, complexity = get_buffer_errors(source)
    assert 1 in errors
    assert complexity


def test_analyze_file_diagnostics_graph(tmp_path):
    project_dir = tmp_path / "proj"
    project_dir.mkdir()
    main = project_dir / "main.py"
    main.write_text("import os\n", encoding="utf-8")
    project = Project.open(str(project_dir))
    graph = analyze_file_diagnostics(project, str(main))
    assert graph.meta["kind"] == "diagnostics"
    assert graph.nodes
