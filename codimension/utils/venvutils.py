# -*- coding: utf-8 -*-
#
# Legacy logic extracted to codimension_core.venvutils (2026-07-06).
#

"""Venv-related helpers — IDE wrapper over codimension_core.venvutils."""

from codimension_core.venvutils import detect_project_venv_dir, resolve_venv_to_python

resolveVenvToPython = resolve_venv_to_python


def getProjectVenvDir(project):
    """Returns the venv directory path for exclusion from project scan, or None."""
    if project is None or not project.isLoaded():
        return None
    interp = project.props.get("pythoninterpreter", "").strip()
    project_dir = project.getProjectDir() or ""
    return detect_project_venv_dir(project_dir, interp)
