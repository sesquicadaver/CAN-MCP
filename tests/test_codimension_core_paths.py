# -*- coding: utf-8 -*-
"""Tests for project path helpers."""

from __future__ import annotations

import pytest

from codimension_core import Project
from codimension_core.errors import PathOutsideProjectError
from codimension_core.paths import resolve_project_path


def test_to_relative_path_returns_posix_style(tmp_path):
    project_dir = tmp_path / "proj"
    (project_dir / "pkg").mkdir(parents=True)
    target = project_dir / "pkg" / "mod.py"
    target.write_text("x = 1\n", encoding="utf-8")

    project = Project.open(str(project_dir))
    rel = project.to_relative_path(str(target))
    assert rel == "pkg/mod.py"


def test_resolve_project_path_accepts_relative_inside_project(tmp_path):
    project_dir = tmp_path / "proj"
    project_dir.mkdir()
    (project_dir / "main.py").write_text("x = 1\n", encoding="utf-8")
    project = Project.open(str(project_dir))

    resolved = resolve_project_path(project, "main.py")
    assert resolved.endswith("main.py")
    assert project.is_project_path(resolved)


def test_resolve_project_path_rejects_parent_escape(tmp_path):
    project_dir = tmp_path / "proj"
    project_dir.mkdir()
    (project_dir / "main.py").write_text("x = 1\n", encoding="utf-8")
    project = Project.open(str(project_dir))

    with pytest.raises(PathOutsideProjectError):
        resolve_project_path(project, "../outside.py")
