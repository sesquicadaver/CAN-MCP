# -*- coding: utf-8 -*-
"""Tests for MCP capability catalog."""

from __future__ import annotations

import json

from codimension_mcp.catalog import CATALOG_VERSION, TOOLS, build_mcp_catalog, read_mcp_catalog


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
    tool_names = {item["name"] for item in payload["tools"]}
    assert "impact_analysis" in tool_names
    assert "get_control_flow" in tool_names
