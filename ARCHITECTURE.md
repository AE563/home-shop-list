# ARCHITECTURE.md

> Обновляй **перед** реализацией новой фичи.
> Проверяется на актуальность в pre-push-review (Фаза 6).

---

## Место в инфраструктуре

Этот проект — один из нескольких Django-сервисов на одном сервере (см. `TASK_docker_infrastructure.md`).

| Роль | Детали |
|------|--------|
| Имя контейнера | `groceries_web` |
| Внешний URL | `groceries.mysite.com` |
| Общая сеть | `shared_net` (создаётся в `mysite-infrastructure`) |
| PostgreSQL / Redis | Общие, в `mysite-infrastructure` |
| Продакшн-запуск | `docker compose -f docker-compose.prod.yml up -d` |

Nginx, PostgreSQL и Redis вынесены в отдельный репо `mysite-infrastructure`. Этот репо содержит только приложение.

---

## Принятые решения

| Решение | Почему |
|---------|--------|
| **Без DRF** | Проект маленький, DRF избыточен. REST через `JsonResponse` + `require_http_methods`. |
| **Без Celery** | Redis только как channel layer для WebSocket. |
| **Без регистрации** | Пользователей создаёт суперюзер. Семейное приложение. |
| **Last-write-wins** | При одновременном редактировании побеждает последнее сохранение. Без предупреждений. |
| **Один общий список** | Не персонализированный — семья видит одно и то же. |
| **Server-only WebSocket push** | Клиент не шлёт WS-сообщения. Все изменения через REST → `_broadcast()` → WS. |
| **Fat models** | Бизнес-логика в моделях (`create_with_order_shift`, `set_need_to_buy`), не во views. |
| **SQLite dev / PostgreSQL prod** | SQLite для простоты разработки. Prod — PostgreSQL в Docker. ⚠️ PostgreSQL строже с типами — тестировать миграции на обоих. |
| **Mobile-first** | Bootstrap 5, минимум 390px, touch-target 44×44pt (iPhone 15, Safari). |

---

## Известные баги

*Нет открытых багов.*

---

## Статус реализации

### Готово

| Модуль | FR |
|--------|----|
| Авторизация | FR-01..03 |
| Категории CRUD | FR-04..07 |
| Товары CRUD | FR-08..11 |
| Страница просмотра | FR-12 |
| Страница редактирования | FR-13 |
| Переключатель страниц | FR-14 |
| Чекбокс is_need_to_buy | FR-15 |
| Accordion | FR-16 |
| Свернуть/развернуть всё | FR-17 |
| WebSocket трансляция | FR-18 |
| WS авто-переподключение | FR-19 |

### Осталось сделать

| Задача | Приоритет |
|--------|-----------|
| Кастомные страницы 404/500 | SHOULD |
| E2E тесты (Selenium) | NICE |

---

## Feature Backlog

> Перед началом работы над фичей — добавь запись ниже.
> Формат: дата, название, решение, затронутые файлы.

<!-- Пример:

### [2026-03-09] Сортировка товаров drag-and-drop
**Решение:** Используем SortableJS (новая зависимость — получить ОК). Order сохраняется через PATCH /api/purchases/<pk>/ с новым полем position.
**Файлы:** apps/shop/models.py, apps/shop/views.py, static/js/ui.js, tests/test_api.py
**Статус:** planned

-->

---

## Технический долг

> Реальные проблемы, найденные в ревью, но выходящие за скоп текущего PR.
> Добавляется автоматически в Фазе 3 pre-push-review (приоритет Medium/High).

| Дата | Описание | Файл(ы) |
|------|----------|---------|
| 2026-03-09 | N последовательных `async_to_sync` вызовов в цикле `_broadcast_shifted_categories` — блокирует HTTP-ответ пропорционально числу сдвинутых категорий; при росте нагрузки заменить на один батч-coroutine | `apps/shop/views.py` |
| 2026-03-09 | Event type strings (`'category.created'`, `'category.updated'` и др.) — raw literals в views.py и тестах; опечатка даёт silent fail; вынести в константы (`consumers.py` или отдельный `events.py`) | `apps/shop/views.py`, `tests/test_api.py` |

---

## Стратегическое видение

> Концепт на проработку — не задача для ближайшего спринта.

### Публичное многопользовательское приложение

**Идея:** Из семейного приложения — в публичный сервис. Каждый пользователь
создаёт свои списки продуктов и приглашает/исключает участников.

**Ключевые изменения архитектуры:**

| Блок | Текущее | Нужно |
|------|---------|-------|
| Пользователи | `createsuperuser` only | Self-registration + OAuth |
| Списки | Один общий | Многопользовательские списки (модель ShoppingList) |
| Доступ | Все видят всё | Membership (owner + invited users) |
| WS группы | `'shop'` — одна | `'shop_{list_id}'` — по списку |
| Деплой | Single VPS | Масштабируемый (минимум: несколько workers) |

**Мобильное приложение (кросс-платформенное):**
- Приоритет: Android (начать с PWA или React Native / Flutter)
- UI уже mobile-first — стартовая точка хорошая
- Потребуется: REST API + JWT auth (WebSocket через cookie не работает в native apps)
- Нужен отдельный APK/AAB для публикации в Google Play

**Что нужно проработать перед реализацией:**
- Модель данных: ShoppingList → Membership → Category → Purchase
- Способ приглашения: по ссылке / по email / по username
- Монетизация (если публичный сервис): free tier / premium?
- Выбор мобильного стека: PWA vs React Native vs Flutter
