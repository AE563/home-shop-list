# /check — Быстрая проверка без пуша

Запускай параллельно:

```bash
# Линтеры
.venv2/bin/ruff check apps/ tests/ --fix
.venv2/bin/ruff format apps/ tests/
npx eslint static/js/ tests/js/ --fix

# Тесты
.venv2/bin/pytest --no-cov -q
npm test

# Django system check
.venv2/bin/python manage.py check
```

Покажи итог: что исправлено линтером (git diff), сколько тестов прошло, есть ли warnings Django.

Это не pre-push — коммит и пуш не делать.
