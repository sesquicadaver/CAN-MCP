# -*- coding: utf-8 -*-
#
# codimension - graphics python two-way code editor and analyzer
# Copyright (C) 2010-2017 Sergey Satskiy <sergey.satskiy@gmail.com>
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.
#

"""Encoding related functions"""

# pylint: disable=W0702
# pylint: disable=W0703

import encodings
import logging
import os.path
from codecs import BOM_UTF8, BOM_UTF16, BOM_UTF32

from codimension_core.encoding_utils import (
    EncodingReadOptions,
    are_encodings_equal as areEncodingsEqual,
    convert_line_ends as convertLineEnds,
    detect_bom_encoding,
    detect_eol_string as detectEolString,
    detect_read_encoding_from_header,
    encoding_sanity_check as encodingSanityCheck,
    get_coding_from_bytes as getCodingFromBytes,
    get_coding_from_text as getCodingFromText,
    get_normalized_encoding as getNormalizedEncoding,
    is_valid_encoding as isValidEncoding,
    read_encoded_bytes,
)

from .config import DEFAULT_ENCODING
from .diskvaluesrelay import getFileEncoding
from .fileutils import isPythonFile
from .globals import GlobalData
from .settings import Settings


def detectEncodingOnClearExplicit(fName, content):
    """Provides the reading encoding as a file would be read"""
    # The function is used in case the user reset the explicit encoding
    # so the current encoding needs to be set as if the file would be
    # read again
    try:
        with open(fName, "rb") as diskfile:
            text = diskfile.read(1024)

        if text.startswith(BOM_UTF8):
            return "bom-utf-8"
        if text.startswith(BOM_UTF16):
            return "bom-utf-16"
        if text.startswith(BOM_UTF32):
            return "bom-utf-32"

        # The function is called when an explicit encoding is reset so
        # there is no need to check for it

        encFromBuffer = getCodingFromText(content)
        if encFromBuffer:
            if isValidEncoding(encFromBuffer):
                return encFromBuffer

        project = GlobalData().project
        if project.isLoaded():
            projectEncoding = project.props["encoding"]
            if projectEncoding:
                if isValidEncoding(projectEncoding):
                    return projectEncoding

        ideEncoding = Settings()["encoding"]
        if ideEncoding:
            if isValidEncoding(ideEncoding):
                return ideEncoding

        return DEFAULT_ENCODING
    except Exception as exc:
        logging.warning("Error while guessing encoding for reading %s: %s", fName, str(exc))
        logging.warning("The default encoding %s will be used", DEFAULT_ENCODING)
        return DEFAULT_ENCODING


def detectFileEncodingToRead(fName, text=None):
    """Detects the read encoding"""
    if text is None:
        with open(fName, "rb") as diskfile:
            text = diskfile.read(1024)

    userAssignedEncoding = getFileEncoding(fName)
    if userAssignedEncoding:
        return userAssignedEncoding

    project_encoding = None
    project = GlobalData().project
    if project.isLoaded():
        project_encoding = project.props.get("encoding") or None
    ide_encoding = Settings()["encoding"] or None
    return detect_read_encoding_from_header(
        text,
        project_encoding=project_encoding,
        ide_encoding=ide_encoding,
        default_encoding=DEFAULT_ENCODING,
    )


def decode(content):
    """Decode bytes to (text, encoding). For VCS annotate etc.
    content: bytes to decode (or str, returned as-is)
    Returns: (decoded_text, encoding_name)
    """
    if isinstance(content, str):
        return content, DEFAULT_ENCODING
    bom = detect_bom_encoding(content)
    if bom == "bom-utf-8":
        content = content[len(BOM_UTF8) :]
        enc = "bom-utf-8"
    elif bom == "bom-utf-16":
        content = content[len(BOM_UTF16) :]
        enc = "bom-utf-16"
    elif bom == "bom-utf-32":
        content = content[len(BOM_UTF32) :]
        enc = "bom-utf-32"
    else:
        project_encoding = None
        project = GlobalData().project
        if project.isLoaded():
            project_encoding = project.props.get("encoding") or None
        ide_encoding = Settings()["encoding"] or None
        enc = detect_read_encoding_from_header(
            content,
            project_encoding=project_encoding,
            ide_encoding=ide_encoding,
            default_encoding=DEFAULT_ENCODING,
        )
    norm_enc = encodings.normalize_encoding(enc)
    return content.decode(norm_enc), enc


def readEncodedFile(fName):
    """Reads the encoded file"""
    project_encoding = None
    project = GlobalData().project
    if project.isLoaded():
        project_encoding = project.props.get("encoding") or None
    options = EncodingReadOptions(
        user_encoding=getFileEncoding(fName),
        project_encoding=project_encoding,
        ide_encoding=Settings()["encoding"] or None,
        default_encoding=DEFAULT_ENCODING,
        check_python_source=isPythonFile(fName),
        file_name=fName,
    )
    with open(fName, "rb") as diskfile:
        return read_encoded_bytes(diskfile.read(), options)


def detectNewFileWriteEncoding(editor, fName):
    """Detects a new file encoding"""
    # It could be one of two cases:
    # - the file is just created and there is no user typed content yet
    # - a new content has been modified
    isPython = isPythonFile(fName)

    if editor.explicitUserEncoding:
        # The user specifically set an encoding for a new buffer
        # It is impossible to set an invalid encoding
        if isPython:
            encFromText = getCodingFromText(editor.text)
            if encFromText:
                if not isValidEncoding(encFromText):
                    logging.warning(
                        "Encoding from the buffer (%s) is invalid and does not "
                        "match the explicitly set encoding %s. The %s is used",
                        encFromText,
                        editor.explicitUserEncoding,
                        editor.explicitUserEncoding,
                    )
                elif not areEncodingsEqual(editor.explicitUserEncoding, encFromText):
                    logging.warning(
                        "Encoding from the buffer (%s) does not match the explicitly set encoding %s. The %s is used",
                        encFromText,
                        editor.explicitUserEncoding,
                        editor.explicitUserEncoding,
                    )
        return editor.explicitUserEncoding

    # This is rather paranoic. The user could have a file with a specific
    # encoding assigned. Then the file was deleted and the buffer is saved
    # again.
    userAssignedEncoding = getFileEncoding(fName)
    if userAssignedEncoding:
        if not isValidEncoding(userAssignedEncoding):
            logging.error(
                "User assigned encoding %s is invalid. Please assign a valid one and try again.", userAssignedEncoding
            )
            return None
        if isPython:
            encFromText = getCodingFromText(editor.text)
            if encFromText:
                if not isValidEncoding(encFromText):
                    logging.warning(
                        "Encoding from the buffer (%s) is invalid and does not "
                        "match the explicitly set encoding %s. The %s is used",
                        encFromText,
                        userAssignedEncoding,
                        userAssignedEncoding,
                    )
                elif not areEncodingsEqual(userAssignedEncoding, encFromText):
                    logging.warning(
                        "Encoding from the buffer (%s) does not match the explicitly set encoding %s. The %s is used",
                        encFromText,
                        userAssignedEncoding,
                        userAssignedEncoding,
                    )
        return userAssignedEncoding

    # Check the buffer
    if isPython:
        encFromText = getCodingFromText(editor.text)
        if encFromText:
            if not isValidEncoding(encFromText):
                logging.error(
                    "Encoding from the buffer (%s) is invalid. Please fix the "
                    "encoding in the source or explicitly set the required one "
                    "and try again.",
                    encFromText,
                )
                return None
            return encFromText

    # Check the project default encoding
    project = GlobalData().project
    if project.isLoaded():
        projectEncoding = project.props["encoding"]
        if projectEncoding:
            if not isValidEncoding(projectEncoding):
                logging.error(
                    "The project encoding %s is invalid. Please select a valid "
                    "one in the project properties and try again.",
                    projectEncoding,
                )
                return None
            return projectEncoding

    # Check the IDE wide encoding
    ideEncoding = Settings()["encoding"]
    if ideEncoding:
        if not isValidEncoding(ideEncoding):
            logging.error("The ide encoding %s is invalid. Please set a valid one and try again.", ideEncoding)
            return None
        return ideEncoding

    # The default one
    return DEFAULT_ENCODING


def detectExistingFileWriteEncoding(editor, fName):
    """Provides the previously opened file encoding"""
    isPython = isPythonFile(fName)

    # The file is not new and there are a few sources of the encoding:
    # - the one which was used during reading (editor.encoding)
    # - user explicitly specified
    # - encoding in the buffer
    userAssignedEncoding = getFileEncoding(fName)
    if userAssignedEncoding:
        if not isValidEncoding(userAssignedEncoding):
            logging.error(
                "User assigned encoding %s is invalid. Please assign a valid one and try again.", userAssignedEncoding
            )
            return None
        if isPython:
            encFromText = getCodingFromText(editor.text)
            if encFromText:
                if not isValidEncoding(encFromText):
                    logging.warning(
                        "Encoding from the buffer (%s) is invalid and "
                        "does not match the explicitly set encoding %s. "
                        "The %s is used",
                        encFromText,
                        userAssignedEncoding,
                        userAssignedEncoding,
                    )
                elif not areEncodingsEqual(userAssignedEncoding, encFromText):
                    logging.warning(
                        "Encoding from the buffer (%s) does not match the explicitly set encoding %s. The %s is used",
                        encFromText,
                        userAssignedEncoding,
                        userAssignedEncoding,
                    )
        return userAssignedEncoding

    # Check the buffer
    if isPython:
        encFromText = getCodingFromText(editor.text)
        if encFromText:
            if not isValidEncoding(encFromText):
                logging.error(
                    "Encoding from the buffer (%s) is invalid. Please fix the"
                    "encoding in the source or explicitly set the required one "
                    "and try again.",
                    encFromText,
                )
                return None
            return encFromText

    # Here: no explicitly specified encoding, no encoding in the buffer,
    #       then use the encoding the file was read with
    return editor.encoding


def detectWriteEncoding(editor, fName):
    """Detects the write encoding for a buffer"""
    # If editor.encoding is None => the file has never been saved
    # At the same time fName may exist, i.e. a new file overwrites the existing
    # one.
    if os.path.isabs(fName) and os.path.exists(fName) and editor.encoding is not None:
        return detectExistingFileWriteEncoding(editor, fName)
    return detectNewFileWriteEncoding(editor, fName)


def writeEncodedFile(fName, content, encoding):
    """Writes into a file taking care of encoding"""
    normEnc = getNormalizedEncoding(encoding)
    try:
        if normEnc.startswith("bom_"):
            enc = normEnc[4:]
            if enc == "utf_8":
                encContent = BOM_UTF8 + content.encode(enc)
            elif enc == "utf_16":
                encContent = BOM_UTF16 + content.encode(enc)
            else:
                encContent = BOM_UTF32 + content.encode(enc)
        else:
            encContent = content.encode(normEnc)

            # Workaround for empty files: if there is no visible content and
            # the file is saved then the editor reports precisely \n which is
            # saved on disk and then detected as octet-stream. If there are
            # more than one \n then the file is detected as plain text.
            # The octet stream files are not openable in Codimension
            if encContent == b"\n":
                encContent = b""
    except (UnicodeError, LookupError) as exc:
        raise Exception("Error encoding the buffer content with " + encoding + ": " + str(exc))

    try:
        with open(fName, "wb") as diskfile:
            diskfile.write(encContent)
    except Exception as exc:
        raise Exception("Error writing encoded buffer content into " + fName + ": " + str(exc))


def decodeURLContent(content):
    """Decodes the content read from a URL"""
    project = GlobalData().project
    if project.isLoaded():
        projectEncoding = project.props["encoding"]
        if projectEncoding:
            if not isValidEncoding(projectEncoding):
                raise Exception(
                    "The prject encoding " + projectEncoding + " is invalid. "
                    "Please select a valid one in the project properties and "
                    "try again."
                )
            return content.decode(encodings.normalize_encoding(projectEncoding))

    # Check the IDE wide encoding
    ideEncoding = Settings()["encoding"]
    if ideEncoding:
        if not isValidEncoding(ideEncoding):
            raise Exception("The ide encoding " + ideEncoding + " is invalid. Please set a valid one and try again.")
        return content.decode(encodings.normalize_encoding(ideEncoding))

    # The default one
    return content.decode(DEFAULT_ENCODING)
