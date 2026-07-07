# -*- coding: utf-8 -*-
"""Tests for MCP path security policy."""

from __future__ import annotations

import json

import pytest

from codimension_core.errors import PathOutsideProjectError
from codimension_core.paths import resolve_project_path
from codimension_mcp.schemas import WorkspaceState
from codimension_mcp.tools import analyze_file_tool, format_tool_error, open_project


def test_resolve_project_path_rejects_outside_project(tmp_path):
    project_dir = tmp_path / "proj"
    project_dir.mkdir()
    (project_dir / "main.py").write_text("x = 1\n", encoding="utf-8")
    state = WorkspaceState()
    open_project(state, str(project_dir))
    assert state.project is not None

    outside = tmp_path / "outside.py"
    outside.write_text("x = 2\n", encoding="utf-8")

    with pytest.raises(PathOutsideProjectError):
        resolve_project_path(state.project, str(outside))


def test_analyze_file_tool_rejects_outside_project(tmp_path):
    project_dir = tmp_path / "proj"
    project_dir.mkdir()
    (project_dir / "main.py").write_text("x = 1\n", encoding="utf-8")
    outside = tmp_path / "outside.py"
    outside.write_text("x = 2\n", encoding="utf-8")

    state = WorkspaceState()
    open_project(state, str(project_dir))
    with pytest.raises(PathOutsideProjectError):
        analyze_file_tool(state, str(outside))


def test_format_tool_error_includes_path_error_code():
    payload = json.loads(format_tool_error(PathOutsideProjectError("Path is outside project: /etc/passwd")))
    assert payload["error_code"] == "path_outside_project"
