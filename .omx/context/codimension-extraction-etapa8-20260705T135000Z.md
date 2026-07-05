# Context: Codimension extraction etapa 8

**Task:** CODIMENSION-EVO §5 — інкрементальний кеш (file fingerprint, graph cache, CFG cache).

**Outcome:**
- `ProjectAnalysisCache` — import/call graph + per-function CFG
- `ModuleInfoCache` stats (hits/misses)
- `Project.get_cache_stats()`, `rescan()`, cascade `invalidate_file`
- MCP `get_cache_stats` + resource `codimension://cache/stats`
- Tests, docs, core 0.8.0 / mcp 0.4.0

**Constraints:** Headless; без змін PyQt; мінімальний diff у graph builders.
