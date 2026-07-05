# -*- coding: utf-8 -*-
"""Tests for incremental analysis cache."""

from __future__ import annotations

from codimension_core.dependency_graph import build_import_graph
from codimension_core.callgraph import build_call_graph
from codimension_core.project import Project


def test_import_graph_cache_hit(tmp_path):
    project_dir = tmp_path / "proj"
    project_dir.mkdir()
    (project_dir / "a.py").write_text("import os\n", encoding="utf-8")
    project = Project.open(str(project_dir))
    project.analyze_all()

    build_import_graph(project)
    stats = project.get_cache_stats()
    assert stats["import_graph_misses"] == 1

    build_import_graph(project)
    stats = project.get_cache_stats()
    assert stats["import_graph_hits"] == 1


def test_invalidate_file_clears_graph_cache(tmp_path):
    project_dir = tmp_path / "proj"
    project_dir.mkdir()
    main = project_dir / "main.py"
    main.write_text("def f():\n    pass\n", encoding="utf-8")
    project = Project.open(str(project_dir))
    project.analyze_all()

    build_call_graph(project)
    assert project.get_cache_stats()["call_index_cached"] is True

    project.invalidate_file(str(main))
    stats = project.get_cache_stats()
    assert stats["call_index_cached"] is False


def test_module_cache_hits(tmp_path):
    project_dir = tmp_path / "proj"
    project_dir.mkdir()
    main = project_dir / "main.py"
    main.write_text("x = 1\n", encoding="utf-8")
    project = Project.open(str(project_dir))

    project.cache.get(str(main))
    project.cache.get(str(main))
    stats = project.cache.stats()
    assert stats["hits"] == 1
    assert stats["misses"] == 1


def test_reverse_index_cache_hit(tmp_path):
    from codimension_core.reverse_index import build_reverse_index

    project_dir = tmp_path / "proj"
    project_dir.mkdir()
    (project_dir / "main.py").write_text("def foo():\n    pass\n", encoding="utf-8")
    project = Project.open(str(project_dir))
    project.analyze_all()

    build_reverse_index(project)
    stats = project.get_cache_stats()
    assert stats["reverse_index_misses"] == 1

    build_reverse_index(project)
    stats = project.get_cache_stats()
    assert stats["reverse_index_hits"] == 1
