# -*- coding: utf-8 -*-
"""Tests for project summary helpers."""

from __future__ import annotations

from codimension_core.project import Project
from codimension_core.summaries import build_dependency_summary, build_symbol_summary


def test_build_dependency_summary_project(tmp_path):
    project_dir = tmp_path / "proj"
    project_dir.mkdir()
    (project_dir / "helper.py").write_text("VALUE = 1\n", encoding="utf-8")
    main = project_dir / "main.py"
    main.write_text("import os\nimport helper\n", encoding="utf-8")

    project = Project.open(str(project_dir))
    summary = build_dependency_summary(project)
    assert summary["status"] == "ok"
    assert summary["scope"] == "project"
    assert summary["totals"]["project"] == 1
    assert summary["totals"]["system"] >= 1
    assert summary["files_analyzed"] == 2
    assert "helper" in summary["unique_modules"]["project"]
    assert "os" in summary["unique_modules"]["system"]


def test_build_dependency_summary_single_file(tmp_path):
    project_dir = tmp_path / "proj"
    project_dir.mkdir()
    main = project_dir / "main.py"
    main.write_text("import json\n", encoding="utf-8")

    project = Project.open(str(project_dir))
    summary = build_dependency_summary(project, str(main))
    assert summary["scope"] == "file"
    assert summary["files_analyzed"] == 1
    assert summary["totals"]["system"] == 1


def test_build_symbol_summary_project(tmp_path):
    project_dir = tmp_path / "proj"
    project_dir.mkdir()
    (project_dir / "main.py").write_text(
        "class A:\n    pass\n\ndef f():\n    x = 1\n",
        encoding="utf-8",
    )

    project = Project.open(str(project_dir))
    summary = build_symbol_summary(project)
    assert summary["status"] == "ok"
    assert summary["counts"]["function"] >= 1
    assert summary["counts"]["class"] >= 1
    assert summary["total_symbols"] >= 3
