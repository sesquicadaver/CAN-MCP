# -*- coding: utf-8 -*-
"""Headless code analysis core for Codimension."""

from . import graph_ir
from .analysis_cache import ProjectAnalysisCache, compute_project_revision, file_content_hash, file_fingerprint
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
from .errors import (
    AmbiguousSymbolIdError,
    AnalysisError,
    PathOutsideProjectError,
    ProjectNotOpenError,
    SymbolNotFoundError,
)
from .explain import explain_symbol
from .graph_layout import Graph, layout_graph_from_dot
from .graph_render import graph_to_html, graph_to_mermaid
from .import_diagram import (
    ImportDiagramModel,
    ImportDiagramOptions,
    build_import_diagram_graph_ir,
    build_import_diagram_model,
    import_diagram_model_to_graph_ir,
)
from .imports import (
    ImportResolver,
    build_import_context,
    collect_import_resolutions_classified,
    collect_unresolved_packages,
    generate_requirements_from_project,
    resolve_imports_for_file,
)
from .paths import resolve_project_path
from .project import Project
from .reverse_index import lookup_symbol as lookup_symbol_definitions
from .summaries import build_dependency_summary, build_symbol_summary
from .symbol_registry import build_legacy_alias_map, resolve_symbol_reference
from .symbols import analyze_file, find_usages, get_symbols, legacy_symbol_id, symbol_id

__all__ = [
    "AnalysisError",
    "AmbiguousSymbolIdError",
    "ModuleInfoCache",
    "PathOutsideProjectError",
    "Project",
    "ProjectAnalysisCache",
    "ProjectNotOpenError",
    "SymbolNotFoundError",
    "ImportDiagramModel",
    "ImportDiagramOptions",
    "OPT_NO_OPTIMIZATION",
    "OPT_OPTIMIZE_ASSERT",
    "OPT_OPTIMIZE_DOCSTRINGS",
    "analyze_file",
    "analyze_dead_code",
    "analyze_file_diagnostics",
    "build_call_graph",
    "ImportResolver",
    "build_import_context",
    "build_import_diagram_graph_ir",
    "build_import_diagram_model",
    "import_diagram_model_to_graph_ir",
    "build_dependency_summary",
    "build_import_graph",
    "build_symbol_summary",
    "collect_import_resolutions_classified",
    "collect_unresolved_packages",
    "generate_requirements_from_project",
    "compute_project_revision",
    "explain_symbol",
    "find_callers",
    "find_callees",
    "find_usages",
    "file_content_hash",
    "file_fingerprint",
    "get_buffer_disassembled",
    "get_file_disassembled",
    "get_buffer_errors",
    "get_control_flow",
    "get_symbols",
    "Graph",
    "graph_ir",
    "graph_to_html",
    "graph_to_mermaid",
    "layout_graph_from_dot",
    "impact_analysis",
    "lookup_symbol_definitions",
    "legacy_symbol_id",
    "parse_source_to_ast",
    "resolve_imports_for_file",
    "resolve_project_path",
    "resolve_symbol_reference",
    "build_legacy_alias_map",
    "symbol_id",
]

__version__ = "0.27.0"
