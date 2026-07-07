# Living Specification: CAN-MCP

> **Languages:** [English](../en/plugins/living-specification.md) · [Українська](../uk/plugins/living-specification.md)

**Версія:** 2.0  
**Оновлено:** 2026-07

Матриця «модуль → тести → CI». Оновлюється при extraction з [CODIMENSION-CORE-MAP.md](../CODIMENSION-CORE-MAP.md).

---

## 1. Матриця модуль → тести

| Модуль | Тести |
| ------ | ----- |
| **codimension_core.project** | tests/test_codimension_core.py, test_codimension_core_cache.py |
| **codimension_core.symbols / brief_ast** | test_codimension_core_brief_ast.py, test_codimension_core_symbol_ids.py |
| **codimension_core.paths / symbol_registry** | test_codimension_core_paths.py, test_codimension_core_symbol_ids.py |
| **codimension_core.imports / deps / ImportResolver** | test_codimension_core_imports.py, test_codimension_core_imports_concurrent.py, test_codimension_core_imports_subprocess.py, test_codimension_core_deps.py |
| **codimension_core.dependency_graph (import kind)** | test_codimension_core.py, test_codimension_core_dependency_import_kind.py |
| **codimension_core.callgraph / impact / jedi_bridge** | test_codimension_core.py, test_codimension_core_impact.py, test_codimension_core_callgraph_semantic.py, test_codimension_core_jedi_callgraph.py, test_codimension_core_semantic_fixtures.py |
| **codimension_core.cfg / flow_ast** | test_codimension_core_flow_ast.py |
| **codimension_core.capabilities / optional deps** | test_codimension_core_capabilities.py |
| **codimension_core.analyzer** | test_codimension_core_analyzer.py |
| **codimension_core.encoding_utils** | test_codimension_core_encoding_utils.py |
| **codimension_core.file_io** | test_codimension_core_file_io.py |
| **codimension_core.venvutils** | test_codimension_core_venvutils.py |
| **codimension_core.graph_*** | test_codimension_core_graph_layout.py, test_codimension_core_graph_render.py, test_codimension_core_graph_ir_contract.py, test_codimension_core_graph_ir_v2.py |
| **codimension_core.import_diagram** | test_codimension_core_import_diagram.py |
| **codimension_core.summaries / explain / reverse_index / usages** | test_codimension_core_summaries.py, test_codimension_core_explain.py, test_codimension_core_reverse_index.py, test_codimension_core_usages.py |
| **codimension_mcp tools/resources** | test_codimension_mcp.py, test_codimension_mcp_workspace.py, test_codimension_mcp_path_security.py, test_codimension_mcp_symbol_resource.py, test_codimension_mcp_cfg_resources.py, test_codimension_mcp_impact_resources.py |
| **codimension_mcp prompts** | test_codimension_mcp.py, test_codimension_mcp_prompts_v2.py |
| **codimension_mcp catalog** | test_codimension_mcp_catalog.py + scripts/verify-mcp-catalog.sh |
| **Bootstrap / CI scripts** | scripts/dev-setup.sh, scripts/test-analysis.sh, scripts/verify-mcp-catalog.sh, scripts/verify-vscode.sh, scripts/check-anti-stub.sh |
| **Cursor MCP HOWTO** | doc/en/MCP-CURSOR-HOWTO.md, doc/uk/MCP-CURSOR-HOWTO.md |
| **VS Code extension** | codimension-vscode (npm run compile) |

---

## 2. CI

| Перевірка | Команда |
| --------- | ------- |
| Ruff | `ruff check codimension_core codimension_mcp` |
| Mypy | `mypy codimension_core` (`ignore_missing_imports=false`, stubs in `codimension_core/stubs/`) |
| Pytest | `pytest tests/` |
| MCP catalog | `./scripts/verify-mcp-catalog.sh` |
| VS Code compile | `./scripts/verify-vscode.sh` |
| Anti-stub grep | `./scripts/check-anti-stub.sh` (`ENFORCE=1` in CI / local gate) |
| pip-audit | `pip-audit -r requirements-dev.txt` |
| Local gate | `./scripts/test-analysis.sh` |

---

## 3. Оновлення

При extraction або новому MCP tool:

1. Оновити [CODIMENSION-CORE-MAP.md](../CODIMENSION-CORE-MAP.md).
2. Додати/оновити рядок у розд. 1.
3. Запустити `./scripts/test-analysis.sh`.
