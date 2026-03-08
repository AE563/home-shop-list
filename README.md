<div align="center">

# 🛒 Home Shop List

**Семейный список покупок с синхронизацией в реальном времени**

[![CI](https://github.com/AE563/home-shop-list/actions/workflows/ci.yml/badge.svg)](https://github.com/AE563/home-shop-list/actions/workflows/ci.yml)
[![Python](https://img.shields.io/badge/python-3.12-blue?logo=python&logoColor=white)](https://www.python.org/)
[![Django](https://img.shields.io/badge/django-4.2-green?logo=django&logoColor=white)](https://www.djangoproject.com/)
[![Ruff](https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/astral-sh/ruff/main/assets/badge/v2.json)](https://github.com/astral-sh/ruff)
[![License: MIT](https://img.shields.io/badge/license-MIT-yellow.svg)](LICENSE)

</div>

---

## Возможности

- **Общий список** — вся семья видит одно и то же, изменения мгновенно
- **WebSocket** — обновления без перезагрузки страницы (Django Channels + Redis)
- **Две страницы**: просмотр (только «нужно купить») и редактирование (все товары)
- **Категории с приоритетом** — порядок определяет расположение в списке
- **Единицы измерения** — шт., кг, г, л, мл
- **Accordion** — сворачивание/разворачивание категорий, «Свернуть всё»
- **Чекбокс** — отметить товар как купленный одним нажатием
- **Mobile-first** — Bootstrap 5, touch-target 44×44pt (iPhone 15)

---

## Быстрый старт

### Требования

- Python 3.12+
- Redis 7+
- Node.js 20+ (только для JS-тестов)

### Установка

```bash
# Клонировать репозиторий
git clone git@github.com:AE563/home-shop-list.git
cd home-shop-list

# Создать виртуальное окружение и установить зависимости
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

# Создать .env файл
cp .env.example .env   # отредактируйте SECRET_KEY и REDIS_URL

# Применить миграции
python manage.py migrate

# Загрузить начальные данные (единицы измерения)
python manage.py loaddata fixtures/units.json

# Создать суперпользователя
python manage.py createsuperuser

# Запустить Redis (если не запущен)
redis-server --daemonize yes

# Запустить сервер
python manage.py runserver
```

Открыть: [http://localhost:8000](http://localhost:8000)

### Переменные окружения (.env)

```ini
SECRET_KEY=your-secret-key-here
DEBUG=True
ALLOWED_HOSTS=localhost,127.0.0.1
REDIS_URL=redis://localhost:6379/0
```

---

## API

Все эндпоинты требуют авторизации. Неавторизованный запрос → `302` на `/login/`.

| Метод | URL | Действие |
|-------|-----|----------|
| `GET` | `/` | Страница просмотра (только `is_need_to_buy=True`) |
| `GET` | `/edit/` | Страница редактирования |
| `POST` | `/api/categories/` | Создать категорию |
| `PATCH` | `/api/categories/<pk>/` | Редактировать категорию |
| `DELETE` | `/api/categories/<pk>/` | Удалить категорию |
| `POST` | `/api/purchases/` | Создать товар |
| `PATCH` | `/api/purchases/<pk>/` | Редактировать товар |
| `DELETE` | `/api/purchases/<pk>/` | Удалить товар |
| `PATCH` | `/api/purchases/<pk>/toggle/` | Переключить `is_need_to_buy` |
| `WS` | `ws/shop/` | WebSocket-соединение |

---

## WebSocket события

Сервер транслирует события через Redis channel layer (группа `shop`):

```json
{ "type": "purchase.created",  "purchase":  { "id": 1, "name": "Молоко", "quantity": "2.00" } }
{ "type": "purchase.updated",  "purchase":  { "id": 1, "is_need_to_buy": false } }
{ "type": "purchase.deleted",  "purchase_id": 1 }
{ "type": "category.created",  "category":  { "id": 7, "name": "Молочное", "order": 2 } }
{ "type": "category.updated",  "category":  { "id": 7, "name": "Молочное", "order": 2 } }
{ "type": "category.deleted",  "category_id": 7 }
```

---

## Стек технологий

| Слой | Технология |
|------|------------|
| Backend | Django 4.2 |
| WebSocket | Django Channels 4 + Daphne (ASGI) |
| Channel layer | Redis 7 |
| База данных | SQLite |
| Конфигурация | python-decouple |
| Frontend | Vanilla JS (ES6+), Bootstrap 5 |
| Линтер Python | Ruff |
| Линтер JS | ESLint 9 |
| Тесты Python | pytest-django, pytest-asyncio |
| Тесты JS | Jest + JSDOM |

---

## Тесты

```bash
# Python тесты (с покрытием)
pytest

# Python тесты без покрытия (быстрее)
pytest --no-cov -q

# JavaScript тесты
npm test

# Только конкретный файл / тест
pytest tests/test_consumers.py
pytest -k "toggle"
```

### Текущее покрытие

| Файл | Покрытие |
|------|----------|
| `apps/shop/models.py` | ~95% |
| `apps/shop/views.py` | ~95% |
| `apps/shop/serializers.py` | 100% |
| `apps/shop/consumers.py` | ~90% |
| `apps/users/views.py` | ~90% |
| **Итого** | **~93%** |

JS: 46 тестов для `ui.js` и `websocket.js`

---

## Структура проекта

```
config/          — settings.py, urls.py, asgi.py
apps/
  users/         — авторизация (AbstractUser)
  shop/          — Category, Purchase, UnitOfMeasurement; API; WebSocket consumer
  core/          — вспомогательные функции
templates/       — base.html, shop/view.html, shop/edit.html
static/js/
  ui.js          — DOM: accordion, CRUD-формы, AJAX
  websocket.js   — WebSocket клиент
tests/           — pytest тесты + tests/js/ Jest тесты
fixtures/        — начальные данные
```

---

## Лицензия

[MIT](LICENSE) © 2024 AE563
