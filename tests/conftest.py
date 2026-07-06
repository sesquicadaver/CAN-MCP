# -*- coding: utf-8 -*-
"""Pytest configuration for CAN-MCP (codimension_core + codimension_mcp)."""

import os
import sys

import pytest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CORE_DIR = os.path.join(ROOT, "codimension_core")
MCP_DIR = os.path.join(ROOT, "codimension_mcp")

for path in (ROOT, CORE_DIR, MCP_DIR):
    if path not in sys.path:
        sys.path.insert(0, path)


@pytest.fixture(scope="session")
def repo_root():
    """Repository root path."""
    return ROOT
