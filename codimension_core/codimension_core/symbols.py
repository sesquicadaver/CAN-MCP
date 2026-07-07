# -*- coding: utf-8 -*-
"""Symbol extraction via brief parser."""

from __future__ import annotations

import sys
from os.path import basename, realpath

from .brief_ast import getBriefModuleInfoFromFile, getBriefModuleInfoFromMemory
from .capabilities import attach_capability_status, missing_for_feature
from .graph_ir import GraphEdge, GraphIR, GraphNode, enrich_graph_meta, standard_symbol_extra
from .project import Project


def legacy_symbol_id(file_path: str, kind: str, name: str) -> str:
    """Build a basename-based symbol id (legacy, collision-prone)."""
    rel_name = basename(file_path)
    return f"{rel_name}:{kind}:{name}"


def symbol_id(project: Project, file_path: str, kind: str, name: str) -> str:
    """Build a stable project-relative symbol id."""
    rel_path = project.to_relative_path(file_path)
    return f"{rel_path}:{kind}:{name}"


def file_node_id(project: Project, file_path: str) -> str:
    """Build a stable project-relative file node id for Graph IR."""
    rel_path = project.to_relative_path(file_path)
    return f"file:{rel_path}"


def _symbol_id(file_path: str, kind: str, name: str) -> str:
    """Backward-compatible alias for legacy basename ids."""
    return legacy_symbol_id(file_path, kind, name)


def analyze_file(project: Project, path: str) -> GraphIR:
    """Analyze one file and return symbol nodes as Graph IR."""
    project.require_open()
    abs_path = realpath(path)
    if not project.is_project_path(abs_path):
        raise ValueError(f"Path is outside project: {path}")
    info = project.cache.get(abs_path)
    graph = _symbols_from_brief_info(project, abs_path, info)
    return enrich_graph_meta(graph, project_root=project.root)


def get_symbols(project: Project, path: str | None = None) -> GraphIR:
    """Return symbols for one file or the whole project."""
    project.require_open()
    graph = GraphIR(meta={"kind": "symbols"})
    if path:
        graph.nodes.extend(analyze_file(project, path).nodes)
        return enrich_graph_meta(graph, project_root=project.root)
    for file_path in project.python_files:
        info = project.cache.get(file_path)
        graph.nodes.extend(_symbols_from_brief_info(project, file_path, info).nodes)
    return enrich_graph_meta(graph, project_root=project.root)


def _symbols_from_brief_info(project: Project | None, file_path: str, info: object) -> GraphIR:
    graph = GraphIR(meta={"file": file_path, "kind": "symbols"})
    module_name = basename(file_path)
    max_line = 1
    for fn in getattr(info, "functions", []):
        max_line = max(max_line, fn.line, getattr(fn, "colonLine", fn.line))
    for cls in getattr(info, "classes", []):
        max_line = max(max_line, cls.line, getattr(cls, "colonLine", cls.line))
    for glob in getattr(info, "globals", []):
        max_line = max(max_line, glob.line)

    def _node_id(kind: str, name: str) -> str:
        if project is not None:
            return symbol_id(project, file_path, kind, name)
        return legacy_symbol_id(file_path, kind, name)

    graph.add_node(
        GraphNode(
            id=_node_id("module", module_name),
            type="module",
            name=module_name,
            file=file_path,
            line_start=1,
            line_end=max_line,
            extra=_legacy_extra(project, file_path, "module", module_name),
        )
    )

    for fn in getattr(info, "functions", []):
        graph.add_node(
            GraphNode(
                id=_node_id("function", fn.name),
                type="function",
                name=fn.name,
                file=file_path,
                line_start=fn.line,
                line_end=getattr(fn, "colonLine", fn.line),
                extra={
                    "is_async": getattr(fn, "isAsync", False),
                    **standard_symbol_extra(qualname=fn.name, provenance="brief_ast"),
                    **_legacy_extra(project, file_path, "function", fn.name),
                },
            )
        )

    for cls in getattr(info, "classes", []):
        graph.add_node(
            GraphNode(
                id=_node_id("class", cls.name),
                type="class",
                name=cls.name,
                file=file_path,
                line_start=cls.line,
                line_end=getattr(cls, "colonLine", cls.line),
                extra={
                    **standard_symbol_extra(qualname=cls.name, provenance="brief_ast"),
                    **_legacy_extra(project, file_path, "class", cls.name),
                },
            )
        )

    for glob in getattr(info, "globals", []):
        graph.add_node(
            GraphNode(
                id=_node_id("global", glob.name),
                type="global",
                name=glob.name,
                file=file_path,
                line_start=glob.line,
                line_end=glob.line,
                extra=_legacy_extra(project, file_path, "global", glob.name),
            )
        )
    return graph


def _legacy_extra(project: Project | None, file_path: str, kind: str, name: str) -> dict[str, str]:
    if project is None:
        return {}
    canonical = symbol_id(project, file_path, kind, name)
    legacy = legacy_symbol_id(file_path, kind, name)
    if legacy == canonical:
        return {}
    return {"legacy_id": legacy}


def analyze_source(source: str, file_name: str = "<memory>") -> GraphIR:
    """Analyze in-memory source (used in tests)."""
    info = getBriefModuleInfoFromMemory(source, file_name)
    return _symbols_from_brief_info(None, file_name, info)


def analyze_file_direct(path: str) -> GraphIR:
    """Analyze a standalone file without a project context."""
    info = getBriefModuleInfoFromFile(path)
    return _symbols_from_brief_info(None, realpath(path), info)


def parse_symbol_query(symbol: str) -> tuple[str | None, str]:
    parts = symbol.split(":")
    if len(parts) >= 3 and parts[1] in ("function", "class", "global"):
        return parts[0], ":".join(parts[2:])
    return None, symbol


def _definition_sites(project: Project, file_hint: str | None, name: str) -> list[tuple[str, int, int]]:
    sites: list[tuple[str, int, int]] = []
    files = project.python_files
    if file_hint:
        files = [path for path in files if path.endswith("/" + file_hint) or path.endswith("\\" + file_hint)]
    for path in files:
        info = project.cache.get(path)
        for fn in getattr(info, "functions", []):
            if fn.name == name:
                sites.append((path, fn.line, fn.pos))
        for cls in getattr(info, "classes", []):
            if cls.name == name:
                sites.append((path, cls.line, cls.pos))
            for method in getattr(cls, "functions", []):
                qual = f"{cls.name}.{method.name}"
                if qual == name or method.name == name:
                    sites.append((path, method.line, method.pos))
        for glob in getattr(info, "globals", []):
            if glob.name == name:
                sites.append((path, glob.line, glob.pos))
    return sites


def find_usages(project: Project, symbol: str) -> GraphIR:
    """Find references to a symbol using jedi (headless)."""
    project.require_open()
    graph = GraphIR(meta={"kind": "usages", "symbol": symbol})
    missing = missing_for_feature("find_usages")
    if missing:
        attach_capability_status(graph.meta, "find_usages")
        return graph

    import jedi
    from jedi.api.project import Project as JediProject

    file_hint, name = parse_symbol_query(symbol)
    sites = _definition_sites(project, file_hint, name)
    if not sites:
        attach_capability_status(graph.meta, "find_usages")
        return graph

    jedi_project = JediProject(
        path=project.root,
        sys_path=list(sys.path),
        added_sys_path=project.get_import_dirs_absolute(),
    )
    seen: set[tuple[str, int, int]] = set()
    for def_path, line, col in sites:
        with open(def_path, encoding="utf-8", errors="replace") as handle:
            source = handle.read()
        lines = source.splitlines()
        if 0 < line <= len(lines):
            name_col = lines[line - 1].find(name)
            if name_col >= 0:
                col = name_col
        script = jedi.Script(code=source, path=def_path, project=jedi_project)
        try:
            references = script.get_references(line=line, column=col)
        except Exception:
            continue
        for ref in references:
            ref_path = ref.module_path
            if ref_path is None:
                continue
            ref_path = realpath(str(ref_path))
            if not project.is_project_path(ref_path):
                continue
            key = (ref_path, ref.line or 0, ref.column or 0)
            if key in seen:
                continue
            seen.add(key)
            node_id = f"{basename(ref_path)}:usage:{ref.line}:{ref.column}"
            graph.add_node(
                GraphNode(
                    id=node_id,
                    type="usage",
                    name=name,
                    file=ref_path,
                    line_start=ref.line or 0,
                    line_end=ref.line or 0,
                    extra={"column": ref.column or 0},
                )
            )
            graph.add_edge(
                GraphEdge(
                    from_id=symbol_id(project, def_path, "function", name),
                    to_id=node_id,
                    type="usage",
                )
            )
    attach_capability_status(graph.meta, "find_usages")
    return graph
