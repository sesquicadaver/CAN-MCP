# -*- coding: utf-8 -*-
"""Prompt templates v2 — canonical symbol id guidance."""

from __future__ import annotations

from codimension_mcp.prompts import (
    CANONICAL_SYMBOL_EXAMPLE,
    build_analyze_module_prompt,
    build_assess_change_impact_prompt,
    build_refactor_symbol_prompt,
)


def test_refactor_prompt_uses_canonical_symbol_guidance():
    text = build_refactor_symbol_prompt("pkg/mod.py:function:run")
    assert CANONICAL_SYMBOL_EXAMPLE in text
    assert "project-relative canonical symbol ids" in text
    assert "not basename-only" in text


def test_analyze_module_prompt_mentions_canonical_cfg_id():
    text = build_analyze_module_prompt("pkg/mod.py")
    assert CANONICAL_SYMBOL_EXAMPLE in text
    assert "get_control_flow" in text


def test_assess_change_impact_prompt_prefers_canonical_targets():
    text = build_assess_change_impact_prompt("pkg/leaf.py:function:leaf")
    assert "pkg/mod.py:function:run" in text
    assert "pkg/mod.py" in text
