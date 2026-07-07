#!/usr/bin/env bash
# Anti-stub grep for codimension_core (ROAD-6.5).
# Default: warning only. Set ENFORCE=1 to fail the gate.
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
TARGET="$ROOT/codimension_core/codimension_core"

if [[ ! -d "$TARGET" ]]; then
  echo "Target not found: $TARGET" >&2
  exit 1
fi

ENFORCE="${ENFORCE:-0}"
FOUND=0

filter_without_marker() {
  local marker="$1"
  awk -v marker="$marker" 'index($0, marker) == 0 { print }'
}

report_matches() {
  local label="$1"
  local pattern="$2"
  local marker="${3:-TEMP-STUB}"
  local matches
  matches="$(rg -n --glob '*.py' "$pattern" "$TARGET" 2>/dev/null | filter_without_marker "$marker" || true)"
  if [[ -n "$matches" ]]; then
    FOUND=1
    echo "anti-stub [$label]:"
    echo "$matches"
  fi
}

report_matches "pass-todo" 'pass\s+#\s*TODO'
report_matches "return-none-todo" 'return\s+None\s+#\s*TODO'
report_matches "mock-stub" '\bMock\s*\(' '___no_skip___'

if [[ "$FOUND" -eq 0 ]]; then
  echo "Anti-stub check OK (no suspicious patterns)"
  exit 0
fi

if [[ "$ENFORCE" == "1" ]]; then
  echo "Anti-stub ENFORCE=1: failing gate" >&2
  exit 1
fi

echo "Anti-stub warning only (set ENFORCE=1 to fail)" >&2
exit 0
