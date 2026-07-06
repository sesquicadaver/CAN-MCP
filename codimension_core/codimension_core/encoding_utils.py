# -*- coding: utf-8 -*-
"""Headless encoding helpers extracted from codimension.utils.encoding."""

from __future__ import annotations

import encodings
import logging
import re
from codecs import BOM_UTF8, BOM_UTF16, BOM_UTF32
from dataclasses import dataclass
from pathlib import Path

from .brief_ast import getBriefModuleInfoFromMemory

DEFAULT_TEXT_ENCODING = "utf-8"


@dataclass
class EncodingReadOptions:
    """Injectable fallbacks for headless encoded file reads."""

    user_encoding: str | None = None
    project_encoding: str | None = None
    ide_encoding: str | None = None
    default_encoding: str = DEFAULT_TEXT_ENCODING
    check_python_source: bool = False
    file_name: str = "<unknown>"


STANDARD_CODECS = [
    "ascii",
    "big5",
    "big5hkscs",
    "cp037",
    "cp273",
    "cp424",
    "cp437",
    "cp500",
    "cp720",
    "cp737",
    "cp775",
    "cp850",
    "cp852",
    "cp855",
    "cp856",
    "cp857",
    "cp858",
    "cp860",
    "cp861",
    "cp862",
    "cp863",
    "cp864",
    "cp865",
    "cp866",
    "cp869",
    "cp874",
    "cp875",
    "cp932",
    "cp949",
    "cp950",
    "cp1006",
    "cp1026",
    "cp1125",
    "cp1140",
    "cp1250",
    "cp1251",
    "cp1252",
    "cp1253",
    "cp1254",
    "cp1255",
    "cp1256",
    "cp1257",
    "cp1258",
    "cp65001",
    "euc_jp",
    "euc-jis-2004",
    "euc-jisx0213",
    "euc-kr",
    "gb2312",
    "gbk",
    "gb18030",
    "hz",
    "iso2022-jp",
    "iso2022-jp-1",
    "iso2022-jp-2",
    "iso2022-jp-2004",
    "iso2022-jp-3",
    "iso2022_jp-ext",
    "iso2022-kr",
    "latin-1",
    "iso8859-2",
    "iso8859-3",
    "iso8859-4",
    "iso8859-5",
    "iso8859-6",
    "iso8859-7",
    "iso8859-8",
    "iso8859-9",
    "iso8859-10",
    "iso8859-11",
    "iso8859-13",
    "iso8859-14",
    "iso8859-15",
    "iso8859-16",
    "johab",
    "koi8-r",
    "koi8-t",
    "koi8-u",
    "kz1048",
    "mac-cyrillic",
    "mac-greek",
    "mac-iceland",
    "mac-latin2",
    "mac-roman",
    "mac-turkish",
    "ptcp154",
    "shift-jis",
    "shift-jis-2004",
    "shift-jisx0213",
    "utf-32",
    "utf-32-be",
    "utf-32-le",
    "utf-16",
    "utf-16-be",
    "utf-16-le",
    "utf-7",
    "utf-8",
    "utf-8-sig",
]

SYNTHETIC_CODECS = ["bom-utf-8", "bom-utf-16", "bom-utf-32"]
SUPPORTED_CODECS = STANDARD_CODECS + SYNTHETIC_CODECS

CODING_FROM_BYTES = [
    (2, re.compile(rb"""coding[:=]\s*([-\w_.]+)""")),
    (1, re.compile(rb"""<\?xml.*\bencoding\s*=\s*['"]([-\w_.]+)['"]\?>""")),
]

CODING_FROM_TEXT = [
    (2, re.compile(r"""coding[:=]\s*([-\w_.]+)""")),
    (1, re.compile(r"""<\?xml.*\bencoding\s*=\s*['"]([-\w_.]+)['"]\?>""")),
]


def _replace_eol(match: re.Match[str], replacement: str) -> str:
    return replacement


def convert_line_ends(text: str, eol: str) -> str:
    """Convert end-of-line characters in text to the given eol."""
    if eol == "\r\n":
        regexp = re.compile(r"(\r(?!\n)|(?<!\r)\n)")
        return regexp.sub(lambda match: _replace_eol(match, "\r\n"), text)
    if eol == "\n":
        regexp = re.compile(r"(\r\n|\r)")
        return regexp.sub(lambda match: _replace_eol(match, "\n"), text)
    if eol == "\r":
        regexp = re.compile(r"(\r\n|\n)")
        return regexp.sub(lambda match: _replace_eol(match, "\r"), text)
    return text


def detect_eol_string(text: str) -> str:
    """Detect the eol string using the first split."""
    if len(text.split("\r\n", 1)) == 2:
        return "\r\n"
    if len(text.split("\r", 1)) == 2:
        return "\r"
    return "\n"


def is_valid_encoding(enc: str) -> bool:
    """Return True when encoding is supported."""
    norm_enc = encodings.normalize_encoding(enc).lower()
    if norm_enc in SUPPORTED_CODECS:
        return True
    if norm_enc in [encodings.normalize_encoding(supp_enc) for supp_enc in SUPPORTED_CODECS]:
        return True
    return norm_enc in encodings.aliases.aliases


def get_normalized_encoding(enc: str, *, validity_check: bool = True) -> str:
    """Return a normalized encoding or raise when invalid."""
    if validity_check and not is_valid_encoding(enc):
        raise Exception("Unsupported encoding " + enc)
    norm_enc = encodings.normalize_encoding(enc).lower()
    return encodings.aliases.aliases.get(norm_enc, norm_enc)


def are_encodings_equal(enc_lhs: str, enc_rhs: str) -> bool:
    """Return True when encodings are essentially the same."""
    return get_normalized_encoding(enc_lhs) == get_normalized_encoding(enc_rhs)


def get_coding_from_bytes(text: bytes) -> str | None:
    """Try to find an encoding spec from binary file content."""
    lines = text.splitlines()
    for line_count, regexp in CODING_FROM_BYTES:
        head = lines[:line_count]
        for line in head:
            match = regexp.search(line)
            if match:
                return str(match.group(1), "ascii")
    return None


def get_coding_from_text(text: str) -> str | None:
    """Try to find an encoding spec from text file content."""
    lines = text.splitlines()
    for line_count, regexp in CODING_FROM_TEXT:
        head = lines[:line_count]
        for line in head:
            match = regexp.search(line)
            if match:
                return match.group(1)
    return None


def detect_bom_encoding(data: bytes) -> str | None:
    """Return synthetic BOM encoding name when a BOM signature is present."""
    if data.startswith(BOM_UTF8):
        return "bom-utf-8"
    if data.startswith(BOM_UTF16):
        return "bom-utf-16"
    if data.startswith(BOM_UTF32):
        return "bom-utf-32"
    return None


def detect_read_encoding_from_header(
    data: bytes,
    *,
    project_encoding: str | None = None,
    ide_encoding: str | None = None,
    default_encoding: str = DEFAULT_TEXT_ENCODING,
) -> str:
    """Detect read encoding from BOM, coding cookie, and fallbacks."""
    bom = detect_bom_encoding(data)
    if bom:
        return bom
    enc_from_file = get_coding_from_bytes(data)
    if enc_from_file:
        return enc_from_file
    if project_encoding:
        return project_encoding
    if ide_encoding:
        return ide_encoding
    return default_encoding


def encoding_sanity_check(file_name: str, decoded_text: str, expected_encoding: str) -> bool:
    """Check whether expected encoding matches the encoding declared in Python source."""
    try:
        mod_info = getBriefModuleInfoFromMemory(decoded_text, file_name)
        mod_encoding = mod_info.encoding
        if mod_encoding:
            if not is_valid_encoding(mod_encoding.name):
                logging.warning("Invalid encoding %s found in the file %s", mod_encoding.name, file_name)
                return False
            if not are_encodings_equal(mod_encoding.name, expected_encoding):
                if expected_encoding.startswith("bom-"):
                    no_bom_encoding = expected_encoding[4:]
                    if are_encodings_equal(mod_encoding.name, no_bom_encoding):
                        return True
                logging.warning(
                    "The explicitly set encoding %s does not match encoding %s found in the file %s",
                    expected_encoding,
                    mod_encoding.name,
                    file_name,
                )
                return False
    except Exception:
        pass
    return True


def _try_bom_decode(raw: bytes, options: EncodingReadOptions) -> tuple[str, str] | None:
    """Decode raw bytes when a BOM signature is present."""
    bom = detect_bom_encoding(raw)
    if bom == "bom-utf-8":
        payload = raw[len(BOM_UTF8) :]
        norm_enc = encodings.normalize_encoding("utf-8")
        label = "bom-utf-8"
    elif bom == "bom-utf-16":
        payload = raw[len(BOM_UTF16) :]
        norm_enc = encodings.normalize_encoding("utf-16")
        label = "bom-utf-16"
    elif bom == "bom-utf-32":
        payload = raw[len(BOM_UTF32) :]
        norm_enc = encodings.normalize_encoding("utf-32")
        label = "bom-utf-32"
    else:
        return None
    try:
        decoded = payload.decode(norm_enc)
    except (UnicodeError, LookupError) as exc:
        logging.error("BOM signature %s found in %s but decoding failed: %s", label, options.file_name, exc)
        return None
    if options.check_python_source:
        encoding_sanity_check(options.file_name, decoded, label)
    return decoded, label


def read_encoded_bytes(raw: bytes, options: EncodingReadOptions) -> tuple[str, str]:
    """Decode bytes using BOM, user, cookie, project, IDE, and default fallbacks."""
    bom_result = _try_bom_decode(raw, options)
    if bom_result is not None:
        return bom_result

    tried: list[str] = []
    candidates: list[str | None] = [
        options.user_encoding,
        get_coding_from_bytes(raw),
        options.project_encoding,
        options.ide_encoding,
        options.default_encoding,
    ]
    for encoding in candidates:
        if not encoding:
            continue
        if not is_valid_encoding(encoding):
            logging.error("Invalid encoding %s for %s. Continue trying...", encoding, options.file_name)
            continue
        norm_enc = encodings.normalize_encoding(encoding)
        if norm_enc in tried:
            continue
        tried.append(norm_enc)
        try:
            decoded = raw.decode(norm_enc)
        except (UnicodeError, LookupError) as exc:
            logging.error("Failed to decode %s using encoding %s: %s", options.file_name, encoding, exc)
            continue
        if options.check_python_source:
            encoding_sanity_check(options.file_name, decoded, encoding)
        return decoded, encoding

    logging.warning("Last try: utf-8 decoding ignoring the errors for %s", options.file_name)
    return raw.decode("utf-8", "ignore"), "utf-8"


def read_encoded_file(path: str | Path, options: EncodingReadOptions) -> tuple[str, str]:
    """Read a file from disk and decode it with the configured fallback chain."""
    file_path = Path(path)
    payload = file_path.read_bytes()
    read_options = EncodingReadOptions(
        user_encoding=options.user_encoding,
        project_encoding=options.project_encoding,
        ide_encoding=options.ide_encoding,
        default_encoding=options.default_encoding,
        check_python_source=options.check_python_source,
        file_name=str(file_path),
    )
    return read_encoded_bytes(payload, read_options)
