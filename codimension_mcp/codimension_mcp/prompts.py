# -*- coding: utf-8 -*-
"""MCP prompt templates for common Codimension analysis workflows."""

from __future__ import annotations

from mcp.server.fastmcp import FastMCP


def register_prompts(mcp: FastMCP) -> None:
    """Register analysis workflow prompts on the MCP server."""

    @mcp.prompt(
        name="refactor_symbol",
        description="Plan a safe refactor using explain_symbol, impact_analysis, and find_usages.",
    )
    def refactor_symbol(symbol: str) -> str:
        return (
            f"You are refactoring `{symbol}` in an open Python project.\n"
            "1. Call `explain_symbol` with the full symbol id (e.g. file.py:function:name).\n"
            "2. Call `impact_analysis` for the same target to list transitive callers and import dependents.\n"
            "3. Call `find_usages` and `find_callers` to confirm references.\n"
            "4. Propose minimal edits and list tests to run before merging."
        )

    @mcp.prompt(
        name="review_dead_code",
        description="Review vulture findings before deletion.",
    )
    def review_dead_code() -> str:
        return (
            "Review dead code candidates for the open project.\n"
            "1. Call `find_dead_code` on the project root.\n"
            "2. For each finding, call `find_usages` and `impact_analysis` to avoid false positives.\n"
            "3. Group safe removals vs items kept for API/public surface.\n"
            "4. Output a deletion plan with file:line references only."
        )
