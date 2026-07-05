# -*- coding: utf-8 -*-
"""Incremental brief module info cache (headless port of BriefModuleInfoCache)."""

from __future__ import annotations

from os.path import exists, getmtime, realpath

import codimension.parsers  # noqa: F401 — install cdmpyparser fallbacks
from cdmpyparser import getBriefModuleInfoFromFile


class ModuleInfoCache:
    """mtime-based cache for brief module info objects."""

    def __init__(self) -> None:
        self._cache: dict[str, tuple[float, object]] = {}

    def get(self, path: str) -> object:
        """Return cached brief module info for an absolute or relative path."""
        path = realpath(path)
        if path in self._cache:
            mod_time, info = self._cache[path]
            if not exists(path):
                del self._cache[path]
                raise FileNotFoundError(f"Cannot open {path}")
            last_mod_time = getmtime(path)
            if last_mod_time <= mod_time:
                return info
            info = getBriefModuleInfoFromFile(path)
            self._cache[path] = (last_mod_time, info)
            return info

        if not exists(path):
            raise FileNotFoundError(f"Cannot open {path}")
        info = getBriefModuleInfoFromFile(path)
        self._cache[path] = (getmtime(path), info)
        return info

    def remove(self, path: str) -> None:
        """Drop one cache entry."""
        self._cache.pop(realpath(path), None)

    def clear(self) -> None:
        """Drop all cache entries."""
        self._cache.clear()
