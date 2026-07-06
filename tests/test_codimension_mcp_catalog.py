# -*- coding: utf-8 -*-
"""Tests for MCP capability catalog."""

from __future__ import annotations

import json
import re
from pathlib import Path

from codimension_mcp.catalog import (
    CATALOG_VERSION,
    RESOURCES,
    TOOLS,
    build_mcp_catalog,
    catalog_prompt_names,
    catalog_resource_uris,
    catalog_tool_names,
    read_mcp_catalog,
)
from codimension_mcp.prompts import PROMPT_BUILDERS

ROOT = Path(__file__).resolve().parents[1]
VSCODE_URIS_GENERATED = ROOT / "codimension-vscode" / "src" / "mcpResourceUris.generated.ts"
MCP_README = ROOT / "codimension_mcp" / "README.md"


def _extract_markdown_table_first_column(section: str) -> set[str]:
    """Return first-column backtick values from a markdown table under ## section."""
    match = re.search(rf"## {section}\n\n\|[^\n]+\n\|[^\n]+\n((?:\|[^\n]+\n)+)", MCP_README.read_text(encoding="utf-8"))
    assert match, f"Missing ## {section} table in README"
    names: set[str] = set()
    for row in match.group(1).splitlines():
        cell = re.match(r"\|\s*`([^`]+)`\s*\|", row)
        if cell:
            names.add(cell.group(1))
    return names


def test_build_mcp_catalog_structure():
    catalog = build_mcp_catalog()
    assert catalog["status"] == "ok"
    assert catalog["catalog_version"] == CATALOG_VERSION
    assert len(catalog["tools"]) == len(TOOLS)
    assert any(tool["name"] == "list_mcp_catalog" for tool in catalog["tools"])
    assert any(res["uri"] == "codimension://catalog" for res in catalog["resources"])
    assert len(catalog["prompts"]) >= 6
    assert "function_key" in catalog["encoding"]


def test_read_mcp_catalog_json():
    payload = json.loads(read_mcp_catalog())
    assert payload["discovery"]
    tool_names = set(catalog_tool_names())
    assert "impact_analysis" in tool_names
    assert "get_control_flow" in tool_names
    assert "list_mcp_catalog" in tool_names


def test_catalog_prompts_match_prompt_builders():
    assert set(catalog_prompt_names()) == set(PROMPT_BUILDERS)


def test_generated_vscode_uris_match_catalog():
    source = VSCODE_URIS_GENERATED.read_text(encoding="utf-8")
    generated_uris = set(re.findall(r'"(codimension://[^"]+)"', source))
    catalog_uris = set(catalog_resource_uris())
    assert generated_uris == catalog_uris, f"missing={catalog_uris - generated_uris} extra={generated_uris - catalog_uris}"


def test_readme_tools_match_catalog():
    readme_tools = _extract_markdown_table_first_column("Tools")
    assert readme_tools == set(catalog_tool_names())


def test_readme_resources_match_catalog():
    readme_resources = _extract_markdown_table_first_column("Resources")
    assert readme_resources == set(catalog_resource_uris())


def test_readme_prompts_match_catalog():
    readme_prompts = _extract_markdown_table_first_column("Prompts")
    assert readme_prompts == set(catalog_prompt_names())


def test_catalog_has_required_resource_templates():
    uris = catalog_resource_uris()
    assert "codimension://catalog" in uris
    assert any("{path}" in uri for uri in uris)
    assert any("{function_key}" in uri for uri in uris)
    assert any("{target_key}" in uri for uri in uris)
    assert len(uris) == len(RESOURCES)
