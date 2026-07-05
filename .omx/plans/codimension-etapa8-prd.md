# PRD: Etapa 8 — incremental analysis cache

## Acceptance

1. Second `build_import_graph` / `build_call_graph` hit cache (same revision).
2. `invalidate_file` clears module + derived graph caches.
3. `get_control_flow` caches per function until file fingerprint changes.
4. `get_cache_stats` returns hits/misses/revision.
5. Unit + MCP tests pass.
