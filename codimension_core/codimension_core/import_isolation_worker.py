# -*- coding: utf-8 -*-
"""Child-process entry point for subprocess import isolation."""

from __future__ import annotations

import json
import sys
from typing import cast

from .import_isolation import brief_import_from_dict, resolution_to_dict
from .imports import ImportContext, resolve_imports_inprocess
from .parser_types import BriefImport


def main() -> int:
    payload = json.load(sys.stdin)
    context_payload = payload["context"]
    context = ImportContext(
        file_name=context_payload.get("file_name"),
        search_paths=list(context_payload.get("search_paths", [])),
        sys_path_base=context_payload.get("sys_path_base"),
    )
    imports = cast(list[BriefImport], [brief_import_from_dict(item) for item in payload["imports"]])
    resolutions = resolve_imports_inprocess(context, context.file_name, imports)
    json.dump({"resolutions": [resolution_to_dict(resolution) for resolution in resolutions]}, sys.stdout)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
