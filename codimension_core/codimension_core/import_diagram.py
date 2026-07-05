# -*- coding: utf-8 -*-
"""Headless import diagram data model extracted from codimension.diagram.importsdgm."""

from __future__ import annotations

from dataclasses import dataclass
from os.path import basename, dirname, isabs, isfile, realpath

from .imports import build_import_context, resolve_imports
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
        label = ""
        for item in self.labels:
            if label:
                label += "\\n"
            label += item
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
        classes_part = ""
        funcs_part = ""
        globs_part = ""
        for klass in self.classes:
            classes_part += ("\\n" if classes_part else "") + klass.name
        for func in self.funcs:
            funcs_part += ("\\n" if funcs_part else "") + func.name
        for glob in self.globs:
            globs_part += ("\\n" if globs_part else "") + glob.name
        spare = "\\n"
        attributes = "shape=box, fontname=Arial, fontsize=10"
        if self.is_project_module():
            return (
                f'{self.objName} [ {attributes}, label="{spare}{self.title}\\n'
                f"{classes_part}\\n{funcs_part}\\n{globs_part}\" ];"
            )
        return f'{self.objName} [ {attributes}, label="{self.title}" ];'

    toGraphviz = to_graphviz

    def is_project_module(self) -> bool:
        return self.kind in (self.ModuleOfInterest, self.OtherProjectModule)

    isProjectModule = is_project_module

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, DgmModule):
            return NotImplemented
        if self.is_project_module() and other.is_project_module():
            return self.refFile == other.refFile
        return self.refFile == other.refFile and self.kind == other.kind and self.title == other.title

    def getTooltip(self) -> str:
        tooltip = self.refFile or ""
        if self.docstring:
            tooltip = f"{tooltip}\n\n{self.docstring}" if tooltip else self.docstring
        return tooltip


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

    @classmethod
    def from_legacy(
        cls,
        *,
        include_classes: bool = True,
        include_funcs: bool = True,
        include_globs: bool = True,
        include_docs: bool = False,
        include_conn_text: bool = True,
    ) -> ImportDiagramOptions:
        return cls(
            include_classes=include_classes,
            include_funcs=include_funcs,
            include_globs=include_globs,
            include_docs=include_docs,
            include_conn_text=include_conn_text,
        )


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

    def add_rank(self, rank: DgmRank) -> None:
        if rank not in self.ranks:
            self.ranks.append(rank)

    def add_connection(self, conn: DgmConnection) -> str:
        for index, existing in enumerate(self.connections):
            if existing == conn:
                existing.labels.extend(conn.labels)
                return existing.objName
        conn.objName = self._new_name()
        self.connections.append(conn)
        return conn.objName

    def add_docstring_box(self, doc_box: DgmDocstring) -> str:
        doc_box.objName = self._new_name()
        self.docstrings.append(doc_box)
        return doc_box.objName

    def add_module(self, mod_box: DgmModule) -> str:
        for index, existing in enumerate(self.modules):
            if existing == mod_box:
                if mod_box.kind == existing.kind:
                    return existing.objName
                if mod_box.kind == DgmModule.ModuleOfInterest:
                    mod_box.objName = existing.objName
                    self.modules[index] = mod_box
                    return mod_box.objName
                return existing.objName
        mod_box.objName = self._new_name()
        self.modules.append(mod_box)
        return mod_box.objName

    def find_module(self, name: str) -> DgmModule | None:
        for obj in self.modules:
            if obj.objName == name:
                return obj
        return None

    def find_connection(self, name: str, tail: str = "") -> DgmConnection | None:
        if not tail:
            for obj in self.connections:
                if obj.objName == name:
                    return obj
            return None
        for obj in self.connections:
            if obj.source == name and obj.target == tail:
                return obj
        return None

    def find_docstring(self, name: str) -> DgmDocstring | None:
        for obj in self.docstrings:
            if obj.objName == name:
                return obj
        return None

    addRank = add_rank
    addConnection = add_connection
    addDocstringBox = add_docstring_box
    addModule = add_module
    findModule = find_module
    findConnection = find_connection
    findDocstring = find_docstring


def module_title_from_path(file_name: str) -> str:
    base_title = basename(file_name).split(".")[0]
    if base_title != "__init__":
        return base_title
    top_dir = basename(dirname(file_name))
    return f"{top_dir}({base_title})"


def is_local_or_project(project: Project, file_name: str, resolved_path: str | None) -> bool:
    if resolved_path is None or not isabs(resolved_path):
        return False
    if project.is_project_path(resolved_path):
        return True
    resolved_dir = dirname(realpath(resolved_path))
    base_dir = dirname(realpath(file_name))
    return resolved_dir.startswith(base_dir)


def populate_module_box(box: DgmModule, info: object, options: ImportDiagramOptions) -> None:
    if getattr(info, "docstring", None) is not None:
        box.docstring = info.docstring.text
    if options.include_classes:
        box.classes.extend(getattr(info, "classes", []))
    if options.include_funcs:
        box.funcs.extend(getattr(info, "functions", []))
    if options.include_globs:
        box.globs.extend(getattr(info, "globals", []))
    if options.include_conn_text:
        box.imports.extend(getattr(info, "imports", []))


def system_wide_docstring(project: Project, path: str) -> str:
    if not path.endswith(".py") or not isfile(path):
        return ""
    try:
        info = project.cache.get(realpath(path))
        if getattr(info, "docstring", None) is not None:
            return info.docstring.text
    except (OSError, FileNotFoundError):
        return ""
    return ""


def add_docstring_box(
    model: ImportDiagramModel,
    info: object,
    file_name: str,
    mod_box_name: str,
    options: ImportDiagramOptions,
) -> None:
    if not options.include_docs or getattr(info, "docstring", None) is None:
        return
    doc_box = DgmDocstring()
    doc_box.docstring = info.docstring
    doc_box.refFile = file_name
    doc_box_name = model.add_docstring_box(doc_box)
    conn = DgmConnection()
    conn.kind = DgmConnection.ModuleDoc
    conn.source = mod_box_name
    conn.target = doc_box_name
    model.add_connection(conn)
    rank = DgmRank()
    rank.firstObj = mod_box_name
    rank.secondObj = doc_box_name
    model.add_rank(rank)


def add_single_file_to_model(
    project: Project,
    model: ImportDiagramModel,
    info: object,
    file_name: str,
    options: ImportDiagramOptions,
    errors: list[str] | None = None,
) -> None:
    """Add one file module and its import dependencies to the diagram model."""
    if file_name.endswith("__init__.py"):
        if not getattr(info, "classes", []) and not getattr(info, "functions", []) and not getattr(info, "globals", []) and not getattr(info, "imports", []):
            return

    mod_box = DgmModule()
    mod_box.refFile = file_name
    mod_box.kind = DgmModule.ModuleOfInterest
    mod_box.title = module_title_from_path(file_name)
    populate_module_box(mod_box, info, options)
    mod_box_name = model.add_module(mod_box)
    add_docstring_box(model, info, file_name, mod_box_name, options)

    context = build_import_context(project, file_name)
    resolved_imports, import_errors = resolve_imports(context, file_name, info.imports)
    if errors is not None:
        errors.extend(import_errors)

    for import_name, resolved_path, imported_names in resolved_imports:
        imp_box = DgmModule()
        imp_box.title = import_name
        if is_local_or_project(project, file_name, resolved_path):
            imp_box.kind = DgmModule.OtherProjectModule
            imp_box.refFile = realpath(resolved_path) if resolved_path else ""
            if resolved_path and resolved_path.endswith(".py") and isfile(resolved_path):
                other_info = project.cache.get(realpath(resolved_path))
                populate_module_box(imp_box, other_info, options)
        elif resolved_path is None:
            imp_box.kind = DgmModule.UnknownModule
        elif isabs(resolved_path):
            imp_box.kind = DgmModule.SystemWideModule
            imp_box.refFile = resolved_path
            imp_box.docstring = system_wide_docstring(project, resolved_path)
        else:
            imp_box.kind = DgmModule.BuiltInModule

        imp_box_name = model.add_module(imp_box)
        imp_conn = DgmConnection()
        imp_conn.kind = DgmConnection.ModuleDependency
        imp_conn.source = mod_box_name
        imp_conn.target = imp_box_name
        if options.include_conn_text:
            for imp_what in imported_names:
                if imp_what:
                    imp_conn.labels.append(imp_what)
        model.add_connection(imp_conn)


def build_import_diagram_model(
    project: Project,
    files: list[str] | None = None,
    options: ImportDiagramOptions | None = None,
) -> ImportDiagramModel:
    """Build import diagram model for project files using full resolution logic."""
    opts = options or ImportDiagramOptions()
    project.require_open()
    target_files = files if files is not None else project.python_files
    model = ImportDiagramModel()
    errors: list[str] = []
    for file_name in target_files:
        info = project.cache.get(realpath(file_name))
        add_single_file_to_model(project, model, info, file_name, opts, errors)
    return model


def _module_kind_name(kind: int) -> str:
    mapping = {
        DgmModule.ModuleOfInterest: "module_of_interest",
        DgmModule.OtherProjectModule: "other_project_module",
        DgmModule.SystemWideModule: "system_wide_module",
        DgmModule.BuiltInModule: "builtin_module",
        DgmModule.UnknownModule: "unknown_module",
    }
    return mapping.get(kind, "module")


def import_diagram_model_to_graph_ir(model: ImportDiagramModel) -> GraphIR:
    """Convert import diagram model to Graph IR for HTML/Mermaid renderers."""
    from .graph_ir import GraphEdge, GraphIR, GraphNode

    graph = GraphIR(
        meta={
            "kind": "import_diagram",
            "modules": len(model.modules),
            "connections": len(model.connections),
            "docstrings": len(model.docstrings),
            "graphviz": model.to_graphviz(),
        }
    )
    for mod in model.modules:
        if not mod.objName:
            continue
        graph.add_node(
            GraphNode(
                id=mod.objName,
                type=_module_kind_name(mod.kind),
                name=mod.title or mod.objName,
                file=mod.refFile,
                line_start=1,
                line_end=1,
                extra={"classes": len(mod.classes), "funcs": len(mod.funcs), "globs": len(mod.globs)},
            )
        )
    for doc in model.docstrings:
        if not doc.objName:
            continue
        graph.add_node(
            GraphNode(
                id=doc.objName,
                type="docstring",
                name="docstring",
                file=doc.refFile,
                line_start=1,
                line_end=1,
            )
        )
    for conn in model.connections:
        label = "\\n".join(conn.labels) if conn.labels else ""
        edge_type = "module_doc" if conn.kind == DgmConnection.ModuleDoc else "module_dependency"
        graph.add_edge(
            GraphEdge(
                from_id=conn.source,
                to_id=conn.target,
                type=edge_type,
                label=label,
            )
        )
    return graph


def build_import_diagram_graph_ir(project: Project, options: ImportDiagramOptions | None = None) -> GraphIR:
    """Build Graph IR from the full import diagram model."""
    model = build_import_diagram_model(project, options=options)
    return import_diagram_model_to_graph_ir(model)
