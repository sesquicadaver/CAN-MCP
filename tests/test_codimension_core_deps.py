# -*- coding: utf-8 -*-
"""Tests for depsdiagram classification extraction."""

from __future__ import annotations

from codimension_core.imports import collect_import_resolutions_classified
from codimension_core.project import Project


def test_collect_import_resolutions_classified_internal(tmp_path):
    project_dir = tmp_path / "proj"
    project_dir.mkdir()
    (project_dir / "helper.py").write_text("VALUE = 1\n", encoding="utf-8")
    main = project_dir / "main.py"
    main.write_text("import helper\n", encoding="utf-8")

    project = Project.open(str(project_dir))
    result = collect_import_resolutions_classified(main.read_text(encoding="utf-8"), str(main), project)
    assert result["totalCount"] == 1
    assert len(result["project"]) == 1
    assert not result["errors"]


def test_collect_import_resolutions_classified_stdlib_frozen(tmp_path):
    project_dir = tmp_path / "proj"
    project_dir.mkdir()
    main = project_dir / "main.py"
    main.write_text("import os\nimport json\n", encoding="utf-8")

    project = Project.open(str(project_dir))
    result = collect_import_resolutions_classified(main.read_text(encoding="utf-8"), str(main), project)
    assert result["totalCount"] == 2
    assert len(result["system"]) == 2
    assert len(result["unresolved"]) == 0
    names = {resolution.getVisibleName() for resolution in result["system"]}
    assert names == {"os", "json"}


def test_collect_import_resolutions_classified_from_os_import(tmp_path):
    project_dir = tmp_path / "proj"
    project_dir.mkdir()
    main = project_dir / "main.py"
    main.write_text("from os import path\n", encoding="utf-8")

    project = Project.open(str(project_dir))
    result = collect_import_resolutions_classified(main.read_text(encoding="utf-8"), str(main), project)
    assert result["totalCount"] == 1
    assert len(result["system"]) == 1
    assert result["system"][0].builtIn is True
    assert result["system"][0].errMessage is None
