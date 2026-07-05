# -*- coding: utf-8 -*-
#
# codimension - graphics python two-way code editor and analyzer
# Copyright (C) 2010-2020 Sergey Satskiy <sergey.satskiy@gmail.com>
#
# Legacy archive: Carantine/codimension/diagram/depsdiagram_legacy.py

"""Dependencies diagram — IDE wrapper over codimension_core.imports."""

import sys

from analysis.core_bridge import core_project_from_ide
from codimension_core.imports import collect_import_resolutions_classified


def collectImportResolutions(content, fileName):
    """Provides classified import information and errors if so."""
    return collect_import_resolutions_classified(content, fileName, core_project_from_ide(), sys.path)


# Re-export for callers that import resolution helpers from this module.
