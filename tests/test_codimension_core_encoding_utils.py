# -*- coding: utf-8 -*-
"""Tests for codimension_core encoding_utils extraction."""

from __future__ import annotations

from codimension_core.encoding_utils import (
    EncodingReadOptions,
    convert_line_ends,
    decode_content,
    detect_bom_encoding,
    detect_eol_string,
    detect_read_encoding_from_header,
    get_coding_from_bytes,
    get_coding_from_text,
    is_valid_encoding,
    read_encoded_bytes,
    read_encoded_file,
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


def test_read_encoded_bytes_bom_utf8():
    raw = b"\xef\xbb\xbfprint('ok')\n"
    text, enc = read_encoded_bytes(raw, EncodingReadOptions())
    assert enc == "bom-utf-8"
    assert "print('ok')" in text


def test_read_encoded_bytes_coding_cookie(tmp_path):
    path = tmp_path / "mod.py"
    path.write_bytes(b"# -*- coding: latin-1 -*-\nprint('ok')\n")
    text, enc = read_encoded_file(path, EncodingReadOptions(check_python_source=True))
    assert enc == "latin-1"
    assert "print('ok')" in text


def test_decode_content_passthrough_str():
    text, enc = decode_content("already text", EncodingReadOptions(default_encoding="utf-8"))
    assert text == "already text"
    assert enc == "utf-8"


def test_decode_content_bytes_use_fallback():
    raw = b"hello"
    text, enc = decode_content(raw, EncodingReadOptions(default_encoding="utf-8"))
    assert text == "hello"
    assert enc == "utf-8"


def test_read_encoded_bytes_user_encoding_override(tmp_path):
    path = tmp_path / "plain.txt"
    path.write_bytes("café".encode("latin-1"))
    text, enc = read_encoded_bytes(
        path.read_bytes(),
        EncodingReadOptions(user_encoding="latin-1", file_name=str(path)),
    )
    assert enc == "latin-1"
    assert text == "café"
