# Etapa 14 — Content-hash cache + granular file invalidation

**Task:** Replace mtime-only revision with content SHA256; keep per-function CFG invalidation scoped to changed files.

**Desired outcome:** Cache hits when mtime changes but content unchanged; misses on content change; `file_hashes` stats in get_cache_stats.

**Touchpoints:** `analysis_cache.py`, `cache.py`, tests, versions, living-spec.
