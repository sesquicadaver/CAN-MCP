# -*- coding: utf-8 -*-
"""Lint and complexity analysis extracted from codimension.analysis.ierrors."""

from __future__ import annotations

import ast
import os
import re
import sys
from os.path import basename, dirname, isdir, isfile, join, realpath
from subprocess import PIPE, Popen
from typing import Any

from .capabilities import attach_capability_status, missing_for_feature
from .graph_ir import GraphIR, GraphNode, enrich_graph_meta
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
        if value.text is None or value.lineno is None:
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
    graph = GraphIR(meta={"kind": "diagnostics", "file": abs_path})
    missing = missing_for_feature("diagnostics")
    if missing:
        attach_capability_status(graph.meta, "diagnostics")
        return enrich_graph_meta(graph, project_root=project.root)
    with open(abs_path, encoding="utf-8", errors="replace") as handle:
        source = handle.read()
    errors, complexity = get_buffer_errors(source, abs_path)
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
                extra={"rank": item.letter, "complexity": item.complexity},
            )
            )
    attach_capability_status(graph.meta, "diagnostics")
    return enrich_graph_meta(graph, project_root=project.root)


def build_vulture_exclude_patterns(project: Project) -> str:
    """Build comma-separated vulture --exclude patterns for a project."""
    project.require_open()
    patterns = [".venv", "venv", "__pycache__", ".git", ".mypy_cache", ".ruff_cache"]
    venv_dir = project.get_site_packages()
    if venv_dir:
        patterns.append(dirname(dirname(venv_dir)))
    for path in project.exclude_from_analysis:
        abs_path = path if os.path.isabs(path) else join(project.root, path)
        if abs_path:
            patterns.append(realpath(abs_path))
    return ",".join(patterns)


def find_pyproject_vulture_config(project: Project) -> str | None:
    """Return pyproject.toml path if it contains [tool.vulture]."""
    config_path = join(project.root, "pyproject.toml")
    if not isfile(config_path):
        return None
    with open(config_path, encoding="utf-8", errors="replace") as handle:
        content = handle.read()
    if "[tool.vulture]" in content:
        return config_path
    return None


def run_vulture(
    target_path: str,
    *,
    exclude: str | None = None,
    config_path: str | None = None,
    python_executable: str | None = None,
) -> tuple[list[str], str]:
    """Run vulture and return stdout lines and stderr text."""
    interpreter = python_executable or sys.executable
    cmd = [interpreter, "-m", "vulture"]
    if config_path:
        cmd.extend(["--config", config_path])
    if exclude and isdir(target_path):
        cmd.extend(["--exclude", exclude])
    cmd.append(target_path)
    process = Popen(cmd, stdout=PIPE, stderr=PIPE)
    stdout_bytes, stderr_bytes = process.communicate()
    stdout = stdout_bytes.decode("utf-8", errors="replace")
    stderr = stderr_bytes.decode("utf-8", errors="replace").strip()
    lines = [line.strip() for line in stdout.splitlines() if line.strip()]
    return lines, stderr


def _parse_vulture_line(line: str) -> tuple[str, int, str] | None:
    try:
        first = line.find(":")
        if first < 0:
            return None
        second = line.find(":", first + 1)
        if second < 0:
            return None
        file_name = realpath(line[:first])
        line_no = int(line[first + 1 : second])
        message = line[second + 1 :].strip()
        return file_name, line_no, message
    except (ValueError, OSError):
        return None


def analyze_dead_code(project: Project, path: str | None = None) -> GraphIR:
    """Run vulture on project root or one path; return findings as Graph IR."""
    project.require_open()
    target = realpath(path) if path else project.root
    graph = GraphIR(meta={"kind": "dead_code", "target": target})
    missing = missing_for_feature("dead_code")
    if missing:
        attach_capability_status(graph.meta, "dead_code")
        return graph
    exclude = build_vulture_exclude_patterns(project) if isdir(target) else None
    config_path = find_pyproject_vulture_config(project)
    lines, stderr = run_vulture(
        target,
        exclude=exclude,
        config_path=config_path,
        python_executable=project.get_python_executable(),
    )
    graph.meta["stderr"] = stderr
    for index, line in enumerate(lines):
        parsed = _parse_vulture_line(line)
        if parsed is None:
            continue
        file_name, line_no, message = parsed
        node_id = f"{basename(file_name)}:dead_code:{line_no}:{index}"
        graph.add_node(
            GraphNode(
                id=node_id,
                type="dead_code",
                name=message,
                file=file_name,
                line_start=line_no,
                line_end=line_no,
                extra={"source": "vulture"},
            )
        )
    attach_capability_status(graph.meta, "dead_code")
    return graph
