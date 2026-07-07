#!/usr/bin/env bash
# Bootstrap CAN-MCP dev environment: venv, editable installs, Cursor MCP, merge gate.
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"

log() { printf '[dev-setup] %s\n' "$*"; }

if [[ ! -d "$ROOT/.venv" ]]; then
  log "Creating virtual environment at $ROOT/.venv"
  python3 -m venv "$ROOT/.venv"
fi

# shellcheck disable=SC1091
source "$ROOT/.venv/bin/activate"

log "Installing dependencies"
pip install --upgrade pip -q
pip install -r "$ROOT/requirements-dev.txt" -q
pip install -e "$ROOT/codimension_core[analysis]" -e "$ROOT/codimension_mcp" -q

log "Configuring Cursor MCP"
"$ROOT/scripts/install-cursor-mcp.sh"

log "Running merge gate"
"$ROOT/scripts/test-analysis.sh"

log "Development environment ready"
