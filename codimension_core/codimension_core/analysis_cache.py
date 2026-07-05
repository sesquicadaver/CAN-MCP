# -*- coding: utf-8 -*-
"""Project-level incremental cache for derived analysis graphs."""

from __future__ import annotations

import hashlib
from dataclasses import dataclass, field
from os.path import basename, exists, getmtime, getsize, realpath
from typing import Any, Callable, TypeVar

from .graph_ir import GraphIR

T = TypeVar("T")
_HASH_BYTES = 65536


@dataclass(frozen=True)
class FileFingerprint:
    """Change detector for a file on disk (mtime/size fast path + content hash)."""

    mtime: float
    size: int
    content_hash: str


def file_content_hash(path: str) -> str:
    """Return a stable short hash of file contents."""
    path = realpath(path)
    digest = hashlib.sha256()
    with open(path, "rb") as handle:
        while True:
            chunk = handle.read(_HASH_BYTES)
            if not chunk:
                break
            digest.update(chunk)
    return digest.hexdigest()[:16]


def file_fingerprint(path: str) -> FileFingerprint:
    """Build a fingerprint including content hash."""
    path = realpath(path)
    return FileFingerprint(
        mtime=getmtime(path),
        size=getsize(path),
        content_hash=file_content_hash(path),
    )


def compute_project_revision(paths: list[str], file_hashes: dict[str, FileFingerprint] | None = None) -> str:
    """Hash of project file content fingerprints."""
    cached = file_hashes if file_hashes is not None else {}
    parts: list[str] = []
    for path in sorted(realpath(item) for item in paths):
        if not exists(path):
            cached.pop(path, None)
            continue
        mtime = getmtime(path)
        size = getsize(path)
        stored = cached.get(path)
        if stored is not None and stored.mtime == mtime and stored.size == size:
            parts.append(f"{path}:{stored.content_hash}")
            continue
        fingerprint = file_fingerprint(path)
        cached[path] = fingerprint
        parts.append(f"{path}:{fingerprint.content_hash}")
    digest = hashlib.sha256("\n".join(parts).encode("utf-8")).hexdigest()
    return digest[:16]


@dataclass
class ProjectAnalysisCache:
    """Caches derived graphs keyed by project or file revision."""

    project_revision: str | None = None
    file_fingerprints: dict[str, FileFingerprint] = field(default_factory=dict)
    import_graph: GraphIR | None = None
    call_index: Any | None = None
    cfg_by_function: dict[str, tuple[FileFingerprint, GraphIR]] = field(default_factory=dict)
    import_graph_hits: int = 0
    import_graph_misses: int = 0
    call_index_hits: int = 0
    call_index_misses: int = 0
    reverse_index: Any | None = None
    reverse_index_hits: int = 0
    reverse_index_misses: int = 0
    cfg_hits: int = 0
    cfg_misses: int = 0

    def compute_revision(self, paths: list[str]) -> str:
        return compute_project_revision(paths, self.file_fingerprints)

    def get_or_build_import_graph(self, paths: list[str], builder: Callable[[], GraphIR]) -> GraphIR:
        revision = self.compute_revision(paths)
        if self.import_graph is not None and self.project_revision == revision:
            self.import_graph_hits += 1
            return self.import_graph
        self.import_graph_misses += 1
        self.project_revision = revision
        self.import_graph = builder()
        self.call_index = None
        self.reverse_index = None
        return self.import_graph

    def get_or_build_call_index(self, paths: list[str], builder: Callable[[], T]) -> T:
        revision = self.compute_revision(paths)
        if self.call_index is not None and self.project_revision == revision:
            self.call_index_hits += 1
            return self.call_index
        self.call_index_misses += 1
        self.project_revision = revision
        self.call_index = builder()
        self.reverse_index = None
        return self.call_index

    def get_or_build_reverse_index(self, paths: list[str], builder: Callable[[], T]) -> T:
        revision = self.compute_revision(paths)
        if self.reverse_index is not None and self.project_revision == revision:
            self.reverse_index_hits += 1
            return self.reverse_index
        self.reverse_index_misses += 1
        self.project_revision = revision
        self.reverse_index = builder()
        return self.reverse_index

    def get_cfg(self, function_id: str, file_path: str) -> GraphIR | None:
        entry = self.cfg_by_function.get(function_id)
        if entry is None:
            return None
        stored_fp, graph = entry
        if not exists(file_path):
            del self.cfg_by_function[function_id]
            return None
        file_path = realpath(file_path)
        mtime = getmtime(file_path)
        size = getsize(file_path)
        if stored_fp.mtime == mtime and stored_fp.size == size:
            self.cfg_hits += 1
            return graph
        if stored_fp.content_hash == file_content_hash(file_path):
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
        self.reverse_index = None

    def invalidate_file(self, path: str) -> None:
        """Drop derived graph caches and CFG entries for one file."""
        path = realpath(path)
        self.file_fingerprints.pop(path, None)
        self.invalidate_graphs()
        file_name = basename(path)
        prefix = f"{file_name}:function:"
        for function_id in list(self.cfg_by_function):
            if function_id.startswith(prefix):
                del self.cfg_by_function[function_id]

    def clear(self) -> None:
        self.invalidate_graphs()
        self.file_fingerprints.clear()
        self.cfg_by_function.clear()

    def stats(self, module_cache_stats: dict[str, int]) -> dict[str, Any]:
        return {
            "project_revision": self.project_revision,
            "file_fingerprint_entries": len(self.file_fingerprints),
            "import_graph_cached": self.import_graph is not None,
            "call_index_cached": self.call_index is not None,
            "reverse_index_cached": self.reverse_index is not None,
            "cfg_entries": len(self.cfg_by_function),
            "import_graph_hits": self.import_graph_hits,
            "import_graph_misses": self.import_graph_misses,
            "call_index_hits": self.call_index_hits,
            "call_index_misses": self.call_index_misses,
            "reverse_index_hits": self.reverse_index_hits,
            "reverse_index_misses": self.reverse_index_misses,
            "cfg_hits": self.cfg_hits,
            "cfg_misses": self.cfg_misses,
            "module_cache": module_cache_stats,
        }
