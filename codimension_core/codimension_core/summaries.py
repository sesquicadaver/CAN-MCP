# -*- coding: utf-8 -*-
"""Compact project summaries for MCP resources and tools."""

from __future__ import annotations

import sys
from os.path import basename, realpath

from .imports import ClassifiedImportResolutions, ImportResolution, collect_import_resolutions_classified
from .project import Project
from .symbols import get_symbols


def _resolution_entry(resolution: ImportResolution, file_path: str) -> dict[str, object]:
    return {
        "file": basename(file_path),
        "name": resolution.getVisibleName(),
        "line": resolution.importObj.line,
        "resolved": resolution.isResolved(),
        "path": resolution.path,
        "built_in": resolution.builtIn,
        "error": resolution.errMessage,
    }


def _accumulate_classified(
    classified: ClassifiedImportResolutions,
    file_path: str,
    totals: dict[str, int],
    unique: dict[str, set[str]],
    entries: dict[str, list[dict[str, object]]],
) -> None:
    for bucket in ("system", "project", "other", "unresolved"):
        for resolution in classified[bucket]:  # type: ignore[literal-required]
            totals[bucket] += 1
            unique[bucket].add(resolution.getVisibleName())
            entries[bucket].append(_resolution_entry(resolution, file_path))


def build_dependency_summary(project: Project, path: str | None = None) -> dict[str, object]:
    """Aggregate classified import resolutions for one file or the whole project."""
    project.require_open()
    files = [realpath(path)] if path else list(project.python_files)
    totals = {"system": 0, "project": 0, "other": 0, "unresolved": 0}
    unique: dict[str, set[str]] = {key: set() for key in totals}
    entries: dict[str, list[dict[str, object]]] = {key: [] for key in totals}
    errors: list[str] = []

    for file_path in files:
        if not project.is_project_path(file_path):
            raise ValueError(f"Path is outside project: {path}")
        try:
            with open(file_path, encoding="utf-8", errors="replace") as handle:
                content = handle.read()
        except OSError as exc:
            errors.append(f"{basename(file_path)}: {exc}")
            continue
        classified = collect_import_resolutions_classified(content, file_path, project, sys.path)
        errors.extend(classified["errors"])
        _accumulate_classified(classified, file_path, totals, unique, entries)

    return {
        "status": "ok",
        "scope": "file" if path else "project",
        "path": basename(realpath(path)) if path else None,
        "files_analyzed": len(files),
        "totals": totals,
        "unique_modules": {key: sorted(values) for key, values in unique.items()},
        "entries": entries,
        "errors": errors,
    }


def build_symbol_summary(project: Project, path: str | None = None) -> dict[str, object]:
    """Count symbols by type for one file or the whole project."""
    project.require_open()
    graph = get_symbols(project, realpath(path) if path else None)
    counts: dict[str, int] = {}
    files: set[str] = set()
    for node in graph.nodes:
        counts[node.type] = counts.get(node.type, 0) + 1
        if node.file:
            files.add(basename(node.file))
    return {
        "status": "ok",
        "scope": "file" if path else "project",
        "path": basename(realpath(path)) if path else None,
        "counts": counts,
        "total_symbols": sum(counts.values()),
        "files": sorted(files),
    }
