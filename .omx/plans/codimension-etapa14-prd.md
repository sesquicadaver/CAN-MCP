# PRD: Etapa 14 — Content-hash incremental cache

## US-001: Content hash fingerprints
- `FileFingerprint.content_hash` (sha256 truncated 16 hex)
- `compute_project_revision` uses content hashes with mtime/size fast-path cache

## US-002: Module cache content hash
- `ModuleInfoCache` validates via content hash after mtime/size fast path

## US-003: Granular invalidate_file
- Drop file fingerprint cache entry + module cache + project graphs + CFG entries for that file only

## Tests
- mtime touch without content → import graph cache hit
- content change → cache miss
- invalidate_file removes only matching CFG entries

## Verification
`python -m pytest tests/test_codimension_core_cache.py -q`
