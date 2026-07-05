# -*- coding: utf-8 -*-
#
# Legacy logic extracted to codimension_core.brief_ast (2026-07-05).
#

"""Pure-Python cdmpyparser replacement — IDE wrapper over codimension_core.brief_ast."""

from codimension_core.brief_ast import (  # noqa: F401
    VERSION,
    Argument,
    BriefModuleInfo,
    Class,
    ClassAttribute,
    Decorator,
    Docstring,
    Encoding,
    Function,
    Global,
    Import,
    ImportWhat,
    InstanceAttribute,
    ModuleInfoBase,
    getBriefModuleInfoFromFile,
    getBriefModuleInfoFromMemory,
    getVersion,
    trim_docstring,
)

__all__ = [
    "VERSION",
    "Argument",
    "BriefModuleInfo",
    "Class",
    "ClassAttribute",
    "Decorator",
    "Docstring",
    "Encoding",
    "Function",
    "Global",
    "Import",
    "ImportWhat",
    "InstanceAttribute",
    "ModuleInfoBase",
    "getBriefModuleInfoFromFile",
    "getBriefModuleInfoFromMemory",
    "getVersion",
    "trim_docstring",
]
