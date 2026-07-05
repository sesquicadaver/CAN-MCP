# -*- coding: utf-8 -*-
"""Headless import diagram data model extracted from codimension.diagram.importsdgm."""

from __future__ import annotations

from dataclasses import dataclass
from os.path import basename

from .dependency_graph import build_import_graph
from .graph_ir import GraphIR
from .project import Project


class DgmConnection:
    """Holds information about one connection."""

    ModuleDoc = 0
    ModuleDependency = 1

    def __init__(self) -> None:
        self.objName = ""
        self.kind = -1
        self.source = ""
        self.target = ""
        self.labels: list[str] = []

    def to_graphviz(self) -> str:
        attributes = f'id="{self.objName}", arrowhead=none'
        label = "\\n".join(self.labels)
        if label:
            attributes += f', label="{label}", fontname=Arial, fontsize=10'
        return f"{self.source} -> {self.target}[ {attributes} ];"

    toGraphviz = to_graphviz

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, DgmConnection):
            return NotImplemented
        return self.source == other.source and self.target == other.target


class DgmDocstring:
    """Holds information about one docstring box."""

    def __init__(self) -> None:
        self.objName = ""
        self.docstring = None
        self.refFile = ""

    def to_graphviz(self) -> str:
        text = getattr(self.docstring, "text", str(self.docstring or ""))
        escaped = text.replace("\n", "\\n").replace('"', '\\"')
        attributes = "shape=box, fontname=Arial, fontsize=10"
        return f'{self.objName} [ {attributes}, label="{escaped}" ];'

    toGraphviz = to_graphviz


class DgmModule:
    """Holds information about one module box."""

    ModuleOfInterest = 0
    OtherProjectModule = 1
    SystemWideModule = 2
    BuiltInModule = 3
    UnknownModule = 4

    def __init__(self) -> None:
        self.objName = ""
        self.kind = -1
        self.title = ""
        self.classes: list[object] = []
        self.funcs: list[object] = []
        self.globs: list[object] = []
        self.imports: list[object] = []
        self.refFile = ""
        self.docstring = ""

    def to_graphviz(self) -> str:
        classes_part = "\\n".join(getattr(item, "name", str(item)) for item in self.classes)
        funcs_part = "\\n".join(getattr(item, "name", str(item)) for item in self.funcs)
        globs_part = "\\n".join(getattr(item, "name", str(item)) for item in self.globs)
        attributes = "shape=box, fontname=Arial, fontsize=10"
        if self.is_project_module():
            label = f"\\n{self.title}\\n{classes_part}\\n{funcs_part}\\n{globs_part}"
            return f'{self.objName} [ {attributes}, label="{label}" ];'
        return f'{self.objName} [ {attributes}, label="{self.title}" ];'

    toGraphviz = to_graphviz

    def is_project_module(self) -> bool:
        return self.kind in (self.ModuleOfInterest, self.OtherProjectModule)

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, DgmModule):
            return NotImplemented
        if self.is_project_module() and other.is_project_module():
            return self.refFile == other.refFile
        return self.refFile == other.refFile and self.kind == other.kind and self.title == other.title


class DgmRank:
    """Graphviz rank constraint."""

    def __init__(self) -> None:
        self.firstObj = ""
        self.secondObj = ""

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, DgmRank):
            return NotImplemented
        return self.firstObj == other.firstObj and self.secondObj == other.secondObj

    def to_graphviz(self) -> str:
        return f'{{ rank=same; "{self.firstObj}"; "{self.secondObj}"; }}'

    toGraphviz = to_graphviz


@dataclass
class ImportDiagramOptions:
    include_classes: bool = True
    include_funcs: bool = True
    include_globs: bool = True
    include_docs: bool = False
    include_conn_text: bool = True


class ImportDiagramModel:
    """Import diagram data model (Graphviz-oriented)."""

    def __init__(self) -> None:
        self.modules: list[DgmModule] = []
        self.docstrings: list[DgmDocstring] = []
        self.connections: list[DgmConnection] = []
        self.ranks: list[DgmRank] = []
        self._objects_counter = -1

    def clear(self) -> None:
        self.modules = []
        self.docstrings = []
        self.connections = []
        self.ranks = []
        self._objects_counter = -1

    def to_graphviz(self) -> str:
        result = "digraph ImportsDiagram { "
        for item in self.docstrings:
            result += item.to_graphviz() + "\n"
        for item in self.modules:
            result += item.to_graphviz() + "\n"
        for item in self.connections:
            result += item.to_graphviz() + "\n"
        for item in self.ranks:
            result += item.to_graphviz() + "\n"
        result += "}"
        return result

    toGraphviz = to_graphviz

    def _new_name(self) -> str:
        self._objects_counter += 1
        return f"obj{self._objects_counter}"

    def add_module(self, mod_box: DgmModule) -> str:
        for index, existing in enumerate(self.modules):
            if existing == mod_box:
                if mod_box.kind == DgmModule.ModuleOfInterest and existing.kind != mod_box.kind:
                    mod_box.objName = existing.objName
                    self.modules[index] = mod_box
                return existing.objName
        mod_box.objName = self._new_name()
        self.modules.append(mod_box)
        return mod_box.objName

    def add_connection(self, conn: DgmConnection) -> str:
        for index, existing in enumerate(self.connections):
            if existing == conn:
                existing.labels.extend(conn.labels)
                return existing.objName
        conn.objName = self._new_name()
        self.connections.append(conn)
        return conn.objName


def build_import_diagram_model(
    project: Project,
    options: ImportDiagramOptions | None = None,
) -> ImportDiagramModel:
    """Build a headless import diagram model from the resolved import graph."""
    _ = options or ImportDiagramOptions()
    project.require_open()
    import_graph: GraphIR = build_import_graph(project)
    model = ImportDiagramModel()
    node_ids: dict[str, str] = {}

    for node in import_graph.nodes:
        if not node.id.startswith("file:"):
            continue
        module = DgmModule()
        module.kind = DgmModule.ModuleOfInterest
        module.title = node.name
        module.refFile = node.file
        node_ids[node.id] = model.add_module(module)

    for edge in import_graph.edges:
        source_id = node_ids.get(edge.from_id)
        target_id = node_ids.get(edge.to_id)
        if source_id is None or target_id is None:
            if edge.to_id.startswith("file:"):
                imported = DgmModule()
                imported.kind = DgmModule.OtherProjectModule
                imported.title = basename(edge.to_id.replace("file:", ""))
                target_id = model.add_module(imported)
                node_ids[edge.to_id] = target_id
            else:
                imported = DgmModule()
                if edge.to_id.startswith("builtin:"):
                    imported.kind = DgmModule.BuiltInModule
                else:
                    imported.kind = DgmModule.UnknownModule
                imported.title = edge.to_id.split(":", 1)[-1]
                target_id = model.add_module(imported)
            source_id = node_ids.get(edge.from_id)
        if source_id is None or target_id is None:
            continue
        conn = DgmConnection()
        conn.kind = DgmConnection.ModuleDependency
        conn.source = source_id
        conn.target = target_id
        if edge.label:
            conn.labels.append(edge.label)
        model.add_connection(conn)

    return model
