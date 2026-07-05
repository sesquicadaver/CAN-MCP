# -*- coding: utf-8 -*-
"""Lint and complexity analysis extracted from codimension.analysis.ierrors."""

from __future__ import annotations

import ast
import re
from os.path import basename, join, realpath
from typing import Any

from .graph_ir import GraphIR, GraphNode
from .project import Project

IGNORE_REGEXP = re.compile(r"analysis:\s*(off|disable|ignore)", re.IGNORECASE)


def get_buffer_errors(source_code: str, file_name: str = "<string>") -> tuple[dict[int, list[str]], list[Any]]:
    """Return pyflakes messages by line and radon complexity results."""
    from pyflakes.checker import Checker
    from radon.complexity import cc_visit_ast, sorted_results

    source_code += "\n"
    try:
        tree = compile(source_code, file_name, "exec", ast.PyCF_ONLY_AST)
    except SyntaxError as value:
        if value.text is None:
            return {}, []
        return {value.lineno: [value.args[0]]}, []
    except (ValueError, TypeError) as value:
        msg = str(value)
        if msg == "":
            return {-1: ["Could not compile buffer: unknown error"]}, []
        return {-1: ["Could not compile buffer: " + msg]}, []

    check = Checker(tree, file_name)
    results: dict[int, list[str]] = {}
    lines = source_code.splitlines()
    for warning in check.messages:
        if isinstance(warning.lineno, int):
            lineno = warning.lineno
        else:
            lineno = warning.lineno.lineno
        if 0 < lineno <= len(lines) and IGNORE_REGEXP.search(lines[lineno - 1]):
            continue
        message = warning.message % warning.message_args
        results.setdefault(lineno, []).append(message)

    return results, sorted_results(cc_visit_ast(tree))


def analyze_file_diagnostics(project: Project, path: str) -> GraphIR:
    """Return lint/complexity findings as Graph IR nodes."""
    project.require_open()
    abs_path = realpath(path) if path.startswith("/") else realpath(join(project.root, path))
    with open(abs_path, encoding="utf-8", errors="replace") as handle:
        source = handle.read()
    errors, complexity = get_buffer_errors(source, abs_path)
    graph = GraphIR(meta={"kind": "diagnostics", "file": abs_path})
    for line_no, messages in errors.items():
        for index, message in enumerate(messages):
            node_id = f"{basename(abs_path)}:lint:{line_no}:{index}"
            graph.add_node(
                GraphNode(
                    id=node_id,
                    type="lint",
                    name=message,
                    file=abs_path,
                    line_start=max(line_no, 1),
                    line_end=max(line_no, 1),
                    extra={"severity": "warning"},
                )
            )
    for item in complexity:
        node_id = f"{basename(abs_path)}:complexity:{item.lineno}:{item.name}"
        graph.add_node(
            GraphNode(
                id=node_id,
                type="complexity",
                name=item.name,
                file=abs_path,
                line_start=item.lineno,
                line_end=item.lineno,
                extra={"rank": item.rank, "complexity": item.complexity},
            )
        )
    return graph
