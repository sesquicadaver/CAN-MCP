# -*- coding: utf-8 -*-
"""Tests for codimension_core venvutils extraction."""

from __future__ import annotations

import os
import stat

from codimension_core.venvutils import detect_project_venv_dir, resolve_venv_to_python


def _make_fake_venv(tmp_path, name: str = ".venv") -> str:
    venv_dir = tmp_path / name
    bin_dir = venv_dir / "bin"
    bin_dir.mkdir(parents=True)
    python = bin_dir / "python"
    python.write_text("#!/bin/sh\n", encoding="utf-8")
    python.chmod(python.stat().st_mode | stat.S_IXUSR)
    return str(venv_dir)


def test_resolve_venv_to_python(tmp_path):
    venv_dir = _make_fake_venv(tmp_path)
    resolved = resolve_venv_to_python(venv_dir)
    assert resolved is not None
    assert resolved.endswith("/bin/python")


def test_detect_project_venv_dir_auto(tmp_path):
    _make_fake_venv(tmp_path, "venv")
    assert detect_project_venv_dir(str(tmp_path)) is not None


def test_detect_project_venv_dir_from_interpreter(tmp_path):
    venv_dir = _make_fake_venv(tmp_path)
    python = os.path.join(venv_dir, "bin", "python")
    assert detect_project_venv_dir(str(tmp_path), python) == os.path.realpath(venv_dir)
