# -*- coding: utf-8 -*-
"""Render MCP catalog tables for codimension_mcp README."""

from __future__ import annotations

import re

from codimension_mcp.catalog import PROMPTS, RESOURCES, TOOLS

TOOLS_MARKER = "catalog:tools"
RESOURCES_MARKER = "catalog:resources"
PROMPTS_MARKER = "catalog:prompts"


def _ordered_tools() -> list[dict[str, str | bool]]:
    """Return tools with discovery entry first."""
    discovery = [tool for tool in TOOLS if tool["name"] == "list_mcp_catalog"]
    rest = [tool for tool in TOOLS if tool["name"] != "list_mcp_catalog"]
    return discovery + rest


def _resource_content(resource: dict[str, str]) -> str:
    """Return README content cell for a catalog resource."""
    description = resource["description"]
    if resource["uri"] == "codimension://catalog":
        return f"**Start here** — {description.lower()}"
    return description


def _prompt_args_cell(args: str) -> str:
    """Format prompt args column for README."""
    return "—" if not args else f"`{args}`"


def render_readme_tools_table() -> str:
    """Return markdown table body for MCP tools."""
    header = "| Tool | Purpose |\n| ---- | ------- |"
    rows = [f"| `{tool['name']}` | {tool['description']} |" for tool in _ordered_tools()]
    return "\n".join([header, *rows])


def render_readme_resources_table() -> str:
    """Return markdown table body for MCP resources."""
    header = "| URI | MIME | Content |\n| --- | ---- | ------- |"
    rows = [
        f"| `{resource['uri']}` | {resource['mime_type']} | {_resource_content(resource)} |"
        for resource in RESOURCES
    ]
    return "\n".join([header, *rows])


def render_readme_prompts_table() -> str:
    """Return markdown table body for MCP prompts."""
    header = "| Name | Args | Workflow |\n| ---- | ---- | -------- |"
    rows = [
        f"| `{prompt['name']}` | {_prompt_args_cell(prompt['args'])} | {prompt['workflow']} |"
        for prompt in PROMPTS
    ]
    return "\n".join([header, *rows])


def _replace_marked_block(readme: str, marker: str, table: str) -> str:
    """Replace content between catalog markers with rendered table."""
    start = f"<!-- {marker} -->"
    end = f"<!-- /{marker} -->"
    pattern = re.compile(rf"{re.escape(start)}\n.*?\n{re.escape(end)}", re.DOTALL)
    replacement = f"{start}\n{table}\n{end}"
    if not pattern.search(readme):
        raise ValueError(f"Missing README markers for {marker}")
    return pattern.sub(replacement, readme, count=1)


def patch_readme_catalog_tables(readme: str) -> str:
    """Inject generated catalog tables into README markdown."""
    readme = _replace_marked_block(readme, TOOLS_MARKER, render_readme_tools_table())
    readme = _replace_marked_block(readme, RESOURCES_MARKER, render_readme_resources_table())
    return _replace_marked_block(readme, PROMPTS_MARKER, render_readme_prompts_table())
