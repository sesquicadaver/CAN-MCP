# -*- coding: utf-8 -*-
"""Venv path helpers extracted from codimension.utils.venvutils."""

from __future__ import annotations

import os
from os.path import abspath, dirname, isabs, isdir, isfile, join, normpath, realpath

_VENV_BIN_NAMES = ("bin", "Scripts")


def resolve_venv_to_python(venv_dir: str | None) -> str | None:
    """Resolve a venv directory to its Python executable, if present."""
    if not venv_dir or not isdir(venv_dir):
        return None
    for candidate in (
        join(venv_dir, "bin", "python"),
        join(venv_dir, "bin", "python3"),
        join(venv_dir, "Scripts", "python.exe"),
    ):
        if isfile(candidate) and os.access(candidate, os.X_OK):
            # Keep the venv shim path — realpath() would follow symlinks to system python
            # and break ``python -m vulture`` (packages live in the venv site-packages).
            return abspath(candidate)
    return None


def detect_project_venv_dir(project_dir: str, python_interpreter: str = "") -> str | None:
    """Return absolute venv directory for project scan exclusion."""
    interp = python_interpreter.strip()
    if interp:
        if project_dir and not isabs(interp):
            interp = normpath(join(project_dir, interp))
        if isfile(interp) and os.access(interp, os.X_OK):
            bin_dir = dirname(realpath(interp))
            if os.path.basename(bin_dir) in _VENV_BIN_NAMES:
                return dirname(bin_dir)
            return None
        if isdir(interp) and resolve_venv_to_python(interp):
            return realpath(interp)
        return None
    if not project_dir:
        return None
    for venv_name in (".venv", "venv", "env"):
        venv_path = join(project_dir, venv_name)
        if resolve_venv_to_python(venv_path):
            return realpath(venv_path)
    return None
