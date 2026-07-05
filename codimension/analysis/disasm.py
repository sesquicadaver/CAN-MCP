# -*- coding: utf-8 -*-
#
# Legacy logic extracted to codimension_core.disasm (2026-07-05).
#

"""Disassembling files and buffers — IDE wrapper over codimension_core.disasm."""

from codimension_core import disasm as _core_disasm

OPT_NO_OPTIMIZATION = _core_disasm.OPT_NO_OPTIMIZATION
OPT_OPTIMIZE_ASSERT = _core_disasm.OPT_OPTIMIZE_ASSERT
OPT_OPTIMIZE_DOCSTRINGS = _core_disasm.OPT_OPTIMIZE_DOCSTRINGS

optToString = _core_disasm.optimization_to_string
getCodeDisassembly = _core_disasm.get_code_disassembly
getCompiledfileDisassembled = _core_disasm.get_compiled_file_disassembled
getFileDisassembled = _core_disasm.get_file_disassembled
getBufferDisassembled = _core_disasm.get_buffer_disassembled
getCompiledfileBinary = _core_disasm.get_compiled_file_binary
getFileBinary = _core_disasm.get_file_binary
getBufferBinary = _core_disasm.get_buffer_binary
_stringify = _core_disasm.stringify_disassembly

DIS_OBJECTS: set[str] = set()


def recursiveDisassembly(codeObject, name=None):
    seen: set[str] = set()
    return _core_disasm.recursive_disassembly(codeObject, seen, name)


def safeUnlink(path):
    """No exception unlink."""
    _core_disasm._safe_unlink(path)
