#!/usr/bin/env bash
# Run the CAN-MCP analysis merge gate locally (matches ci.yml analysis job).
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"

python -m pip install --upgrade pip
pip install pytest ruff mypy pyflakes radon jedi vulture mistune pygments
pip install -e "./codimension_core[analysis]" -e ./codimension_mcp

ruff check codimension_core codimension_mcp
( cd codimension_core && mypy codimension_core )

python -m pytest tests/ -q
./scripts/verify-mcp-catalog.sh

echo "Analysis gate OK"
