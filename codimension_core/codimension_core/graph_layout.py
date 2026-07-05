# -*- coding: utf-8 -*-
"""Headless Graphviz plain output parser extracted from codimension.diagram.plaindotparser."""

from __future__ import annotations

import os
import shutil
import subprocess
import tempfile
from os.path import exists

from .errors import AnalysisError


def split_with_quotes_respect(line: str) -> list[str]:
    """Split space-separated values while respecting quoted strings."""

    def skip_spaces(text: str, start_pos: int) -> int:
        while start_pos < len(text):
            if text[start_pos] != " ":
                return start_pos
            start_pos += 1
        return start_pos

    def skip_till_space(text: str, start_pos: int) -> int:
        while start_pos < len(text):
            if text[start_pos] == " ":
                return start_pos
            start_pos += 1
        return start_pos

    def skip_till_closed_quote(text: str, start_pos: int) -> int:
        while start_pos < len(text):
            if text[start_pos] == '"':
                if text[start_pos - 1] == "\\":
                    start_pos += 1
                    continue
                return start_pos
            start_pos += 1
        return start_pos

    result: list[str] = []
    index = 0
    while index < len(line):
        index = skip_spaces(line, index)
        if index >= len(line):
            return result
        start_index = index
        if line[start_index] == '"':
            next_index = skip_till_closed_quote(line, start_index + 1)
            result.append(line[start_index + 1 : next_index])
            index = next_index + 1
        else:
            next_index = skip_till_space(line, start_index)
            result.append(line[start_index:next_index])
            index = next_index
    return result


splitWithQuotasRespect = split_with_quotes_respect


class Graph:
    """Holds a description of a single laid-out graph."""

    def __init__(self) -> None:
        self.scale = 0.0
        self.width = 0.0
        self.height = 0.0
        self.vSpace = 10.0
        self.hSpace = 10.0
        self.edges: list[Edge] = []
        self.nodes: list[Node] = []

    def normalize(self, scale_x: float, scale_y: float) -> None:
        self.width = self.width * self.scale * scale_x
        self.height = self.height * self.scale * scale_y
        for edge in self.edges:
            edge.normalize(self, scale_x, scale_y)
        for node in self.nodes:
            node.normalize(self, scale_x, scale_y)
        self.width = self.width + 2.0 * self.hSpace
        self.height = self.height + 2.0 * self.vSpace

    def init_from_line(self, line: str) -> None:
        parts = line.strip().split()
        if len(parts) != 4:
            raise AnalysisError("Unexpected number of parts in 'graph' statement")
        self.scale = float(parts[1].strip())
        self.width = float(parts[2].strip())
        self.height = float(parts[3].strip())

    initFromLine = init_from_line


class Edge:
    """Holds a single graph edge description."""

    def __init__(self) -> None:
        self.tail = ""
        self.head = ""
        self.points: list[list[float]] = []
        self.label = ""
        self.labelX = 0.0
        self.labelY = 0.0
        self.style = ""
        self.color = ""

    def normalize(self, graph: Graph, scale_x: float, scale_y: float) -> None:
        self.labelX = self.labelX * graph.scale * scale_x + graph.hSpace
        self.labelY = graph.height - self.labelY * graph.scale * scale_y + graph.vSpace
        for point in self.points:
            point[0] = point[0] * graph.scale * scale_x + graph.hSpace
            point[1] = graph.height - point[1] * graph.scale * scale_y + graph.vSpace

    def init_from_line(self, line: str) -> None:
        parts = split_with_quotes_respect(line.strip())
        if len(parts) < 8:
            raise AnalysisError(f"Unexpected number of parts in 'edge' statement. Line: {line}")
        self.tail = parts[1]
        self.head = parts[2]
        number_of_points = int(parts[3])
        if len(parts) < (number_of_points * 2 + 5):
            raise AnalysisError(f"Unexpected number of parts in 'edge' statement. Line: {line}")
        self.points = []
        for point in range(number_of_points):
            self.points.append([float(parts[point * 2 + 4]), float(parts[point * 2 + 4 + 1])])
        parts = parts[number_of_points * 2 + 4 :]
        self.label = ""
        self.labelX = 0.0
        self.labelY = 0.0
        self.style = ""
        self.color = ""
        if len(parts) == 2:
            self.style = parts[0]
            self.color = parts[1]
        else:
            self.label = parts[0]
            self.labelX = float(parts[1])
            self.labelY = float(parts[2])
            self.style = parts[3]
            self.color = parts[4]

    initFromLine = init_from_line


class Node:
    """Holds a single node description."""

    def __init__(self) -> None:
        self.name = ""
        self.posX = 0.0
        self.posY = 0.0
        self.width = 0.0
        self.height = 0.0
        self.label = ""
        self.style = ""
        self.shape = ""
        self.color = ""
        self.fillcolor = ""

    def normalize(self, graph: Graph, scale_x: float, scale_y: float) -> None:
        self.posX = self.posX * graph.scale * scale_x + graph.hSpace
        self.posY = graph.height - self.posY * graph.scale * scale_y + graph.vSpace
        self.width = self.width * graph.scale * scale_x
        self.height = self.height * graph.scale * scale_y

    def init_from_line(self, line: str) -> None:
        parts = split_with_quotes_respect(line.strip())
        if len(parts) < 11:
            raise AnalysisError(f"Unexpected number of parts in 'node' statement. Line: {line}")
        self.name = parts[1]
        self.posX = float(parts[2].strip())
        self.posY = float(parts[3].strip())
        self.width = float(parts[4].strip())
        self.height = float(parts[5].strip())
        self.label = parts[6]
        self.style = parts[7].strip()
        self.shape = parts[8].strip()
        self.color = parts[9].strip()
        self.fillcolor = parts[10].strip()

    initFromLine = init_from_line


def get_graph_from_plain_dot_data(content: str) -> Graph:
    """Parse Graphviz plain output into a layout graph."""
    graph = Graph()
    expect_continue = False
    combined_line = ""
    for line in content.split("\n"):
        line = line.strip()
        if line == "":
            continue
        if line.endswith("\\"):
            combined_line += line[:-1]
            expect_continue = True
            continue
        if expect_continue:
            expect_continue = False
        combined_line += line
        if combined_line.startswith("graph"):
            graph.init_from_line(combined_line)
            combined_line = ""
            continue
        if combined_line.startswith("node"):
            node = Node()
            node.init_from_line(combined_line)
            graph.nodes.append(node)
            combined_line = ""
            continue
        if combined_line.startswith("edge"):
            edge = Edge()
            edge.init_from_line(combined_line)
            graph.edges.append(edge)
            combined_line = ""
            continue
        if combined_line.startswith("stop"):
            break
        raise AnalysisError(f"Unexpected plain dot line: {combined_line}")
    return graph


getGraphFromPlainDotData = get_graph_from_plain_dot_data


def run_dot_plain(dot_path: str) -> str:
    """Run graphviz dot -Tplain on a dot file path."""
    if shutil.which("dot") is None:
        raise AnalysisError("graphviz 'dot' executable not found in PATH")
    try:
        completed = subprocess.run(
            ["dot", "-Tplain", dot_path],
            capture_output=True,
            text=True,
            check=True,
        )
    except subprocess.CalledProcessError as exc:
        message = exc.stderr.strip() or exc.stdout.strip() or str(exc)
        raise AnalysisError(f"graphviz dot failed: {message}") from exc
    return completed.stdout


def get_graph_from_description_file(path: str) -> Graph:
    """Run dot on a dot file and parse plain output."""
    if not exists(path):
        raise AnalysisError(f"Cannot open {path}")
    return get_graph_from_plain_dot_data(run_dot_plain(path))


getGraphFromDescrptionFile = get_graph_from_description_file


def get_graph_from_description_data(content: str) -> Graph:
    """Write dot source to a temp file, run dot, parse plain output."""
    with tempfile.NamedTemporaryFile(mode="w", suffix=".dot", delete=False, encoding="utf-8") as handle:
        handle.write(content)
        temp_path = handle.name
    try:
        return get_graph_from_description_file(temp_path)
    finally:
        os.unlink(temp_path)


getGraphFromDescriptionData = get_graph_from_description_data


def layout_graph_from_dot(
    dot_source: str,
    *,
    scale_x: float = 72.0,
    scale_y: float = 72.0,
) -> Graph:
    """Layout Graphviz DOT and return normalized screen coordinates."""
    graph = get_graph_from_description_data(dot_source)
    graph.normalize(scale_x, scale_y)
    return graph
