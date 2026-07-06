# -*- coding: utf-8 -*-
"""Tests for vendored flow_ast parser in codimension_core."""

from __future__ import annotations

from codimension_core.flow_ast import FUNCTION_FRAGMENT, IMPORT_FRAGMENT, getControlFlowFromMemory


def test_flow_ast_builds_function_fragment():
    source = """\
def run():
    if True:
        return 1
"""
    cflow = getControlFlowFromMemory(source)
    assert cflow.nsuite
    fn = cflow.nsuite[0]
    assert fn.kind == FUNCTION_FRAGMENT
    assert fn.name is not None
    assert fn.name.getContent() == "run"
    assert fn.nsuite


def test_flow_ast_import_fragment():
    source = "import os\n"
    cflow = getControlFlowFromMemory(source)
    assert len(cflow.nsuite) == 1
    assert cflow.nsuite[0].kind == IMPORT_FRAGMENT
