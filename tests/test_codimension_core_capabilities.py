# -*- coding: utf-8 -*-
"""Graceful degradation when optional analysis packages are missing."""

from __future__ import annotations

import importlib
import json

import pytest

from codimension_core.analyzer import analyze_dead_code, analyze_file_diagnostics
from codimension_core.capabilities import FEATURE_DEPENDENCIES, missing_for_feature
from codimension_core.errors import MissingOptionalDependencyError
from codimension_core.project import Project
from codimension_core.symbols import find_usages
from codimension_mcp.tools import format_tool_error


@pytest.mark.parametrize(
    ("feature", "packages"),
    sorted(FEATURE_DEPENDENCIES.items()),
)
def test_missing_for_feature_reports_each_dependency(feature: str, packages: tuple[str, ...]):
    assert missing_for_feature(feature) == [] or isinstance(missing_for_feature(feature), list)


def _block_packages(monkeypatch: pytest.MonkeyPatch, blocked: set[str]) -> None:
    real_import_module = importlib.import_module

    def guarded_import(name: str, package: str | None = None):
        root = name.split(".", 1)[0]
        if root in blocked:
            raise ImportError(f"blocked for test: {name}")
        return real_import_module(name, package)

    monkeypatch.setattr(importlib, "import_module", guarded_import)


def test_diagnostics_partial_without_pyflakes(monkeypatch, tmp_path):
    _block_packages(monkeypatch, {"pyflakes"})
    project_dir = tmp_path / "proj"
    project_dir.mkdir()
    main = project_dir / "main.py"
    main.write_text("x = 1\n", encoding="utf-8")
    project = Project.open(str(project_dir))

    graph = analyze_file_diagnostics(project, str(main))
    assert graph.meta["status"] == "partial"
    assert "pyflakes" in graph.meta["missing"]


def test_dead_code_partial_without_vulture(monkeypatch, tmp_path):
    _block_packages(monkeypatch, {"vulture"})
    project_dir = tmp_path / "proj"
    project_dir.mkdir()
    (project_dir / "main.py").write_text("def dead_fn():\n    pass\n", encoding="utf-8")
    project = Project.open(str(project_dir))

    graph = analyze_dead_code(project)
    assert graph.meta["status"] == "partial"
    assert graph.meta["missing"] == ["vulture"]


def test_find_usages_partial_without_jedi(monkeypatch, tmp_path):
    _block_packages(monkeypatch, {"jedi"})
    project_dir = tmp_path / "proj"
    project_dir.mkdir()
    (project_dir / "main.py").write_text("def helper():\n    pass\n", encoding="utf-8")
    project = Project.open(str(project_dir))

    graph = find_usages(project, "helper")
    assert graph.meta["status"] == "partial"
    assert graph.meta["missing"] == ["jedi"]


def test_format_tool_error_partial_missing_dependency():
    exc = MissingOptionalDependencyError("find_usages", ["jedi"])
    payload = json.loads(format_tool_error(exc))
    assert payload["status"] == "partial"
    assert payload["missing"] == ["jedi"]
    assert payload["feature"] == "find_usages"
