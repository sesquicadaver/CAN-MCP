# -*- coding: utf-8 -*-
"""Headless file I/O helpers extracted from codimension.utils.fileutils."""

from __future__ import annotations

import json
import logging
from typing import Any

DEFAULT_TEXT_ENCODING = "utf-8"


def is_python_source_path(path: str) -> bool:
    """Return True when path looks like a Python source file."""
    return path.endswith((".py", ".pyw"))


def load_json(
    file_name: str,
    error_what: str,
    default_value: Any,
    *,
    encoding: str = DEFAULT_TEXT_ENCODING,
) -> Any:
    """Load JSON from disk, returning default_value on failure."""
    try:
        with open(file_name, encoding=encoding) as diskfile:
            return json.load(diskfile)
    except Exception as exc:
        logging.error("Error loading %s (from %s): %s", error_what, file_name, exc)
        return default_value


def save_json(
    file_name: str,
    values: Any,
    error_what: str,
    *,
    encoding: str = DEFAULT_TEXT_ENCODING,
) -> bool:
    """Save JSON to disk. Returns False on failure."""
    try:
        with open(file_name, "w", encoding=encoding) as diskfile:
            json.dump(values, diskfile, indent=4)
    except Exception as exc:
        logging.error("Error saving %s (to %s): %s", error_what, file_name, exc)
        return False
    return True


def read_text_file(
    file_name: str,
    *,
    encoding: str = DEFAULT_TEXT_ENCODING,
    allow_exception: bool = True,
) -> str | None:
    """Read a text file and return its content."""
    try:
        with open(file_name, encoding=encoding) as diskfile:
            return diskfile.read()
    except Exception as exc:
        if allow_exception:
            raise
        logging.error("Error reading from file %s: %s", file_name, exc)
        return None


def write_text_file(
    file_name: str,
    content: str,
    *,
    encoding: str = DEFAULT_TEXT_ENCODING,
    allow_exception: bool = True,
) -> bool:
    """Overwrite a text file. Returns False on failure when exceptions are suppressed."""
    try:
        with open(file_name, "w", encoding=encoding) as diskfile:
            diskfile.write(content)
    except Exception as exc:
        if allow_exception:
            raise
        logging.error("Error writing to file %s: %s", file_name, exc)
        return False
    return True
