# -*- coding: utf-8 -*-
#
# codimension - graphics python two-way code editor and analyzer
# Copyright (C) 2010-2017  Sergey Satskiy <sergey.satskiy@gmail.com>
#
# Legacy archive: Carantine/codimension/analysis/ierrors_legacy.py

"""Interactive errors report — IDE wrapper over codimension_core.analyzer."""

from codimension_core.analyzer import get_buffer_errors as _core_get_buffer_errors


def getBufferErrors(sourceCode):
    """Provides a list of warnings/errors for the given source code."""
    return _core_get_buffer_errors(sourceCode)
