#!/usr/bin/env bash
# Remove local UI and Python build artifacts (safe; does not touch tracked sources).
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"

find . -type d -name __pycache__ -prune -exec rm -rf {} +
rm -rf .pytest_cache codimension-vscode/node_modules codimension-vscode/out .codimension
echo "UI/build artifacts removed under $ROOT"
