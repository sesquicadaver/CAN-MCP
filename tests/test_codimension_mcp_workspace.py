# -*- coding: utf-8 -*-
"""MCP workspace lock and invalidate_file tool tests."""

from __future__ import annotations

import json
from concurrent.futures import ThreadPoolExecutor

from codimension_mcp.schemas import WorkspaceState
from codimension_mcp.tools import (
    analyze_project,
    get_symbols_tool,
    invalidate_file_tool,
    open_project,
)


def test_concurrent_open_project_no_corrupt_state(tmp_path):
    project_dirs = []
    for index in range(5):
        project_dir = tmp_path / f"proj{index}"
        project_dir.mkdir()
        (project_dir / "main.py").write_text(f"x = {index}\n", encoding="utf-8")
        project_dirs.append(project_dir)

    state = WorkspaceState()

    def open_one(path: str) -> dict[str, object]:
        return json.loads(open_project(state, path))

    with ThreadPoolExecutor(max_workers=5) as pool:
        results = list(pool.map(open_one, [str(path) for path in project_dirs]))

    assert state.project is not None
    assert state.workspace in {str(path) for path in project_dirs}
    assert all(result["status"] == "ok" for result in results)


def test_invalidate_file_refreshes_symbols(tmp_path):
    project_dir = tmp_path / "proj"
    project_dir.mkdir()
    main = project_dir / "main.py"
    main.write_text("def old_fn():\n    pass\n", encoding="utf-8")

    state = WorkspaceState()
    open_project(state, str(project_dir))
    analyze_project(state)

    before = json.loads(get_symbols_tool(state, "main.py"))
    before_names = {node["name"] for node in before["nodes"]}
    assert "old_fn" in before_names

    main.write_text("def new_fn():\n    pass\n", encoding="utf-8")
    payload = json.loads(invalidate_file_tool(state, "main.py"))
    assert payload["status"] == "ok"

    after = json.loads(get_symbols_tool(state, "main.py"))
    after_names = {node["name"] for node in after["nodes"]}
    assert "new_fn" in after_names
    assert "old_fn" not in after_names
