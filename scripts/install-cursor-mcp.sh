#!/usr/bin/env bash
# Install Codimension MCP for Cursor: venv packages + local .cursor/mcp.json
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
TARGET="$ROOT/.cursor/mcp.json"
VENV="$ROOT/.venv"
MCP_BIN="$VENV/bin/codimension-mcp"

log() { printf '[install-cursor-mcp] %s\n' "$*"; }

if [[ ! -d "$VENV" ]]; then
  log "Creating venv at $VENV"
  python3 -m venv "$VENV"
fi

# shellcheck disable=SC1091
source "$VENV/bin/activate"
pip install --upgrade pip -q
pip install -e "$ROOT/codimension_core" -e "$ROOT/codimension_mcp" -q
pip install pyflakes radon jedi vulture -q

# Legacy root editable install shadows codimension_core via namespace — breaks MCP CLI.
if pip show codimension >/dev/null 2>&1; then
  log "Removing legacy codimension editable (conflicts with codimension-mcp imports)"
  pip uninstall -y codimension >/dev/null
fi

if ! "$MCP_BIN" --help >/dev/null 2>&1; then
  log "FAIL: codimension-mcp not runnable at $MCP_BIN"
  exit 1
fi

mkdir -p "$ROOT/.cursor"
cat >"$TARGET" <<EOF
{
  "mcpServers": {
    "codimension": {
      "command": "$MCP_BIN",
      "args": ["--workspace", "\${workspaceFolder}"],
      "env": {
        "VIRTUAL_ENV": "$VENV",
        "PATH": "$VENV/bin:/usr/local/bin:/usr/bin:/bin"
      }
    }
  }
}
EOF

log "Created $TARGET"
log "Reload MCP in Cursor: Settings → MCP → codimension → Reload (or restart Cursor)"
log "Smoke test in Agent chat: list_mcp_catalog via codimension MCP"
