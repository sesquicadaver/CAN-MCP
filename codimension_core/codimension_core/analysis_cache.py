# -*- coding: utf-8 -*-
"""Project-level incremental cache for derived analysis graphs."""

from __future__ import annotations

import ast
import hashlib
from dataclasses import dataclass, field
from os.path import basename, exists, getmtime, getsize, realpath
from typing import Any, Callable, TypeVar, cast

from .graph_ir import GraphIR

T = TypeVar("T")
_HASH_BYTES = 65536


@dataclass(frozen=True)
class FileFingerprint:
    """Change detector for a file on disk (mtime/size fast path + content hash)."""

    mtime: float
    size: int
    content_hash: str


@dataclass(frozen=True)
class FileDerivedSignatures:
    """Per-file facets used for selective derived-graph invalidation."""

    imports: str
    symbols: str
    calls: str
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


def _digest_parts(parts: list[str]) -> str:
    return hashlib.sha256("\n".join(parts).encode("utf-8")).hexdigest()[:16]


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
    return _digest_parts(parts)


def _import_signature(info: object) -> str:
    parts: list[str] = []
    for import_obj in getattr(info, "imports", []):
        what = getattr(import_obj, "what", []) or []
        if what:
            items = "|".join(f"{item.name}:{getattr(item, 'alias', '')}" for item in what)
            parts.append(f"from:{import_obj.name}:{items}:{import_obj.line}")
        else:
            parts.append(f"import:{import_obj.name}:{getattr(import_obj, 'alias', '')}:{import_obj.line}")
    return _digest_parts(parts)


def _symbol_signature(info: object) -> str:
    parts: list[str] = []
    for fn in getattr(info, "functions", []):
        parts.append(f"fn:{fn.name}")
    for cls in getattr(info, "classes", []):
        parts.append(f"cls:{cls.name}")
        for method in getattr(cls, "functions", []):
            parts.append(f"meth:{cls.name}.{method.name}")
    for glob in getattr(info, "globals", []):
        parts.append(f"global:{glob.name}")
    return _digest_parts(parts)


def _call_target_name(node: ast.Call) -> str | None:
    func = node.func
    if isinstance(func, ast.Name):
        return func.id
    if isinstance(func, ast.Attribute):
        return func.attr
    return None


def _function_qualname_for_line(info: object, line: int) -> str | None:
    for fn in getattr(info, "functions", []):
        end = getattr(fn, "colonLine", fn.line)
        if fn.line <= line <= end:
            return str(fn.name)
        for nested in getattr(fn, "functions", []):
            nested_end = getattr(nested, "colonLine", nested.line)
            if nested.line <= line <= nested_end:
                return f"{fn.name}.{nested.name}"
    for cls in getattr(info, "classes", []):
        for method in getattr(cls, "functions", []):
            end = getattr(method, "colonLine", method.line)
            if method.line <= line <= end:
                return f"{cls.name}.{method.name}"
    return None


def _calls_signature(info: object, source: str) -> str:
    import_part = _import_signature(info)
    call_parts: list[str] = []
    try:
        tree = ast.parse(source, mode="exec", type_comments=True)
    except SyntaxError:
        return _digest_parts([import_part, "syntax-error"])
    for node in ast.walk(tree):
        if not isinstance(node, ast.Call):
            continue
        qualname = _function_qualname_for_line(info, node.lineno or 0)
        if qualname is None:
            continue
        target = _call_target_name(node)
        if target is None:
            continue
        call_parts.append(f"{qualname}:{node.lineno}:{target}")
    call_parts.sort()
    return _digest_parts([import_part, *call_parts])


def compute_file_derived_signatures(
    info: object,
    source: str,
    *,
    content_hash: str | None = None,
) -> FileDerivedSignatures:
    """Compute import/symbol/call facets for selective cache invalidation."""
    if content_hash is None:
        content_hash = hashlib.sha256(source.encode("utf-8")).hexdigest()[:16]
    return FileDerivedSignatures(
        imports=_import_signature(info),
        symbols=_symbol_signature(info),
        calls=_calls_signature(info, source),
        content_hash=content_hash,
    )


@dataclass
class ProjectAnalysisCache:
    """Caches derived graphs keyed by project or file revision."""

    project_revision: str | None = None
    import_graph_revision: str | None = None
    call_index_revision: str | None = None
    reverse_index_revision: str | None = None
    file_fingerprints: dict[str, FileFingerprint] = field(default_factory=dict)
    file_derived_signatures: dict[str, FileDerivedSignatures] = field(default_factory=dict)
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

    def _layer_revision(self, paths: list[str], facet: str) -> str:
        parts: list[str] = []
        for path in sorted(realpath(item) for item in paths):
            if not exists(path):
                self.file_fingerprints.pop(path, None)
                self.file_derived_signatures.pop(path, None)
                continue
            fingerprint = self.file_fingerprints.get(path)
            if fingerprint is None or fingerprint.mtime != getmtime(path) or fingerprint.size != getsize(path):
                fingerprint = file_fingerprint(path)
                self.file_fingerprints[path] = fingerprint
            signatures = self.file_derived_signatures.get(path)
            if signatures is None or signatures.content_hash != fingerprint.content_hash:
                facet_value = fingerprint.content_hash
            else:
                facet_value = getattr(signatures, facet)
            parts.append(f"{path}:{facet_value}")
        return _digest_parts(parts)

    def refresh_signatures(self, python_files: list[str], module_cache: Any) -> None:
        """Store derived signatures for all project files."""
        for path in python_files:
            path = realpath(path)
            if not exists(path):
                continue
            info = module_cache.get(path)
            with open(path, encoding="utf-8", errors="replace") as handle:
                source = handle.read()
            fingerprint = file_fingerprint(path)
            self.file_fingerprints[path] = fingerprint
            self.file_derived_signatures[path] = compute_file_derived_signatures(
                info,
                source,
                content_hash=fingerprint.content_hash,
            )

    def _needs_signature_refresh(self, paths: list[str]) -> bool:
        for path in paths:
            if realpath(path) not in self.file_derived_signatures:
                return True
        return False

    def get_or_build_import_graph(
        self,
        paths: list[str],
        builder: Callable[[], GraphIR],
        refresh: Callable[[], None] | None = None,
    ) -> GraphIR:
        if refresh is not None and self._needs_signature_refresh(paths):
            refresh()
        revision = self._layer_revision(paths, "imports")
        if self.import_graph is not None and self.import_graph_revision == revision:
            self.import_graph_hits += 1
            return self.import_graph
        self.import_graph_misses += 1
        self.import_graph = builder()
        if refresh is not None:
            refresh()
        self.import_graph_revision = revision
        self.project_revision = revision
        return self.import_graph

    def get_or_build_call_index(
        self,
        paths: list[str],
        builder: Callable[[], T],
        refresh: Callable[[], None] | None = None,
    ) -> T:
        if refresh is not None and self._needs_signature_refresh(paths):
            refresh()
        revision = self._layer_revision(paths, "calls")
        if self.call_index is not None and self.call_index_revision == revision:
            self.call_index_hits += 1
            return cast(T, self.call_index)
        self.call_index_misses += 1
        self.call_index = builder()
        if refresh is not None:
            refresh()
        self.call_index_revision = revision
        return self.call_index

    def get_or_build_reverse_index(
        self,
        paths: list[str],
        builder: Callable[[], T],
        refresh: Callable[[], None] | None = None,
    ) -> T:
        if refresh is not None and self._needs_signature_refresh(paths):
            refresh()
        revision = self._layer_revision(paths, "symbols")
        if self.reverse_index is not None and self.reverse_index_revision == revision:
            self.reverse_index_hits += 1
            return cast(T, self.reverse_index)
        self.reverse_index_misses += 1
        self.reverse_index = builder()
        if refresh is not None:
            refresh()
        self.reverse_index_revision = revision
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
        self.import_graph_revision = None
        self.call_index_revision = None
        self.reverse_index_revision = None
        self.import_graph = None
        self.call_index = None
        self.reverse_index = None

    def invalidate_file(
        self,
        path: str,
        *,
        old_signatures: FileDerivedSignatures | None,
        new_signatures: FileDerivedSignatures,
    ) -> None:
        """Drop only derived caches affected by a file change."""
        path = realpath(path)
        self.file_fingerprints.pop(path, None)
        self.file_derived_signatures[path] = new_signatures

        if old_signatures is None:
            self.invalidate_graphs()
        else:
            if old_signatures.imports != new_signatures.imports:
                self.import_graph = None
                self.import_graph_revision = None
            if old_signatures.calls != new_signatures.calls:
                self.call_index = None
                self.call_index_revision = None
            if old_signatures.symbols != new_signatures.symbols:
                self.reverse_index = None
                self.reverse_index_revision = None

        file_name = basename(path)
        prefix = f"{file_name}:function:"
        for function_id in list(self.cfg_by_function):
            if function_id.startswith(prefix):
                del self.cfg_by_function[function_id]

    def clear(self) -> None:
        self.invalidate_graphs()
        self.file_fingerprints.clear()
        self.file_derived_signatures.clear()
        self.cfg_by_function.clear()

    def stats(self, module_cache_stats: dict[str, int]) -> dict[str, Any]:
        return {
            "project_revision": self.project_revision,
            "import_graph_revision": self.import_graph_revision,
            "call_index_revision": self.call_index_revision,
            "reverse_index_revision": self.reverse_index_revision,
            "file_fingerprint_entries": len(self.file_fingerprints),
            "file_signature_entries": len(self.file_derived_signatures),
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
