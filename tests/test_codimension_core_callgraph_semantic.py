# -*- coding: utf-8 -*-
"""Semantic resolution tests for static call graph."""

from __future__ import annotations

from codimension_core import Project
from codimension_core.callgraph import build_call_graph, impact_analysis


def _call_targets(graph) -> set[str]:
    return {edge.to_id for edge in graph.edges if edge.type == "calls"}


def test_callgraph_resolves_package_import_to_nested_module(tmp_path):
    project_dir = tmp_path / "proj"
    (project_dir / "pkg" / "sub").mkdir(parents=True)
    (project_dir / "pkg" / "sub" / "lib.py").write_text("def fn():\n    return 1\n", encoding="utf-8")
    (project_dir / "pkg" / "app.py").write_text(
        "from pkg.sub.lib import fn\n\ndef run():\n    return fn()\n",
        encoding="utf-8",
    )

    project = Project.open(str(project_dir))
    graph = build_call_graph(project)
    targets = _call_targets(graph)
    assert any(target.endswith("pkg/sub/lib.py:function:fn") for target in targets)


def test_callgraph_resolves_relative_import(tmp_path):
    project_dir = tmp_path / "proj"
    (project_dir / "pkg").mkdir(parents=True)
    (project_dir / "pkg" / "__init__.py").write_text("", encoding="utf-8")
    (project_dir / "pkg" / "utils.py").write_text("def helper():\n    return 1\n", encoding="utf-8")
    (project_dir / "pkg" / "app.py").write_text(
        "from .utils import helper\n\ndef run():\n    return helper()\n",
        encoding="utf-8",
    )

    project = Project.open(str(project_dir))
    graph = build_call_graph(project)
    targets = _call_targets(graph)
    assert any(target.endswith("pkg/utils.py:function:helper") for target in targets)


def test_callgraph_resolves_self_method_call(tmp_path):
    project_dir = tmp_path / "proj"
    project_dir.mkdir()
    (project_dir / "main.py").write_text(
        "class Worker:\n    def run(self):\n        return self.process()\n\n    def process(self):\n        return 1\n",
        encoding="utf-8",
    )

    project = Project.open(str(project_dir))
    graph = build_call_graph(project)
    targets = _call_targets(graph)
    assert any(target.endswith("main.py:function:Worker.process") for target in targets)
    edge = next(edge for edge in graph.edges if edge.type == "calls")
    assert edge.extra.get("confidence", 0) >= 0.8


def test_callgraph_propagates_instance_type_through_alias(tmp_path):
    project_dir = tmp_path / "proj"
    (project_dir / "pkg").mkdir(parents=True)
    (project_dir / "pkg" / "worker.py").write_text(
        "class Worker:\n    def run(self):\n        return self.process()\n\n    def process(self):\n        return 1\n",
        encoding="utf-8",
    )
    (project_dir / "main.py").write_text(
        "from pkg.worker import Worker\n\ndef main():\n    worker = Worker()\n    w = worker\n    w.run()\n",
        encoding="utf-8",
    )

    project = Project.open(str(project_dir))
    graph = build_call_graph(project)
    edge = next(edge for edge in graph.edges if edge.type == "calls" and edge.label.startswith("w.run:"))
    assert edge.to_id.endswith("pkg/worker.py:function:Worker.run")
    assert edge.extra.get("confidence", 0) >= 0.8


def test_callgraph_nested_import_attribute_has_dotted_label(tmp_path):
    project_dir = tmp_path / "proj"
    project_dir.mkdir()
    (project_dir / "main.py").write_text(
        "import os\n\ndef main():\n    return os.path.join('a', 'b')\n",
        encoding="utf-8",
    )

    project = Project.open(str(project_dir))
    graph = build_call_graph(project)
    edge = next(edge for edge in graph.edges if edge.type == "calls")
    assert edge.label == "os.path.join:4"
    assert edge.to_id == "external:function:os.path.join"
    assert edge.extra.get("confidence", 0) >= 0.55


def test_callgraph_resolves_instance_method_on_local_variable(tmp_path):
    project_dir = tmp_path / "proj"
    (project_dir / "pkg").mkdir(parents=True)
    (project_dir / "pkg" / "worker.py").write_text(
        "class Worker:\n    def run(self):\n        return self.process()\n\n    def process(self):\n        return 1\n",
        encoding="utf-8",
    )
    (project_dir / "main.py").write_text(
        "from pkg.app import run\nfrom pkg.worker import Worker\n\ndef main():\n    worker = Worker()\n    worker.run()\n    return run()\n",
        encoding="utf-8",
    )
    (project_dir / "pkg" / "app.py").write_text("def run():\n    return 0\n", encoding="utf-8")

    project = Project.open(str(project_dir))
    graph = build_call_graph(project)
    worker_run = next(
        edge
        for edge in graph.edges
        if edge.type == "calls" and edge.label.startswith("worker.run:")
    )
    assert worker_run.to_id.endswith("pkg/worker.py:function:Worker.run")
    assert worker_run.extra.get("confidence", 0) >= 0.8


def test_callgraph_external_call_has_low_confidence(tmp_path):
    project_dir = tmp_path / "proj"
    project_dir.mkdir()
    (project_dir / "main.py").write_text("def run():\n    return unknown()\n", encoding="utf-8")

    project = Project.open(str(project_dir))
    graph = build_call_graph(project)
    edge = next(edge for edge in graph.edges if edge.type == "calls")
    assert edge.to_id.startswith("external:function:")
    assert edge.extra.get("confidence") == 0.3


def test_impact_analysis_accepts_canonical_symbol_id(tmp_path):
    project_dir = tmp_path / "proj"
    project_dir.mkdir()
    (project_dir / "pkg").mkdir()
    (project_dir / "pkg" / "leaf.py").write_text("def leaf():\n    return 1\n", encoding="utf-8")
    (project_dir / "pkg" / "mid.py").write_text(
        "from pkg.leaf import leaf\n\ndef middle():\n    return leaf()\n",
        encoding="utf-8",
    )
    (project_dir / "pkg" / "top.py").write_text(
        "from pkg.mid import middle\n\ndef top():\n    return middle()\n",
        encoding="utf-8",
    )

    project = Project.open(str(project_dir))
    project.analyze_all()
    graph = impact_analysis(project, "pkg/leaf.py:function:leaf")
    assert graph.meta.get("resolved_symbol", "").endswith("pkg/leaf.py:function:leaf")
    assert graph.meta["impacted_count"] >= 2
