# -*- coding: utf-8 -*-
"""Subprocess import isolation integration tests."""

from __future__ import annotations

import sys

import pytest

from codimension_core.imports import build_import_context, get_import_resolutions, resolve_imports_inprocess
from codimension_core.import_isolation import import_isolation_mode
from codimension_core.project import Project


def test_subprocess_isolation_resolves_internal_import(tmp_path, monkeypatch):
    monkeypatch.setenv("CODIMENSION_IMPORT_ISOLATION", "subprocess")
    assert import_isolation_mode() == "subprocess"

    project_dir = tmp_path / "proj"
    project_dir.mkdir()
    (project_dir / "helper.py").write_text("VALUE = 1\n", encoding="utf-8")
    (project_dir / "main.py").write_text("import helper\n", encoding="utf-8")

    project = Project.open(str(project_dir))
    info = project.cache.get(str(project_dir / "main.py"))
    context = build_import_context(project, str(project_dir / "main.py"))
    resolutions = get_import_resolutions(context, str(project_dir / "main.py"), info.imports)
    assert resolutions
    assert any(res.isResolved() and res.path and res.path.endswith("helper.py") for res in resolutions)


def test_subprocess_isolation_matches_inprocess(tmp_path, monkeypatch):
    monkeypatch.setenv("CODIMENSION_IMPORT_ISOLATION", "subprocess")

    project_dir = tmp_path / "proj"
    project_dir.mkdir()
    (project_dir / "helper.py").write_text("VALUE = 1\n", encoding="utf-8")
    (project_dir / "main.py").write_text("from helper import VALUE\n", encoding="utf-8")

    project = Project.open(str(project_dir))
    main_path = str(project_dir / "main.py")
    info = project.cache.get(main_path)
    context = build_import_context(project, main_path)

    monkeypatch.delenv("CODIMENSION_IMPORT_ISOLATION", raising=False)
    inprocess = resolve_imports_inprocess(context, main_path, info.imports)

    monkeypatch.setenv("CODIMENSION_IMPORT_ISOLATION", "subprocess")
    isolated = get_import_resolutions(context, main_path, info.imports)

    assert len(isolated) == len(inprocess)
    for left, right in zip(isolated, inprocess):
        assert left.isResolved() == right.isResolved()
        assert left.path == right.path
        assert left.builtIn == right.builtIn


def test_subprocess_isolation_does_not_mutate_parent_sys_path(tmp_path, monkeypatch):
    monkeypatch.setenv("CODIMENSION_IMPORT_ISOLATION", "subprocess")

    project_dir = tmp_path / "proj"
    project_dir.mkdir()
    (project_dir / "main.py").write_text("import os\n", encoding="utf-8")

    project = Project.open(str(project_dir))
    main_path = str(project_dir / "main.py")
    info = project.cache.get(main_path)
    context = build_import_context(project, main_path)
    baseline = list(sys.path)

    get_import_resolutions(context, main_path, info.imports)
    assert list(sys.path) == baseline
