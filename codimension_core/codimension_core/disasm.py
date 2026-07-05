# -*- coding: utf-8 -*-
"""Bytecode disassembly extracted from codimension.analysis.disasm."""

from __future__ import annotations

import dis
import marshal
import os
import platform
import py_compile
import sys
import tempfile
from io import StringIO
from types import CodeType

OPT_NO_OPTIMIZATION = 0
OPT_OPTIMIZE_ASSERT = 1
OPT_OPTIMIZE_DOCSTRINGS = 2

_CONVERSION = {
    OPT_NO_OPTIMIZATION: "no optimization",
    OPT_OPTIMIZE_ASSERT: "assert optimization",
    OPT_OPTIMIZE_DOCSTRINGS: "assert + docstring optimization",
}


def optimization_to_string(optimization: int) -> str:
    """Convert optimization level to human-readable text."""
    return _CONVERSION.get(optimization, "unknown optimization")


def _make_temp_file(suffix: str) -> str:
    handle, path = tempfile.mkstemp(suffix=suffix, prefix="cdm_")
    os.close(handle)
    return path


def _safe_unlink(path: str) -> None:
    try:
        os.unlink(path)
    except OSError:
        pass


def _write_text_file(path: str, content: str, *, encoding: str = "utf-8") -> None:
    with open(path, "w", encoding=encoding) as handle:
        handle.write(content)


def get_code_disassembly(code: CodeType) -> str:
    """Return disassembly text for a code object."""
    buffer = StringIO()
    dis.dis(code, file=buffer)
    buffer.seek(0)
    return buffer.read()


_DIS_PATTERN = "Disassembly of <code object "
_DIS_PATTERN_LEN = len(_DIS_PATTERN)


def _update_disassembled_names(disassembly: str, seen: set[str]) -> None:
    for line in disassembly.splitlines():
        if line.startswith(_DIS_PATTERN):
            name = line[_DIS_PATTERN_LEN:].split()[0]
            seen.add(name)


def recursive_disassembly(code_object: CodeType, seen: set[str], name: str | None = None) -> str:
    """Disassemble nested code objects recursively."""
    if name is None:
        label = "module"
    else:
        if name in seen:
            return ""
        label = name

    disassembly = get_code_disassembly(code_object)
    _update_disassembled_names(disassembly, seen)
    result = f"\n\nDisassembly of {label}:\n{disassembly}"
    for item in code_object.co_consts:
        if isinstance(item, CodeType):
            nested_name = item.co_name if name is None else f"{name}.{item.co_name}"
            result += recursive_disassembly(item, seen, nested_name)
    return result


def get_compiled_file_disassembled(
    pyc_path: str,
    py_path: str,
    optimization: int,
    *,
    for_buffer: bool = False,
) -> tuple[list[tuple[str, str]], str]:
    """Read a .pyc file and return metadata plus disassembly text."""
    props: list[tuple[str, str]] = [
        ("Python version", platform.python_version()),
        ("Python interpreter path", sys.executable),
    ]
    with open(pyc_path, "rb") as handle:
        handle.read(4)
        handle.read(4)
        handle.read(4)
        handle.read(4)
        code = marshal.load(handle)

    buffer_spec = " (unsaved buffer)" if for_buffer else ""
    props.append(("Python module", py_path + buffer_spec))
    props.append(("Optimization", optimization_to_string(optimization)))

    seen: set[str] = set()
    disassembly = recursive_disassembly(code, seen)
    return props, disassembly


def stringify_disassembly(props: list[tuple[str, str]], disassembly: str) -> str:
    """Combine metadata and disassembly into one text block."""
    result = "-" * 80
    for key, value in props:
        result += f"\n{key}: {value}"
    result += "\n" + "-" * 80
    result += disassembly
    return result


def _compile_to_temp_pyc(source_path: str, optimization: int) -> str:
    temp_pyc = _make_temp_file(suffix=".pyc")
    try:
        py_compile.compile(source_path, temp_pyc, doraise=True, optimize=optimization)
    except Exception as exc:
        _safe_unlink(temp_pyc)
        raise ValueError(f"Cannot compile {source_path}: {exc}") from exc
    return temp_pyc


def get_file_disassembled(
    path: str,
    optimization: int,
    *,
    stringify: bool = True,
) -> str | tuple[list[tuple[str, str]], str]:
    """Disassemble a Python file on disk."""
    if not os.path.exists(path):
        raise FileNotFoundError(f"Cannot find {path} to disassemble")
    if not os.access(path, os.R_OK):
        raise PermissionError(f"No read permissions for {path}")

    temp_pyc = _compile_to_temp_pyc(path, optimization)
    try:
        props, disassembly = get_compiled_file_disassembled(temp_pyc, path, optimization)
    finally:
        _safe_unlink(temp_pyc)
    if stringify:
        return stringify_disassembly(props, disassembly)
    return props, disassembly


def get_buffer_disassembled(
    content: str,
    encoding: str,
    path: str,
    optimization: int,
    *,
    stringify: bool = True,
) -> str | tuple[list[tuple[str, str]], str]:
    """Disassemble unsaved buffer content."""
    temp_src = _make_temp_file(suffix=".py")
    temp_pyc = _make_temp_file(suffix=".pyc")
    try:
        _write_text_file(temp_src, content, encoding=encoding)
        py_compile.compile(temp_src, temp_pyc, path, doraise=True, optimize=optimization)
        props, disassembly = get_compiled_file_disassembled(temp_pyc, path, optimization, for_buffer=True)
        if path:
            disassembly = disassembly.replace(f'file "{path}",', f'unsaved buffer "{path}",')
        if stringify:
            return stringify_disassembly(props, disassembly)
        return props, disassembly
    finally:
        _safe_unlink(temp_src)
        _safe_unlink(temp_pyc)


def get_compiled_file_binary(
    pyc_path: str,
    py_path: str,
    optimization: int,
    *,
    for_buffer: bool = False,
) -> tuple[list[tuple[str, str]], bytes]:
    """Return metadata and raw .pyc bytes."""
    props: list[tuple[str, str]] = [
        ("Python version", platform.python_version()),
        ("Python interpreter path", sys.executable),
    ]
    with open(pyc_path, "rb") as handle:
        content = handle.read()
    buffer_spec = " (unsaved buffer)" if for_buffer else ""
    props.append(("Python module", py_path + buffer_spec))
    props.append(("Optimization", optimization_to_string(optimization)))
    return props, content


def get_file_binary(path: str, optimization: int) -> tuple[list[tuple[str, str]], bytes]:
    """Compile a file and return raw .pyc bytes."""
    temp_pyc = _compile_to_temp_pyc(path, optimization)
    try:
        return get_compiled_file_binary(temp_pyc, path, optimization)
    finally:
        _safe_unlink(temp_pyc)


def get_buffer_binary(content: str, encoding: str, path: str, optimization: int) -> tuple[list[tuple[str, str]], bytes]:
    """Compile buffer content and return raw .pyc bytes."""
    temp_src = _make_temp_file(suffix=".py")
    temp_pyc = _make_temp_file(suffix=".pyc")
    try:
        _write_text_file(temp_src, content, encoding=encoding)
        py_compile.compile(temp_src, temp_pyc, path, doraise=True, optimize=optimization)
        return get_compiled_file_binary(temp_pyc, path, optimization, for_buffer=True)
    finally:
        _safe_unlink(temp_src)
        _safe_unlink(temp_pyc)
