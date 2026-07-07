Оцінка CAN-MCP: **архітектура добра, реалізація активно наближається до production MVP**.

| Критерій                             | Оцінка |
| ------------------------------------ | -----: |
| Розділення `core` / `mcp` / `vscode` |   9/10 |
| MCP-модель tools/resources/prompts   |   8/10 |
| Graph IR                             |   7/10 |
| Project model / workspace handling   |   7/10 |
| Static analysis depth                |   6/10 |
| Cache / incremental design           |   7/10 |
| Production readiness                 |   6/10 |

Джерело задач: [doc/ROADMAP.md](doc/ROADMAP.md). Living spec: [doc/plugins/living-specification.md](doc/plugins/living-specification.md).

## Status tracker (Analize-AI → ROAD)

| Недолік | ROAD | Статус | Примітка |
| ------- | ---- | ------ | -------- |
| Graph IR примітивний | ROAD-2.1–2.6 | **done** | Graph IR v2 opt-in (`CODIMENSION_GRAPH_IR=2`), `node.uri`, `edge.provenance` |
| Symbol IDs нестабільні | ROAD-1.1–1.3, 1.5–1.6 | **done** | Project-relative IDs + legacy aliases |
| Call graph поверхневий | ROAD-3.1–3.7 | **partial** | Semantic imports, jedi refinement, fixtures; attribute-call resolution — борг |
| Import `sys.path` мутація | ROAD-4.1–4.4 | **done** | `ImportResolver`, subprocess opt-in, concurrent tests |
| Path security неповна | ROAD-1.4, 1.7 | **done** | `resolve_project_path` у всіх MCP tools |
| Dev-зрілість / optional deps | ROAD-5.1–5.3, 5.6 | **done** | `[analysis]` extra, capabilities matrix, mypy strict + stubs |
| MCP lifecycle / cache API | ROAD-5.4–5.5 | **done** | Workspace lock, `invalidate_file` tool |
| Living spec drift | ROAD-1.8, 6.1 | **done** | Цей tracker + `living-specification.md` |
| Prompt canonical IDs | ROAD-6.2 | **done** | Prompts v2 (`pkg/mod.py:function:name`) |
| Fresh-clone DX | ROAD-6.3 | **done** | `./scripts/dev-setup.sh` |

## Сильні рішення

1. **Правильна декомпозиція.** Репозиторій розділений на `codimension_core`, `codimension_mcp`, `codimension-vscode`, що відповідає правильній моделі: аналізатор окремо, MCP-транспорт окремо, UI окремо.

2. **MCP-шар тонкий.** `server.py` реєструє tools через `FastMCP`, тримає `WorkspaceState` і делегує в `tools.py` / `codimension_core`.

3. **Є машинний catalog.** `catalog.py` — source of truth для tools/resources/prompts; parity з VS Code URI list.

4. **Graph IR версіонований.** `GraphIR` v1 default, v2 opt-in; MCP resource `codimension://symbol/{symbol_key}`.

## Залишкові недоліки

1. **Call graph:** `worker.run()` vs imported `run` — хибне зіставлення; потрібен attribute-aware resolution (post ROAD-3.7).

2. **Import graph nodes:** ще `file:{basename}` у brief mode — окремий борг (canonical file nodes).

3. **Graph IR v2 не default** — потрібен період opt-in перед flip default.

4. **VS Code extension CI** — ROAD-6.4 (npm compile smoke) ще не в merge gate.

## Вердикт

Проєкт **зрілий як agent-facing analysis MVP** на гілці `reserv-1`. Архітектурна рамка `core → MCP → clients` реалізована; Phase 0–5 roadmap переважно закрито.

Оновлена оцінка: **8/10 як архітектура, 6/10 як аналізатор, 6/10 як production tool**.

До **1.0.0** залишилось: ROAD-6.4 (VS Code CI), attribute-call precision, Graph IR v2 default flip.
