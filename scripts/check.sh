#!/bin/bash
# Run ruff, mypy, and pip-audit checks
set -e
cd "$(dirname "$0")/.."

echo "=== Ruff ==="
ruff check codimension
echo "Ruff OK"

echo ""
echo "=== Mypy (core modules) ==="
# Exclude flowui/everything.py - demo file with intentional patterns
python -m mypy codimension/parsers/flow_ast.py codimension/parsers/brief_ast.py \
  codimension/debugger/client/bp_wp_cdm_dbg.py codimension/editor/flakesmargin.py
echo "Mypy OK"

echo ""
echo "=== pip-audit ==="
python -m pip install --upgrade pip >/dev/null
pip install pip-audit >/dev/null
pip-audit -r requirements.txt
echo "pip-audit OK"
