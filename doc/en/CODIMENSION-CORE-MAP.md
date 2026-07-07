# Module Map: Codimension → codimension_core

**Languages:** [English](../en/CODIMENSION-CORE-MAP.md) | [Українська](../uk/CODIMENSION-CORE-MAP.md)

**Version:** 1.0  
**Date:** 2026-07-05  
**Strategy source:** [README.md](../../README.md) (CAN-MCP scope)

Traceability matrix: «Codimension file → codimension_core module → extraction status».

---

## 1. Target codimension_core structure

```text
codimension_core/
  project.py           — headless project, scan, exclusions
  analyzer.py          — lint, complexity, dead code, disasm
  symbols.py           — brief parse, symbol index, jedi scope
  imports.py           — resolve imports, requirements
  cfg.py               — control-flow AST, CML validation
  callgraph.py         — static call graph (NEW)
  dependency_graph.py  — import/deps graph → Graph IR
  cache.py             — incremental parse caches
  graph_ir.py          — stable JSON IR (nodes/edges, v2 default / v1 opt-out)
  paths.py             — resolve_project_path policy gate
  symbol_registry.py   — legacy symbol id aliases
  errors.py            — typed exceptions
```

---

## 1.1 Graph IR versions

| Version | Enable | Additional fields |
| ------- | ------ | ----------------- |
| **v2** (default) | — | `node.uri` (`codimension://symbol/...`), `edge.provenance` |
| **v1** (legacy) | `CODIMENSION_GRAPH_IR=1` | no top-level `uri` / `provenance`; only `node.extra` |

MCP resource: `codimension://symbol/{symbol_key}` — single symbol node from Graph IR.

v1 meta example:

```json
{
  "graph_ir_version": 2,
  "meta": {
    "kind": "call_graph",
    "schema_id": "codimension.graph.calls.v1",
    "capabilities": ["calls"],
    "project_root": "/path/to/project",
    "generated_at": "2026-07-07T06:30:00+00:00"
  }
}
```

v2 node example (opt-in):

```json
{
  "id": "pkg/mod.py:function:run",
  "type": "function",
  "uri": "codimension://symbol/pkg__path__mod.py__function__run",
  "extra": { "language": "py", "provenance": "ast", "confidence": 0.7 }
}
```

---

## 1.2 Import resolution isolation

`ImportResolver` (`imports.py`) — context manager + `threading.RLock` to isolate side effects of `importlib.util.find_spec`:

| State | Action on `__enter__` | Action on `__exit__` |
| ----- | --------------------- | -------------------- |
| `sys.path` | save → override | restore |
| `sys.path_importer_cache` | snapshot keys | delete new keys |
| `sys.modules` | snapshot keys | delete new keys |

### Call sites (→ `get_import_resolutions` / `resolve_imports`)

| Module | Function | Purpose |
| ------ | -------- | ------- |
| `imports.py` | `get_import_resolutions` | core resolver |
| `imports.py` | `resolve_imports`, `resolve_imports_for_file` | legacy tuple / Graph IR |
| `imports.py` | `collect_import_resolutions_classified` | classified buckets |
| `imports.py` | `collect_unresolved_packages` | requirements scan |
| `dependency_graph.py` | `_build_resolved_import_graph` | import graph edges |
| `import_diagram.py` | diagram builder | IDE-less import diagram |
| `explain.py` | file explain | imports section |
| `summaries.py` | `build_symbol_summary` | classified imports in summary |

**Subprocess isolation (ROAD-4.3):** `CODIMENSION_IMPORT_ISOLATION=subprocess` runs resolution in project venv via `import_isolation_worker`; default is in-process `ImportResolver`.

### Optional analysis dependencies (`capabilities.py`)

| Feature | Packages | Missing response |
| ------- | -------- | ---------------- |
| `diagnostics` | pyflakes, radon | Graph IR `meta.status=partial`, `meta.missing=[...]` |
| `find_usages` | jedi | Graph IR partial meta |
| `dead_code` | vulture | Graph IR partial meta |

Install: `pip install -e "./codimension_core[analysis]"`. MCP depends on `codimension-core[analysis]`.

**Mypy (ROAD-5.3):** `ignore_missing_imports = false`; local stubs in `codimension_core/stubs/` for `jedi` and `radon`; `types-pyflakes` in `[analysis]` extra.

---

## 2. project.py

| Codimension file | Classes / functions | PyQt / GlobalData | Action |
| ---------------- | ------------------- | ----------------- | ------ |
| `codimension/utils/project.py` | `CodimensionProject`, `getProjectProperties`, `__scanDir`, `getImportDirsAsAbsolutePaths`, `getExcludeFromAnalysisAsAbsolutePaths`, `isProjectFile` | QObject, pyqtSignal, Watcher | **Split:** core dataclass without signals/watcher |
| `codimension/utils/venvutils.py` | `resolveVenvToPython`, `getProjectVenvDir` | — | ✅ 0.20.0 thin wrapper → `codimension_core.venvutils` |
| `codimension/utils/run.py` (partial) | `getProjectPythonPath`, `getVenvSitePackages` | — | **Extract** subprocess helpers |
| `codimension/utils/fileutils.py` (partial) | `getFileContent`, `loadJSON`, `saveJSON`, `saveToFile` | QImageReader, Qutepart in icons | ✅ 0.20.1 I/O → `codimension_core.file_io`; mime/icons stay in IDE |
| `codimension/utils/encoding.py` (partial) | `getCodingFromText`, `detectFileEncodingToRead`, `readEncodedFile`, `decode` | editor param | ✅ 0.20.4 `decode_content` + DRY project/IDE fallbacks; ✅ 0.20.3 `read_encoded_bytes` |
| `codimension/utils/globals.py` (partial) | `getSubdirs` | — | **Optional** |

**Do not migrate:** `fsenv.py`, `searchenv.py`, `flowgroups.py`, `debugenv.py`, `runparamscache.py`, `watcher.py`.

**Scaffold (0.1.0):** `Project.open()`, scan `.py`, venv + `excludeFromAnalysis` from `.cdm3`.

**Extraction (0.2.0):** `build_import_search_paths`, `get_python_executable`, `get_site_packages`.

---

## 3. symbols.py

| Codimension file | Classes / functions | PyQt / GlobalData | Action |
| ---------------- | ------------------- | ----------------- | ------ |
| `codimension/parsers/brief_ast.py` | thin wrapper → `codimension_core.brief_ast` | — | ✅ 0.15.0 vendored in core |
| `codimension/parsers/__init__.py` | cdmpyparser/cdmcfparser fallback | — | **Import side-effect** |
| `codimension/autocomplete/bufferutils.py` | `TextCursorContext`, `getContext`, `_IdentifyScope` | lazy `ui.viewitems` | **Extract** scope without viewitems |
| `codimension/autocomplete/completelists.py` | `getJediProject`, `getDefinitions`, `getOccurrences` | QDir, GlobalData | **Extract** jedi with injectable project |
| `codimension/search/occurrencesprovider.py` | `build_occurrence_results` | GlobalData in provider | **Extract** function |
| `codimension/utils/globals.py` (partial) | `getModInfo`, `getFileLineDocstring` | GlobalData | **Replace** cache API |
| `codimension/ui/findname.py` (logic) | `FindNameModel.__populateInfo` | Qt + GlobalData | **Extract** symbol index builder |

**Do not migrate:** `ui/classesbrowsermodel.py`, `ui/functionsbrowsermodel.py`, `ui/outline.py`, `editor/astview.py`.

**Scaffold (0.1.0):** `analyze_file()`, `get_symbols()`, `SymbolRecord` → Graph IR nodes.

---

## 4. imports.py

| Codimension file | Classes / functions | PyQt / GlobalData | Action |
| ---------------- | ------------------- | ----------------- | ------ |
| `codimension/utils/importutils.py` | thin wrapper → `codimension_core.imports` | QApplication.processEvents, GlobalData | ✅ 0.15.0 generateRequirements → core |
| `codimension/diagram/depsdiagram.py` | `collectImportResolutions`, `__isLocalOrProject`, `__isSystem` | GlobalData.project | **Extract** classification |

**Do not migrate:** GUI parts of `importsdgm.py`.

**Scaffold (0.1.0):** stub + docstring; MVP import edges from brief parser (no resolution).

**Extraction (0.2.0):** full `importutils` headless API + IDE wrapper.

---

## 5. cfg.py

| Codimension file | Classes / functions | PyQt / GlobalData | Action |
| ---------------- | ------------------- | ----------------- | ------ |
| `codimension/parsers/flow_ast.py` | thin wrapper → `codimension_core.flow_ast` | — | ✅ 0.16.0 vendored in core |
| `codimension/flowui/cml.py` | `CMLVersion.validateCMLComments`, `validateCMLList` | buildColor via colorfont | **Extract** validation without color |

**Do not migrate:** `flowui/vcanvas.py`, `flowui/*items*.py`, `flowui/routines.py` (QPainterPath).

**Scaffold (0.1.0):** `get_control_flow(function_id)` → Graph IR subgraph.

---

## 6. dependency_graph.py

| Codimension file | Classes / functions | PyQt / GlobalData | Action |
| ---------------- | ------------------- | ----------------- | ------ |
| `codimension/diagram/importsdgm.py` (data) | `DgmModule`, `DgmConnection`, `ImportDiagramModel`, `__addSingleFileToDataModel` | QDialog, GlobalData | **Split:** model + builder → core |
| `codimension/diagram/plaindotparser.py` | thin wrapper → `codimension_core.graph_layout` | subprocess dot | ✅ 0.14.0 layout in core |
| `codimension/diagram/depsdiagram.py` | `collectImportResolutions` | — | see imports.py |

**Do not migrate:** `importsdgmgraphics.py`, `depsitems.py`, `depsvcanvas.py`.

**Scaffold (0.1.0):** `build_import_graph()` — `imports` edges between project files.

---

## 7. callgraph.py

| What exists now | Where | Status |
| --------------- | ----- | ------ |
| Runtime call graph | `profiling/profgraph.py` (gprof2dot + pstats) | Not static analysis |
| Debugger call trace | `debugger/calltraceviewer.py` | Runtime debug |

**Grep:** `callgraph`, `impact analysis` — **0 matches** in Codimension.

**Scaffold (0.1.0):** stub `NotImplementedError`; greenfield AST-based builder.

**Extraction (0.2.0):** AST static call graph, `find_callers/callees`, MVP `impact_analysis`.

---

## 8. analyzer.py

| Codimension file | Classes / functions | PyQt / GlobalData | Action |
| ---------------- | ------------------- | ----------------- | ------ |
| `codimension/analysis/ierrors.py` | `getBufferErrors` (pyflakes + radon) | — | ✅ thin wrapper → `analyzer` |
| `codimension/analysis/disasm.py` | `disassemble*`, marshal helpers | — | **Copy** |
| `codimension/analysis/notused.py` | vulture runner | QDialog, GlobalData | ✅ thin wrapper → `analyzer` |
| `codimension/analysis/core_bridge.py` | `core_project_from_ide` | GlobalData | ✅ IDE bridge |
| `codimension/utils/astutils.py` | `parseSourceToAST` | — | ✅ thin wrapper → `codimension_core.astutils` |
| `codimension/search/searchsupport.py` | `Match`, `ItemToSearchIn`, regex search | GlobalData buffers | **Extract** text search |

**Status (0.8.0):** analyzer extracted; IDE thin wrappers via `core_bridge`.

---

## 9. cache.py

| Codimension file | Classes / functions | PyQt / GlobalData | Action |
| ---------------- | ------------------- | ----------------- | ------ |
| `codimension/utils/briefmodinfocache.py` | `BriefModuleInfoCache.get/remove/clear` | — | ✅ thin wrapper → `codimension_core.cache.ModuleInfoCache` |

**Do not migrate:** `pixmapcache.py`, `webresourcecache.py`, `plantumlcache.py`.

**Scaffold (0.1.0):** `ModuleInfoCache` (mtime-based, as in IDE).

---

## 10. GUI-only — do NOT migrate

| Directory | Reason |
| --------- | ------ |
| `codimension/ui/*` | PyQt widgets, browsers, dialogs |
| `codimension/editor/*` | Text editor + flow UI widgets |
| `codimension/debugger/*` | Runtime debugger |
| `codimension/plugins/*`, `cdmplugins/*` | Plugin UI shells |
| `codimension/diagram/*graphics*` | QGraphicsScene items |
| `codimension/flowui/*` (except cml validation) | Canvas, painters |
| `codimension/profiling/profwidget.py`, `proftable.py` | Qt profiling UI |

---

## 11. codimension_mcp → tools mapping

| MCP tool | codimension_core API | Status |
| -------- | -------------------- | ------ |
| `open_project(path)` | `Project.open()` | ✅ MVP |
| `analyze_project()` | `Project.analyze_all()` | ✅ MVP |
| `invalidate_file(path)` | `Project.invalidate_file()` | ✅ 0.22.0 MCP |
| **Workspace lock** | `WorkspaceState.workspace_lock()` on open/analyze/invalidate | ✅ 0.22.0 single-workspace |
| `analyze_file(path)` | `symbols.analyze_file()` | ✅ MVP |
| `get_project_tree()` | `Project.python_files()` | ✅ MVP |
| `get_symbols(path?)` | `symbols.get_symbols()` | ✅ MVP |
| `get_import_graph()` | `dependency_graph.build_import_graph()` | ✅ MVP |
| `get_call_graph(symbol?)` | `callgraph.build_call_graph()` | ✅ 0.2.0 |
| `get_control_flow(function_id)` | `cfg.get_control_flow()` | ✅ MVP |
| `find_callers(symbol)` | `callgraph.find_callers()` | ✅ 0.2.0 |
| `find_callees(symbol)` | `callgraph.find_callees()` | ✅ 0.2.0 |
| `find_usages(symbol)` | `symbols.find_usages()` | ✅ 0.3.0 |
| `get_diagnostics(path)` | `analyzer.analyze_file_diagnostics()` | ✅ 0.4.0 |
| `find_dead_code(path?)` | `analyzer.analyze_dead_code()` | ✅ 0.5.0 |
| `explain_symbol(symbol)` | `explain.explain_symbol()` — structured context | ✅ 0.5.0 MVP |
| `impact_analysis(path\|symbol)` | `callgraph.impact_analysis()` | ✅ 0.6.0 transitive |
| **MCP resources** | `codimension://workspace/status`, `graph/import`, `graph/call` | ✅ 0.2.0 |
| **MCP prompts** | `refactor_symbol`, `review_dead_code` | ✅ 0.2.0 |
| **Graph render** | `graph_render.graph_to_html/mermaid` | ✅ 0.7.0 |
| **Incremental cache** | `analysis_cache`, `Project.get_cache_stats` | selective import/call/reverse invalidation | ✅ 0.17.0 |
| **MCP get_cache_stats** | cache stats tool + `codimension://cache/stats` | ✅ 0.4.0 |
| **codimension_core disasm/astutils** | disasm.py, astutils.py, venvutils.py | unit: tests/test_codimension_core_disasm.py, test_codimension_core_astutils.py, test_codimension_core_venvutils.py |
| **codimension_core reverse index** | reverse_index.lookup_symbol | unit: tests/test_codimension_core_reverse_index.py |
| **codimension_core import diagram** | import_diagram model | unit: tests/test_codimension_core_import_diagram.py |
| **codimension_core graph layout** | graph_layout.py | unit: tests/test_codimension_core_graph_layout.py |
| **MCP get_import_diagram layout** | layout summary in tool payload | unit: tests/test_codimension_mcp.py |
| **MCP lookup_symbol** | reverse index tool | unit: tests/test_codimension_mcp.py |
| **codimension-vscode** | extension scaffold | Manual: npm run compile |
| **MCP render_diagram** | `.codimension/diagrams/*.html` WebView | ✅ 0.7.0 full import diagram model |
| `render_diagram(kind, target?)` | `import_diagram` Graph IR + Graphviz DOT in payload | ✅ 0.7.0 |

---

## 12. Recommended extraction order

1. `parsers/` + `briefmodinfocache` → `symbols.py` + `cache.py`
2. `flow_ast` + `cml` validation → `cfg.py`
3. `importutils` + `depsdiagram` → `imports.py`
4. `ImportDiagramModel` builder → `dependency_graph.py`
5. `ierrors`, `disasm`, vulture → `analyzer.py`
6. jedi + `bufferutils` → `symbols.py`
7. `project` scan/exclusions → `project.py`
8. **New** `callgraph.py` — static AST analysis

---

## 13. Package dependencies

```text
codimension (IDE, GPL v3)
    ↑ reuse parsers/utils (transitional)
codimension_core (headless, GPL v3)
    ↑
codimension_mcp (MCP server, GPL v3)
    ↑
Cursor / Claude / MCP host
```

---

## 14. Updates

When extracting a module:

1. Update the row in this table (status → Done).
2. Add a row in [living-specification.md](plugins/living-specification.md).
3. Add a contract test in `tests/test_codimension_core*.py`.
