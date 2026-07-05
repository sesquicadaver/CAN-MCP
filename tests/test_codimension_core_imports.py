# -*- coding: utf-8 -*-
"""Tests for codimension_core imports extraction."""

from __future__ import annotations

from codimension_core.imports import (
    build_import_context,
    get_import_resolutions,
    get_unresolved_package_names,
    resolve_imports,
    resolve_imports_for_file,
)
from codimension_core.project import Project


def test_resolve_internal_import(tmp_path):
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


def test_resolve_imports_graph_ir(tmp_path):
    project_dir = tmp_path / "proj"
    project_dir.mkdir()
    (project_dir / "helper.py").write_text("def run():\n    pass\n", encoding="utf-8")
    (project_dir / "main.py").write_text("import helper\n", encoding="utf-8")
    project = Project.open(str(project_dir))
    graph = resolve_imports_for_file(project, str(project_dir / "main.py"))
    assert graph.edges
    assert graph.meta["kind"] == "resolved_imports"


def test_unresolved_packages_skip_relative():
    errors = ["Could not resolve 'from .pkg import x' at line 1"]
    assert get_unresolved_package_names(errors) == set()


def test_legacy_resolve_imports_tuple(tmp_path):
    project_dir = tmp_path / "proj"
    project_dir.mkdir()
    helper = project_dir / "helper.py"
    helper.write_text("x = 1\n", encoding="utf-8")
    main = project_dir / "main.py"
    main.write_text("import helper\n", encoding="utf-8")
    project = Project.open(str(project_dir))
    info = project.cache.get(str(main))
    context = build_import_context(project, str(main))
    resolved, errors = resolve_imports(context, str(main), info.imports)
    assert not errors
    assert resolved
