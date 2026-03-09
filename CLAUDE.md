# CLAUDE.md — Инструкция для ИИ-агента

> PRD.md — требования. CLAUDE.md — реализация. ARCHITECTURE.md — решения, статус, бэклог.

---

## 1. Проект

**Home Shop List** — мобильное веб-приложение для общего списка покупок с WebSocket-синхронизацией.

---

## 2. Как запустить

```bash
source .venv2/bin/activate   # Python 3.12 (не .venv/ — там Python 3.6)
redis-cli ping               # PONG
python manage.py runserver
pytest --no-cov -q           # Python тесты
npm test                     # JS тесты
python manage.py loaddata fixtures/units.json
```

---

## 3. Стек

| Слой | Технология |
|------|------------|
| Backend | Django 4.2, Python 3.12 |
| WebSocket | Django Channels 4 + Daphne |
| Channel layer | Redis 7+ |
| БД | SQLite (dev) / PostgreSQL (prod) |
| Config | python-decouple (`.env`) |
| Frontend | Vanilla JS ES6+, Bootstrap 5 |
| Static | Whitenoise 6 |
| Тесты | pytest-django, pytest-asyncio, Jest |
| Линтеры | Ruff, ESLint |
| Деплой | Docker, docker-compose, GitHub Actions |

---

## 4. Структура

```
config/      — settings.py, urls.py, asgi.py
apps/users/  — User (AbstractUser), login/logout
apps/shop/   — Category, Purchase, UoM; все API; consumers.py, serializers.py, routing.py
templates/   — base.html, shop/view.html, shop/edit.html, users/login.html
static/js/   — ui.js, websocket.js, utils.js (window.shopUtils)
tests/       — test_models, test_api, test_views, test_consumers, test_serializers
tests/js/    — ui.test.js, websocket.test.js
```

---

## 5. Соглашения

- Python: `PascalCase` классы, `snake_case` остальное
- Коммиты: Conventional Commits (`feat:`, `fix:`, `refactor:`, `chore:`, `docs:`, `test:`)
- Язык UI: только русский
- API: REST без DRF, `JsonResponse`
- Пользователи: только через `createsuperuser` / `/admin`
- **Без новых зависимостей** без явного ОК
- **TDD обязателен:** баг — сначала красный тест, потом фикс (`/fix-bug`); фича — сначала тесты, потом реализация (`/new-feature`)
- **Технический долг:** находки ревью вне скопа с приоритетом Medium/High фиксируются в `ARCHITECTURE.md → Технический долг` (автоматически в Фазе 3 pre-push-review)

---

## 6. API endpoints

| Метод | URL | Действие |
|-------|-----|----------|
| GET | `/` | Просмотр (only is_need_to_buy=True) |
| GET | `/edit/` | Редактирование (все товары) |
| GET | `/login/` | Форма входа |
| POST | `/api/categories/` | Создать + каскадный сдвиг order |
| PATCH/DELETE | `/api/categories/<pk>/` | Редактировать / удалить |
| POST | `/api/purchases/` | Создать |
| PATCH/DELETE | `/api/purchases/<pk>/` | Редактировать / удалить |
| PATCH | `/api/purchases/<pk>/toggle/` | Переключить is_need_to_buy |
| WS | `ws/shop/` | WebSocket (только авторизованные) |

Все endpoints → `@login_required` → 302 на `/login/`.

---

## 7. WebSocket

`WS_GROUP = 'shop'` в `consumers.py`. `_broadcast(event_type, payload)` в `views.py`.

```json
{ "type": "purchase.created",  "purchase": {...} }
{ "type": "purchase.updated",  "purchase": {...} }
{ "type": "purchase.deleted",  "purchase_id": 1, "category_id": 5 }
{ "type": "category.created",  "category": {...} }
{ "type": "category.updated",  "category": {...} }
{ "type": "category.deleted",  "category_id": 7 }
```

---

## 8. Модели

**Category:** `order` (1=высший), `create_with_order_shift(name, order)`, `update_with_order_shift(name, order)`, QuerySet: `with_active_purchases()`, `with_all_purchases()`

**Purchase:** `is_need_to_buy=True` default, сортировка `[category__order, name]`, `set_need_to_buy(value)`, `update_fields(name, qty, unit)`

**UnitOfMeasurement:** `on_delete=PROTECT`, данные: `fixtures/units.json`

---

## 9. Тесты

```bash
pytest --no-cov -q            # 98 Python тестов
pytest tests/test_api.py -v   # конкретный файл
pytest -k "toggle"            # по имени
npm test                      # 50 JS тестов
```

Фикстуры (`tests/conftest.py`): `user`, `auth_client`, `unit`, `category`, `purchase`.

---

## → ARCHITECTURE.md

Архитектурные решения, статус фич, бэклог: **[ARCHITECTURE.md](ARCHITECTURE.md)**

Обновляй перед новой фичей. Проверяется автоматически в pre-push-review (Фаза 6).
