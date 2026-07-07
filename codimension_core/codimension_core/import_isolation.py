# -*- coding: utf-8 -*-
"""Subprocess-backed import resolution (opt-in via environment)."""

from __future__ import annotations

import json
import os
import subprocess
import sys
from dataclasses import dataclass
from typing import Any, cast

from .parser_types import BriefImport

_ISOLATION_ENV = "CODIMENSION_IMPORT_ISOLATION"
_INPROCESS = "inprocess"
_SUBPROCESS = "subprocess"


def import_isolation_mode() -> str:
    """Return configured import isolation mode."""
    return os.environ.get(_ISOLATION_ENV, _INPROCESS).strip().lower()


def use_subprocess_isolation() -> bool:
    """True when import resolution should run in a child interpreter."""
    return import_isolation_mode() == _SUBPROCESS


@dataclass
class _BriefWhatShim:
    name: str
    alias: str


@dataclass
class _BriefImportShim:
    name: str
    line: int
    alias: str
    what: list[_BriefWhatShim]


def brief_import_to_dict(import_obj: BriefImport) -> dict[str, Any]:
    """Serialize a brief import for the isolation worker."""
    return {
        "name": import_obj.name,
        "line": import_obj.line,
        "alias": import_obj.alias,
        "what": [{"name": item.name, "alias": item.alias} for item in import_obj.what],
    }


def brief_import_from_dict(payload: dict[str, Any]) -> _BriefImportShim:
    """Deserialize a brief import payload from the worker."""
    return _BriefImportShim(
        name=str(payload["name"]),
        line=int(payload["line"]),
        alias=str(payload.get("alias", "")),
        what=[_BriefWhatShim(name=str(item["name"]), alias=str(item.get("alias", ""))) for item in payload["what"]],
    )


def resolution_to_dict(resolution: Any) -> dict[str, Any]:
    """Serialize one ImportResolution for JSON transport."""
    return {
        "import_name": resolution.importObj.name,
        "import_line": resolution.importObj.line,
        "itemIndex": resolution.itemIndex,
        "path": resolution.path,
        "what": resolution.what,
        "builtIn": resolution.builtIn,
        "errMessage": resolution.errMessage,
    }


def resolution_from_dict(import_obj: BriefImport, payload: dict[str, Any]) -> Any:
    """Rebuild ImportResolution using the original import object."""
    from .imports import ImportResolution

    return ImportResolution(
        import_obj,
        payload.get("itemIndex"),
        bool(payload.get("builtIn")),
        payload.get("path"),
        payload.get("what"),
        payload.get("errMessage"),
    )


def resolve_imports_subprocess(
    context: Any,
    file_name: str | None,
    imports: list[BriefImport],
) -> list[Any]:
    """Run in-process resolution inside a child interpreter."""
    python_executable = getattr(context, "python_executable", None) or sys.executable
    worker_payload = {
        "context": {
            "file_name": file_name,
            "search_paths": list(context.search_paths),
            "sys_path_base": list(context.sys_path_base) if context.sys_path_base else None,
        },
        "imports": [brief_import_to_dict(import_obj) for import_obj in imports],
    }
    env = os.environ.copy()
    env[_ISOLATION_ENV] = _INPROCESS
    completed = subprocess.run(
        [python_executable, "-m", "codimension_core.import_isolation_worker"],
        input=json.dumps(worker_payload),
        capture_output=True,
        text=True,
        env=env,
        check=False,
    )
    if completed.returncode != 0:
        message = completed.stderr.strip() or completed.stdout.strip() or "unknown worker error"
        raise RuntimeError(f"import isolation worker failed: {message}")
    response = json.loads(completed.stdout)
    resolutions_payload = cast(list[dict[str, Any]], response["resolutions"])
    return _attach_resolutions(imports, resolutions_payload)


def _attach_resolutions(imports: list[BriefImport], payloads: list[dict[str, Any]]) -> list[Any]:
    if len(payloads) == len(imports):
        return [resolution_from_dict(import_obj, payload) for import_obj, payload in zip(imports, payloads)]

    grouped: dict[tuple[str, int], list[dict[str, Any]]] = {}
    for payload in payloads:
        key = (str(payload["import_name"]), int(payload["import_line"]))
        grouped.setdefault(key, []).append(payload)

    results: list[Any] = []
    for import_obj in imports:
        key = (import_obj.name, import_obj.line)
        for payload in grouped.get(key, []):
            results.append(resolution_from_dict(import_obj, payload))
    return results
