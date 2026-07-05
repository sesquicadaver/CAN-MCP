# PRD: Etapa 17 — brief_ast + requirements

## US-001: codimension_core.brief_ast
- Full vendored parser; used by cache, symbols, imports

## US-002: IDE thin wrappers
- parsers/brief_ast.py re-export
- importutils.generateRequirementsFromProject → collect_unresolved_packages

## US-003: Tests
- test_codimension_core_brief_ast.py
- collect_unresolved_packages test in imports tests

## Verification
- pytest tests/test_codimension_core*.py
- mypy codimension_core
