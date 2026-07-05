# PRD: Etapa 7 — diagram WebView export

## Acceptance

1. `graph_to_mermaid(graph)` and `graph_to_html(graph, title)` in core.
2. `render_diagram(state, kind, target?)` produces HTML under `.codimension/diagrams/`.
3. MCP tool + resource `codimension://diagram/import|call|control_flow|impact`.
4. Unit tests for mermaid/HTML output; MCP smoke test.

## Kinds

| kind | core API | target |
|------|----------|--------|
| import | build_import_graph | — |
| call | build_call_graph | symbol optional |
| control_flow | get_control_flow | function_id required |
| impact | impact_analysis | path/symbol required |
