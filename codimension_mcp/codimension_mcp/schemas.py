# -*- coding: utf-8 -*-
"""Shared MCP tool schemas and runtime state."""

from __future__ import annotations

import threading
from contextlib import contextmanager
from dataclasses import dataclass, field
from typing import Iterator

from codimension_core.project import Project


@dataclass
class WorkspaceState:
    """In-memory workspace bound to one MCP server instance (single-workspace model)."""

    workspace: str = ""
    project: Project | None = None
    analyzed_files: int = 0
    tool_calls: dict[str, int] = field(default_factory=dict)
    _lock: threading.RLock = field(default_factory=threading.RLock, repr=False, compare=False)

    @contextmanager
    def workspace_lock(self) -> Iterator[None]:
        """Serialize workspace mutations (open, analyze, invalidate)."""
        self._lock.acquire()
        try:
            yield
        finally:
            self._lock.release()

    def record_tool(self, name: str) -> None:
        self.tool_calls[name] = self.tool_calls.get(name, 0) + 1
