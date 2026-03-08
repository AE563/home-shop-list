---
name: pre-push-review
description: Pre-push code review for Home Shop List. Runs linters (ruff, eslint), tests, and Django checks. Auto-fixes everything fixable. Commits fixes and pushes only when all checks pass. Invoke when the user says "push", "let's push", "code review before push", "давай запушим", "прогони линтеры" or similar.
---

# Pre-Push Review

Запускай этот процесс перед каждым `git push`. Порядок фиксированный — нарушать нельзя.

## Шаг 1 — Python: ruff (линтинг + форматирование)

```bash
.venv2/bin/ruff check apps/ tests/ --fix
.venv2/bin/ruff format apps/ tests/
```

- `--fix` автоматически устраняет всё исправимое (импорты, форматирование, устаревший синтаксис)
- Конфиг в `ruff.toml`: правила E, F, I, B, UP; миграции исключены
- Если после `--fix` остались ошибки — исправь их в коде вручную и повтори
- Покажи `git diff` пользователю: что именно изменилось

## Шаг 2 — JavaScript: eslint (линтинг)

```bash
npx eslint static/js/ tests/js/ --fix
```

- Конфиг в `eslint.config.js`: проверяет `no-undef`, `eqeqeq`, `no-eval`
- `--fix` устраняет автоисправимые проблемы
- Ошибки (errors) блокируют пуш, предупреждения (warnings) — нет
- Если ошибки остались — исправь в коде вручную

## Шаг 3 — Тесты

```bash
.venv2/bin/pytest --no-cov -q     # быстро, без отчёта покрытия
npm test                           # Jest
```

- Все тесты должны пройти (зелёные)
- Если тест красный — исправь код или тест до пуша
- Нельзя пушить с падающими тестами

## Шаг 4 — Django system check

```bash
.venv2/bin/python manage.py check
```

- Ожидаемый результат: `System check identified no issues (0 silenced)`
- Errors блокируют пуш, warnings — нет (но покажи пользователю)

## Шаг 5 — Коммит и пуш

Только если шаги 1–4 завершились без ошибок:

```bash
git status                          # показать что изменилось
git add <только релевантные файлы>  # НЕ git add -A
git diff --cached                   # показать пользователю staged diff
git commit -m "..."                 # коммит по Conventional Commits
git push
```

### Conventional Commits

```
feat:     новая функциональность
fix:      исправление бага
refactor: рефакторинг без изменения поведения
chore:    зависимости, конфиги, скрипты
test:     добавление/исправление тестов
docs:     документация
style:    только форматирование (lint fix)
```

## Правила

- **Стоп при ошибках линтера** — не пушить, пока не чисто
- **Авто-фикс без вопросов** — `--fix` применяй всегда на шагах 1 и 2
- **Показывай diff** — пользователь должен видеть что изменилось после авто-фикса
- **Стоп при красных тестах** — сначала исправь, потом пуш
- **Итоговый отчёт**: `✅ Все проверки прошли, пушу` или `❌ Стоп: [что именно не прошло]`

## Установка инструментов (если не установлены)

```bash
# Python
.venv2/bin/pip install "ruff>=0.4"

# JS
npm install    # eslint и globals уже в package.json
```
