# -*- coding: utf-8 -*-
"""Tests for codimension_core analyzer extraction."""

from __future__ import annotations

import pytest

from codimension_core.analyzer import (
    _parse_vulture_line,
    analyze_dead_code,
    analyze_file_diagnostics,
    build_vulture_exclude_patterns,
    get_buffer_errors,
)
from codimension_core.project import Project

pytest.importorskip("pyflakes")
pytest.importorskip("radon")


def test_get_buffer_errors_unused_import():
    source = "import os\n\ndef f():\n    pass\n"
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


def test_parse_vulture_line():
    parsed = _parse_vulture_line("/tmp/foo.py:12: unused function 'bar'")
    assert parsed is not None
    file_name, line_no, message = parsed
    assert file_name.endswith("foo.py")
    assert line_no == 12
    assert "bar" in message


def test_build_vulture_exclude_patterns(tmp_path):
    project = Project.open(str(tmp_path))
    patterns = build_vulture_exclude_patterns(project)
    assert ".venv" in patterns
    assert "__pycache__" in patterns


def test_analyze_dead_code_graph(tmp_path):
    pytest.importorskip("vulture")
    project_dir = tmp_path / "proj"
    project_dir.mkdir()
    main = project_dir / "main.py"
    main.write_text("def dead_fn():\n    pass\n", encoding="utf-8")
    project = Project.open(str(project_dir))
    graph = analyze_dead_code(project)
    assert graph.meta["kind"] == "dead_code"
