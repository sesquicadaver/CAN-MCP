# Codimension MCP × Cursor — повний HOWTO

Практичний посібник для підключення **codimension-mcp** до Cursor і роботи з 22 tools, 16 resources та 6 prompts.

**Джерело правди:** `codimension_mcp/catalog.py`  
**Короткий catalog:** [codimension_mcp/README.md](../codimension_mcp/README.md)  
**Локальний конфіг (не в git):** `.cursor/mcp.json` — згенеровано для цього checkout

---

## Зміст

1. [Архітектура](#1-архітектура)
2. [Встановлення](#2-встановлення)
3. [Підключення до Cursor](#3-підключення-до-cursor)
4. [Перевірка підключення](#4-перевірка-підключення)
5. [Базовий workflow](#5-базовий-workflow)
6. [Формати даних](#6-формати-даних)
7. [Tools — довідник з прикладами](#7-tools--довідник-з-прикладами)
8. [Resources — довідник з прикладами](#8-resources--довідник-з-прикладами)
9. [Prompts — готові сценарії](#9-prompts--готові-сценарії)
10. [Діаграми та WebView](#10-діаграми-та-webview)
11. [End-to-end сценарії](#11-end-to-end-сценарії)
12. [Приклади промптів для Cursor Agent](#12-приклади-промптів-для-cursor-agent)
13. [Troubleshooting](#13-troubleshooting)
14. [Чеклист](#14-чеклист)

---

## 1. Архітектура

```text
Cursor Agent (MCP host)
        │  JSON-RPC / stdio
        ▼
codimension-mcp          ← MCP server (codimension_mcp/)
        │
        ▼
codimension_core         ← headless analysis (без PyQt)
        │
        ├─ symbols, imports, callgraph, cfg
        ├─ diagnostics (pyflakes/radon)
        └─ Graph IR v1 → JSON
```

Legacy PyQt IDE (`codimension/`) для MCP **не потрібна**.

---

## 2. Встановлення

### 2.1. Клонування та venv

```bash
git clone https://github.com/sesquicadaver/CAN-MCP.git
cd CAN-MCP

python3 -m venv .venv
source .venv/bin/activate          # Windows: .venv\Scripts\activate
pip install --upgrade pip
```

### 2.2. MCP-пакети (обов'язково окремо)

```bash
pip install -e ./codimension_core -e ./codimension_mcp
```

> Не покладайтеся лише на `pip install -e .` — root setup ставить legacy IDE, але не замінює окремий MCP install.

### 2.3. Аналітичні залежності (рекомендовано)

```bash
pip install pyflakes radon jedi vulture
```

| Пакет | Для чого |
|-------|----------|
| `pyflakes` + `radon` | `get_diagnostics` |
| `jedi` | `find_usages` |
| `vulture` | `find_dead_code` |

### 2.4. Перевірка

```bash
which codimension-mcp
# → .../CAN-MCP/.venv/bin/codimension-mcp

codimension-mcp --help

# Повний merge gate (як CI):
./scripts/test-analysis.sh
```

---

## 3. Підключення до Cursor

### 3.1. Локальний конфіг цього checkout

Файл **`.cursor/mcp.json`** (gitignored) уже згенеровано з абсолютними шляхами:

```json
{
  "mcpServers": {
    "codimension": {
      "command": "/home/sesquicadaver/GITFOLDER/CAN-MCP/.venv/bin/codimension-mcp",
      "args": ["--workspace", "${workspaceFolder}"]
    }
  }
}
```

| Поле | Значення |
|------|----------|
| `command` | Повний шлях до `codimension-mcp` у venv CAN-MCP |
| `args[1]` | `${workspaceFolder}` — корінь **відкритого в Cursor** Python-проєкту |

Шаблон без конкретних шляхів: [`.cursor/mcp.json.example`](../.cursor/mcp.json.example)

### 3.2. Глобальний конфіг

Файл: `~/.cursor/mcp.json` — той самий JSON, MCP доступний у всіх workspace.

### 3.3. Два типові setup

**A. Аналізуєте CAN-MCP:**

- Workspace у Cursor = `/home/sesquicadaver/GITFOLDER/CAN-MCP`
- `--workspace ${workspaceFolder}` → аналізує сам репозиторій

**B. Аналізуєте інший проєкт:**

- Workspace у Cursor = ваш Python-проєкт
- `command` → все одно вказує на venv CAN-MCP
- `--workspace` → `${workspaceFolder}` = цільовий проєкт

### 3.4. Активація

1. Зберегти `mcp.json`
2. Cursor Settings → **MCP** → сервер `codimension` → увімкнути / Reload
3. Або перезапустити Cursor

---

## 4. Перевірка підключення

### 4.1. У чаті Agent

```text
Використай MCP codimension: виклич list_mcp_catalog і коротко підсумуй tools/resources/prompts.
```

Очікувано: **22 tools**, **16 resources**, **6 prompts**.

```text
Виклич get_project_tree через codimension MCP.
```

Очікувано: JSON з масивом `"files": ["...", ...]`.

### 4.2. Resource без tool

```text
Прочитай MCP resource codimension://workspace/status
```

Очікувано:

```json
{
  "status": "open",
  "workspace": "/abs/path/to/project",
  "python_files": 27,
  "analyzed_files": 27,
  "tool_calls": { "open_project": 1 }
}
```

---

## 5. Базовий workflow

```text
┌─────────────────────────────────────────────────────────┐
│ 1. open_project(path)     — якщо не передано --workspace │
│ 2. analyze_project()      — прогріти кеші               │
│ 3. get_symbols()          — огляд символів              │
│ 4. … цільовий аналіз …                                  │
└─────────────────────────────────────────────────────────┘
```

Якщо в `mcp.json` є `"args": ["--workspace", "..."]`, крок 1 уже виконано при старті сервера.

**Discovery (завжди першим для нового агента):**

- Tool: `list_mcp_catalog`
- Resource: `codimension://catalog`

---

## 6. Формати даних

### 6.1. Graph IR v1

Більшість tools повертають Graph IR:

```json
{
  "graph_ir_version": 1,
  "meta": {
    "kind": "symbols"
  },
  "nodes": [
    {
      "id": "codimension_core/project.py:function:open",
      "type": "function",
      "name": "open",
      "file": "codimension_core/project.py",
      "line_start": 52,
      "line_end": 60
    }
  ],
  "edges": []
}
```

### 6.2. Symbol ID (для tools)

| Тип | Формат | Приклад |
|-----|--------|---------|
| Функція | `file.py:function:name` | `codimension_core/project.py:function:open` |
| Клас | `file.py:class:Name` | `codimension_core/project.py:class:Project` |

### 6.3. URI-ключі (для resources)

| Концепт | Tool ID | URI key |
|---------|---------|---------|
| Функція | `main.py:function:foo` | `main.py__function__foo` |
| Клас | `pkg/mod.py:class:Bar` | `pkg/mod.py__class__Bar` |
| Файл (impact) | `lib/mod.py` | `lib__mod.py` |

**Приклад CFG resource:**

```text
codimension://graph/control_flow/codimension_core__project.py__function__open
```

### 6.4. Помилки

```json
{
  "status": "error",
  "error": "Call open_project(path) first"
}
```

---

## 7. Tools — довідник з прикладами

### Discovery

#### `list_mcp_catalog`

```json
{}
```

**Відповідь (фрагмент):**

```json
{
  "status": "ok",
  "catalog_version": "1.0",
  "tools": [{ "name": "open_project" }],
  "resources": [{ "uri": "codimension://catalog" }],
  "prompts": [{ "name": "refactor_symbol" }]
}
```

### Проєкт

| Tool | Аргументи | Приклад відповіді |
|------|-----------|-------------------|
| `open_project` | `{ "path": "/abs/project" }` | `{ "status": "ok", "python_files": 42 }` |
| `analyze_project` | `{}` | `{ "status": "ok", "analyzed_files": 42 }` |
| `get_project_tree` | `{}` | `{ "files": ["main.py", "pkg/api.py"] }` |

### Символи

| Tool | Аргументи |
|------|-----------|
| `get_symbols` | `{}` або `{ "path": "pkg/mod.py" }` |
| `analyze_file` | `{ "path": "pkg/mod.py" }` |
| `lookup_symbol` | `{ "name": "Project" }` |
| `explain_symbol` | `{ "symbol": "pkg/mod.py:function:api" }` |

### Графи

| Tool | Аргументи |
|------|-----------|
| `get_import_graph` | `{}` |
| `get_call_graph` | `{}` або `{ "symbol": "main.py:function:main" }` |
| `get_control_flow` | `{ "function_id": "file.py:function:name" }` |
| `find_callers` / `find_callees` | `{ "symbol": "file.py:function:name" }` |
| `find_usages` | `{ "symbol": "file.py:class:Name" }` |
| `impact_analysis` | `{ "target": "file.py" }` або `{ "target": "file.py:function:name" }` |

### Якість коду

| Tool | Аргументи | Залежність |
|------|-----------|------------|
| `get_diagnostics` | `{ "path": "file.py" }` | pyflakes, radon |
| `find_dead_code` | `{}` або `{ "path": "file.py" }` | vulture |

### Summaries та діаграми

| Tool | Аргументи |
|------|-----------|
| `get_dependency_summary` | `{}` або `{ "path": "file.py" }` |
| `get_symbol_summary` | `{}` або `{ "path": "file.py" }` |
| `get_import_diagram` | `{}` |
| `render_diagram` | `{ "kind": "import" }` / `"call"` / `"control_flow"` + `target` / `"impact"` + `target` |
| `get_cache_stats` | `{}` |

**`render_diagram` — приклад відповіді:**

```json
{
  "status": "ok",
  "kind": "import",
  "html_path": "/project/.codimension/diagrams/import-project.html",
  "mermaid": "graph TD\n...",
  "nodes": 12,
  "edges": 8,
  "webview_hint": "Open ... in Cursor Simple Browser..."
}
```

---

## 8. Resources — довідник з прикладами

### Статичні

| URI | MIME | Зміст |
|-----|------|-------|
| `codimension://catalog` | JSON | Повний catalog |
| `codimension://workspace/status` | JSON | Стан workspace |
| `codimension://project/tree` | JSON | Список `.py` |
| `codimension://deps/summary` | JSON | Класифікація імпортів |
| `codimension://symbols/summary` | JSON | Лічильники символів |
| `codimension://graph/import` | JSON | Import Graph IR |
| `codimension://graph/call` | JSON | Call Graph IR |
| `codimension://diagram/import` | HTML | Import diagram |
| `codimension://diagram/call` | HTML | Call diagram |
| `codimension://cache/stats` | JSON | Статистика кешу |

### Шаблонні

| URI | Приклад |
|-----|---------|
| `codimension://deps/file/{path}` | `codimension://deps/file/main.py` |
| `codimension://symbols/file/{path}` | `codimension://symbols/file/pkg/api.py` |
| `codimension://graph/control_flow/{function_key}` | `.../main.py__function__api` |
| `codimension://diagram/control_flow/{function_key}` | HTML CFG |
| `codimension://graph/impact/{target_key}` | `.../codimension_core__project.py` |
| `codimension://diagram/impact/{target_key}` | HTML impact |

---

## 9. Prompts — готові сценарії

| Prompt | Аргументи | Workflow |
|--------|-----------|----------|
| `refactor_symbol` | `symbol` | explain → impact → usages → plan |
| `review_dead_code` | — | vulture → verify → deletion plan |
| `review_imports` | — | import graph → cycles → fixes |
| `analyze_module` | `path` | symbols → CFG → callers → summary |
| `audit_dependencies` | — | deps/symbols summary → graph → fixes |
| `assess_change_impact` | `target` | impact graph/diagram → callers → test plan |

**У Cursor Agent:**

```text
Використай MCP prompt refactor_symbol з symbol="pkg/api.py:function:fetch"
і виконай описаний workflow.
```

---

## 10. Діаграми та WebView

1. Agent викликає `render_diagram("import")` (або `"call"`, `"control_flow"`, `"impact"`).
2. У відповіді — `html_path` (`.codimension/diagrams/*.html`).
3. Відкрийте у **Simple Browser** / preview HTML.

Або resource: `codimension://diagram/import`, `codimension://diagram/call`.

**Допустимі `kind`:** `import`, `call`, `control_flow`, `impact`.

---

## 11. End-to-end сценарії

### A. Огляд нового проєкту

```text
open_project → analyze_project → get_project_tree →
get_symbol_summary → get_dependency_summary → get_import_graph → find_dead_code
```

### B. Рефакторинг функції

```text
explain_symbol → impact_analysis → find_callers → find_usages → get_control_flow
```

Промпт: MCP prompt `refactor_symbol`.

### C. Перевірка перед зміною файлу

```text
impact_analysis → codimension://graph/impact/{key} → render_diagram(impact) → find_callers
```

Промпт: MCP prompt `assess_change_impact`.

### D. Аудит import graph

```text
get_import_graph → get_import_diagram → render_diagram(import) → get_dependency_summary
```

Промпт: MCP prompt `review_imports`.

### E. Deep-dive модуля

```text
analyze_file → get_diagnostics → get_control_flow → find_callers / find_callees
```

Промпт: MCP prompt `analyze_module`.

---

## 12. Приклади промптів для Cursor Agent

```text
list_mcp_catalog → скільки tools?
get_symbols для codimension_core/project.py
lookup_symbol name="open"
impact_analysis target="codimension_core/project.py"
```

```text
1. analyze_project
2. get_call_graph
3. Для top-3 функцій з найбільшою fan-in — find_callers
4. Таблиця: function | callers count | files
```

---

## 13. Troubleshooting

| Симптом | Рішення |
|---------|---------|
| `ImportError: codimension_core` | `pip install -e ./codimension_core -e ./codimension_mcp` |
| `Unknown tool: open_project` | Оновити CAN-MCP (etapa 40+) |
| Cursor не стартує MCP | Абсолютний шлях у `command` |
| `Call open_project first` | `open_project` або `--workspace` в args |
| Diagnostics порожні | `pip install pyflakes radon` |
| `find_usages` fail | `pip install jedi` |
| `find_dead_code` fail | `pip install vulture` |
| CFG invalid function_id | Формат `file.py:function:name` |

```bash
./scripts/test-analysis.sh
./scripts/verify-mcp-catalog.sh
```

---

## 14. Чеклист

- [ ] Python 3.10+
- [ ] `pip install -e ./codimension_core -e ./codimension_mcp`
- [ ] `pip install pyflakes radon jedi vulture`
- [ ] `codimension-mcp --help` OK
- [ ] `.cursor/mcp.json` з абсолютним `command`
- [ ] Cursor MCP reloaded
- [ ] `list_mcp_catalog` → 22 / 16 / 6
- [ ] `get_project_tree` → список файлів
- [ ] `codimension://workspace/status` → `"status": "open"`

---

## Швидка довідка: усі 22 tools

| # | Tool | Аргументи |
|---|------|-----------|
| 1 | `list_mcp_catalog` | — |
| 2 | `open_project` | `path` |
| 3 | `analyze_project` | — |
| 4 | `analyze_file` | `path` |
| 5 | `get_project_tree` | — |
| 6 | `get_symbols` | `path?` |
| 7 | `get_import_graph` | — |
| 8 | `get_call_graph` | `symbol?` |
| 9 | `get_control_flow` | `function_id` |
| 10 | `find_callers` | `symbol` |
| 11 | `find_callees` | `symbol` |
| 12 | `find_usages` | `symbol` |
| 13 | `impact_analysis` | `target` |
| 14 | `explain_symbol` | `symbol` |
| 15 | `lookup_symbol` | `name` |
| 16 | `find_dead_code` | `path?` |
| 17 | `get_diagnostics` | `path` |
| 18 | `get_import_diagram` | — |
| 19 | `get_cache_stats` | — |
| 20 | `get_dependency_summary` | `path?` |
| 21 | `get_symbol_summary` | `path?` |
| 22 | `render_diagram` | `kind`, `target?` |
