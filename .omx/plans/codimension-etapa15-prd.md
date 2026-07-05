# PRD: Etapa 15 — codimension_core mypy

## US-001: parser_types Protocols
- BriefModuleInfo, BriefImport, BriefNamed, BriefDocstring

## US-002: Fix 6 modules with mypy errors
- imports, import_diagram, dependency_graph, analyzer, cfg, analysis_cache

## US-003: CI analysis job runs mypy
- `cd codimension_core && mypy codimension_core`

## Verification
- mypy codimension_core — 0 errors
- pytest tests/test_codimension_core*.py tests/test_codimension_mcp.py
