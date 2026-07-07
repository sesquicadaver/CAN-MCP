# ROADMAP: CAN-MCP — виправлення недоліків і вдосконалення

> **Languages:** [English](../en/ROADMAP.md) · [Українська](../uk/ROADMAP.md)

**Версія:** 1.0  
**Дата:** 2026-07-06  
**Базова оцінка:** [Analize-AI.md](Analize-AI.md)  
**Жива специфікація:** [plugins/living-specification.md](plugins/living-specification.md)  
**Architecture map:** [CODIMENSION-CORE-MAP.md](CODIMENSION-CORE-MAP.md)

---

## Принципи (не ламати проєкт)

1. **Test-first** — кожна задача починається з тесту (red → green), потім код.
2. **Прогін `./scripts/test-analysis.sh`** — після кожної задачі: `./scripts/test-analysis.sh` (у venv).
3. **Backward compatibility** — старі ID/URI працюють через alias layer мінімум один реліз.
4. **Один PR = одна атомарна задача** — легкий revert.
5. **Core vs MCP** — бізнес-логіка лише в `codimension_core`; MCP — транспорт і policy.

---

## Фази (огляд)

| Фаза | Фокус | Задач | Ризик |
| ---- | ----- | ----- | ----- |
| 0 | Safety net (регресійні тести) | 6 | Низький |
| 1 | P0: Symbol IDs + path security | 8 | Середній |
| 2 | Graph IR v2 (контракт) | 6 | Середній |
| 3 | Semantic resolution | 7 | Високий |
| 4 | Import isolation | 4 | Високий |
| 5 | Production hardening | 6 | Низький |
| 6 | DX, docs, CI | 5 | Низький |

**Орієнтовний порядок:** 0 → 1 → 2 → 3 (паралельно з 5.1–5.3) → 4 → 5 → 6.

---

## Фаза 0 — Safety net (регресійні тести)

> Мета: зафіксувати поточну поведінку перед змінами; жодних змін production-коду.

### ROAD-0.1 — Тест колізії symbol ID

| Поле | Значення |
| ---- | -------- |
| **Файл тесту** | `tests/test_codimension_core_symbol_ids.py` (новий) |
| **Кроки** | 1. Створити `pkg/a/utils.py` і `pkg/b/utils.py` з однаковою функцією `foo`. 2. Викликати `get_symbols(project)`. 3. Assert: два **різні** node.id (тест **падає** на поточному коді — expected red). |
| **Acceptance** | Тест існує, позначений `@pytest.mark.xfail(reason="ROAD-1.1")` до виправлення. |
| **Gate** | `pytest tests/test_codimension_core_symbol_ids.py` |

### ROAD-0.2 — Тест path traversal у MCP tools

| Поле | Значення |
| ---- | -------- |
| **Файл тесту** | `tests/test_codimension_mcp_path_security.py` (новий) |
| **Кроки** | 1. `open_project(tmp_path/proj)`. 2. Викликати `analyze_file_tool` з абсolutним шляхом поза `proj` (напр. `/etc/passwd` або `../outside.py`). 3. Assert: помилка policy, не Graph IR. |
| **Acceptance** | Тест xfail до ROAD-1.4. |
| **Gate** | `pytest tests/test_codimension_mcp_path_security.py` |

### ROAD-0.3 — Contract test Graph IR schema

| Поле | Значення |
| ---- | -------- |
| **Файл тесту** | `tests/test_codimension_core_graph_ir_contract.py` (новий) |
| **Кроки** | Assert `GraphIR.to_dict()` містить `graph_ir_version`, `nodes[]`, `edges[]`, `meta`; кожен node — `id`, `type`, `name`, `file`, `line_start`, `line_end`. |
| **Acceptance** | Green одразу. |
| **Gate** | pytest |

### ROAD-0.4 — Contract test MCP узгодженість catalog

| Поле | Значення |
| ---- | -------- |
| **Файли** | існуючий `tests/test_codimension_mcp_catalog.py` |
| **Кроки** | Додати assert: кожен tool з `catalog.TOOLS` зареєстрований у `server.py` (grep/inspect `mcp._tool_manager`). |
| **Acceptance** | Green; `./scripts/verify-mcp-catalog.sh` без змін. |
| **Gate** | pytest + verify-mcp-catalog |

### ROAD-0.5 — Snapshot test function_key roundtrip

| Поле | Значення |
| ---- | -------- |
| **Файли** | `tests/test_codimension_mcp_cfg_resources.py` |
| **Кроки** | Додати кейси з **project-relative** шляхами: `pkg/mod.py:function:run`, `deep/nested/mod.py:class:Foo`. |
| **Acceptance** | Green (baseline для ROAD-1.6). |
| **Gate** | pytest |

### ROAD-0.6 — Baseline impact/call graph fixtures

| Поле | Значення |
| ---- | -------- |
| **Файл тесту** | `tests/fixtures/collision_project/` (новий каталог) |
| **Кроки** | Міні-проєкт: два `utils.py`, chain викликів, import edges. Зберегти expected edge counts у parametrized test. |
| **Acceptance** | Green на поточному коді; оновлюється в ROAD-1.2. |
| **Gate** | pytest |

---

## Фаза 1 — P0: Symbol IDs і path security

> Мета: стабільні ідентифікатори та єдиний policy-gate. **Non-breaking:** alias lookup для legacy `basename:kind:name`.

### ROAD-1.1 — `symbol_id` з project-relative path

| Поле | Значення |
| ---- | -------- |
| **Модулі** | `codimension_core/codimension_core/symbols.py` |
| **Кроки** | 1. Додати `def symbol_id(project: Project, file_path: str, kind: str, name: str) -> str` → `{rel_path}:{kind}:{name}`. 2. `_symbol_id` залишити deprecated wrapper або видалити після міграції викликів. 3. У `_symbols_from_brief_info` передавати `project` для rel path через `project.to_relative_path(abs_path)`. |
| **Залежності** | ROAD-0.1 |
| **Acceptance** | ROAD-0.1 — тести проходять; існуючі тести — тести проходять. |
| **Non-breaking** | Node.id змінюється — див. ROAD-1.5. |

### ROAD-1.2 — Пропагувати новий ID у callgraph / reverse_index / usages

| Поле | Значення |
| ---- | -------- |
| **Модулі** | `callgraph.py`, `reverse_index.py`, `symbols.py` (find_usages edges) |
| **Кроки** | Замінити всі `_symbol_id(...)` на `symbol_id(project, ...)`. Оновити `tests/test_codimension_core_impact.py` fixtures якщо потрібно. |
| **Залежності** | ROAD-1.1 |
| **Acceptance** | ROAD-0.6 оновлений expected; impact/callers/callees коректні для nested paths. |
| **Gate** | `./scripts/test-analysis.sh` |

### ROAD-1.3 — `Project.to_relative_path()` helper

| Поле | Значення |
| ---- | -------- |
| **Модулі** | `codimension_core/codimension_core/project.py` |
| **Кроки** | 1. `def to_relative_path(self, abs_path: str) -> str` — нормалізований POSIX-style rel path. 2. Unit test у `tests/test_codimension_core.py`. |
| **Acceptance** | Symmetry: `is_project_path(join(root, rel))` для валідних шляхів. |
| **Non-breaking** | Новий метод, без змін API. |

### ROAD-1.4 — Централізований `resolve_project_path()`

| Поле | Значення |
| ---- | -------- |
| **Модулі** | новий `codimension_core/codimension_core/paths.py`; `codimension_mcp/tools.py`, `resources.py` |
| **Кроки** | 1. `resolve_project_path(project, path: str) -> str`: realpath + `is_project_path` або `ValueError`. 2. Замінити `_resolve_path` / `_resolve_project_path` у MCP на core helper. |
| **Залежності** | ROAD-0.2 |
| **Acceptance** | ROAD-0.2 — тести проходять; absolute path всередині project — OK. |
| **Non-breaking** | Раніше «працювало» для paths поза project — тепер явна помилка (security fix). |

### ROAD-1.5 — Legacy symbol ID alias layer

| Поле | Значення |
| ---- | -------- |
| **Модулі** | `codimension_core/codimension_core/symbol_registry.py` (новий) |
| **Кроки** | 1. `build_alias_map(project) -> dict[legacy_id, canonical_id]`. 2. `lookup_symbol`, `impact_analysis`, `find_callers` приймають legacy або canonical (resolve через map). 3. `meta.legacy_id` у GraphNode.extra для debug. |
| **Залежності** | ROAD-1.2 |
| **Acceptance** | Tool `lookup_symbol("utils.py:function:foo")` знаходить символ у `pkg/a/utils.py` якщо однозначно; ambiguous → структурована помилка. |
| **Non-breaking** | Старі MCP URI з basename продовжують працювати один реліз. |

### ROAD-1.6 — Оновити `encode_function_key` / catalog encoding docs

| Поле | Значення |
| ---- | -------- |
| **Модулі** | `codimension_mcp/resources.py`, `catalog.py`, `doc/MCP-CURSOR-HOWTO.md` |
| **Кроки** | Документувати canonical format: `pkg/mod.py__function__name`. Додати приклади nested paths. |
| **Залежності** | ROAD-1.1 |
| **Acceptance** | ROAD-0.5 — тести проходять; catalog encoding section оновлений; `verify-mcp-catalog.sh` OK. |

### ROAD-1.7 — Typed error для path policy

| Поле | Значення |
| ---- | -------- |
| **Модулі** | `codimension_core/errors.py`, `codimension_mcp/errors.py` |
| **Кроки** | `PathOutsideProjectError`; MCP `format_tool_error` повертає JSON з `error_code: "path_outside_project"`. |
| **Acceptance** | MCP test assert error_code; не stack trace у stdout. |

### ROAD-1.8 — Жива специфікація + CORE-MAP (фаза 1)

| Поле | Значення |
| ---- | -------- |
| **Файли** | `doc/plugins/living-specification.md`, `doc/CODIMENSION-CORE-MAP.md` |
| **Кроки** | Додати рядки: `paths.py`, `symbol_registry.py`, нові тести. |
| **Acceptance** | Документи відображають фактичний стан. |

---

## Фаза 2 — Graph IR v2 (контракт без лому v1)

> Мета: багатший контракт для LLM-клієнтів. v1 залишається читабельний; v2 — за env-прапорцем через version bump.

### ROAD-2.1 — Розширити `GraphIR.meta` (без зміни version)

| Поле | Значення |
| ---- | -------- |
| **Модулі** | `graph_ir.py`, builders (`symbols.py`, `callgraph.py`, …) |
| **Кроки** | Додати в `meta`: `schema_id`, `project_root`, `generated_at`, `capabilities[]`. |
| **Acceptance** | ROAD-0.3 оновлений; `graph_ir_version` лишається `1`. |
| **Non-breaking** | Лише нові поля в meta. |

### ROAD-2.2 — `GraphNode.extra` стандартизовані ключі

| Поле | Значення |
| ---- | -------- |
| **Кроки** | Конвенція: `qualname`, `namespace`, `language` (=py), `confidence` (0–1), `provenance` (brief_ast|ast|jedi). Заповнювати в symbols/callgraph. |
| **Acceptance** | Contract test на наявність ключів для function nodes. |

### ROAD-2.3 — `GRAPH_IR_VERSION = 2` + serializer flag

| Поле | Значення |
| ---- | -------- |
| **Модулі** | `graph_ir.py`, `codimension_mcp/serializers.py` |
| **Кроки** | v2 включає `edges[].provenance`, `nodes[].uri` (stable). Env `CODIMENSION_GRAPH_IR=2` або project setting. Default залишити v1. |
| **Acceptance** | Default v1 — тести проходять; v2 за env-прапорцем test — тести проходять. |

### ROAD-2.4 — Stable node URI (`codimension://symbol/{encoded_id}`)

| Поле | Значення |
| ---- | -------- |
| **Модулі** | `graph_ir.py`, `codimension_mcp/resources.py` |
| **Кроки** | Генерувати `uri` у v2 nodes; опційний resource `codimension://symbol/{id}`. |
| **Acceptance** | Resource повертає той самий node JSON що в graph. |

### ROAD-2.5 — Graph capabilities discovery

| Поле | Значення |
| ---- | -------- |
| **Кроки** | `meta.capabilities`: `["symbols","imports","calls","cfg","diagnostics"]` — залежно від builder. |
| **Acceptance** | `get_call_graph` meta містить `"calls"`. |

### ROAD-2.6 — Документація Graph IR v2

| Поле | Значення |
| ---- | -------- |
| **Файли** | `doc/CODIMENSION-CORE-MAP.md`, `codimension_mcp/README.md` |
| **Кроки** | Секція «Graph IR versions» з прикладом JSON v1 vs v2. |
| **Acceptance** | PR checklist item. |

---

## Фаза 3 — Semantic resolution (incremental)

> Мета: точніший call/import graph. Кожен крок — окремий PR, fallback на попередню евристику.

### ROAD-3.1 — Import map з project-relative module names

| Поле | Значення |
| ---- | -------- |
| **Модулі** | `callgraph.py` |
| **Кроки** | `_CallGraphIndex.import_map` ключувати `rel_file → {local_name: fully.qualified.module}`. |
| **Acceptance** | Новий test: `from pkg.sub import fn` резолвиться в `pkg/sub.py`, не basename. |

### ROAD-3.2 — Relative import resolution (`from . import x`)

| Поле | Значення |
| ---- | -------- |
| **Модулі** | `callgraph.py`, можливо `imports.py` reuse |
| **Кроки** | Обробка `ast.ImportFrom` з `level > 0`. |
| **Acceptance** | Fixture `pkg/__init__.py`, `pkg/a.py`, `pkg/b.py` with relative imports. |

### ROAD-3.3 — Method call resolution (`obj.method()`)

| Поле | Значення |
| ---- | -------- |
| **Модулі** | `callgraph.py` |
| **Кроки** | Для `ast.Attribute` з простими type hints або class body lookup — edge з label `method`. |
| **Acceptance** | Test class method call; без resolution — edge з `confidence: 0.3` в meta. |

### ROAD-3.4 — Jedi-assisted call targets (optional)

| Поле | Значення |
| ---- | -------- |
| **Модулі** | новий `codimension_core/codimension_core/jedi_bridge.py` |
| **Кроки** | Wrapper: якщо `jedi` installed → уточнити callee; інакше AST fallback. |
| **Acceptance** | Test skip якщо no jedi; with jedi — higher confidence. |
| **Non-breaking** | Optional dependency. |

### ROAD-3.5 — `impact_analysis` на canonical IDs

| Поле | Значення |
| ---- | -------- |
| **Модулі** | `callgraph.py` |
| **Кроки** | Target matching через `symbol_registry.resolve()`. |
| **Залежності** | ROAD-1.5 |
| **Acceptance** | `impact_analysis(project, "pkg/a/utils.py:function:foo")` точний. |

### ROAD-3.6 — Import graph: classified edges (stdlib/third/party/project)

| Поле | Значення |
| ---- | -------- |
| **Модулі** | `dependency_graph.py`, `imports.py` |
| **Кроки** | Edge type `imports` + `extra.kind` = project|stdlib|third_party. |
| **Acceptance** | `get_dependency_summary` узгоджений з edge labels. |

### ROAD-3.7 — Regression suite «semantic fixtures»

| Поле | Значення |
| ---- | -------- |
| **Файли** | `tests/fixtures/semantic_project/` |
| **Кроки** | 5–10 файлів: packages, re-exports, decorators, type aliases. Parametrized expected edges. |
| **Acceptance** | ≥80% expected edges на фазу 3 (документувати відомі прогалини). |

---

## Фаза 4 — Import isolation

> Мета: прибрати глобальну мутацію `sys.path` / `sys.modules` у long-lived MCP.

### ROAD-4.1 — Audit import resolution call sites

| Поле | Значення |
| ---- | -------- |
| **Кроки** | Grep + doc table: хто викликає `_resolve_import_with_sys_path`, `find_spec`. |
| **Deliverable** | Секція в `doc/CODIMENSION-CORE-MAP.md` § imports isolation. |

### ROAD-4.2 — `ImportResolver` class з context manager

| Поле | Значення |
| ---- | -------- |
| **Модулі** | `imports.py` |
| **Кроки** | Encapsulate save/restore sys.path, path_importer_cache, sys.modules diff. |
| **Acceptance** | Існуючі `test_codimension_core_imports.py` — OK без змін expected. |
| **Non-breaking** | Refactor only. |

### ROAD-4.3 — Subprocess resolver (за env-прапорцем)

| Поле | Значення |
| ---- | -------- |
| **Кроки** | `CODIMENSION_IMPORT_ISOLATION=subprocess` — resolve у `python -c` з project venv. |
| **Acceptance** | Integration test; default in-process. |
| **Non-breaking** | Opt-in env var. |

### ROAD-4.4 — Concurrent tool call stress test

| Поле | Значення |
| ---- | -------- |
| **Файл тесту** | `tests/test_codimension_core_imports_concurrent.py` |
| **Кроки** | ThreadPool: 10× parallel import resolution; assert sys.path restored. |
| **Acceptance** | Green після ROAD-4.2. |

---

## Фаза 5 — Production hardening

### ROAD-5.1 — Optional dependencies у pyproject

| Поле | Значення |
| ---- | -------- |
| **Файли** | `codimension_core/pyproject.toml`, `codimension_mcp/pyproject.toml` |
| **Кроки** | `[project.optional-dependencies] analysis = ["pyflakes","radon","jedi","vulture"]`; MCP depends on `codimension-core[analysis]`. |
| **Acceptance** | `pip install -e ./codimension_core[analysis]` достатньо для diagnostics tests. |
| **Non-breaking** | Plain install лишається; features degrade gracefully з `NotImplementedYetError` / skip. |

### ROAD-5.2 — Graceful degradation matrix

| Поле | Значення |
| ---- | -------- |
| **Модулі** | `analyzer.py`, `symbols.py` (jedi usages) |
| **Кроки** | Таблиця feature→missing dep→response; unit tests на кожен рядок. |
| **Acceptance** | MCP JSON `{ "status": "partial", "missing": ["jedi"] }` де застосовно. |

### ROAD-5.3 — Mypy: поступове вимкнення `ignore_missing_imports`

| Поле | Значення |
| ---- | -------- |
| **Кроки** | 1. `types-*` stubs для jedi, vulture. 2. `ignore_missing_imports = false` для нових модулів. 3. Per-module override для legacy. |
| **Acceptance** | mypy — OK у CI. |

### ROAD-5.4 — MCP server lifecycle / workspace lock

| Поле | Значення |
| ---- | -------- |
| **Модулі** | `codimension_mcp/schemas.py` |
| **Кроки** | `WorkspaceState` thread lock на `open_project` + analyze; document single-workspace model. |
| **Acceptance** | Concurrent open_project test — no corrupt state. |

### ROAD-5.5 — Cache invalidation API для agents

| Поле | Значення |
| ---- | -------- |
| **Кроки** | MCP tool `invalidate_file(path)` → `project.invalidate_file`. Catalog + test. |
| **Acceptance** | Після зміни файлу — fresh symbols без restart MCP. |

### ROAD-5.6 — pip-audit / SBOM у CI

| Поле | Значення |
| ---- | -------- |
| **Файли** | `.github/workflows/ci.yml` |
| **Кроки** | Job `pip-audit -r requirements-dev.txt`; fail on critical. |
| **Acceptance** | CI badge — тести проходять. |

---

## Фаза 6 — DX, docs, agent ergonomics

### ROAD-6.1 — Оновити Analize-AI.md → статус tracker

| Поле | Значення |
| ---- | -------- |
| **Кроки** | Додати колонку «ROAD task» і статус (todo/done) до кожного недоліку. |
| **Acceptance** | Посилання на `doc/ROADMAP.md`. |

### ROAD-6.2 — Prompt templates v2 (canonical IDs)

| Поле | Значення |
| ---- | -------- |
| **Модулі** | `codimension_mcp/prompts.py` |
| **Кроки** | Prompts посилаються на `pkg/mod.py:function:name`, не basename. |
| **Залежності** | ROAD-1.6 |

### ROAD-6.3 — `scripts/dev-setup.sh`

| Поле | Значення |
| ---- | -------- |
| **Кроки** | venv + editable install + optional analysis deps + install-cursor-mcp. |
| **Acceptance** | Новий clone → one script → test gate. |

### ROAD-6.4 — VS Code extension sync check

| Поле | Значення |
| ---- | -------- |
| **Кроки** | CI step `npm run compile` у `codimension-vscode/`; catalog URI parity smoke. |
| **Acceptance** | CI job не блокує core, але попередження при розходженні. |

### ROAD-6.5 — Anti-stub CI grep (optional gate)

| Поле | Значення |
| ---- | -------- |
| **Кроки** | Script: fail якщо новий код у `codimension_core/` містить `pass  # TODO` без `TEMP-STUB` marker. |
| **Acceptance** | Лише warning перший реліз; потім enforce. |

---

## Матриця «недолік → задачі»

| Недолік (Analize-AI) | Задачі |
| -------------------- | ------ |
| Symbol IDs нестабільні | ROAD-0.1, 1.1–1.3, 1.5–1.6 |
| Path security | ROAD-0.2, 1.4, 1.7 |
| Graph IR примітивний | ROAD-0.3, 2.1–2.6 |
| Call graph поверхневий | ROAD-3.1–3.7 |
| sys.path мутація | ROAD-4.1–4.4 |
| Dev-зрілість / deps | ROAD-5.1–5.3, 5.6 |
| Production readiness | ROAD-5.4–5.6, 6.3–6.4 |
| Застаріла специфікація | ROAD-1.8, 6.1 |

---

## Definition of Done (кожна задача)

- [ ] Unit/integration test додано або оновлено  
- [ ] `./scripts/test-analysis.sh` — OK у `.venv`  
- [ ] `./scripts/verify-mcp-catalog.sh` — OK (якщо чіпали MCP)  
- [ ] `doc/plugins/living-specification.md` оновлено (якщо новий модуль/тест)  
- [ ] Немає нових `# noqa` без обґрунтування  
- [ ] CHANGELOG entry (коли накопичиться реліз)

---

## Рекомендований sprint 1 (мінімальний безпечний пакет)

1. ROAD-0.1, ROAD-0.2, ROAD-0.3  
2. ROAD-1.3 → ROAD-1.1 → ROAD-1.2 → ROAD-1.4  
3. ROAD-1.5 (alias) → ROAD-1.8  

**Очікуваний результат:** стабільні IDs, path policy, backward-compatible MCP URI, zero regression у прогін `./scripts/test-analysis.sh`.

---

## Версіонування релізів

| Milestone | Версія core | Критерій |
| --------- | ----------- | -------- |
| Sprint 1 done | 0.21.0 | ROAD 1.x complete |
| Graph IR v2 default | 0.22.0 | ROAD 2.x + за env-прапорцем period |
| Semantic phase 1 | 0.23.0 | ROAD 3.1–3.3 |
| Import isolation default | 0.24.0 | ROAD 4.x |
| Production tag | 1.0.0 | ROAD 5.x + 6.x, Analize-AI ≥ 8/10 production |
