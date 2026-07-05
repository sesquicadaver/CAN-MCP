# -*- coding: utf-8 -*-
#
# codimension - graphics python two-way code editor and analyzer
# Copyright (C) 2010-2017 Sergey Satskiy <sergey.satskiy@gmail.com>
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.
#

"""Import utility functions — IDE wrapper over codimension_core.imports."""

from __future__ import annotations

import os
import sys

from ui.qt import QApplication

from codimension_core.imports import ImportContext
from codimension_core.imports import ImportResolution as CoreImportResolution
from codimension_core.imports import (
    build_dir_modules as core_build_dir_modules,
)
from codimension_core.imports import (
    get_import_resolutions as core_get_import_resolutions,
)
from codimension_core.imports import (
    get_imports_in_line as core_get_imports_in_line,
)
from codimension_core.imports import (
    get_imports_list as core_get_imports_list,
)
from codimension_core.imports import (
    collect_unresolved_packages as core_collect_unresolved_packages,
)
from codimension_core.imports import (
    get_requirements_hint as core_get_requirements_hint,
)
from codimension_core.imports import (
    get_unresolved_package_names as core_get_unresolved_package_names,
)
from codimension_core.imports import (
    is_import_module as core_is_import_module,
)
from codimension_core.imports import (
    is_imported_object as core_is_imported_object,
)
from codimension_core.imports import (
    resolve_imports as core_resolve_imports,
)

from .config import DEFAULT_ENCODING
from .fileutils import isPythonFile
from .globals import GlobalData
from .run import getProjectPythonPath, getVenvSitePackages

from analysis.core_bridge import core_project_from_ide

# Legacy archive before extraction: Carantine/codimension/utils/importutils_legacy.py

ImportResolution = CoreImportResolution


def _ide_import_context(file_name):
    """Build ImportContext from IDE GlobalData/project state."""
    search_paths = []
    if file_name:
        base_path = os.path.dirname(file_name)
        if base_path:
            search_paths.append(base_path)

    project = GlobalData().project
    if project.isLoaded():
        proj_dir = project.getProjectDir()
        if proj_dir and proj_dir not in search_paths:
            search_paths.append(proj_dir)
        for import_dir in project.getImportDirsAsAbsolutePaths():
            if import_dir not in search_paths:
                search_paths.append(import_dir)
        site_pkg = getVenvSitePackages(getProjectPythonPath(project))
        if site_pkg and site_pkg not in search_paths:
            search_paths.append(site_pkg)

    original = GlobalData().originalSysPath
    sys_path_base = list(original) if original else list(sys.path)
    return ImportContext(file_name=file_name, search_paths=search_paths, sys_path_base=sys_path_base)


def getImportsList(fileContent):
    """Parses a python file and provides a list imports in it"""
    return core_get_imports_list(fileContent)


def getImportsInLine(fileContent, lineNumber):
    """Provides a list of imports in in the given import line"""
    return core_get_imports_in_line(fileContent, lineNumber)


def buildDirModules(path, infoLabel=None):
    """Builds a list of modules how they may appear in the import statements"""
    if infoLabel is not None:
        infoLabel.setText("Scanning " + os.path.abspath(path) + "...")
        QApplication.processEvents()
    return core_build_dir_modules(path)


def isImportModule(info, name):
    """Returns the list of really matched modules"""
    return core_is_import_module(info, name)


def isImportedObject(info, name):
    """Returns a list of matched modules with the real name"""
    return core_is_imported_object(info, name)


def getImportResolutions(fileName, imports):
    """Resolves a list of imports."""
    context = _ide_import_context(fileName)
    return core_get_import_resolutions(context, fileName, imports)


def resolveImports(fileName, imports):
    """Resolves a list of imports. Legacy function."""
    context = _ide_import_context(fileName)
    return core_resolve_imports(context, fileName, imports)


def getUnresolvedPackageNames(errors):
    """Extract top-level package names from resolveImports error messages."""
    return core_get_unresolved_package_names(errors)


def getRequirementsHint(projectDir, unresolvedPackages):
    """Return hint string for missing dependencies, or None."""
    return core_get_requirements_hint(projectDir, unresolvedPackages)


def generateRequirementsFromProject(filesList, progressCallback=None):
    """Scan project Python files for unresolved imports and collect third-party package names."""
    core = core_project_from_ide()
    if core is not None:
        return core_collect_unresolved_packages(core, progressCallback)

    all_errors = []
    python_files = [item for item in filesList if not item.endswith(os.sep) and isPythonFile(item)]
    total = len(python_files)
    for idx, f_name in enumerate(python_files):
        if progressCallback:
            progressCallback(idx, total, "Scanning " + os.path.basename(f_name) + "...")
        try:
            info = GlobalData().briefModinfoCache.get(f_name)
            _, errors = resolveImports(f_name, info.imports)
            all_errors.extend(errors)
        except Exception:
            pass

    packages = getUnresolvedPackageNames(all_errors)
    return packages, len(all_errors)


def _parseRequirementsPackageName(line):
    """Extract package name from a requirements line (e.g. 'numpy>=1.0' -> 'numpy')."""
    import re

    line = line.strip().split("#")[0].strip()
    if not line or line.startswith("-"):
        return None
    match = re.match(r"^([a-zA-Z0-9_-]+)", line)
    return match.group(1).lower() if match else None


def writeRequirementsFile(path, packages, mode="w"):
    """Write package names to requirements.txt."""
    sorted_pkgs = sorted(packages)
    if not sorted_pkgs:
        return 0

    existing = set()
    if mode == "a" and os.path.isfile(path):
        with open(path, "r", encoding=DEFAULT_ENCODING) as handle:
            for line in handle:
                pkg = _parseRequirementsPackageName(line)
                if pkg:
                    existing.add(pkg)
        sorted_pkgs = [pkg for pkg in sorted_pkgs if pkg.lower() not in existing]

    if not sorted_pkgs:
        return 0

    with open(path, mode, encoding=DEFAULT_ENCODING) as handle:
        for pkg in sorted_pkgs:
            handle.write(pkg + "\n")
    return len(sorted_pkgs)
