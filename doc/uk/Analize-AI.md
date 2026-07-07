# Оцінка CAN-MCP (Analize-AI)

> **Languages:** [English](../en/Analize-AI.md) · [Українська](../uk/Analize-AI.md)

Оцінка CAN-MCP: **архітектура добра, реалізація наближається до робочого MVP**.

| Критерій                             | Оцінка |
| ------------------------------------ | -----: |
| Розділення `core` / `mcp` / `vscode` |   9/10 |
| MCP-модель tools/resources/prompts   |   8/10 |
| Graph IR                             |   7/10 |
| Project model / workspace handling   |   7/10 |
| Static analysis depth                |   6/10 |
| Cache / incremental design           |   7/10 |
| Production readiness                 |   7/10 |

Джерело задач: [ROADMAP.md](ROADMAP.md). Жива специфікація: [plugins/living-specification.md](plugins/living-specification.md).

## Таблиця статусу (Analize-AI → ROAD)

| Недолік | ROAD | Статус | Примітка |
| ------- | ---- | ------ | -------- |
| Graph IR примітивний | ROAD-2.1–2.6 | **done** | Graph IR v2 default; `CODIMENSION_GRAPH_IR=1` legacy opt-out |
| Symbol IDs нестабільні | ROAD-1.1–1.3, 1.5–1.6 | **done** | Project-relative IDs + legacy aliases |
| Call graph поверхневий | ROAD-3.1–3.7 | **done** | Instance/alias/nested attribute resolution + semantic fixtures |
| Import `sys.path` мутація | ROAD-4.1–4.4 | **done** | `ImportResolver`, subprocess за env-прапорцем, concurrent tests |
| Path security неповна | ROAD-1.4, 1.7 | **done** | `resolve_project_path` у всіх MCP tools |
| Dev-зрілість / optional deps | ROAD-5.1–5.3, 5.6 | **done** | `[analysis]` extra, capabilities matrix, mypy strict + stubs |
| MCP lifecycle / cache API | ROAD-5.4–5.5 | **done** | Workspace lock, `invalidate_file` tool |
| Застаріла специфікація | ROAD-1.8, 6.1 | **done** | Ця таблиця + `living-specification.md` |
| Prompt canonical IDs | ROAD-6.2 | **done** | Prompts v2 (`pkg/mod.py:function:name`) |
| Налаштування після clone | ROAD-6.3 | **done** | `./scripts/dev-setup.sh` |
| VS Code extension CI | ROAD-6.4 | **done** | CI job `vscode`: npm compile + узгодженість catalog |
| Anti-stub grep | ROAD-6.5 | **done** | `scripts/check-anti-stub.sh` (`ENFORCE=1` у CI) |

## Сильні рішення

1. **Правильна декомпозиція.** Репозиторій розділений на `codimension_core`, `codimension_mcp`, `codimension-vscode`, що відповідає правильній моделі: аналізатор окремо, MCP-транспорт окремо, UI окремо.

2. **MCP-шар тонкий.** `server.py` реєструє tools через `FastMCP`, тримає `WorkspaceState` і делегує в `tools.py` / `codimension_core`.

3. **Є машинний catalog.** `catalog.py` — еталонний опис для tools/resources/prompts; узгодженість з VS Code URI list.

4. **Graph IR версіонований.** `GraphIR` v2 default (`node.uri`, `edge.provenance`); legacy v1 через `CODIMENSION_GRAPH_IR=1`.

## Залишкові недоліки

1. **Call graph / import graph:** основні semantic шляхи закрито; подальше — jedi refinement edge cases.

2. _(resolved)_ brief import stem collision — module map у brief mode.

## Вердикт

Проєкт **зрілий як MVP аналізу для AI-агентів** на гілці `reserv-1`. Архітектурна рамка `core → MCP → clients` реалізована; Phase 0–5 roadmap переважно закрито.

Оновлена оцінка: **8/10 архітектура, 7/10 аналізатор, 7/10 як інструмент для продакшену**.

**1.0.0** (2026-07-07): Phase 0–6 закрито; `./scripts/test-analysis.sh` — 153 тести.
