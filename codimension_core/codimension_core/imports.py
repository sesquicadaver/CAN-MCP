# -*- coding: utf-8 -*-
"""Headless import resolution extracted from codimension.utils.importutils."""

from __future__ import annotations

import importlib
import importlib.util
import os
import re
import sys
from dataclasses import dataclass, field
from os.path import basename, dirname, realpath, sep

import codimension.parsers  # noqa: F401
from cdmpyparser import getBriefModuleInfoFromMemory

from .graph_ir import GraphEdge, GraphIR, GraphNode
from .project import Project

_STDLIB_MODULES = frozenset(
    {
        "os",
        "io",
        "sys",
        "re",
        "json",
        "math",
        "datetime",
        "time",
        "logging",
        "pathlib",
        "subprocess",
        "argparse",
        "collections",
        "itertools",
        "functools",
        "typing",
        "abc",
        "copy",
        "hashlib",
        "uuid",
        "tempfile",
        "shutil",
        "glob",
        "socket",
        "threading",
        "multiprocessing",
        "asyncio",
        "contextlib",
        "unittest",
        "doctest",
        "pdb",
        "traceback",
        "warnings",
        "importlib",
        "configparser",
        "csv",
        "xml",
        "html",
        "email",
        "urllib",
        "http",
        "sqlite3",
        "pickle",
        "shelve",
        "getpass",
        "platform",
        "errno",
        "ctypes",
    }
)


@dataclass
class ImportContext:
    """Search paths and sys.path baseline for import resolution."""

    file_name: str | None = None
    search_paths: list[str] = field(default_factory=list)
    sys_path_base: list[str] | None = None


class ImportResolution:
    """Resolution result for one import statement."""

    def __init__(self, import_obj, item_index, built_in, path, what, message=None):
        self.importObj = import_obj
        self.itemIndex = item_index
        self.path = path
        self.what = what
        self.builtIn = built_in
        self.errMessage = message

    def isResolved(self) -> bool:
        return self.path is not None or self.builtIn

    def getVisibleName(self) -> str:
        name = self.importObj.name
        if self.itemIndex is not None:
            name += "." + self.importObj.what[self.itemIndex].name
        return name


def get_imports_list(file_content: str) -> list[object]:
    """Return brief-parser Import objects from source text."""
    info = getBriefModuleInfoFromMemory(file_content)
    return info.imports


def get_imports_in_line(file_content: str, line_number: int) -> tuple[list[str], list[str]]:
    """Return module names and imported object names on a given line."""
    imports: list[str] = []
    imports_what: list[str] = []
    info = getBriefModuleInfoFromMemory(str(file_content))
    for import_obj in info.imports:
        if import_obj.line == line_number:
            if import_obj.name not in imports:
                imports.append(import_obj.name)
            for what_obj in import_obj.what:
                if what_obj.name not in imports_what:
                    imports_what.append(what_obj.name)
    return imports, imports_what


def is_python_file(path: str) -> bool:
    return path.endswith(".py") and os.path.isfile(path)


def _scan_dir(prefix: str, path: str) -> list[str]:
    result: list[str] = []
    for item in os.listdir(path):
        if item in (".svn", ".cvs", ".git", ".hg"):
            continue
        if os.path.isdir(path + item):
            result.extend(_scan_dir(prefix + item + ".", path + item + sep))
            continue
        if not is_python_file(path + item):
            continue
        if item.startswith("__init__."):
            if prefix:
                result.append(prefix[:-1])
            continue
        name_parts = item.split(".")
        result.append(prefix + name_parts[0])
    return result


def build_dir_modules(path: str) -> list[str]:
    """Build module names as they may appear in import statements."""
    abspath = os.path.abspath(path)
    if not os.path.exists(abspath):
        raise FileNotFoundError(f"Cannot build list of modules for missing dir ({path})")
    if not os.path.isdir(abspath):
        raise NotADirectoryError(f"Cannot build list of modules. The path {path} is not a directory.")
    if not abspath.endswith(sep):
        abspath += sep
    return _scan_dir("", abspath)


def is_import_module(info: object, name: str) -> list[str]:
    matches: list[str] = []
    for item in info.imports:
        if item.what:
            continue
        if item.alias == "":
            if item.name == name and name not in matches:
                matches.append(name)
        elif item.alias == name and item.name not in matches:
            matches.append(item.name)
    return matches


def is_imported_object(info: object, name: str) -> list[list[str]]:
    matches: list[list[str]] = []
    for item in info.imports:
        if not item.what:
            continue
        for what_item in item.what:
            if what_item.alias == "":
                if what_item.name == name and name not in matches:
                    matches.append([item.name, name])
            elif what_item.alias == name and what_item.name not in matches:
                matches.append([item.name, what_item.name])
    return matches


def _sys_path_base(context: ImportContext) -> list[str]:
    if context.sys_path_base and len(context.sys_path_base) > 0:
        return list(context.sys_path_base)
    return list(sys.path)


def _resolve_import(
    import_obj,
    base_and_project_paths: list[str],
    result: list[ImportResolution],
    context: ImportContext,
) -> None:
    if import_obj.name in sys.builtin_module_names:
        result.append(ImportResolution(import_obj, None, True, None, None))
        return

    old_sys_path = sys.path
    sys.path = _sys_path_base(context) + base_and_project_paths
    try:
        spec = importlib.util.find_spec(import_obj.name)
        if spec and spec.has_location:
            result.append(ImportResolution(import_obj, None, False, spec.origin, None))
            return
    except Exception:
        pass
    finally:
        sys.path = old_sys_path

    result.append(
        ImportResolution(
            import_obj,
            None,
            False,
            None,
            None,
            f"Could not resolve 'import {import_obj.name}' at line {import_obj.line}",
        )
    )


def _resolve_from(import_obj, import_name: str, result: list[ImportResolution]) -> None:
    if import_obj.name in sys.builtin_module_names:
        result.append(
            ImportResolution(import_obj, None, True, None, [what.name for what in import_obj.what])
        )
        return

    try:
        spec = importlib.util.find_spec(import_name)
        if spec and spec.has_location:
            result.append(
                ImportResolution(
                    import_obj,
                    None,
                    False,
                    spec.origin,
                    [what.name for what in import_obj.what],
                )
            )
            return

        if spec and spec.loader is not None:
            result.append(
                ImportResolution(
                    import_obj,
                    None,
                    False,
                    None,
                    None,
                    f"Could not resolve 'from {import_obj.name} import ...' at line {import_obj.line}",
                )
            )
            return

        if spec and spec.submodule_search_locations:
            for index, what in enumerate(import_obj.what):
                imp_name = import_name + "." + what.name
                found = False
                try:
                    sub_spec = importlib.util.find_spec(imp_name)
                    if sub_spec and sub_spec.has_location:
                        result.append(ImportResolution(import_obj, index, False, sub_spec.origin, None))
                        found = True
                except Exception:
                    pass
                if not found:
                    result.append(
                        ImportResolution(
                            import_obj,
                            index,
                            False,
                            None,
                            None,
                            f"Could not resolve 'from {import_obj.name} import {what.name}' "
                            f"at line {import_obj.line}",
                        )
                    )
            return
    except Exception:
        pass

    result.append(
        ImportResolution(
            import_obj,
            None,
            False,
            None,
            None,
            f"Could not resolve 'from {import_obj.name} import ...' at line {import_obj.line}",
        )
    )


def _resolve_from_import(
    import_obj,
    base_path: str | None,
    base_and_project_paths: list[str],
    result: list[ImportResolution],
    context: ImportContext,
) -> None:
    old_sys_path = sys.path
    sys.path = _sys_path_base(context) + base_and_project_paths
    _resolve_from(import_obj, import_obj.name, result)
    sys.path = old_sys_path


def _resolve_relative_import(
    import_obj,
    base_path: str | None,
    result: list[ImportResolution],
) -> None:
    if base_path is None:
        result.append(
            ImportResolution(
                import_obj,
                None,
                False,
                None,
                None,
                f"Could not resolve 'from {import_obj.name} import ...' at line {import_obj.line} "
                "because the editing buffer has not been saved yet",
            )
        )
        return

    path = base_path
    current = import_obj.name[1:]
    error = False
    while current.startswith("."):
        if not path:
            error = True
            break
        current = current[1:]
        path = dirname(path)
    if error:
        result.append(
            ImportResolution(
                import_obj,
                None,
                False,
                None,
                None,
                f"Could not resolve 'from {import_obj.name} import ...' at line {import_obj.line}",
            )
        )
        return

    if not path:
        path = sep

    old_sys_path = sys.path
    sys.path = [path]
    _resolve_from(import_obj, current, result)
    sys.path = old_sys_path


def get_import_resolutions(
    context: ImportContext,
    file_name: str | None,
    imports: list[object],
) -> list[ImportResolution]:
    """Resolve import objects using the provided search context."""
    result: list[ImportResolution] = []
    orig_importer_cache_keys = set(sys.path_importer_cache.keys())
    orig_sys_modules_keys = set(sys.modules.keys())

    if file_name:
        base_path = dirname(file_name)
        base_and_project_paths = [base_path]
    else:
        base_path = None
        base_and_project_paths = []

    for path in context.search_paths:
        if path and path not in base_and_project_paths:
            base_and_project_paths.append(path)

    for import_obj in imports:
        if not import_obj.what:
            _resolve_import(import_obj, base_and_project_paths, result, context)
        elif not import_obj.name.startswith("."):
            _resolve_from_import(import_obj, base_path, base_and_project_paths, result, context)
        else:
            _resolve_relative_import(import_obj, base_path, result)

    importlib.invalidate_caches()
    for key in set(sys.path_importer_cache.keys()) - orig_importer_cache_keys:
        del sys.path_importer_cache[key]
    for key in set(sys.modules.keys()) - orig_sys_modules_keys:
        del sys.modules[key]
    return result


def resolve_imports(
    context: ImportContext,
    file_name: str | None,
    imports: list[object],
) -> tuple[list[tuple[str, str | None, list[str]]], list[str]]:
    """Legacy triple format: (name, path, what), errors."""
    resolved: list[tuple[str, str | None, list[str]]] = []
    errors: list[str] = []
    for resolution in get_import_resolutions(context, file_name, imports):
        if resolution.isResolved():
            path = "built-in" if resolution.builtIn else resolution.path
            what = resolution.what if resolution.what is not None else []
            resolved.append((resolution.getVisibleName(), path, what))
        else:
            errors.append(resolution.errMessage)
    return resolved, errors


def build_import_context(project: Project, file_path: str | None = None) -> ImportContext:
    """Build import resolution context from a headless project."""
    project.require_open()
    search_paths = project.build_import_search_paths(file_path)
    return ImportContext(file_name=file_path, search_paths=search_paths)


def resolve_imports_for_file(project: Project, file_path: str) -> GraphIR:
    """Resolve imports for one file and return Graph IR edges."""
    project.require_open()
    abs_path = realpath(file_path)
    context = build_import_context(project, abs_path)
    info = project.cache.get(abs_path)
    graph = GraphIR(meta={"kind": "resolved_imports", "file": abs_path})
    source_id = f"file:{basename(abs_path)}"
    graph.add_node(
        GraphNode(
            id=source_id,
            type="file",
            name=basename(abs_path),
            file=abs_path,
            line_start=1,
            line_end=1,
        )
    )
    for resolution in get_import_resolutions(context, abs_path, info.imports):
        target_id = _resolution_node_id(resolution, graph)
        graph.add_edge(
            GraphEdge(
                from_id=source_id,
                to_id=target_id,
                type="imports",
                label=resolution.getVisibleName(),
            )
        )
    return graph


def _resolution_node_id(resolution: ImportResolution, graph: GraphIR) -> str:
    if resolution.builtIn:
        node_id = f"builtin:{resolution.importObj.name}"
        graph.add_node(
            GraphNode(
                id=node_id,
                type="builtin_module",
                name=resolution.importObj.name,
                file="",
                line_start=0,
                line_end=0,
            )
        )
        return node_id
    if resolution.path:
        node_id = f"module:{resolution.path}"
        graph.add_node(
            GraphNode(
                id=node_id,
                type="resolved_module",
                name=basename(resolution.path),
                file=resolution.path,
                line_start=0,
                line_end=0,
            )
        )
        return node_id
    node_id = f"unresolved:{resolution.getVisibleName()}:{resolution.importObj.line}"
    graph.add_node(
        GraphNode(
            id=node_id,
            type="unresolved_import",
            name=resolution.getVisibleName(),
            file="",
            line_start=resolution.importObj.line,
            line_end=resolution.importObj.line,
            extra={"error": resolution.errMessage or ""},
        )
    )
    return node_id


def _top_level_import_name(import_name: str) -> str | None:
    if not import_name or import_name.startswith("."):
        return None
    top = import_name.split(".", 1)[0]
    if not top or not top.isidentifier():
        return None
    return top


def get_unresolved_package_names(errors: list[str]) -> set[str]:
    names: set[str] = set()
    for err in errors:
        match = re.search(r"'import ([^']+)'", err)
        if match:
            top = _top_level_import_name(match.group(1))
            if top and top not in _STDLIB_MODULES:
                names.add(top)
            continue
        match = re.search(r"'from ([^']+) import", err)
        if match:
            top = _top_level_import_name(match.group(1))
            if top and top not in _STDLIB_MODULES:
                names.add(top)
    return names


def get_requirements_hint(project_dir: str, unresolved_packages: set[str]) -> str | None:
    packages = sorted(unresolved_packages)
    if not project_dir or not packages:
        return None
    req_path = os.path.join(project_dir, "requirements.txt")
    if os.path.isfile(req_path):
        return (
            "Unresolved imports (possibly missing dependencies): "
            + ", ".join(packages)
            + ". Consider: pip install -r requirements.txt"
        )
    return (
        "Unresolved imports (possibly missing dependencies): "
        + ", ".join(packages)
        + ". Consider: pip install "
        + " ".join(packages)
    )


def collect_unresolved_packages(project: Project, progress_callback=None) -> tuple[set[str], int]:
    """Scan project files and collect unresolved third-party package names."""
    project.require_open()
    all_errors: list[str] = []
    python_files = list(project.python_files)
    total = len(python_files)
    for idx, file_path in enumerate(python_files):
        if progress_callback:
            progress_callback(idx, total, "Scanning " + basename(file_path) + "...")
        try:
            info = project.cache.get(file_path)
            context = build_import_context(project, file_path)
            _, errors = resolve_imports(context, file_path, info.imports)
            all_errors.extend(errors)
        except Exception:
            pass
    return get_unresolved_package_names(all_errors), len(all_errors)


def classify_resolution(
    resolution: ImportResolution,
    source_file: str,
    project: Project | None,
    sys_path: list[str] | None = None,
) -> str:
    """Classify a resolution as system, project, other, or unresolved."""
    if not resolution.isResolved():
        return "unresolved"
    if resolution.builtIn:
        return "system"
    if resolution.path and project and project.is_project_path(resolution.path):
        return "project"
    if resolution.path and source_file:
        source_dir = dirname(realpath(source_file))
        if dirname(realpath(resolution.path)).startswith(source_dir):
            return "project"
    if resolution.path and sys_path:
        resolved_dir = dirname(realpath(resolution.path))
        for path in sys_path:
            if path and resolved_dir.startswith(path):
                return "system"
    if resolution.path:
        return "other"
    return "unresolved"


def collect_import_resolutions_classified(
    content: str,
    file_name: str | None,
    project: Project | None = None,
    sys_path: list[str] | None = None,
) -> dict[str, object]:
    """Classify import resolutions like codimension.diagram.depsdiagram."""
    dep_classes: dict[str, object] = {
        "system": [],
        "project": [],
        "other": [],
        "unresolved": [],
        "totalCount": 0,
        "errors": [],
    }
    try:
        imports = get_imports_list(content)
        context = build_import_context(project, file_name) if project and file_name else ImportContext(
            file_name=file_name,
            search_paths=[dirname(realpath(file_name))] if file_name else [],
        )
        if project is None and file_name:
            context.search_paths = [dirname(realpath(file_name))]
        for resolution in get_import_resolutions(context, file_name, imports):
            bucket = classify_resolution(resolution, file_name or "", project, sys_path)
            if bucket == "other":
                bucket = "unresolved"
            dep_classes[bucket].append(resolution)
            dep_classes["totalCount"] = int(dep_classes["totalCount"]) + 1
    except Exception as exc:
        dep_classes["errors"].append(str(exc))
    return dep_classes
