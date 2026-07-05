# -*- coding: utf-8 -*-
"""Import resolution — extraction from codimension.utils.importutils (stub)."""

from __future__ import annotations

from .errors import NotImplementedYetError
from .graph_ir import GraphIR
from .project import Project


def resolve_imports(project: Project, file_path: str) -> GraphIR:
    """Resolve imports for one file using project import dirs and venv site-packages."""
    project.require_open()
    raise NotImplementedYetError(
        "Full import resolution will be extracted from codimension/utils/importutils.py"
    )


def generate_requirements(project: Project) -> str:
    """Generate requirements.txt content from project imports."""
    project.require_open()
    raise NotImplementedYetError(
        "Requirements generation will be extracted from codimension/utils/importutils.py"
    )
