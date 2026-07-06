#!/usr/bin/env bash
# Verify MCP catalog integrity (parity with VS Code URI list and prompts).
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"

python -m pytest tests/test_codimension_mcp_catalog.py -q
echo "MCP catalog OK"
