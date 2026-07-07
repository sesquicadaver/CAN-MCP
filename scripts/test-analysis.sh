#!/usr/bin/env bash
# Run the CAN-MCP analysis merge gate locally (matches ci.yml analysis job).
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"

if [[ -x "$ROOT/.venv/bin/python" ]]; then
  PYTHON="$ROOT/.venv/bin/python"
  PIP="$ROOT/.venv/bin/pip"
else
  PYTHON=python
  PIP=pip
fi

"$PYTHON" -m pip install --upgrade pip
"$PIP" install pytest ruff mypy types-pyflakes pyflakes radon jedi vulture mistune pygments
"$PIP" install -e "./codimension_core[analysis]" -e ./codimension_mcp

ruff check codimension_core codimension_mcp
( cd codimension_core && "$PYTHON" -m mypy codimension_core )

"$PYTHON" -m pytest tests/ -q
"$PYTHON" scripts/generate_mcp_catalog_artifacts.py --check
"$PYTHON" -m pytest tests/test_codimension_mcp_catalog.py -q
ENFORCE=1 ./scripts/check-anti-stub.sh

echo "Analysis gate OK"
