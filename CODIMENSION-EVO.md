Найкраще — **не “перетворювати весь Codimension на MCP”**, а винести з нього **headless analysis core** і поверх нього зробити MCP-сервер.

MCP архітектурно є client-host-server протоколом на JSON-RPC, де сервер експонує tools/resources/prompts для AI-клієнтів. ([Model Context Protocol][1]) Cursor підключає зовнішні інструменти саме через MCP-сервери. ([Cursor][2])

## Цільова архітектура

```text
Cursor / Claude / інший MCP host
        │
        ▼
codimension-mcp-server
        │
        ▼
codimension-analysis-core
        │
        ├─ parser
        ├─ symbol index
        ├─ import graph
        ├─ call graph
        ├─ control-flow graph
        ├─ dependency graph
        └─ impact analyzer
```

## Правильний порядок робіт

### 1. Відділити GUI від аналізатора

У Codimension треба знайти й ізолювати все, що будує:

```text
symbols
imports
classes/functions
control-flow diagrams
call relationships
project structure
```

Це має стати окремим Python-пакетом:

```text
codimension_core/
  project.py
  analyzer.py
  symbols.py
  imports.py
  cfg.py
  callgraph.py
  dependency_graph.py
  cache.py
```

PyQt, editor, dock widgets, menus — не мають потрапити в MCP-шар.

### 2. Зробити стабільний внутрішній Graph IR

Не віддавати MCP напряму внутрішні класи Codimension. Потрібен проміжний формат:

```json
{
  "nodes": [
    {
      "id": "file.py:function:foo",
      "type": "function",
      "name": "foo",
      "file": "file.py",
      "line_start": 10,
      "line_end": 42
    }
  ],
  "edges": [
    {
      "from": "file.py:function:foo",
      "to": "file.py:function:bar",
      "type": "calls"
    }
  ]
}
```

Це критично. Без Graph IR MCP стане тонкою обгорткою над legacy-кодом.

### 3. Почати з MCP tools, не resources

Для Cursor практичніше першими зробити **tools**, бо вони напряму викликаються агентом. MCP tools призначені для обчислень і взаємодії із зовнішніми системами. ([Model Context Protocol][3]) Resources можна додати пізніше для читання кешованих графів і індексів; MCP resources призначені для надання контекстних даних через URI. ([Model Context Protocol][4])

Мінімальний набір tools:

```text
open_project(path)
analyze_project()
analyze_file(path)
get_project_tree()
get_symbols(path?)
get_import_graph()
get_call_graph(symbol?)
get_control_flow(function_id)
find_callers(symbol)
find_callees(symbol)
find_usages(symbol)
explain_symbol(symbol)
impact_analysis(path | symbol)
```

### 4. MCP server зробити окремим пакетом

Структура:

```text
codimension-mcp/
  pyproject.toml
  codimension_mcp/
    server.py
    tools.py
    serializers.py
    schemas.py
    errors.py
```

Запуск:

```bash
codimension-mcp --workspace /path/to/project
```

Cursor-конфіг:

```json
{
  "mcpServers": {
    "codimension": {
      "command": "codimension-mcp",
      "args": ["--workspace", "/path/to/project"]
    }
  }
}
```

### 5. Додати інкрементальний кеш

Без кешу на великих проєктах MCP буде повільним.

Потрібно кешувати:

```text
file hash
AST
symbol table
imports
per-file CFG
project graph
reverse index
```

Інвалідація:

```text
changed file → rebuild AST
changed imports → rebuild dependency graph
changed function body → rebuild CFG only for function
```

## Пріоритет реалізації

| Етап | Що зробити                    |    Цінність |
| ---- | ----------------------------- | ----------: |
| 1    | `codimension_core` без GUI    |        база |
| 2    | symbol/import index           |      висока |
| 3    | MCP tools для аналізу файлів  |      висока |
| 4    | call graph / dependency graph | дуже висока |
| 5    | CFG для функцій               | дуже висока |
| 6    | impact analysis               |      висока |
| 7    | Cursor WebView для діаграм    |     середня |
| 8    | prompts/resources             |   додатково |

## Ключове рішення

**Codimension має стати не MCP-сервером-IDE, а MCP-сервером аналізу коду.**

Назва пакета:

```text
codimension-core
codimension-mcp
codimension-vscode
```

Це найчистіший і найперспективніший варіант.

**Детальна карта модулів:** [doc/CODIMENSION-CORE-MAP.md](doc/CODIMENSION-CORE-MAP.md)  
**Scaffold (0.1.0):** `codimension_core/`, `codimension_mcp/`

[1]: https://modelcontextprotocol.io/specification/2025-06-18/architecture?utm_source=chatgpt.com "Architecture"
[2]: https://cursor.com/docs/mcp?utm_source=chatgpt.com "Model Context Protocol (MCP) | Cursor Docs"
[3]: https://modelcontextprotocol.io/specification/draft/server/tools?utm_source=chatgpt.com "Tools"
[4]: https://modelcontextprotocol.io/specification/2025-06-18/server/resources?utm_source=chatgpt.com "Resources"
