# -*- coding: utf-8 -*-
"""Typed errors for codimension_core."""


class AnalysisError(Exception):
    """Base class for analysis failures."""


class ProjectNotOpenError(AnalysisError):
    """Raised when an operation requires an open project."""


class SymbolNotFoundError(AnalysisError):
    """Raised when a symbol id cannot be resolved."""


class PathOutsideProjectError(AnalysisError):
    """Raised when a path escapes the open project root."""


class AmbiguousSymbolIdError(AnalysisError):
    """Raised when a legacy symbol id maps to multiple definitions."""


class NotImplementedYetError(AnalysisError):
    """Raised for planned but not yet extracted features."""


class MissingOptionalDependencyError(AnalysisError):
    """Raised when a feature requires optional packages that are not installed."""

    def __init__(self, feature: str, missing: list[str]) -> None:
        self.feature = feature
        self.missing = list(missing)
        packages = ", ".join(missing)
        super().__init__(f"Feature '{feature}' requires optional packages: {packages}")
