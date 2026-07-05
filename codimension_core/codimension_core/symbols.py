# -*- coding: utf-8 -*-
"""Symbol extraction via brief parser."""

from __future__ import annotations

from os.path import basename, realpath

import codimension.parsers  # noqa: F401
from cdmpyparser import getBriefModuleInfoFromFile, getBriefModuleInfoFromMemory

from .graph_ir import GraphIR, GraphNode
from .project import Project


def _symbol_id(file_path: str, kind: str, name: str) -> str:
    rel_name = basename(file_path)
    return f"{rel_name}:{kind}:{name}"


def analyze_file(project: Project, path: str) -> GraphIR:
    """Analyze one file and return symbol nodes as Graph IR."""
    project.require_open()
    abs_path = realpath(path)
    if not project.is_project_path(abs_path):
        raise ValueError(f"Path is outside project: {path}")
    info = project.cache.get(abs_path)
    return _symbols_from_brief_info(abs_path, info)


def get_symbols(project: Project, path: str | None = None) -> GraphIR:
    """Return symbols for one file or the whole project."""
    project.require_open()
    graph = GraphIR(meta={"kind": "symbols"})
    if path:
        graph.nodes.extend(analyze_file(project, path).nodes)
        return graph
    for file_path in project.python_files:
        info = project.cache.get(file_path)
        graph.nodes.extend(_symbols_from_brief_info(file_path, info).nodes)
    return graph


def _symbols_from_brief_info(file_path: str, info: object) -> GraphIR:
    graph = GraphIR(meta={"file": file_path, "kind": "symbols"})
    module_name = basename(file_path)
    max_line = 1
    for fn in getattr(info, "functions", []):
        max_line = max(max_line, fn.line, getattr(fn, "colonLine", fn.line))
    for cls in getattr(info, "classes", []):
        max_line = max(max_line, cls.line, getattr(cls, "colonLine", cls.line))
    for glob in getattr(info, "globals", []):
        max_line = max(max_line, glob.line)

    graph.add_node(
        GraphNode(
            id=_symbol_id(file_path, "module", module_name),
            type="module",
            name=module_name,
            file=file_path,
            line_start=1,
            line_end=max_line,
        )
    )

    for fn in getattr(info, "functions", []):
        graph.add_node(
            GraphNode(
                id=_symbol_id(file_path, "function", fn.name),
                type="function",
                name=fn.name,
                file=file_path,
                line_start=fn.line,
                line_end=getattr(fn, "colonLine", fn.line),
                extra={"is_async": getattr(fn, "isAsync", False)},
            )
        )

    for cls in getattr(info, "classes", []):
        graph.add_node(
            GraphNode(
                id=_symbol_id(file_path, "class", cls.name),
                type="class",
                name=cls.name,
                file=file_path,
                line_start=cls.line,
                line_end=getattr(cls, "colonLine", cls.line),
            )
        )

    for glob in getattr(info, "globals", []):
        graph.add_node(
            GraphNode(
                id=_symbol_id(file_path, "global", glob.name),
                type="global",
                name=glob.name,
                file=file_path,
                line_start=glob.line,
                line_end=glob.line,
            )
        )
    return graph


def analyze_source(source: str, file_name: str = "<memory>") -> GraphIR:
    """Analyze in-memory source (used in tests)."""
    info = getBriefModuleInfoFromMemory(source, file_name)
    return _symbols_from_brief_info(file_name, info)


def analyze_file_direct(path: str) -> GraphIR:
    """Analyze a standalone file without a project context."""
    info = getBriefModuleInfoFromFile(path)
    return _symbols_from_brief_info(realpath(path), info)
