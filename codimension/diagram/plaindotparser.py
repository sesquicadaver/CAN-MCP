# -*- coding: utf-8 -*-
#
# Legacy logic extracted to codimension_core.graph_layout (2026-07-05).
#

"""dot output (plain) parser — IDE wrapper over codimension_core.graph_layout."""

from codimension_core.graph_layout import (
    Edge,
    Graph,
    Node,
    getGraphFromDescriptionData,
    getGraphFromDescrptionFile,
    getGraphFromPlainDotData,
    splitWithQuotasRespect,
)

from utils.fileutils import getFileContent


def getGraphFromPlainDotFile(fName):
    """Parses file and builds a normalized graph."""
    return getGraphFromPlainDotData(getFileContent(fName))
