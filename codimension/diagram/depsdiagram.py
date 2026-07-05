# -*- coding: utf-8 -*-
#
# codimension - graphics python two-way code editor and analyzer
# Copyright (C) 2010-2020 Sergey Satskiy <sergey.satskiy@gmail.com>
#
# Legacy archive: Carantine/codimension/diagram/depsdiagram_legacy.py

"""Dependencies diagram — IDE wrapper over codimension_core.imports."""

import os
import sys

from utils.globals import GlobalData

from codimension_core.imports import collect_import_resolutions_classified
from codimension_core.project import Project as CoreProject


def _core_project_from_ide():
    """Build headless project context from the loaded IDE project."""
    project = GlobalData().project
    if not project.isLoaded():
        return None
    project_dir = project.getProjectDir()
    if not project_dir:
        return None
    return CoreProject.open(project_dir.rstrip(os.sep))


def collectImportResolutions(content, fileName):
    """Provides classified import information and errors if so."""
    core_project = _core_project_from_ide()
    return collect_import_resolutions_classified(content, fileName, core_project, sys.path)


# Re-export for callers that import resolution helpers from this module.
