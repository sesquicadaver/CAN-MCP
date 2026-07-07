# -*- coding: utf-8 -*-
"""Project path resolution and validation."""

from __future__ import annotations

from os.path import isabs, join, realpath

from .errors import PathOutsideProjectError
from .project import Project


def resolve_project_path(project: Project, path: str) -> str:
    """Resolve a relative or absolute path and ensure it stays inside the project."""
    project.require_open()
    if isabs(path):
        abs_path = realpath(path)
    else:
        abs_path = realpath(join(project.root, path))
    if not project.is_project_path(abs_path):
        raise PathOutsideProjectError(f"Path is outside project: {path}")
    return abs_path
