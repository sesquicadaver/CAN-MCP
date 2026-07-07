# -*- coding: utf-8 -*-
"""Optional jedi refinement for call graph edges."""

from __future__ import annotations

import pytest

from codimension_core import Project
from codimension_core.callgraph import build_call_graph

pytest.importorskip("jedi")


def test_jedi_refines_import_resolved_call(tmp_path):
    project_dir = tmp_path / "proj"
    project_dir.mkdir()
    (project_dir / "pkg").mkdir()
    (project_dir / "pkg" / "utils.py").write_text("def helper():\n    return 1\n", encoding="utf-8")
    (project_dir / "pkg" / "app.py").write_text(
        "from pkg.utils import helper\n\ndef run():\n    return helper()\n",
        encoding="utf-8",
    )

    project = Project.open(str(project_dir))
    graph = build_call_graph(project)
    edge = next(edge for edge in graph.edges if edge.type == "calls")
    assert edge.to_id.endswith("pkg/utils.py:function:helper")
    assert edge.extra.get("provenance") == "jedi"
    assert edge.extra.get("confidence", 0) >= 0.9
