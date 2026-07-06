# Living Specification: Плагіни Codimension

<!-- markdownlint-disable MD060 -->

**Версія:** 1.0  
**Дата:** 2025-03  
**Джерело:** [plugins-implementation-plan.md](plugins-implementation-plan.md)

Матриця відповідності «ТЗ → модуль → тести». Оновлюється при кожній зміні плагінів.

---

## 1. Матриця ТЗ → модуль → тести

| ТЗ (план) | Модуль | Файли | Тести |
| --------- | ------ | ----- | ----- |
| **Фаза 1: Coverage** | cdmplugins.coverage | coverage.cdmp, __init__.py, coveragedriver.py, coverageresultviewer.py | Smoke: Run with coverage (Ctrl+Shift+C), вкладка результатів |
| **Фаза 2: Bandit** | cdmplugins.bandit | bandit.cdmp, __init__.py, banditdriver.py (LintDriverBase), banditresultviewer.py | Smoke: Run bandit (Ctrl+Shift+B); unit: tests/test_lint_drivers.py |
| **Фаза 3: pip-audit** | cdmplugins.pipaudit | pipaudit.cdmp, __init__.py, pipauditdriver.py, pipauditresultviewer.py | Smoke: Audit dependencies (Ctrl+Shift+A), вкладка CVE |
| **Фаза 4: Ruff format** | cdmplugins.ruffformat | ruffformat.cdmp, __init__.py, ruffformatdriver.py, ruffformatconfig.py | Smoke: Format (Ctrl+Shift+F), format-on-save (config) |
| **Фаза 5: TODO panel** | cdmplugins.todopanel | todopanel.cdmp, __init__.py, todopaneldriver.py, todopanelviewer.py, todoscanner.py | Smoke: Scan TODO (Ctrl+Shift+O), unit: tests/test_todoscanner.py |
| **Референс: Ruff** | cdmplugins.ruff | ruff.cdmp, __init__.py, ruffdriver.py (LintDriverBase), ruffresultviewer.py | Smoke: Run ruff (Ctrl+Shift+R); unit: tests/test_lint_drivers.py |
| **Референс: Mypy** | cdmplugins.mypy | mypy.cdmp, __init__.py, mypydriver.py (LintDriverBase), mypyresultviewer.py | Smoke: Run mypy (Ctrl+Shift+M); unit: tests/test_lint_drivers.py |
| **Референс: Pytest** | cdmplugins.pytest | pytest.cdmp, __init__.py, pytestdriver.py, pytestresultviewer.py | Smoke: Run pytest (Ctrl+Shift+T) |
| **Базовий клас** | cdmplugins.lintdriverbase | lintdriverbase.py | Використовується ruff, bandit, mypy |
| **Git VCS** | cdmplugins.git | git.cdmp, __init__.py, gitdriver.py, gitstatusparser.py, gitdialogs.py, gitconfig.py, githubapi.py | Smoke: status, Create PR, View PRs; unit: tests/test_gitstatusparser.py |
| **Flow AST fallback** | codimension.parsers.flow_ast | flow_ast.py | unit: tests/test_flow_ast.py |
| **Binary hexdump** | codimension.utils.binfiles | binfiles.py | unit: tests/test_binfiles.py |
| **Markdown (mistune 3)** | codimension.utils.md | md.py | unit: tests/test_md.py |
| **FS smart zoom** | codimension.editor.flowuiwidget | flowuiwidget.py | unit: tests/test_flowuiwidget.py |
| **Debugger watchpoints** | codimension.debugger | wputils.py, editwatchpoint.py, server.py, wpointviewer.py | unit: tests/test_watchpoints.py |
| **Greenlet debugger** | codimension.debugger.client | threadextension_cdm_dbg.py, threadutils_cdm_dbg.py | unit: tests/test_greenlet_trace.py |
| **Occurrences search redo** | codimension.search | occurrencesprovider.py, searchresultsviewer.py | unit: tests/test_occurrencesprovider.py |
| **codimension_core scaffold** | codimension_core | project.py, symbols.py, cache.py, graph_ir.py, dependency_graph.py, cfg.py | unit: tests/test_codimension_core.py |
| **codimension_core imports** | codimension_core.imports | imports.py | unit: tests/test_codimension_core_imports.py |
| **codimension_core callgraph** | codimension_core.callgraph | callgraph.py | unit: tests/test_codimension_core.py |
| **codimension_core deps classification** | codimension_core.imports | collect_import_resolutions_classified + frozen stdlib | unit: tests/test_codimension_core_deps.py |
| **codimension_core analyzer** | codimension_core.analyzer | get_buffer_errors, analyze_file_diagnostics, analyze_dead_code | unit: tests/test_codimension_core_analyzer.py |
| **codimension_core explain** | codimension_core.explain | explain_symbol | unit: tests/test_codimension_core_explain.py |
| **MCP get_diagnostics** | codimension_mcp | get_diagnostics tool | Smoke: MCP tool call |
| **MCP find_dead_code** | codimension_mcp | find_dead_code tool | Smoke: MCP tool call |
| **codimension_core impact** | codimension_core.callgraph | impact_analysis transitive | unit: tests/test_codimension_core_impact.py |
| **MCP resources** | codimension_mcp.resources | codimension:// URIs | unit: tests/test_codimension_mcp.py |
| **codimension_core summaries** | codimension_core.summaries | build_dependency_summary, build_symbol_summary | unit: tests/test_codimension_core_summaries.py |
| **MCP catalog** | codimension_mcp.catalog | codimension://catalog, list_mcp_catalog | unit: tests/test_codimension_mcp_catalog.py |
| **MCP assess_change_impact prompt** | codimension_mcp.prompts | blast-radius workflow | unit: tests/test_codimension_mcp.py |
| **Cursor MCP sample** | .cursor/mcp.json.example | install-cursor-mcp.sh | Manual |
| **MCP symbol summary** | codimension_mcp | get_symbol_summary tool + codimension://symbols/summary | unit: tests/test_codimension_mcp.py |
| **VS Code MCP config** | codimension-vscode/mcpConfig.ts | copyMcpConfig, showMcpResources | CI: npm run compile |
| **Legacy IDE policy** | doc/LEGACY-IDE.md | maintenance mode for codimension/ + cdmplugins | Review on IDE changes |
| **MCP diagram WebView** | codimension_mcp.diagrams | render_diagram, codimension://diagram/* | unit: tests/test_codimension_mcp.py |
| **codimension_core incremental cache** | codimension_core.analysis_cache | selective import/call/reverse invalidation + CFG | unit: tests/test_codimension_core_cache.py |
| **codimension_core brief_ast** | codimension_core.brief_ast | getBriefModuleInfoFromMemory/File | unit: tests/test_codimension_core_brief_ast.py |
| **codimension_core requirements scan** | collect_unresolved_packages / generate_requirements_from_project | headless pip hint source | unit: tests/test_codimension_core_imports.py |
| **codimension_core flow_ast** | codimension_core.flow_ast | getControlFlowFromMemory/File | unit: tests/test_codimension_core_flow_ast.py |
| **codimension_core mypy** | codimension_core + parser_types | Protocol types for brief AST | CI: mypy codimension_core |
| **codimension_core import diagram** | codimension_core.import_diagram | build_import_diagram_model, add_single_file_to_model | unit: tests/test_codimension_core_import_diagram.py |
| **codimension_core graph layout** | codimension_core.graph_layout | layout_graph_from_dot, plain dot parser | unit: tests/test_codimension_core_graph_layout.py |
| **IDE plaindotparser wrapper** | codimension.diagram.plaindotparser | re-export from codimension_core.graph_layout | Smoke: import diagram dialog |
| **IDE import diagram wrapper** | codimension.diagram.importsdgm | core model + PyQt scene | Smoke: imports diagram dialog |
| **VS Code diagram WebView** | codimension-vscode | codimension.showDiagram | Smoke: open `.codimension/diagrams/*.html` |
| **MCP import diagram render parity** | codimension_mcp.diagrams | render_diagram import + graphviz payload | unit: tests/test_codimension_mcp.py |
| **GitHub Actions CI (merge gate)** | .github/workflows/ci.yml | analysis + security | CI on push/PR |
| **GitHub Actions CI (legacy UI)** | .github/workflows/ci-legacy-ui.yml | ide lint + vscode compile (path filter) | CI on UI paths / manual |
| **Local analysis gate** | scripts/test-analysis.sh | parity with ci.yml analysis job | Manual |
| **UI artifact cleanup** | scripts/clean-ui-artifacts.sh | doc/www, VisioDiagrams removed | Manual: `./scripts/clean-ui-artifacts.sh` |
| **CI pip-audit** | .github/workflows/ci.yml `security` job | requirements.txt CVE scan | CI on push/PR |
| **IDE core_bridge** | codimension.analysis.core_bridge | core_project_from_ide | Review: thin wrapper PR |
| **IDE notused wrapper** | codimension.analysis.notused | run_vulture via core | Smoke: dead code dialog |
| **codimension_mcp scaffold** | codimension_mcp | server.py, tools.py, serializers.py | unit: tests/test_codimension_mcp.py |
| **Module extraction map** | doc | CODIMENSION-CORE-MAP.md | Review on each extraction PR |

---

## 2. CI-перевірки

| Перевірка | Команда | Джерело |
| --------- | ------- | ------- |
| Ruff (core + mcp) | `ruff check codimension_core codimension_mcp` | .github/workflows/ci.yml `analysis` |
| Mypy (core) | `mypy codimension_core` | .github/workflows/ci.yml `analysis` |
| Pytest (headless, full suite) | `pytest tests/ -m "not pyqt"` | .github/workflows/ci.yml `analysis` |
| Pytest (PyQt legacy) | `pytest tests/ -m pyqt` | .github/workflows/ci-legacy-ui.yml `ide` |
| Local analysis gate | `./scripts/test-analysis.sh` | scripts/test-analysis.sh |
| Ruff (IDE) | `ruff check codimension cdmplugins` | .github/workflows/ci-legacy-ui.yml `ide` |
| Mypy (IDE) | `mypy codimension cdmplugins` | .github/workflows/ci-legacy-ui.yml `ide` |
| pip-audit | `pip-audit -r requirements.txt` | .github/workflows/ci.yml `security` |
| VS Code compile | `npm ci && npm run compile` | .github/workflows/ci-legacy-ui.yml `vscode` |

---

## 3. Відповідність плану

- [x] Усі плагіни в `cdmplugins/`
- [x] setup.py оновлено
- [x] requirements.txt оновлено
- [x] Документація оновлена (plugins.md, living-specification.md)
- [x] CI merge gate проходить (analysis, security/pip-audit)
- [x] Legacy UI CI окремо (ci-legacy-ui.yml)
- [x] Smoke-тест: codimension запускається

---

## 4. Оновлення

При додаванні/зміні плагіна:

1. Додати рядок у матрицю (розд. 1).
2. Оновити setup.py (getPackages, package_data).
3. Оновити requirements.txt (якщо нова залежність).
4. Додати посилання на цей документ у MR.
