# -*- coding: utf-8 -*-
"""Concurrent import resolution must not leak sys.path mutations."""

from __future__ import annotations

import sys
from concurrent.futures import ThreadPoolExecutor

from codimension_core.imports import build_import_context, get_import_resolutions
from codimension_core.project import Project


def _make_project(tmp_path):
    project_dir = tmp_path / "proj"
    project_dir.mkdir()
    for index in range(5):
        (project_dir / f"mod{index}.py").write_text(f"VALUE_{index} = {index}\n", encoding="utf-8")
    main = project_dir / "main.py"
    imports = "\n".join(f"import mod{i}" for i in range(5))
    main.write_text(f"{imports}\n\ndef run():\n    return 0\n", encoding="utf-8")
    return project_dir, main


def test_parallel_import_resolution_restores_sys_path(tmp_path):
    project_dir, main = _make_project(tmp_path)
    baseline = list(sys.path)

    def resolve_once(_: int) -> list[str]:
        project = Project.open(str(project_dir))
        info = project.cache.get(str(main))
        context = build_import_context(project, str(main))
        get_import_resolutions(context, str(main), info.imports)
        return list(sys.path)

    with ThreadPoolExecutor(max_workers=10) as pool:
        results = list(pool.map(resolve_once, range(10)))

    assert list(sys.path) == baseline
    assert all(path == baseline for path in results)
