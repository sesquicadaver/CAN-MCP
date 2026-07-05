# -*- coding: utf-8 -*-
"""Lint/complexity/dead-code analysis — extraction from codimension.analysis (stub)."""

from __future__ import annotations

from dataclasses import dataclass, field

from .errors import NotImplementedYetError
from .project import Project


@dataclass
class AnalysisSession:
    """Holds project-wide analyzer state."""

    project: Project | None = None
    diagnostics: list[dict[str, object]] = field(default_factory=list)

    def analyze_file_errors(self, path: str) -> list[dict[str, object]]:
        """Return pyflakes/radon diagnostics for one file."""
        if self.project is None:
            raise NotImplementedYetError("Analysis session has no project")
        raise NotImplementedYetError(
            "Analyzer extraction pending — source: codimension/analysis/ierrors.py"
        )
