# -*- coding: utf-8 -*-
"""Project-level incremental cache for derived analysis graphs."""

from __future__ import annotations

import hashlib
from dataclasses import dataclass, field
from os.path import basename, exists, getmtime, getsize, realpath
from typing import Any, Callable, TypeVar

from .graph_ir import GraphIR

T = TypeVar("T")


@dataclass(frozen=True)
class FileFingerprint:
    """Lightweight change detector for a file on disk."""

    mtime: float
    size: int


def file_fingerprint(path: str) -> FileFingerprint:
    path = realpath(path)
    return FileFingerprint(mtime=getmtime(path), size=getsize(path))


def compute_project_revision(paths: list[str]) -> str:
    """Hash of all project file fingerprints."""
    parts: list[str] = []
    for path in sorted(realpath(item) for item in paths):
        if not exists(path):
            continue
        fp = file_fingerprint(path)
        parts.append(f"{path}:{fp.mtime}:{fp.size}")
    digest = hashlib.sha256("\n".join(parts).encode("utf-8")).hexdigest()
    return digest[:16]


@dataclass
class ProjectAnalysisCache:
    """Caches derived graphs keyed by project or file revision."""

    project_revision: str | None = None
    import_graph: GraphIR | None = None
    call_index: Any | None = None
    cfg_by_function: dict[str, tuple[FileFingerprint, GraphIR]] = field(default_factory=dict)
    import_graph_hits: int = 0
    import_graph_misses: int = 0
    call_index_hits: int = 0
    call_index_misses: int = 0
    cfg_hits: int = 0
    cfg_misses: int = 0

    def compute_revision(self, paths: list[str]) -> str:
        return compute_project_revision(paths)

    def get_or_build_import_graph(self, paths: list[str], builder: Callable[[], GraphIR]) -> GraphIR:
        revision = self.compute_revision(paths)
        if self.import_graph is not None and self.project_revision == revision:
            self.import_graph_hits += 1
            return self.import_graph
        self.import_graph_misses += 1
        self.project_revision = revision
        self.import_graph = builder()
        self.call_index = None
        return self.import_graph

    def get_or_build_call_index(self, paths: list[str], builder: Callable[[], T]) -> T:
        revision = self.compute_revision(paths)
        if self.call_index is not None and self.project_revision == revision:
            self.call_index_hits += 1
            return self.call_index
        self.call_index_misses += 1
        self.project_revision = revision
        self.call_index = builder()
        return self.call_index

    def get_cfg(self, function_id: str, file_path: str) -> GraphIR | None:
        entry = self.cfg_by_function.get(function_id)
        if entry is None:
            return None
        stored_fp, graph = entry
        if not exists(file_path):
            del self.cfg_by_function[function_id]
            return None
        if file_fingerprint(file_path) == stored_fp:
            self.cfg_hits += 1
            return graph
        del self.cfg_by_function[function_id]
        return None

    def store_cfg(self, function_id: str, file_path: str, graph: GraphIR) -> None:
        self.cfg_misses += 1
        self.cfg_by_function[function_id] = (file_fingerprint(file_path), graph)

    def invalidate_graphs(self) -> None:
        self.project_revision = None
        self.import_graph = None
        self.call_index = None

    def invalidate_file(self, path: str) -> None:
        path = realpath(path)
        self.invalidate_graphs()
        file_name = basename(path)
        prefix = f"{file_name}:function:"
        for function_id in list(self.cfg_by_function):
            if function_id.startswith(prefix):
                del self.cfg_by_function[function_id]

    def clear(self) -> None:
        self.invalidate_graphs()
        self.cfg_by_function.clear()

    def stats(self, module_cache_stats: dict[str, int]) -> dict[str, Any]:
        return {
            "project_revision": self.project_revision,
            "import_graph_cached": self.import_graph is not None,
            "call_index_cached": self.call_index is not None,
            "cfg_entries": len(self.cfg_by_function),
            "import_graph_hits": self.import_graph_hits,
            "import_graph_misses": self.import_graph_misses,
            "call_index_hits": self.call_index_hits,
            "call_index_misses": self.call_index_misses,
            "cfg_hits": self.cfg_hits,
            "cfg_misses": self.cfg_misses,
            "module_cache": module_cache_stats,
        }
