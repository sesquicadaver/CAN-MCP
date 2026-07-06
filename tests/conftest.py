# -*- coding: utf-8 -*-
"""Pytest configuration for Codimension tests."""

import importlib.util
import os
import sys

import pytest

# Ensure project root and codimension package dir are in path (cdmplugins imports plugins, ui, utils)
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CODMENSION_DIR = os.path.join(ROOT, "codimension")
CORE_DIR = os.path.join(ROOT, "codimension_core")
MCP_DIR = os.path.join(ROOT, "codimension_mcp")
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)
if CODMENSION_DIR not in sys.path:
    sys.path.insert(0, CODMENSION_DIR)
if CORE_DIR not in sys.path:
    sys.path.insert(0, CORE_DIR)
if MCP_DIR not in sys.path:
    sys.path.insert(0, MCP_DIR)


def _has_pyqt5() -> bool:
    return importlib.util.find_spec("PyQt5") is not None


def pytest_collection_modifyitems(config, items):
    """Skip @pytest.mark.pyqt tests when PyQt5 is not installed."""
    if _has_pyqt5():
        return
    skip = pytest.mark.skip(reason="PyQt5 not installed (legacy IDE)")
    for item in items:
        if "pyqt" in item.keywords:
            item.add_marker(skip)


@pytest.fixture(scope="session")
def qapp():
    """Single QApplication instance for widget/driver tests."""
    pytest.importorskip("PyQt5")
    try:
        from ui.qt import QApplication
    except ImportError:
        from PyQt5.QtWidgets import QApplication

    app = QApplication.instance()
    if app is None:
        app = QApplication([])
    return app
