# -*- coding: utf-8 -*-
"""Tests for vendored brief_ast parser in codimension_core."""

from __future__ import annotations

from codimension_core.brief_ast import (
    BriefModuleInfo,
    getBriefModuleInfoFromMemory,
)


def test_brief_ast_parses_functions_and_classes():
    source = '''"""Module doc."""

import os

GLOBAL = 1

def outer():
    """Outer doc."""
    pass

class Widget:
    """Widget doc."""
    def method(self):
        return 0
'''
    info = getBriefModuleInfoFromMemory(source, "sample.py")
    assert info.docstring is not None
    assert info.docstring.text == "Module doc."
    assert len(info.imports) == 1
    assert info.imports[0].name == "os"
    assert len(info.globals) == 1
    assert info.globals[0].name == "GLOBAL"
    assert len(info.functions) == 1
    assert info.functions[0].name == "outer"
    assert len(info.classes) == 1
    assert info.classes[0].name == "Widget"
    assert len(info.classes[0].functions) == 1


def test_brief_ast_syntax_error():
    info = getBriefModuleInfoFromMemory("def broken(\n", "bad.py")
    assert info.isOK is False
    assert info.errors
