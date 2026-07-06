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
VSCODE_MCP_CONFIG = ROOT / "codimension-vscode" / "src" / "mcpConfig.ts"


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


def test_vscode_resource_list_matches_catalog():
    source = VSCODE_MCP_CONFIG.read_text(encoding="utf-8")
    vscode_uris = set(re.findall(r'"(codimension://[^"]+)"', source))
    catalog_uris = set(catalog_resource_uris())
    assert vscode_uris == catalog_uris, f"missing={catalog_uris - vscode_uris} extra={vscode_uris - catalog_uris}"


def test_catalog_has_required_resource_templates():
    uris = catalog_resource_uris()
    assert "codimension://catalog" in uris
    assert any("{path}" in uri for uri in uris)
    assert any("{function_key}" in uri for uri in uris)
    assert any("{target_key}" in uri for uri in uris)
    assert len(uris) == len(RESOURCES)
