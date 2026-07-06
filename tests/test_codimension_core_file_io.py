# -*- coding: utf-8 -*-
"""Tests for codimension_core file_io extraction."""

from __future__ import annotations

from codimension_core.file_io import (
    is_python_source_path,
    load_json,
    read_text_file,
    save_json,
    write_text_file,
)


def test_is_python_source_path():
    assert is_python_source_path("mod.py")
    assert is_python_source_path("pkg/mod.pyw")
    assert not is_python_source_path("mod.pyc")


def test_json_roundtrip(tmp_path):
    path = tmp_path / "data.json"
    payload = {"a": 1, "b": ["x"]}
    assert save_json(str(path), payload, "test payload")
    loaded = load_json(str(path), "test payload", default_value=None)
    assert loaded == payload


def test_read_and_write_text_file(tmp_path):
    path = tmp_path / "sample.txt"
    assert write_text_file(str(path), "hello\n")
    assert read_text_file(str(path)) == "hello\n"


def test_load_json_default_on_missing(tmp_path):
    missing = tmp_path / "missing.json"
    assert load_json(str(missing), "missing", {"fallback": True}) == {"fallback": True}
