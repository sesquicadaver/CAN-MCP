# -*- coding: utf-8 -*-
"""MCP prompt templates for common Codimension analysis workflows."""

from __future__ import annotations

from collections.abc import Callable

from mcp.server.fastmcp import FastMCP


def build_refactor_symbol_prompt(symbol: str) -> str:
    """Return workflow text for safe symbol refactoring."""
    return (
        f"You are refactoring `{symbol}` in an open Python project.\n"
        "1. Call `explain_symbol` with the full symbol id (e.g. file.py:function:name).\n"
        "2. Call `impact_analysis` for the same target to list transitive callers and import dependents.\n"
        "3. Call `find_usages` and `find_callers` to confirm references.\n"
        "4. Propose minimal edits and list tests to run before merging."
    )


def build_review_dead_code_prompt() -> str:
    """Return workflow text for reviewing vulture findings."""
    return (
        "Review dead code candidates for the open project.\n"
        "1. Call `find_dead_code` on the project root.\n"
        "2. For each finding, call `find_usages` and `impact_analysis` to avoid false positives.\n"
        "3. Group safe removals vs items kept for API/public surface.\n"
        "4. Output a deletion plan with file:line references only."
    )


def build_review_imports_prompt() -> str:
    """Return workflow text for import graph review."""
    return (
        "Review import dependencies for the open Python project.\n"
        "1. Call `open_project` and `analyze_project` if not already done.\n"
        "2. Read resource `codimension://graph/import` or call `get_import_graph`.\n"
        "3. Call `get_import_diagram` for Graphviz layout metadata.\n"
        "4. Flag circular imports, stdlib vs third-party mixing, and unused modules.\n"
        "5. Suggest minimal dependency fixes with file-level rationale."
    )


def build_analyze_module_prompt(path: str) -> str:
    """Return workflow text for deep-diving one module."""
    return (
        f"Analyze module `{path}` in the open project.\n"
        "1. Call `analyze_file` for symbol Graph IR.\n"
        "2. Call `get_diagnostics` for lint/complexity issues.\n"
        "3. For each public function, call `get_control_flow` with file.py:function:name ids.\n"
        "4. Call `find_callers` and `find_callees` for entry points and side effects.\n"
        "5. Summarize responsibilities, risks, and suggested tests."
    )


PROMPT_BUILDERS: dict[str, Callable[..., str]] = {
    "refactor_symbol": build_refactor_symbol_prompt,
    "review_dead_code": build_review_dead_code_prompt,
    "review_imports": build_review_imports_prompt,
    "analyze_module": build_analyze_module_prompt,
}


def register_prompts(mcp: FastMCP) -> None:
    """Register analysis workflow prompts on the MCP server."""

    @mcp.prompt(
        name="refactor_symbol",
        description="Plan a safe refactor using explain_symbol, impact_analysis, and find_usages.",
    )
    def refactor_symbol(symbol: str) -> str:
        return build_refactor_symbol_prompt(symbol)

    @mcp.prompt(
        name="review_dead_code",
        description="Review vulture findings before deletion.",
    )
    def review_dead_code() -> str:
        return build_review_dead_code_prompt()

    @mcp.prompt(
        name="review_imports",
        description="Audit import graph and circular dependencies.",
    )
    def review_imports() -> str:
        return build_review_imports_prompt()

    @mcp.prompt(
        name="analyze_module",
        description="Deep-dive one Python file: symbols, CFG, callers, diagnostics.",
    )
    def analyze_module(path: str) -> str:
        return build_analyze_module_prompt(path)
