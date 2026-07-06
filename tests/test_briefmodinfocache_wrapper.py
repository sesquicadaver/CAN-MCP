# -*- coding: utf-8 -*-
"""Tests for IDE BriefModuleInfoCache wrapper over codimension_core.cache."""

from __future__ import annotations

import importlib.util
import os
import sys

import pytest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
BRIEF_CACHE_PATH = os.path.join(ROOT, "codimension", "utils", "briefmodinfocache.py")


def _load_brief_module_info_cache():
    spec = importlib.util.spec_from_file_location("briefmodinfocache", BRIEF_CACHE_PATH)
    if spec is None or spec.loader is None:
        raise ImportError("Cannot load briefmodinfocache")
    module = importlib.util.module_from_spec(spec)
    sys.modules["briefmodinfocache_test_module"] = module
    spec.loader.exec_module(module)
    return module.BriefModuleInfoCache


def test_brief_modinfo_cache_get_and_hit(tmp_path):
    BriefModuleInfoCache = _load_brief_module_info_cache()
    path = tmp_path / "mod.py"
    path.write_text("def api():\n    return 1\n", encoding="utf-8")

    cache = BriefModuleInfoCache()
    info1 = cache.get(str(path))
    info2 = cache.get(str(path))
    assert info1 is info2
    assert cache._cache.stats()["hits"] == 1


def test_brief_modinfo_cache_missing_file_raises_exception(tmp_path):
    BriefModuleInfoCache = _load_brief_module_info_cache()
    cache = BriefModuleInfoCache()
    with pytest.raises(Exception, match="Cannot open"):
        cache.get(str(tmp_path / "missing.py"))


def test_brief_modinfo_cache_remove_and_clear(tmp_path):
    BriefModuleInfoCache = _load_brief_module_info_cache()
    path = tmp_path / "mod.py"
    path.write_text("x = 1\n", encoding="utf-8")

    cache = BriefModuleInfoCache()
    cache.get(str(path))
    cache.remove(str(path))
    assert cache._cache.stats()["entries"] == 0

    cache.get(str(path))
    cache.clear()
    assert cache._cache.stats()["entries"] == 0
