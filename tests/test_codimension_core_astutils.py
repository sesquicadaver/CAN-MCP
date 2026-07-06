# -*- coding: utf-8 -*-
"""Tests for codimension_core astutils extraction."""

from __future__ import annotations

import ast

from codimension_core.astutils import parse_source_to_ast


def test_parse_source_to_ast():
    tree = parse_source_to_ast("def f():\n    return 1\n", "sample.py")
    assert isinstance(tree, ast.Module)
    assert isinstance(tree.body[0], ast.FunctionDef)
    assert tree.body[0].name == "f"
