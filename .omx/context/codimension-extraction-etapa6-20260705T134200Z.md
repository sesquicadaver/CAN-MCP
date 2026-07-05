# Context: Codimension extraction etapa 6

**Task:** CODIMENSION-EVO etapa 6–8 slice — enhanced impact analysis + MCP resources/prompts.

**Outcome:**
- `callgraph.impact_analysis` — transitive caller closure + import dependents for symbols
- MCP resources: workspace status, cached import/call graphs (URI `codimension://...`)
- MCP prompts: refactor workflow, dead-code review
- Tests, docs, core 0.6.0 / mcp 0.2.0, commit+push

**Constraints:** Headless only; no PyQt; Carantine unchanged unless new archive needed.

**Touchpoints:** `callgraph.py`, `codimension_mcp/resources.py`, `codimension_mcp/prompts.py`, `server.py`, tests, docs.
