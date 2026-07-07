# -*- coding: utf-8 -*-
"""Tests for stable project-relative symbol ids."""

from __future__ import annotations

from codimension_core import Project, get_symbols
from codimension_core.symbol_registry import build_legacy_alias_map, resolve_symbol_reference


def test_symbol_ids_unique_for_same_basename_in_different_packages(tmp_path):
    project_dir = tmp_path / "proj"
    (project_dir / "pkg" / "a").mkdir(parents=True)
    (project_dir / "pkg" / "b").mkdir(parents=True)
    (project_dir / "pkg" / "a" / "utils.py").write_text("def foo():\n    return 1\n", encoding="utf-8")
    (project_dir / "pkg" / "b" / "utils.py").write_text("def foo():\n    return 2\n", encoding="utf-8")

    project = Project.open(str(project_dir))
    graph = get_symbols(project)
    foo_ids = [node.id for node in graph.nodes if node.type == "function" and node.name == "foo"]
    assert len(foo_ids) == 2
    assert len(set(foo_ids)) == 2
    assert "pkg/a/utils.py:function:foo" in foo_ids
    assert "pkg/b/utils.py:function:foo" in foo_ids


def test_legacy_alias_map_resolves_unambiguous_basename(tmp_path):
    project_dir = tmp_path / "proj"
    project_dir.mkdir()
    (project_dir / "main.py").write_text("def run():\n    pass\n", encoding="utf-8")

    project = Project.open(str(project_dir))
    alias_map = build_legacy_alias_map(project)
    assert alias_map["main.py:function:run"] == "main.py:function:run"
    assert resolve_symbol_reference(project, "main.py:function:run") == "main.py:function:run"
