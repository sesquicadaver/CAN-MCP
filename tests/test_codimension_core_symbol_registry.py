# -*- coding: utf-8 -*-
"""Tests for ambiguous legacy symbol resolution."""

from __future__ import annotations

import pytest

from codimension_core import Project
from codimension_core.callgraph import find_callers
from codimension_core.errors import AmbiguousSymbolIdError


def test_find_callers_rejects_ambiguous_legacy_id(tmp_path):
    project_dir = tmp_path / "proj"
    (project_dir / "pkg" / "a").mkdir(parents=True)
    (project_dir / "pkg" / "b").mkdir(parents=True)
    (project_dir / "pkg" / "a" / "utils.py").write_text(
        "def foo():\n    return 1\n",
        encoding="utf-8",
    )
    (project_dir / "pkg" / "b" / "utils.py").write_text(
        "def foo():\n    return 2\n",
        encoding="utf-8",
    )
    (project_dir / "main.py").write_text(
        "from pkg.a.utils import foo\n\ndef run():\n    return foo()\n",
        encoding="utf-8",
    )

    project = Project.open(str(project_dir))
    project.analyze_all()

    with pytest.raises(AmbiguousSymbolIdError):
        find_callers(project, "utils.py:function:foo")
