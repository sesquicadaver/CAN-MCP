# -*- coding: utf-8 -*-
"""Structural types for cdmpyparser brief AST objects used by codimension_core."""

from __future__ import annotations

from typing import Protocol, TypedDict, runtime_checkable


@runtime_checkable
class BriefWhat(Protocol):
    name: str
    alias: str


@runtime_checkable
class BriefImport(Protocol):
    name: str
    line: int
    alias: str
    what: list[BriefWhat]


@runtime_checkable
class BriefDocstring(Protocol):
    text: str


@runtime_checkable
class BriefNamed(Protocol):
    name: str


@runtime_checkable
class BriefModuleInfo(Protocol):
    imports: list[BriefImport]
    classes: list[BriefNamed]
    functions: list[BriefNamed]
    globals: list[BriefNamed]
    docstring: BriefDocstring | None


class ClassifiedImportBuckets(TypedDict):
    system: list[object]
    project: list[object]
    other: list[object]
    unresolved: list[object]
    totalCount: int
    errors: list[str]
