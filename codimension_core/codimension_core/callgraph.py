# -*- coding: utf-8 -*-
"""Static call graph — planned extraction (currently stub)."""

from __future__ import annotations

from .errors import NotImplementedYetError
from .graph_ir import GraphIR
from .project import Project


def build_call_graph(project: Project, symbol: str | None = None) -> GraphIR:
    """Build a static inter-procedural call graph."""
    project.require_open()
    raise NotImplementedYetError(
        "Static call graph is not implemented yet. "
        "See doc/CODIMENSION-CORE-MAP.md — codimension/profiling/profgraph.py "
        "only provides runtime profiling graphs."
    )


def find_callers(project: Project, symbol: str) -> GraphIR:
    """Find functions that call the given symbol."""
    project.require_open()
    raise NotImplementedYetError("find_callers requires static call graph (not implemented).")


def find_callees(project: Project, symbol: str) -> GraphIR:
    """Find functions called by the given symbol."""
    project.require_open()
    raise NotImplementedYetError("find_callees requires static call graph (not implemented).")


def impact_analysis(project: Project, target: str) -> GraphIR:
    """Estimate blast radius for a file or symbol change."""
    project.require_open()
    raise NotImplementedYetError("impact_analysis requires call + dependency graphs (not implemented).")
