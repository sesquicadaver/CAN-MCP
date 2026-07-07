# ROADMAP: CAN-MCP — gap fixes and improvements

**Languages:** [English](../en/ROADMAP.md) | [Українська](../uk/ROADMAP.md)

**Version:** 1.0  
**Date:** 2026-07-06  
**Baseline assessment:** [Analize-AI.md](Analize-AI.md)  
**Living spec:** [plugins/living-specification.md](plugins/living-specification.md)  
**Architecture map:** [CODIMENSION-CORE-MAP.md](CODIMENSION-CORE-MAP.md)

---

## Principles (do not break the project)

1. **Test-first** — every task starts with a test (red → green), then code.
2. **Merge gate** — after each task: `./scripts/test-analysis.sh` (in venv).
3. **Backward compatibility** — legacy ID/URI work via alias layer for at least one release.
4. **One PR = one atomic task** — easy revert.
5. **Core vs MCP** — business logic only in `codimension_core`; MCP is transport and policy.

---

## Phases (overview)

| Phase | Focus | Tasks | Risk |
| ----- | ----- | ----- | ---- |
| 0 | Safety net (regression tests) | 6 | Low |
| 1 | P0: Symbol IDs + path security | 8 | Medium |
| 2 | Graph IR v2 (contract) | 6 | Medium |
| 3 | Semantic resolution | 7 | High |
| 4 | Import isolation | 4 | High |
| 5 | Production hardening | 6 | Low |
| 6 | DX, docs, CI | 5 | Low |

**Suggested order:** 0 → 1 → 2 → 3 (in parallel with 5.1–5.3) → 4 → 5 → 6.

---

## Phase 0 — Safety net (regression tests)

> Goal: lock current behavior before changes; no production code changes.

### ROAD-0.1 — Symbol ID collision test

| Field | Value |
| ----- | ----- |
| **Test file** | `tests/test_codimension_core_symbol_ids.py` (new) |
| **Steps** | 1. Create `pkg/a/utils.py` and `pkg/b/utils.py` with the same function `foo`. 2. Call `get_symbols(project)`. 3. Assert: two **different** node.id values (test **fails** on current code — expected red). |
| **Acceptance** | Test exists, marked `@pytest.mark.xfail(reason="ROAD-1.1")` until fixed. |
| **Gate** | `pytest tests/test_codimension_core_symbol_ids.py` |

### ROAD-0.2 — Path traversal test in MCP tools

| Field | Value |
| ----- | ----- |
| **Test file** | `tests/test_codimension_mcp_path_security.py` (new) |
| **Steps** | 1. `open_project(tmp_path/proj)`. 2. Call `analyze_file_tool` with absolute path outside `proj` (e.g. `/etc/passwd` or `../outside.py`). 3. Assert: policy error, not Graph IR. |
| **Acceptance** | Test xfail until ROAD-1.4. |
| **Gate** | `pytest tests/test_codimension_mcp_path_security.py` |

### ROAD-0.3 — Graph IR schema contract test

| Field | Value |
| ----- | ----- |
| **Test file** | `tests/test_codimension_core_graph_ir_contract.py` (new) |
| **Steps** | Assert `GraphIR.to_dict()` contains `graph_ir_version`, `nodes[]`, `edges[]`, `meta`; each node has `id`, `type`, `name`, `file`, `line_start`, `line_end`. |
| **Acceptance** | Green immediately. |
| **Gate** | pytest |

### ROAD-0.4 — MCP catalog parity contract test

| Field | Value |
| ----- | ----- |
| **Files** | existing `tests/test_codimension_mcp_catalog.py` |
| **Steps** | Add assert: every tool from `catalog.TOOLS` is registered in `server.py` (grep/inspect `mcp._tool_manager`). |
| **Acceptance** | Green; `./scripts/verify-mcp-catalog.sh` unchanged. |
| **Gate** | pytest + verify-mcp-catalog |

### ROAD-0.5 — Snapshot test function_key roundtrip

| Field | Value |
| ----- | ----- |
| **Files** | `tests/test_codimension_mcp_cfg_resources.py` |
| **Steps** | Add cases with **project-relative** paths: `pkg/mod.py:function:run`, `deep/nested/mod.py:class:Foo`. |
| **Acceptance** | Green (baseline for ROAD-1.6). |
| **Gate** | pytest |

### ROAD-0.6 — Baseline impact/call graph fixtures

| Field | Value |
| ----- | ----- |
| **Test file** | `tests/fixtures/collision_project/` (new directory) |
| **Steps** | Mini-project: two `utils.py` files, call chain, import edges. Save expected edge counts in parametrized test. |
| **Acceptance** | Green on current code; updated in ROAD-1.2. |
| **Gate** | pytest |

---

## Phase 1 — P0: Symbol IDs and path security

> Goal: stable identifiers and a single policy gate. **Non-breaking:** alias lookup for legacy `basename:kind:name`.

### ROAD-1.1 — `symbol_id` with project-relative path

| Field | Value |
| ----- | ----- |
| **Modules** | `codimension_core/codimension_core/symbols.py` |
| **Steps** | 1. Add `def symbol_id(project: Project, file_path: str, kind: str, name: str) -> str` → `{rel_path}:{kind}:{name}`. 2. Keep `_symbol_id` as deprecated wrapper or remove after migrating call sites. 3. In `_symbols_from_brief_info`, pass `project` for rel path via `project.to_relative_path(abs_path)`. |
| **Dependencies** | ROAD-0.1 |
| **Acceptance** | ROAD-0.1 green; existing tests green. |
| **Non-breaking** | Node.id changes — see ROAD-1.5. |

### ROAD-1.2 — Propagate new ID to callgraph / reverse_index / usages

| Field | Value |
| ----- | ----- |
| **Modules** | `callgraph.py`, `reverse_index.py`, `symbols.py` (find_usages edges) |
| **Steps** | Replace all `_symbol_id(...)` with `symbol_id(project, ...)`. Update `tests/test_codimension_core_impact.py` fixtures if needed. |
| **Dependencies** | ROAD-1.1 |
| **Acceptance** | ROAD-0.6 expected values updated; impact/callers/callees correct for nested paths. |
| **Gate** | `./scripts/test-analysis.sh` |

### ROAD-1.3 — `Project.to_relative_path()` helper

| Field | Value |
| ----- | ----- |
| **Modules** | `codimension_core/codimension_core/project.py` |
| **Steps** | 1. `def to_relative_path(self, abs_path: str) -> str` — normalized POSIX-style rel path. 2. Unit test in `tests/test_codimension_core.py`. |
| **Acceptance** | Symmetry: `is_project_path(join(root, rel))` for valid paths. |
| **Non-breaking** | New method, no API changes. |

### ROAD-1.4 — Centralized `resolve_project_path()`

| Field | Value |
| ----- | ----- |
| **Modules** | new `codimension_core/codimension_core/paths.py`; `codimension_mcp/tools.py`, `resources.py` |
| **Steps** | 1. `resolve_project_path(project, path: str) -> str`: realpath + `is_project_path` or `ValueError`. 2. Replace `_resolve_path` / `_resolve_project_path` in MCP with core helper. |
| **Dependencies** | ROAD-0.2 |
| **Acceptance** | ROAD-0.2 green; absolute path inside project — OK. |
| **Non-breaking** | Previously "worked" for paths outside project — now explicit error (security fix). |

### ROAD-1.5 — Legacy symbol ID alias layer

| Field | Value |
| ----- | ----- |
| **Modules** | `codimension_core/codimension_core/symbol_registry.py` (new) |
| **Steps** | 1. `build_alias_map(project) -> dict[legacy_id, canonical_id]`. 2. `lookup_symbol`, `impact_analysis`, `find_callers` accept legacy or canonical (resolve via map). 3. `meta.legacy_id` in GraphNode.extra for debug. |
| **Dependencies** | ROAD-1.2 |
| **Acceptance** | Tool `lookup_symbol("utils.py:function:foo")` finds symbol in `pkg/a/utils.py` if unambiguous; ambiguous → structured error. |
| **Non-breaking** | Old MCP URIs with basename continue working for one release. |

### ROAD-1.6 — Update `encode_function_key` / catalog encoding docs

| Field | Value |
| ----- | ----- |
| **Modules** | `codimension_mcp/resources.py`, `catalog.py`, `doc/MCP-CURSOR-HOWTO.md` |
| **Steps** | Document canonical format: `pkg/mod.py__function__name`. Add nested path examples. |
| **Dependencies** | ROAD-1.1 |
| **Acceptance** | ROAD-0.5 green; catalog encoding section updated; `verify-mcp-catalog.sh` OK. |

### ROAD-1.7 — Typed error for path policy

| Field | Value |
| ----- | ----- |
| **Modules** | `codimension_core/errors.py`, `codimension_mcp/errors.py` |
| **Steps** | `PathOutsideProjectError`; MCP `format_tool_error` returns JSON with `error_code: "path_outside_project"`. |
| **Acceptance** | MCP test asserts error_code; no stack trace on stdout. |

### ROAD-1.8 — Living spec + CORE-MAP sync (phase 1)

| Field | Value |
| ----- | ----- |
| **Files** | `doc/plugins/living-specification.md`, `doc/CODIMENSION-CORE-MAP.md` |
| **Steps** | Add rows: `paths.py`, `symbol_registry.py`, new tests. |
| **Acceptance** | Documents reflect actual state. |

---

## Phase 2 — Graph IR v2 (contract without breaking v1)

> Goal: richer contract for LLM clients. v1 stays readable; v2 is opt-in via version bump.

### ROAD-2.1 — Extend `GraphIR.meta` (without changing version)

| Field | Value |
| ----- | ----- |
| **Modules** | `graph_ir.py`, builders (`symbols.py`, `callgraph.py`, …) |
| **Steps** | Add to `meta`: `schema_id`, `project_root`, `generated_at`, `capabilities[]`. |
| **Acceptance** | ROAD-0.3 updated; `graph_ir_version` remains `1`. |
| **Non-breaking** | New fields in meta only. |

### ROAD-2.2 — Standardized `GraphNode.extra` keys

| Field | Value |
| ----- | ----- |
| **Steps** | Convention: `qualname`, `namespace`, `language` (=py), `confidence` (0–1), `provenance` (brief_ast\|ast\|jedi). Populate in symbols/callgraph. |
| **Acceptance** | Contract test for key presence on function nodes. |

### ROAD-2.3 — `GRAPH_IR_VERSION = 2` + serializer flag

| Field | Value |
| ----- | ----- |
| **Modules** | `graph_ir.py`, `codimension_mcp/serializers.py` |
| **Steps** | v2 includes `edges[].provenance`, `nodes[].uri` (stable). Env `CODIMENSION_GRAPH_IR=2` or project setting. Default remains v1. |
| **Acceptance** | Default v1 green; v2 opt-in test green. |

### ROAD-2.4 — Stable node URI (`codimension://symbol/{encoded_id}`)

| Field | Value |
| ----- | ----- |
| **Modules** | `graph_ir.py`, `codimension_mcp/resources.py` |
| **Steps** | Generate `uri` in v2 nodes; optional resource `codimension://symbol/{id}`. |
| **Acceptance** | Resource returns the same node JSON as in graph. |

### ROAD-2.5 — Graph capabilities discovery

| Field | Value |
| ----- | ----- |
| **Steps** | `meta.capabilities`: `["symbols","imports","calls","cfg","diagnostics"]` — depending on builder. |
| **Acceptance** | `get_call_graph` meta contains `"calls"`. |

### ROAD-2.6 — Graph IR v2 documentation

| Field | Value |
| ----- | ----- |
| **Files** | `doc/CODIMENSION-CORE-MAP.md`, `codimension_mcp/README.md` |
| **Steps** | Section «Graph IR versions» with JSON v1 vs v2 example. |
| **Acceptance** | PR checklist item. |

---

## Phase 3 — Semantic resolution (incremental)

> Goal: more accurate call/import graph. Each step is a separate PR, fallback to previous heuristic.

### ROAD-3.1 — Import map with project-relative module names

| Field | Value |
| ----- | ----- |
| **Modules** | `callgraph.py` |
| **Steps** | Key `_CallGraphIndex.import_map` as `rel_file → {local_name: fully.qualified.module}`. |
| **Acceptance** | New test: `from pkg.sub import fn` resolves to `pkg/sub.py`, not basename. |

### ROAD-3.2 — Relative import resolution (`from . import x`)

| Field | Value |
| ----- | ----- |
| **Modules** | `callgraph.py`, possibly `imports.py` reuse |
| **Steps** | Handle `ast.ImportFrom` with `level > 0`. |
| **Acceptance** | Fixture `pkg/__init__.py`, `pkg/a.py`, `pkg/b.py` with relative imports. |

### ROAD-3.3 — Method call resolution (`obj.method()`)

| Field | Value |
| ----- | ----- |
| **Modules** | `callgraph.py` |
| **Steps** | For `ast.Attribute` with simple type hints or class body lookup — edge with label `method`. |
| **Acceptance** | Test class method call; without resolution — edge with `confidence: 0.3` in meta. |

### ROAD-3.4 — Jedi-assisted call targets (optional)

| Field | Value |
| ----- | ----- |
| **Modules** | new `codimension_core/codimension_core/jedi_bridge.py` |
| **Steps** | Wrapper: if `jedi` installed → refine callee; otherwise AST fallback. |
| **Acceptance** | Test skip if no jedi; with jedi — higher confidence. |
| **Non-breaking** | Optional dependency. |

### ROAD-3.5 — `impact_analysis` on canonical IDs

| Field | Value |
| ----- | ----- |
| **Modules** | `callgraph.py` |
| **Steps** | Target matching via `symbol_registry.resolve()`. |
| **Dependencies** | ROAD-1.5 |
| **Acceptance** | `impact_analysis(project, "pkg/a/utils.py:function:foo")` is accurate. |

### ROAD-3.6 — Import graph: classified edges (stdlib/third/party/project)

| Field | Value |
| ----- | ----- |
| **Modules** | `dependency_graph.py`, `imports.py` |
| **Steps** | Edge type `imports` + `extra.kind` = project\|stdlib\|third_party. |
| **Acceptance** | `get_dependency_summary` consistent with edge labels. |

### ROAD-3.7 — Regression suite «semantic fixtures»

| Field | Value |
| ----- | ----- |
| **Files** | `tests/fixtures/semantic_project/` |
| **Steps** | 5–10 files: packages, re-exports, decorators, type aliases. Parametrized expected edges. |
| **Acceptance** | ≥80% expected edges in phase 3 (document known gaps). |

---

## Phase 4 — Import isolation

> Goal: remove global mutation of `sys.path` / `sys.modules` in long-lived MCP.

### ROAD-4.1 — Audit import resolution call sites

| Field | Value |
| ----- | ----- |
| **Steps** | Grep + doc table: who calls `_resolve_import_with_sys_path`, `find_spec`. |
| **Deliverable** | Section in `doc/CODIMENSION-CORE-MAP.md` § imports isolation. |

### ROAD-4.2 — `ImportResolver` class with context manager

| Field | Value |
| ----- | ----- |
| **Modules** | `imports.py` |
| **Steps** | Encapsulate save/restore sys.path, path_importer_cache, sys.modules diff. |
| **Acceptance** | Existing `test_codimension_core_imports.py` green without changing expected values. |
| **Non-breaking** | Refactor only. |

### ROAD-4.3 — Subprocess resolver (opt-in)

| Field | Value |
| ----- | ----- |
| **Steps** | `CODIMENSION_IMPORT_ISOLATION=subprocess` — resolve in `python -c` with project venv. |
| **Acceptance** | Integration test; default in-process. |
| **Non-breaking** | Opt-in env var. |

### ROAD-4.4 — Concurrent tool call stress test

| Field | Value |
| ----- | ----- |
| **Test file** | `tests/test_codimension_core_imports_concurrent.py` |
| **Steps** | ThreadPool: 10× parallel import resolution; assert sys.path restored. |
| **Acceptance** | Green after ROAD-4.2. |

---

## Phase 5 — Production hardening

### ROAD-5.1 — Optional dependencies in pyproject

| Field | Value |
| ----- | ----- |
| **Files** | `codimension_core/pyproject.toml`, `codimension_mcp/pyproject.toml` |
| **Steps** | `[project.optional-dependencies] analysis = ["pyflakes","radon","jedi","vulture"]`; MCP depends on `codimension-core[analysis]`. |
| **Acceptance** | `pip install -e ./codimension_core[analysis]` sufficient for diagnostics tests. |
| **Non-breaking** | Plain install remains; features degrade gracefully with `NotImplementedYetError` / skip. |

### ROAD-5.2 — Graceful degradation matrix

| Field | Value |
| ----- | ----- |
| **Modules** | `analyzer.py`, `symbols.py` (jedi usages) |
| **Steps** | Table feature→missing dep→response; unit tests for each row. |
| **Acceptance** | MCP JSON `{ "status": "partial", "missing": ["jedi"] }` where applicable. |

### ROAD-5.3 — Mypy: gradual disable of `ignore_missing_imports`

| Field | Value |
| ----- | ----- |
| **Steps** | 1. `types-*` stubs for jedi, vulture. 2. `ignore_missing_imports = false` for new modules. 3. Per-module override for legacy. |
| **Acceptance** | mypy green in CI. |

### ROAD-5.4 — MCP server lifecycle / workspace lock

| Field | Value |
| ----- | ----- |
| **Modules** | `codimension_mcp/schemas.py` |
| **Steps** | `WorkspaceState` thread lock on `open_project` + analyze; document single-workspace model. |
| **Acceptance** | Concurrent open_project test — no corrupt state. |

### ROAD-5.5 — Cache invalidation API for agents

| Field | Value |
| ----- | ----- |
| **Steps** | MCP tool `invalidate_file(path)` → `project.invalidate_file`. Catalog + test. |
| **Acceptance** | After file change — fresh symbols without MCP restart. |

### ROAD-5.6 — pip-audit / SBOM in CI

| Field | Value |
| ----- | ----- |
| **Files** | `.github/workflows/ci.yml` |
| **Steps** | Job `pip-audit -r requirements-dev.txt`; fail on critical. |
| **Acceptance** | CI badge green. |

---

## Phase 6 — DX, docs, agent ergonomics

### ROAD-6.1 — Update Analize-AI.md → status tracker

| Field | Value |
| ----- | ----- |
| **Steps** | Add «ROAD task» column and status (todo/done) for each gap. |
| **Acceptance** | Link to `doc/en/ROADMAP.md`. |

### ROAD-6.2 — Prompt templates v2 (canonical IDs)

| Field | Value |
| ----- | ----- |
| **Modules** | `codimension_mcp/prompts.py` |
| **Steps** | Prompts reference `pkg/mod.py:function:name`, not basename. |
| **Dependencies** | ROAD-1.6 |

### ROAD-6.3 — `scripts/dev-setup.sh`

| Field | Value |
| ----- | ----- |
| **Steps** | venv + editable install + optional analysis deps + install-cursor-mcp. |
| **Acceptance** | Fresh clone → one script → test gate. |

### ROAD-6.4 — VS Code extension sync check

| Field | Value |
| ----- | ----- |
| **Steps** | CI step `npm run compile` in `codimension-vscode/`; catalog URI parity smoke. |
| **Acceptance** | CI job does not block core, but signals on drift. |

### ROAD-6.5 — Anti-stub CI grep (optional gate)

| Field | Value |
| ----- | ----- |
| **Steps** | Script: fail if new code in `codimension_core/` contains `pass  # TODO` without `TEMP-STUB` marker. |
| **Acceptance** | Warning only first release; then enforce. |

---

## Matrix «gap → tasks»

| Gap (Analize-AI) | Tasks |
| ---------------- | ----- |
| Unstable symbol IDs | ROAD-0.1, 1.1–1.3, 1.5–1.6 |
| Path security | ROAD-0.2, 1.4, 1.7 |
| Primitive Graph IR | ROAD-0.3, 2.1–2.6 |
| Shallow call graph | ROAD-3.1–3.7 |
| sys.path mutation | ROAD-4.1–4.4 |
| Dev maturity / deps | ROAD-5.1–5.3, 5.6 |
| Production readiness | ROAD-5.4–5.6, 6.3–6.4 |
| Living spec drift | ROAD-1.8, 6.1 |

---

## Definition of Done (each task)

- [ ] Unit/integration test added or updated  
- [ ] `./scripts/test-analysis.sh` green in `.venv`  
- [ ] `./scripts/verify-mcp-catalog.sh` green (if MCP touched)  
- [ ] `doc/plugins/living-specification.md` updated (if new module/test)  
- [ ] No new `# noqa` without justification  
- [ ] CHANGELOG entry (when accumulating a release)

---

## Recommended sprint 1 (minimal safe package)

1. ROAD-0.1, ROAD-0.2, ROAD-0.3  
2. ROAD-1.3 → ROAD-1.1 → ROAD-1.2 → ROAD-1.4  
3. ROAD-1.5 (alias) → ROAD-1.8  

**Expected outcome:** stable IDs, path policy, backward-compatible MCP URI, zero regression in merge gate.

---

## Release versioning

| Milestone | Core version | Criterion |
| --------- | ------------ | --------- |
| Sprint 1 done | 0.21.0 | ROAD 1.x complete |
| Graph IR v2 default | 0.22.0 | ROAD 2.x + opt-in period |
| Semantic phase 1 | 0.23.0 | ROAD 3.1–3.3 |
| Import isolation default | 0.24.0 | ROAD 4.x |
| Production tag | 1.0.0 | ROAD 5.x + 6.x, Analize-AI ≥ 8/10 production |
