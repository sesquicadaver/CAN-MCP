# -*- coding: utf-8 -*-
"""Optional dependency probes and graceful degradation for analysis features."""

from __future__ import annotations

import importlib
from typing import Final

FEATURE_DEPENDENCIES: Final[dict[str, tuple[str, ...]]] = {
    "diagnostics": ("pyflakes", "radon"),
    "find_usages": ("jedi",),
    "dead_code": ("vulture",),
}


def missing_packages(*package_names: str) -> list[str]:
    """Return package names that are not importable in the current environment."""
    missing: list[str] = []
    for name in package_names:
        try:
            importlib.import_module(name)
        except ImportError:
            missing.append(name)
    return missing


def missing_for_feature(feature: str) -> list[str]:
    """Return missing packages required for a named analysis feature."""
    return missing_packages(*FEATURE_DEPENDENCIES.get(feature, ()))


def attach_capability_status(meta: dict[str, object], feature: str) -> dict[str, object]:
    """Set meta status to ok or partial based on optional dependency availability."""
    missing = missing_for_feature(feature)
    if missing:
        meta["status"] = "partial"
        meta["missing"] = missing
        meta["feature"] = feature
    else:
        meta.setdefault("status", "ok")
    return meta
