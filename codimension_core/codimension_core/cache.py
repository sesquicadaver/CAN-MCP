# -*- coding: utf-8 -*-
"""Incremental brief module info cache (headless port of BriefModuleInfoCache)."""

from __future__ import annotations

from os.path import exists, getmtime, getsize, realpath

from .brief_ast import getBriefModuleInfoFromFile

from .analysis_cache import file_content_hash


class ModuleInfoCache:
    """Content-hash cache for brief module info objects."""

    def __init__(self) -> None:
        self._cache: dict[str, tuple[float, int, str, object]] = {}
        self.hits: int = 0
        self.misses: int = 0

    def get(self, path: str) -> object:
        """Return cached brief module info for an absolute or relative path."""
        path = realpath(path)
        if not exists(path):
            self._cache.pop(path, None)
            raise FileNotFoundError(f"Cannot open {path}")

        last_mod_time = getmtime(path)
        last_size = getsize(path)
        if path in self._cache:
            mod_time, size, content_hash, info = self._cache[path]
            if mod_time == last_mod_time and size == last_size:
                self.hits += 1
                return info
            if file_content_hash(path) == content_hash:
                self._cache[path] = (last_mod_time, last_size, content_hash, info)
                self.hits += 1
                return info

        info = getBriefModuleInfoFromFile(path)
        content_hash = file_content_hash(path)
        self._cache[path] = (last_mod_time, last_size, content_hash, info)
        self.misses += 1
        return info

    def remove(self, path: str) -> None:
        """Drop one cache entry."""
        self._cache.pop(realpath(path), None)

    def clear(self) -> None:
        """Drop all cache entries."""
        self._cache.clear()

    def stats(self) -> dict[str, int]:
        return {"entries": len(self._cache), "hits": self.hits, "misses": self.misses}
