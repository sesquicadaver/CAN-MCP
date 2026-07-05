# Carantine

Тимчасове сховище коду, який **не входить у MCP / codimension_core**, але ще потрібен як довідник під час extraction.

## Правила

1. Перед видаленням з `codimension/` — **спочатку** копіювати сюди.
2. Після повного від’єднання IDE від архівного коду — **видалити** відповідний файл з `Carantine/`.
3. Не імпортувати з `Carantine/` у production-код (IDE, core, MCP).

## Статус (etapa 9)

Усі модулі extraction etapas 1–5 повністю делегують у `codimension_core`; архівні копії **видалено**:

| Модуль IDE | Core API | Carantine |
| ---------- | -------- | --------- |
| `importutils.py` | `codimension_core.imports` | видалено |
| `depsdiagram.py` | `collect_import_resolutions_classified` | видалено |
| `ierrors.py` | `get_buffer_errors` | видалено |
| `notused.py` | `run_vulture`, exclude/config helpers | видалено |

Каталог залишається для майбутніх extraction (flow UI, importsdgm graphics тощо).

## Видалені UI-артефакти (2026-07-05)

З репозиторію CAN-MCP прибрано застарілі джерела, не потрібні для MCP/core:

| Шлях | Причина |
| ---- | ------- |
| `doc/www/` | Статичне дзеркало codimension.org (~32 MB) |
| `doc/VisioDiagrams/` | Visio-макети PyQt IDE (~2.5 MB) |

Скріншот IDE збережено в `doc/images/overview.png`. Локальні build-артефакти: `scripts/clean-ui-artifacts.sh`.

`codimension/analysis/core_bridge.py` — `core_project_from_ide()` для thin wrappers.
