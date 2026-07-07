# CAN-MCP AI Analysis

> **Languages:** [English](../en/Analize-AI.md) · [Українська](../uk/Analize-AI.md)

CAN-MCP assessment: **solid architecture, actively approaching production MVP**.

| Criterion | Score |
| --------- | ----: |
| Separation `core` / `mcp` / `vscode` | 9/10 |
| MCP tools/resources/prompts model | 8/10 |
| Graph IR | 7/10 |
| Project model / workspace handling | 7/10 |
| Static analysis depth | 6/10 |
| Cache / incremental design | 7/10 |
| Production readiness | 7/10 |

Task source: [doc/en/ROADMAP.md](ROADMAP.md). Living spec: [doc/en/plugins/living-specification.md](plugins/living-specification.md).

## Status tracker (Analize-AI → ROAD)

| Gap | ROAD | Status | Note |
| --- | ---- | ------ | ---- |
| Primitive Graph IR | ROAD-2.1–2.6 | **done** | Graph IR v2 default; legacy v1 via `CODIMENSION_GRAPH_IR=1` |
| Unstable symbol IDs | ROAD-1.1–1.3, 1.5–1.6 | **done** | Project-relative IDs + legacy aliases |
| Shallow call graph | ROAD-3.1–3.7 | **done** | Instance/alias/nested attribute resolution + semantic fixtures |
| Import `sys.path` mutation | ROAD-4.1–4.4 | **done** | `ImportResolver`, subprocess opt-in, concurrent tests |
| Incomplete path security | ROAD-1.4, 1.7 | **done** | `resolve_project_path` in all MCP tools |
| Dev maturity / optional deps | ROAD-5.1–5.3, 5.6 | **done** | `[analysis]` extra, capabilities matrix, mypy strict + stubs |
| MCP lifecycle / cache API | ROAD-5.4–5.5 | **done** | Workspace lock, `invalidate_file` tool |
| Living spec drift | ROAD-1.8, 6.1 | **done** | This tracker + living specification |
| Prompt canonical IDs | ROAD-6.2 | **done** | Prompts v2 (`pkg/mod.py:function:name`) |
| Fresh-clone DX | ROAD-6.3 | **done** | `./scripts/dev-setup.sh` |
| VS Code extension CI | ROAD-6.4 | **done** | CI job `vscode`: npm compile + catalog parity |
| Anti-stub grep | ROAD-6.5 | **done** | `scripts/check-anti-stub.sh` (`ENFORCE=1` in CI) |

## Strengths

1. **Correct decomposition.** Repository split into `codimension_core`, `codimension_mcp`, `codimension-vscode` — analyzer, MCP transport, and UI separated properly.

2. **Thin MCP layer.** `server.py` registers tools via `FastMCP`, holds `WorkspaceState`, delegates to `tools.py` / `codimension_core`.

3. **Machine-readable catalog.** `catalog.py` is source of truth for tools/resources/prompts; parity with VS Code URI list.

4. **Versioned Graph IR.** Graph IR v2 default (`node.uri`, `edge.provenance`); legacy v1 via `CODIMENSION_GRAPH_IR=1`.

## Remaining gaps

1. **Call / import graph:** main semantic paths closed; further work — jedi refinement edge cases.

2. _(resolved)_ brief import stem collision — module map in brief mode.

## Verdict

The project is **mature as an agent-facing analysis MVP**. Architectural frame `core → MCP → clients` is implemented; roadmap Phase 0–5 largely complete.

Updated score: **8/10 architecture, 7/10 analyzer, 7/10 production tool**.

**1.0.0 released** (2026-07-07): roadmap Phase 0–6 complete; merge gate 153 tests.
