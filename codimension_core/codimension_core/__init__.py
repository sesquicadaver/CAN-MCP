# -*- coding: utf-8 -*-
"""Headless code analysis core for Codimension."""

from . import graph_ir
from .analyzer import AnalysisSession
from .cache import ModuleInfoCache
from .callgraph import build_call_graph, find_callees, find_callers, impact_analysis
from .cfg import get_control_flow
from .dependency_graph import build_import_graph
from .errors import AnalysisError, ProjectNotOpenError
from .imports import build_import_context, collect_unresolved_packages, resolve_imports_for_file
from .project import Project
from .symbols import analyze_file, get_symbols

__all__ = [
    "AnalysisSession",
    "AnalysisError",
    "ModuleInfoCache",
    "Project",
    "ProjectNotOpenError",
    "analyze_file",
    "build_call_graph",
    "build_import_context",
    "build_import_graph",
    "collect_unresolved_packages",
    "find_callers",
    "find_callees",
    "get_control_flow",
    "get_symbols",
    "graph_ir",
    "impact_analysis",
    "resolve_imports_for_file",
]

__version__ = "0.2.0"
