#!/usr/bin/env bash
# Run the CAN-MCP analysis merge gate locally (matches ci.yml analysis job).
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"

python -m pip install --upgrade pip
pip install pytest ruff mypy pyflakes radon jedi vulture
pip install -e ./codimension_core -e ./codimension_mcp

ruff check codimension_core codimension_mcp
( cd codimension_core && mypy codimension_core )

python -m pytest \
  tests/test_codimension_core*.py \
  tests/test_codimension_mcp.py \
  tests/test_brief_ast.py \
  tests/test_flow_ast.py \
  tests/test_importutils.py \
  tests/test_gitstatusparser.py \
  tests/test_todoscanner.py \
  tests/test_binfiles.py \
  tests/test_occurrencesprovider.py \
  tests/test_lint_drivers.py \
  tests/test_greenlet_trace.py \
  tests/test_astview.py \
  -q

echo "Analysis gate OK"
