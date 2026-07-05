# -*- coding: utf-8 -*-
"""Shared MCP tool schemas and runtime state."""

from __future__ import annotations

from dataclasses import dataclass, field

from codimension_core.project import Project


@dataclass
class WorkspaceState:
    """In-memory workspace bound to one MCP server instance."""

    workspace: str = ""
    project: Project | None = None
    analyzed_files: int = 0
    tool_calls: dict[str, int] = field(default_factory=dict)

    def record_tool(self, name: str) -> None:
        self.tool_calls[name] = self.tool_calls.get(name, 0) + 1
