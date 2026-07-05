# -*- coding: utf-8 -*-
"""Headless project model — scan, exclusions, import dirs."""

from __future__ import annotations

import glob
import json
import os
import re
import sys
from dataclasses import dataclass, field
from os.path import dirname, exists, isabs, isdir, isfile, islink, join, realpath, sep

from .analysis_cache import ProjectAnalysisCache
from .cache import ModuleInfoCache
from .errors import ProjectNotOpenError

_DEFAULT_EXCLUDE_NAMES = (
    r"^\..*",
    r".*\.pyc$",
    r".*\.pyo$",
    r".*\.swp$",
    r".*~$",
    r"^__pycache__$",
    r"^\.git$",
    r"^\.mypy_cache$",
    r"^\.ruff_cache$",
    r"^\.pytest_cache$",
    r"^node_modules$",
)


def _is_python_file(path: str) -> bool:
    return path.endswith(".py") and isfile(path)


def _resolve_venv_dir(project_dir: str, python_interpreter: str) -> str | None:
    """Detect venv directory for exclusion during scan."""
    if python_interpreter:
        interp = python_interpreter
        if not isabs(interp):
            interp = os.path.normpath(join(project_dir, interp))
        if isfile(interp) and os.access(interp, os.X_OK):
            bin_dir = os.path.dirname(realpath(interp))
            if os.path.basename(bin_dir) in ("bin", "Scripts"):
                return os.path.dirname(bin_dir)
        if isdir(interp):
            for candidate in (
                join(interp, "bin", "python"),
                join(interp, "bin", "python3"),
                join(interp, "Scripts", "python.exe"),
            ):
                if isfile(candidate) and os.access(candidate, os.X_OK):
                    return realpath(interp)
    for venv_name in (".venv", "venv", "env"):
        venv_path = join(project_dir, venv_name)
        for candidate in (
            join(venv_path, "bin", "python"),
            join(venv_path, "bin", "python3"),
            join(venv_path, "Scripts", "python.exe"),
        ):
            if isfile(candidate) and os.access(candidate, os.X_OK):
                return realpath(venv_path)
    return None


@dataclass
class Project:
    """Headless project context for analysis."""

    root: str = ""
    import_dirs: list[str] = field(default_factory=list)
    exclude_from_analysis: list[str] = field(default_factory=list)
    python_interpreter: str = ""
    python_files: list[str] = field(default_factory=list)
    cache: ModuleInfoCache = field(default_factory=ModuleInfoCache)
    analysis_cache: ProjectAnalysisCache = field(default_factory=ProjectAnalysisCache)
    _exclude_name_patterns: list[re.Pattern[str]] = field(default_factory=list, repr=False)

    @classmethod
    def open(cls, path: str) -> Project:
        """Open a directory as an analysis project."""
        root = realpath(path)
        if not isdir(root):
            raise FileNotFoundError(f"Not a directory: {root}")

        project = cls(root=root)
        project._exclude_name_patterns = [re.compile(p) for p in _DEFAULT_EXCLUDE_NAMES]
        project._load_cdm3_properties(root)
        project._rescan()
        return project

    def _load_cdm3_properties(self, root: str) -> None:
        """Load optional Codimension project metadata."""
        cdm3_path = join(root, ".cdm3")
        if not exists(cdm3_path):
            return
        with open(cdm3_path, encoding="utf-8") as handle:
            props = json.load(handle)
        self.import_dirs = list(props.get("importdirs", []))
        self.exclude_from_analysis = list(props.get("excludeFromAnalysis", []))
        self.python_interpreter = str(props.get("pythoninterpreter", "")).strip()

    def _absolute_exclude_paths(self) -> list[str]:
        result: list[str] = []
        for path in self.exclude_from_analysis:
            path = path.strip()
            if not path:
                continue
            if isabs(path):
                result.append(realpath(path))
            else:
                result.append(realpath(join(self.root, path)))
        return result

    def _is_excluded_path(self, candidate: str, exclude_paths: list[str]) -> bool:
        cand_real = realpath(candidate)
        for excl in exclude_paths:
            excl_real = realpath(excl)
            if cand_real == excl_real:
                return True
            excl_prefix = excl_real.rstrip(sep) + sep
            if cand_real.startswith(excl_prefix):
                return True
        return False

    def _should_exclude_name(self, name: str) -> bool:
        if name == ".pylintrc":
            return False
        return any(pattern.match(name) for pattern in self._exclude_name_patterns)

    def _rescan(self) -> None:
        """Rebuild the list of project python files."""
        root = self.root.rstrip(sep) + sep
        venv_dir = _resolve_venv_dir(self.root, self.python_interpreter)
        exclude_paths = self._absolute_exclude_paths()
        files: list[str] = []
        self._scan_dir(root, venv_dir, exclude_paths, files)
        self.python_files = sorted(files)

    def _scan_dir(
        self,
        path: str,
        venv_dir: str | None,
        exclude_paths: list[str],
        files: list[str],
    ) -> None:
        for item in os.listdir(path):
            if self._should_exclude_name(item):
                continue
            candidate = path + item
            if venv_dir and isdir(candidate):
                cand_real = realpath(candidate).rstrip(sep) + sep
                venv_real = realpath(venv_dir).rstrip(sep) + sep
                if cand_real == venv_real or cand_real.startswith(venv_real):
                    continue
            if self._is_excluded_path(candidate, exclude_paths):
                continue
            if islink(candidate):
                real_item = realpath(candidate)
                if isdir(real_item):
                    if self.is_project_path(real_item):
                        continue
                elif self.is_project_path(os.path.dirname(real_item)):
                    continue
            if isdir(candidate):
                self._scan_dir(candidate + sep, venv_dir, exclude_paths, files)
                continue
            if _is_python_file(candidate):
                files.append(realpath(candidate))

    def is_project_path(self, path: str) -> bool:
        """True when path is inside the project root."""
        if not self.root:
            return False
        root_real = realpath(self.root).rstrip(sep) + sep
        cand_real = realpath(path).rstrip(sep) + sep
        return cand_real.startswith(root_real)

    def require_open(self) -> None:
        if not self.root:
            raise ProjectNotOpenError("No project is open")

    def get_import_dirs_absolute(self) -> list[str]:
        """Return configured import directories as absolute paths."""
        self.require_open()
        result = [self.root]
        for path in self.import_dirs:
            if isabs(path):
                result.append(realpath(path))
            else:
                result.append(realpath(join(self.root, path)))
        return result

    def get_project_tree(self) -> list[str]:
        """Return relative python file paths for MCP get_project_tree."""
        self.require_open()
        root_prefix = self.root.rstrip(sep) + sep
        return [realpath(path)[len(root_prefix) :] for path in self.python_files]

    def analyze_all(self) -> int:
        """Warm the module cache for all project python files."""
        self.require_open()
        for path in self.python_files:
            self.cache.get(path)
        return len(self.python_files)

    def invalidate_file(self, path: str) -> None:
        """Drop cache entries after external file change."""
        abs_path = realpath(path) if isabs(path) else realpath(join(self.root, path))
        self.cache.remove(abs_path)
        self.analysis_cache.invalidate_file(abs_path)

    def rescan(self) -> int:
        """Rescan project tree; clear derived caches if file set changed."""
        self.require_open()
        previous = set(self.python_files)
        self._rescan()
        if set(self.python_files) != previous:
            self.analysis_cache.clear()
        return len(self.python_files)

    def get_cache_stats(self) -> dict[str, object]:
        """Return module and derived-graph cache statistics."""
        self.require_open()
        return self.analysis_cache.stats(self.cache.stats())

    def get_python_executable(self) -> str:
        """Return Python executable for venv detection and site-packages lookup."""
        self.require_open()
        interp = self.python_interpreter.strip()
        if not interp:
            venv_dir = _resolve_venv_dir(self.root, "")
            if venv_dir:
                for candidate in (
                    join(venv_dir, "bin", "python"),
                    join(venv_dir, "bin", "python3"),
                    join(venv_dir, "Scripts", "python.exe"),
                ):
                    if isfile(candidate) and os.access(candidate, os.X_OK):
                        return realpath(candidate)
            return sys.executable

        if not isabs(interp):
            interp = os.path.normpath(join(self.root, interp))
        if isfile(interp) and os.access(interp, os.X_OK):
            return realpath(interp)
        if isdir(interp):
            for candidate in (
                join(interp, "bin", "python"),
                join(interp, "bin", "python3"),
                join(interp, "Scripts", "python.exe"),
            ):
                if isfile(candidate) and os.access(candidate, os.X_OK):
                    return realpath(candidate)
        return sys.executable

    def get_site_packages(self) -> str | None:
        """Return site-packages path for the project venv, if any."""
        python_path = self.get_python_executable()
        if not python_path or python_path == sys.executable:
            return None
        bin_dir = dirname(realpath(python_path))
        venv_dir = dirname(bin_dir)
        if os.path.basename(bin_dir) not in ("bin", "Scripts"):
            return None
        for lib in ("lib", "lib64"):
            pattern = join(venv_dir, lib, "python*", "site-packages")
            matches = glob.glob(pattern)
            if matches:
                return matches[0]
        return None

    def build_import_search_paths(self, file_path: str | None = None) -> list[str]:
        """Build sys.path entries used for import resolution."""
        self.require_open()
        paths: list[str] = []
        if file_path:
            file_dir = dirname(realpath(file_path))
            if file_dir not in paths:
                paths.append(file_dir)
        root = realpath(self.root)
        if root not in paths:
            paths.append(root)
        for path in self.get_import_dirs_absolute():
            if path not in paths:
                paths.append(path)
        site_packages = self.get_site_packages()
        if site_packages and site_packages not in paths:
            paths.append(site_packages)
        return paths
