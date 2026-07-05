# Carantine

Тимчасове сховище коду, який **не входить у MCP / codimension_core**, але ще потрібен як довідник під час extraction.

## Правила

1. Перед видаленням з `codimension/` — **спочатку** копіювати сюди.
2. Після повного від’єднання IDE від архівного коду — **видалити** відповідний файл з `Carantine/`.
3. Не імпортувати з `Carantine/` у production-код (IDE, core, MCP).

## Зміст

| Шлях | Дата | Причина |
| ---- | ---- | ------- |
| `codimension/utils/importutils_legacy.py` | 2026-07-05 | Повна IDE-версія до extraction у `codimension_core.imports` |
| `codimension/analysis/ierrors_legacy.py` | 2026-07-05 | pyflakes/radon до extraction у `codimension_core.analyzer` |
