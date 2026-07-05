# -*- coding: utf-8 -*-
"""Bridge loaded IDE project state to codimension_core.Project."""

from __future__ import annotations

import os

from utils.globals import GlobalData

from codimension_core.project import Project as CoreProject


def core_project_from_ide() -> CoreProject | None:
    """Build headless project context from the loaded IDE project."""
    project = GlobalData().project
    if not project.isLoaded():
        return None
    project_dir = project.getProjectDir()
    if not project_dir:
        return None
    return CoreProject.open(project_dir.rstrip(os.sep))
