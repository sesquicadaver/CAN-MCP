# -*- coding: utf-8 -*-
"""Tests for codimension_core disasm extraction."""

from __future__ import annotations

from codimension_core.disasm import OPT_NO_OPTIMIZATION, get_buffer_disassembled, get_file_disassembled


def test_get_buffer_disassembled(tmp_path):
    source = "def f():\n    return 1\n"
    text = get_buffer_disassembled(source, "utf-8", "sample.py", OPT_NO_OPTIMIZATION, stringify=True)
    assert isinstance(text, str)
    assert "Disassembly" in text


def test_get_file_disassembled(tmp_path):
    path = tmp_path / "mod.py"
    path.write_text("x = 1\n", encoding="utf-8")
    text = get_file_disassembled(str(path), OPT_NO_OPTIMIZATION, stringify=True)
    assert "Python module" in text
