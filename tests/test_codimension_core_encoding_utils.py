# -*- coding: utf-8 -*-
"""Tests for codimension_core encoding_utils extraction."""

from __future__ import annotations

from codimension_core.encoding_utils import (
    convert_line_ends,
    detect_bom_encoding,
    detect_eol_string,
    detect_read_encoding_from_header,
    get_coding_from_bytes,
    get_coding_from_text,
    is_valid_encoding,
)


def test_get_coding_from_text():
    source = "# -*- coding: latin-1 -*-\nprint('ok')\n"
    assert get_coding_from_text(source) == "latin-1"


def test_get_coding_from_bytes():
    source = b"# -*- coding: utf-8 -*-\n"
    assert get_coding_from_bytes(source) == "utf-8"


def test_detect_bom_encoding():
    assert detect_bom_encoding(b"\xef\xbb\xbfprint()") == "bom-utf-8"


def test_detect_read_encoding_from_header_prefers_bom():
    data = b"\xef\xbb\xbf# coding: latin-1\n"
    assert detect_read_encoding_from_header(data) == "bom-utf-8"


def test_detect_eol_and_convert_line_ends():
    assert detect_eol_string("a\r\nb") == "\r\n"
    assert convert_line_ends("a\r\nb\r\nc", "\n") == "a\nb\nc"


def test_is_valid_encoding():
    assert is_valid_encoding("utf-8")
    assert not is_valid_encoding("not-a-real-encoding-name")
