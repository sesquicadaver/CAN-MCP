#!/usr/bin/env bash
# Compile the VS Code extension (ROAD-6.4). Mirrors the CI vscode job.
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
VSCODE_DIR="$ROOT/codimension-vscode"

if [[ ! -f "$VSCODE_DIR/package.json" ]]; then
  echo "codimension-vscode/package.json not found" >&2
  exit 1
fi

cd "$VSCODE_DIR"
if [[ ! -d node_modules ]]; then
  npm ci
fi
npm run compile
echo "VS Code extension compile OK"
