#!/usr/bin/env bash
# Install Codimension MCP config for Cursor from the repository example.
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
TARGET="$ROOT/.cursor/mcp.json"
mkdir -p "$ROOT/.cursor"
if [[ -f "$TARGET" ]]; then
  echo "Already exists: $TARGET (not overwritten)"
  exit 0
fi
cp "$ROOT/.cursor/mcp.json.example" "$TARGET"
echo "Created $TARGET — restart Cursor or reload MCP servers."
