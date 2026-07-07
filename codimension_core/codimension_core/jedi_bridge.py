# -*- coding: utf-8 -*-
"""Optional jedi-assisted call target resolution for static call graph."""

from __future__ import annotations

import sys
from os.path import realpath

from .project import Project
from .symbols import symbol_id


def resolve_call_callee_jedi(
    project: Project,
    abs_path: str,
    source: str,
    line: int,
    column: int,
) -> tuple[str | None, float]:
    """Infer a project-local callee symbol id at a call site using jedi."""
    try:
        import jedi
        from jedi.api.project import Project as JediProject
    except ImportError:
        return None, 0.0

    jedi_project = JediProject(
        path=project.root,
        sys_path=list(sys.path),
        added_sys_path=project.get_import_dirs_absolute(),
    )
    script = jedi.Script(code=source, path=abs_path, project=jedi_project)
    try:
        definitions = script.infer(line=line, column=column)
    except Exception:
        return None, 0.0

    for definition in definitions:
        if definition.type not in ("function", "method"):
            continue
        module_path = definition.module_path
        if module_path is None:
            continue
        resolved_path = realpath(str(module_path))
        if not project.is_project_path(resolved_path):
            continue
        name = definition.name
        if not name:
            continue
        if definition.type == "method" and definition.full_name:
            parts = definition.full_name.split(".")
            if len(parts) >= 2:
                name = f"{parts[-2]}.{parts[-1]}"
        return symbol_id(project, resolved_path, "function", name), 0.95
    return None, 0.0
