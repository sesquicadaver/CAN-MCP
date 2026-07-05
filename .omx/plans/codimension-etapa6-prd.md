# PRD: Etapa 6 — impact analysis + MCP resources/prompts

## Acceptance criteria

1. `impact_analysis(target)` returns transitive callers (BFS) for symbol targets and import dependents for file targets.
2. MCP exposes `@mcp.resource` URIs:
   - `codimension://workspace/status`
   - `codimension://graph/import`
   - `codimension://graph/call`
3. MCP exposes `@mcp.prompt` templates:
   - `refactor_symbol(symbol)`
   - `review_dead_code`
4. Unit tests in `tests/test_codimension_core_impact.py` and MCP resource smoke test.
5. Docs updated; versions bumped.

## Test spec

- Symbol impact: A→B→C chain; impact on C includes A and B.
- File impact: importers listed when target is `mod.py`.
- MCP resource returns JSON when project open; error JSON when not.
