# Changelog

All notable changes to CAN-MCP (headless Codimension stack) are documented here.

Format based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/).

## [1.0.0] - 2026-07-07

Production release on branch `reserv-1`. ROADMAP Phase 0–6 complete; merge gate green (153 tests).

### codimension-core 1.0.0

- Stable project-relative symbol IDs and path security policy
- Graph IR v2 default (`node.uri`, `edge.provenance`; legacy v1 via `CODIMENSION_GRAPH_IR=1`)
- Semantic call graph: import resolution, `self`/instance/alias/nested attribute calls, jedi refinement
- Import isolation (opt-in subprocess via `CODIMENSION_IMPORT_ISOLATION=subprocess`)
- Canonical import graph file nodes (`file:{rel_path}`) and brief-mode module map
- Analysis cache, impact analysis on canonical IDs, optional `[analysis]` deps

### codimension-mcp 1.0.0

- 23 MCP tools, 17 resources, 6 prompts (canonical symbol IDs in prompts v2)
- Workspace lock and `invalidate_file` cache API
- Catalog parity with VS Code generated URI list

### Repository / DX

- `./scripts/dev-setup.sh` one-shot bootstrap
- CI: analysis gate, VS Code compile job, anti-stub enforce (`ENFORCE=1`)
- Living specification and Analize-AI status tracker

[1.0.0]: https://github.com/sesquicadaver/CAN-MCP/compare/main...reserv-1
