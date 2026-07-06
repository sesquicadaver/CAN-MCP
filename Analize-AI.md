Оцінка CAN-MCP: **архітектура добра, реалізація ще рання**.

| Критерій                             | Оцінка |
| ------------------------------------ | -----: |
| Розділення `core` / `mcp` / `vscode` |   9/10 |
| MCP-модель tools/resources/prompts   |   8/10 |
| Graph IR                             |   7/10 |
| Project model / workspace handling   |   7/10 |
| Static analysis depth                |   5/10 |
| Cache / incremental design           |   6/10 |
| Production readiness                 |   4/10 |

## Сильні рішення

1. **Правильна декомпозиція.** Репозиторій розділений на `codimension_core`, `codimension_mcp`, `codimension-vscode`, що відповідає правильній моделі: аналізатор окремо, MCP-транспорт окремо, UI окремо. README прямо описує `codimension_core` як headless analysis і `codimension_mcp` як MCP-сервер із 22 tools, 16 resources, 6 prompts. ([GitHub][1])

2. **MCP-шар тонкий.** `server.py` фактично лише реєструє tools через `FastMCP`, тримає `WorkspaceState` і делегує роботу в `tools.py` / `codimension_core`. Це правильний напрям: MCP не містить бізнес-логіки. ([GitHub][2])

3. **Є машинний catalog.** `catalog.py` є джерелом списку tools/resources/prompts, плюс README вказує, що source of truth — саме `codimension_mcp/catalog.py`. Це добре для LLM-клієнтів і автогенерації документації. ([GitHub][3])

4. **Graph IR існує.** Є версіонований `GraphIR`, `GraphNode`, `GraphEdge`, тобто MCP не віддає сирі внутрішні класи. Це правильний контракт між core і клієнтами. ([GitHub][4])

## Слабкі місця

1. **Graph IR занадто примітивний.** Поточний IR має лише `nodes`, `edges`, `meta`, базові поля вузла і ребра. Немає schema-id для типів графів, capabilities, provenance, confidence, scope, namespace, language, stable URI, semantic roles. Для серйозної LLM-навігації цього замало. ([GitHub][4])

2. **Symbol IDs нестабільні.** `_symbol_id()` будується через `basename(file_path)`, тип і назву символу. Це створює колізії між файлами з однаковими іменами в різних пакетах. Для великого проєкту це критичний дефект. ([GitHub][5])

3. **Call graph поверхневий.** Він AST-based, project scope, але резолюція викликів груба: `ast.Name`, `ast.Attribute`, basename-модулі, часткова import map. Це корисно як евристика, але не як точний semantic call graph. ([GitHub][6])

4. **Import resolution змінює `sys.path` і чіпає `sys.modules`.** Код намагається відновлювати стан, але це все одно крихке рішення для MCP-сервера довгого життя. Краще ізолювати резолюцію імпортів без глобальної мутації інтерпретатора. ([GitHub][7])

5. **Безпека path handling неповна.** `analyze_file()` перевіряє, що файл у межах проєкту, але `_resolve_path()` в MCP tools повертає absolute realpath без єдиного централізованого policy-gate для всіх tools. Це треба уніфікувати. ([GitHub][8])

6. **Dev-зрілість середня.** Є ruff, mypy, pytest, CI-like script, але `mypy ignore_missing_imports = true`, залежності частково ставляться окремо (`pyflakes`, `radon`, `jedi`, `vulture`), а `codimension-core` має `dependencies = []`, хоча фактично частина функцій потребує зовнішніх пакетів. ([GitHub][9])

## Вердикт

Проєкт **добре спроектований як proof-of-concept / early MVP**. Архітектурна рамка правильна: `core → MCP → clients`. Найбільша цінність — не конкретна поточна точність аналізу, а правильно вибрана модульність.

Але до production-рівня бракує трьох речей:

1. **стабільного Graph IR v2** з повними namespace-ідентифікаторами;
2. **точнішої semantic resolution** для symbol/import/call graph;
3. **жорсткого workspace security boundary** для всіх tools/resources.

Поточна оцінка: **7/10 як архітектура, 5/10 як аналізатор, 4/10 як production tool**.

[1]: https://github.com/sesquicadaver/CAN-MCP "GitHub - sesquicadaver/CAN-MCP · GitHub"
[2]: https://raw.githubusercontent.com/sesquicadaver/CAN-MCP/main/codimension_mcp/codimension_mcp/server.py "raw.githubusercontent.com"
[3]: https://raw.githubusercontent.com/sesquicadaver/CAN-MCP/main/codimension_mcp/codimension_mcp/catalog.py "raw.githubusercontent.com"
[4]: https://raw.githubusercontent.com/sesquicadaver/CAN-MCP/main/codimension_core/codimension_core/graph_ir.py "raw.githubusercontent.com"
[5]: https://raw.githubusercontent.com/sesquicadaver/CAN-MCP/main/codimension_core/codimension_core/symbols.py "raw.githubusercontent.com"
[6]: https://raw.githubusercontent.com/sesquicadaver/CAN-MCP/main/codimension_core/codimension_core/callgraph.py "raw.githubusercontent.com"
[7]: https://raw.githubusercontent.com/sesquicadaver/CAN-MCP/main/codimension_core/codimension_core/imports.py "raw.githubusercontent.com"
[8]: https://raw.githubusercontent.com/sesquicadaver/CAN-MCP/main/codimension_mcp/codimension_mcp/tools.py "raw.githubusercontent.com"
[9]: https://raw.githubusercontent.com/sesquicadaver/CAN-MCP/main/pyproject.toml "raw.githubusercontent.com"
