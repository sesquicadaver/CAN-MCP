# Журнал змін

> **Languages:** [English](CHANGELOG.md) · [Українська](CHANGELOG.uk.md)

Усі помітні зміни CAN-MCP (headless Codimension stack).

Формат на основі [Keep a Changelog](https://keepachangelog.com/uk/1.1.0/).

## [1.0.0] - 2026-07-07

Реліз 1.0 на гілці `reserv-1`. ROADMAP Phase 0–6 завершено; прогін `./scripts/test-analysis.sh` 153 тести проходять.

### codimension-core 1.0.0

- Стабільні project-relative symbol IDs і path security policy
- Graph IR v2 за замовчуванням (`node.uri`, `edge.provenance`; legacy v1 через `CODIMENSION_GRAPH_IR=1`)
- Semantic call graph: import resolution, `self`/instance/alias/nested attribute calls, jedi refinement
- Import isolation (subprocess за env-прапорцем через `CODIMENSION_IMPORT_ISOLATION=subprocess`)
- Canonical import graph file nodes (`file:{rel_path}`) і brief-mode module map
- Analysis cache, impact analysis на canonical IDs, optional `[analysis]` deps

### codimension-mcp 1.0.0

- 23 MCP tools, 17 resources, 6 prompts (canonical symbol IDs у prompts v2)
- Workspace lock і `invalidate_file` cache API
- Catalog узгодженість з VS Code generated URI list

### Репозиторій / DX

- `./scripts/dev-setup.sh` один скрипт `./scripts/dev-setup.sh`
- CI: analysis gate, VS Code compile job, anti-stub enforce (`ENFORCE=1`)
- Жива специфікація і Analize-AI status tracker

[1.0.0]: https://github.com/sesquicadaver/CAN-MCP/compare/main...reserv-1
