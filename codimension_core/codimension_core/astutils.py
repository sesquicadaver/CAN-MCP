# -*- coding: utf-8 -*-
"""AST parsing helpers extracted from codimension.utils.astutils."""

from __future__ import annotations

import ast


def parse_source_to_ast(source: str, filename: str = "<string>") -> ast.AST:
    """Parse Python source into an AST tree."""
    return ast.parse(source, filename, mode="exec", type_comments=True)
