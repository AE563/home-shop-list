# CLAUDE.md — Инструкция для ИИ-агента

> Этот файл читается агентом перед началом любой задачи. PRD.md — источник правды по требованиям. CLAUDE.md — источник правды по реализации.

---

## 1. Проект

**Home Shop List** — мобильное веб-приложение для общего списка покупок семьи с WebSocket-синхронизацией в реальном времени.

Полные требования: `PRD.md`.

---

## 2. Как запустить

```bash
# Активировать виртуальное окружение
source .venv2/bin/activate   # Python 3.12 (.venv/ — устаревший Python 3.6, не использовать)

# Убедиться, что Redis запущен
redis-cli ping   # должен вернуть PONG

# Запустить сервер (ASGI через Daphne — запускается автоматически через Django)
python manage.py runserver

# Запустить тесты
pytest           # Python тесты (101 passed, coverage 93.62%)
npm test         # JS тесты (50 passed, Jest)

# Загрузить начальные данные (единицы измерения)
python manage.py loaddata fixtures/units.json
```

---

## 3. Стек

| Слой | Технология |
|------|------------|
| Backend | Django 4.2, Python 3.12 |
| WebSocket | Django Channels 4 + Daphne (ASGI) |
| Channel layer | Redis 7+ |
| БД (dev) | SQLite (`db.sqlite3`) |
| БД (prod) | PostgreSQL (psycopg2-binary) |
| Config | python-decouple (`.env`) |
| Frontend | Vanilla JS (ES6+), Bootstrap 5 |
| Тесты Python | pytest-django, pytest-asyncio |
| Тесты JS | Jest + jsdom |
| Линтеры | Ruff (Python), ESLint (JS) |
| Static files | Whitenoise 6 (сжатие + отдача статики) |
| Деплой | Docker, docker-compose, GitHub Actions CI |

**Важно:** Никаких новых зависимостей без явного разрешения пользователя.

---

## 4. Структура проекта

```
config/          — settings.py, urls.py, asgi.py, wsgi.py
apps/
  users/         — модель User (AbstractUser), login/logout views
  shop/          — Category, Purchase, UnitOfMeasurement; все API; consumers.py
                   serializers.py — сериализаторы моделей
                   routing.py — WebSocket URL-роутинг (ws/shop/ → ShopConsumer)
  core/          — utils.py (вспомогательные функции, cascade_shift — dead code)
templates/
  base.html      — шапка, переключатель страниц, accordion-кнопки
  shop/view.html — страница просмотра (/)
  shop/edit.html — страница редактирования (/edit/)
  users/login.html
static/
  css/main.css
  js/
    ui.js          — DOM: accordion, CRUD-формы, AJAX-запросы
    websocket.js   — WebSocket клиент, обновление DOM при WS-событиях
    utils.js       — window.shopUtils = { esc, fmtQty } (shared между ui и ws)
tests/
  conftest.py              — фикстуры: user, auth_client, unit, category, purchase
  test_models.py           — unit-тесты моделей
  test_api.py              — тесты API endpoints
  test_views.py            — тесты страниц и авторизации
  test_consumers.py        — тесты WebSocket consumer + broadcast
  test_serializers.py      — тесты сериализаторов
  test_utils.py            — тесты утилит
  js/
    ui.test.js             — Jest тесты для ui.js
    websocket.test.js      — Jest тесты для websocket.js
  e2e/test_shopping_flow.py — Selenium (скелет, все тесты пропущены)
fixtures/units.json   — начальные данные UnitOfMeasurement
Dockerfile, docker-compose.yml, docker-compose.prod.yml
entrypoint.sh, deploy.sh   — CD: тесты → git push → ssh → docker up
requirements.txt, ruff.toml, eslint.config.js, package.json, pytest.ini
README.md, LICENSE
```

---

## 5. Ключевые соглашения

- **Python:** `PascalCase` для классов, `snake_case` для файлов и переменных
- **CSS:** `kebab-case`
- **Коммиты:** Conventional Commits (`feat:`, `fix:`, `refactor:`, `chore:`)
- **Язык UI:** только русский
- **API:** REST без DRF, ответы в JSON
- **Новые пользователи:** только через `createsuperuser` или `/admin`

---

## 6. API endpoints

| Метод | URL | Действие |
|-------|-----|----------|
| GET | `/` | Страница просмотра (только is_need_to_buy=True) |
| GET | `/edit/` | Страница редактирования (все товары) |
| GET | `/login/` | Форма входа |
| GET | `/logout/` | Выход |
| POST | `/api/categories/` | Создать категорию (+ каскадный сдвиг order) |
| PATCH | `/api/categories/<pk>/` | Редактировать категорию |
| DELETE | `/api/categories/<pk>/` | Удалить категорию (CASCADE на purchases) |
| POST | `/api/purchases/` | Создать товар |
| PATCH | `/api/purchases/<pk>/` | Редактировать товар |
| DELETE | `/api/purchases/<pk>/` | Удалить товар |
| PATCH | `/api/purchases/<pk>/toggle/` | Переключить is_need_to_buy |
| WS | `ws/shop/` | WebSocket (только авторизованные) |

Все endpoints требуют авторизации. Неавторизованный запрос → 302 на `/login/`.

---

## 7. WebSocket события

Сервер транслирует 6 типов событий через Redis channel layer (group `shop`):

```json
{ "type": "purchase.created",  "purchase":  { "id": 1, "name": "...", ... } }
{ "type": "purchase.updated",  "purchase":  { "id": 1, "is_need_to_buy": false, ... } }
{ "type": "purchase.deleted",  "purchase_id": 1, "category_id": 5 }
{ "type": "category.created",  "category":  { "id": 7, "name": "...", "order": 2 } }
{ "type": "category.updated",  "category":  { "id": 7, "name": "...", "order": 2 } }
{ "type": "category.deleted",  "category_id": 7 }
```

Клиент (websocket.js) слушает события и обновляет DOM. DOM-билдеры экспортируются из `ui.js`.

Вспомогательная функция `_broadcast(event_type, payload)` в `views.py` — обёртка над `async_to_sync(channel_layer.group_send)`. Устойчива к недоступности Redis (тихо логирует ошибку, не ломает HTTP-ответ).

---

## 8. Модели и ключевая логика

### Category
- `order` — приоритет (1 = наивысший), сортировка по `[order, name]`
- `create_with_order_shift(name, order)` — каскадно сдвигает существующие категории вниз (FR-04)
- `update_with_order_shift(name, order)` — то же при редактировании (FR-06)
- `CategoryQuerySet.with_active_purchases()` — категории с is_need_to_buy=True (для view page)
- `CategoryQuerySet.with_all_purchases()` — все категории (для edit page)

### Purchase
- `is_need_to_buy=True` по умолчанию при создании
- Сортировка: по `[category__order, name]`
- `set_need_to_buy(value)` — FR-15
- `update_fields(name, quantity, unit)` — FR-10

### UnitOfMeasurement
- Начальные данные: `fixtures/units.json` (шт., кг, г, л, мл)
- PROTECT при удалении (нельзя удалить единицу, если есть товары)

---

## 9. Тесты

### Фикстуры (conftest.py)
```python
user          # testuser / testpass123
auth_client   # авторизованный Django test client
unit          # UnitOfMeasurement(name="Штуки", abbreviation="шт.")
category      # Category(name="Молочное", order=1)
purchase      # Purchase(name="Молоко", quantity=2, is_need_to_buy=True)
```

### Запуск
```bash
pytest                        # все Python тесты (101 passed, coverage 93.62%)
pytest tests/test_models.py   # только модели
pytest tests/test_api.py      # только API
pytest -k "toggle"            # по имени
pytest -v                     # с подробным выводом
npm test                      # JS тесты (50 passed, Jest)
```

### Стиль тестов
- Декоратор `@pytest.mark.django_db` для всех тестов с БД
- `@pytest.mark.asyncio` для асинхронных тестов (consumers)
- WebSocket тесты используют `WebsocketCommunicator` из `channels.testing`
- Имена тестов: `test_<действие>_<ожидаемый_результат>`
- JS тесты: jsdom + jest, функции экспортируются через `window.*`

---

## 10. Статус реализации

### Готово (все FR реализованы)

| Модуль | Статус |
|--------|--------|
| Авторизация (FR-01..03) | done |
| Категории CRUD (FR-04..07) | done |
| Товары CRUD (FR-08..11) | done |
| Страница просмотра (FR-12) | done |
| Страница редактирования (FR-13) | done |
| Переключатель страниц (FR-14) | done |
| Чекбокс is_need_to_buy (FR-15) | done |
| Accordion (FR-16) | done |
| Свернуть/развернуть всё (FR-17) | done |
| WebSocket трансляция (FR-18) | done |
| WS авто-переподключение (FR-19) | done |

### Осталось сделать

| Задача | Приоритет | Файлы |
|--------|-----------|-------|
| Кастомные страницы 404/500 | SHOULD | `templates/404.html`, `templates/500.html` |
| E2E тесты (Selenium) | NICE | `tests/e2e/test_shopping_flow.py` |

---

## 11. Важные архитектурные решения

- **Last-write-wins:** при одновременном редактировании — побеждает последнее сохранение, без предупреждений (Q-01)
- **Один общий список** для всей семьи, не персонализированный (Q-02)
- **Регистрации нет** — пользователей создаёт суперюзер (Q-03, Q-04)
- **Без DRF** — REST через стандартные Django views, ответы вручную через `JsonResponse`
- **Без Celery** — Redis только как channel layer для WebSocket
- **Mobile-first** — Bootstrap 5, минимальная ширина 390px, touch-target 44×44pt (iPhone 15)
