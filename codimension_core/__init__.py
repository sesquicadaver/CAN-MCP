# -*- coding: utf-8 -*-
"""Re-export nested codimension_core when the subproject root is on sys.path."""

from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

_INNER = Path(__file__).resolve().parent / "codimension_core"
_spec = importlib.util.spec_from_file_location(
    "codimension_core",
    _INNER / "__init__.py",
    submodule_search_locations=[str(_INNER)],
)
if _spec is None or _spec.loader is None:
    raise ImportError("codimension_core package layout is broken")
_module = importlib.util.module_from_spec(_spec)
sys.modules[__name__] = _module
_spec.loader.exec_module(_module)
