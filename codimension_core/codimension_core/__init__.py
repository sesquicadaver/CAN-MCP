# -*- coding: utf-8 -*-
"""Headless code analysis core for Codimension."""

from . import graph_ir
from .analysis_cache import ProjectAnalysisCache, compute_project_revision, file_fingerprint
from .analyzer import analyze_dead_code, analyze_file_diagnostics, get_buffer_errors
from .astutils import parse_source_to_ast
from .cache import ModuleInfoCache
from .callgraph import build_call_graph, find_callees, find_callers, impact_analysis
from .cfg import get_control_flow
from .dependency_graph import build_import_graph
from .disasm import (
    OPT_NO_OPTIMIZATION,
    OPT_OPTIMIZE_ASSERT,
    OPT_OPTIMIZE_DOCSTRINGS,
    get_buffer_disassembled,
    get_file_disassembled,
)
from .errors import AnalysisError, ProjectNotOpenError
from .explain import explain_symbol
from .graph_render import graph_to_html, graph_to_mermaid
from .import_diagram import (
    ImportDiagramModel,
    ImportDiagramOptions,
    build_import_diagram_graph_ir,
    build_import_diagram_model,
    import_diagram_model_to_graph_ir,
)
from .imports import (
    build_import_context,
    collect_import_resolutions_classified,
    collect_unresolved_packages,
    resolve_imports_for_file,
)
from .project import Project
from .reverse_index import lookup_symbol as lookup_symbol_definitions
from .symbols import analyze_file, find_usages, get_symbols

__all__ = [
    "AnalysisError",
    "ModuleInfoCache",
    "Project",
    "ProjectAnalysisCache",
    "ProjectNotOpenError",
    "ImportDiagramModel",
    "ImportDiagramOptions",
    "OPT_NO_OPTIMIZATION",
    "OPT_OPTIMIZE_ASSERT",
    "OPT_OPTIMIZE_DOCSTRINGS",
    "analyze_file",
    "analyze_dead_code",
    "analyze_file_diagnostics",
    "build_call_graph",
    "build_import_context",
    "build_import_diagram_graph_ir",
    "build_import_diagram_model",
    "import_diagram_model_to_graph_ir",
    "build_import_graph",
    "collect_import_resolutions_classified",
    "collect_unresolved_packages",
    "compute_project_revision",
    "explain_symbol",
    "find_callers",
    "find_callees",
    "find_usages",
    "file_fingerprint",
    "get_buffer_disassembled",
    "get_file_disassembled",
    "get_buffer_errors",
    "get_control_flow",
    "get_symbols",
    "graph_ir",
    "graph_to_html",
    "graph_to_mermaid",
    "impact_analysis",
    "lookup_symbol_definitions",
    "parse_source_to_ast",
    "resolve_imports_for_file",
]

__version__ = "0.11.0"
