# -*- coding: utf-8 -*-
"""Typed errors for codimension_core."""


class AnalysisError(Exception):
    """Base class for analysis failures."""


class ProjectNotOpenError(AnalysisError):
    """Raised when an operation requires an open project."""


class SymbolNotFoundError(AnalysisError):
    """Raised when a symbol id cannot be resolved."""


class NotImplementedYetError(AnalysisError):
    """Raised for planned but not yet extracted features."""
