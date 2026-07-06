# -*- coding: utf-8 -*-
"""Tests for incremental analysis cache."""

from __future__ import annotations

import os
import time

from codimension_core.callgraph import build_call_graph
from codimension_core.cfg import get_control_flow
from codimension_core.dependency_graph import build_import_graph
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


def test_import_graph_cache_hit_after_mtime_touch(tmp_path):
    project_dir = tmp_path / "proj"
    project_dir.mkdir()
    main = project_dir / "a.py"
    main.write_text("import os\n", encoding="utf-8")
    project = Project.open(str(project_dir))
    project.analyze_all()

    build_import_graph(project)
    assert project.get_cache_stats()["import_graph_misses"] == 1

    new_mtime = time.time() + 60
    os.utime(main, (new_mtime, new_mtime))

    build_import_graph(project)
    stats = project.get_cache_stats()
    assert stats["import_graph_hits"] == 1


def test_import_graph_cache_miss_on_content_change(tmp_path):
    project_dir = tmp_path / "proj"
    project_dir.mkdir()
    main = project_dir / "a.py"
    main.write_text("import os\n", encoding="utf-8")
    project = Project.open(str(project_dir))
    project.analyze_all()

    build_import_graph(project)
    assert project.get_cache_stats()["import_graph_misses"] == 1

    main.write_text("import sys\n", encoding="utf-8")
    build_import_graph(project)
    stats = project.get_cache_stats()
    assert stats["import_graph_misses"] == 2


def test_body_change_keeps_call_graph_cache(tmp_path):
    project_dir = tmp_path / "proj"
    project_dir.mkdir()
    main = project_dir / "main.py"
    main.write_text("def f():\n    pass\n", encoding="utf-8")
    project = Project.open(str(project_dir))
    project.analyze_all()

    build_call_graph(project)
    assert project.get_cache_stats()["call_index_cached"] is True

    main.write_text("def f():\n    return 1\n", encoding="utf-8")
    project.invalidate_file(str(main))
    stats = project.get_cache_stats()
    assert stats["call_index_cached"] is True


def test_body_change_keeps_import_graph_cache(tmp_path):
    project_dir = tmp_path / "proj"
    project_dir.mkdir()
    main = project_dir / "main.py"
    main.write_text("import os\n\ndef f():\n    return 1\n", encoding="utf-8")
    project = Project.open(str(project_dir))
    project.analyze_all()

    build_import_graph(project)
    assert project.get_cache_stats()["import_graph_misses"] == 1

    main.write_text("import os\n\ndef f():\n    return 2\n", encoding="utf-8")
    project.invalidate_file(str(main))
    build_import_graph(project)
    stats = project.get_cache_stats()
    assert stats["import_graph_hits"] == 1
    assert stats["import_graph_misses"] == 1


def test_import_change_invalidates_import_graph_only(tmp_path):
    project_dir = tmp_path / "proj"
    project_dir.mkdir()
    main = project_dir / "main.py"
    main.write_text("import os\n", encoding="utf-8")
    project = Project.open(str(project_dir))
    project.analyze_all()

    build_import_graph(project)
    build_call_graph(project)
    assert project.get_cache_stats()["import_graph_misses"] == 1
    assert project.get_cache_stats()["call_index_misses"] == 1

    main.write_text("import sys\n", encoding="utf-8")
    project.invalidate_file(str(main))
    stats = project.get_cache_stats()
    assert stats["import_graph_cached"] is False
    assert stats["call_index_cached"] is False


def test_invalidate_file_keeps_other_cfg_entries(tmp_path):
    project_dir = tmp_path / "proj"
    project_dir.mkdir()
    first = project_dir / "first.py"
    second = project_dir / "second.py"
    first.write_text("def alpha():\n    return 1\n", encoding="utf-8")
    second.write_text("def beta():\n    return 2\n", encoding="utf-8")
    project = Project.open(str(project_dir))
    project.analyze_all()

    get_control_flow(project, "first.py:function:alpha")
    get_control_flow(project, "second.py:function:beta")
    assert project.get_cache_stats()["cfg_entries"] == 2

    project.invalidate_file(str(first))
    stats = project.get_cache_stats()
    assert stats["cfg_entries"] == 1


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


def test_module_cache_hit_after_mtime_touch(tmp_path):
    project_dir = tmp_path / "proj"
    project_dir.mkdir()
    main = project_dir / "main.py"
    main.write_text("x = 1\n", encoding="utf-8")
    project = Project.open(str(project_dir))

    project.cache.get(str(main))
    new_mtime = time.time() + 120
    os.utime(main, (new_mtime, new_mtime))
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
