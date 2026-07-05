# -*- coding: utf-8 -*-
"""Headless code analysis core for Codimension."""

from . import graph_ir
from .analyzer import AnalysisSession
from .cache import ModuleInfoCache
from .cfg import get_control_flow
from .dependency_graph import build_import_graph
from .errors import AnalysisError, ProjectNotOpenError
from .project import Project
from .symbols import analyze_file, get_symbols

__all__ = [
    "AnalysisSession",
    "AnalysisError",
    "ModuleInfoCache",
    "Project",
    "ProjectNotOpenError",
    "analyze_file",
    "build_import_graph",
    "get_control_flow",
    "get_symbols",
    "graph_ir",
]

__version__ = "0.1.0"
