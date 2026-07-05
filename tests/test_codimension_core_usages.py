# -*- coding: utf-8 -*-
"""Tests for find_usages via jedi."""

from __future__ import annotations

import pytest

from codimension_core.project import Project
from codimension_core.symbols import find_usages

pytest.importorskip("jedi")


def test_find_usages_local_function(tmp_path):
    project_dir = tmp_path / "proj"
    project_dir.mkdir()
    (project_dir / "main.py").write_text(
        "def helper():\n    return 1\n\ndef run():\n    x = helper()\n    return x\n",
        encoding="utf-8",
    )
    project = Project.open(str(project_dir))
    graph = find_usages(project, "helper")
    assert graph.meta["kind"] == "usages"
    assert len(graph.nodes) >= 1
