# Legacy PyQt IDE

Каталоги `codimension/` та `cdmplugins/` — **legacy GUI IDE** оригінального Codimension. Активна розробка CAN-MCP зосереджена на headless-аналізі:

| Пакет | Роль | CI |
| ----- | ---- | -- |
| `codimension_core/` | Headless analysis engine | Merge gate (`ci.yml`) |
| `codimension_mcp/` | MCP server для AI-клієнтів | Merge gate |
| `codimension-vscode/` | VS Code extension (WebView) | `ci-legacy-ui.yml` |
| `codimension/` + `cdmplugins/` | PyQt IDE + плагіни | `ci-legacy-ui.yml` |

## Статус

- **Maintenance mode** — bugfix і thin wrappers над `codimension_core`, без нових GUI-фіч.
- Нові можливості аналізу додаються в `codimension_core` і експонуються через `codimension_mcp`.
- Повний запуск IDE потребує PyQt5: `pip install -r requirements.txt && pip install -e .`

## CI

- Merge gate не блокується відсутністю PyQt5.
- Тести з `@pytest.mark.pyqt` — у workflow [ci-legacy-ui.yml](../.github/workflows/ci-legacy-ui.yml).
- Headless unit-тести IDE-модулів (brief_ast, flow_ast, importutils тощо) — у merge gate через `pytest tests/ -m "not pyqt"`.

## Міграція

Див. [CODIMENSION-EVO.md](../CODIMENSION-EVO.md) та [doc/CODIMENSION-CORE-MAP.md](CODIMENSION-CORE-MAP.md).
