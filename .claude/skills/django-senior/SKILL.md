---
name: django-senior
description: Senior Django developer expertise. Use when writing Django models, views, URLs, templates, middleware, admin, migrations, authentication, ORM queries, settings, and project structure. Activates automatically for any Django-related task.
---

# Django — решения этого проекта

Этот скилл только про решения принятые в **этом** проекте. Стандартный Django — ты уже знаешь.

---

## Ключевые решения и почему

**Без DRF** — ответы вручную через `JsonResponse` + `require_http_methods`. Причина: проект маленький, DRF избыточен. Не вводить DRF даже если "было бы удобнее".

**Fat models** — бизнес-логика живёт в моделях, не во views:
- `Category.create_with_order_shift()` — каскадный сдвиг order (FR-04)
- `Category.update_with_order_shift()` — то же при редактировании (FR-06)
- `Purchase.set_need_to_buy()` — сохраняет только нужные поля через `update_fields`
- `Purchase.update_fields()` — обновление товара

Views вызывают эти методы и делают `_broadcast()`. Никакой логики в views.

**`serializers.py`** — отдельный файл для сериализации в WS-события. `serialize_purchase()` и `serialize_category()` возвращают dict. Не смешивать с model методами.

**`WS_GROUP = 'shop'`** — константа в `apps/shop/consumers.py`. Импортируется в `views.py`. Не дублировать строку.

---

## Структура view (шаблон)

```python
@login_required
@require_http_methods(['POST'])
def create_something(request):
    try:
        data = json.loads(request.body)
    except (json.JSONDecodeError, ValueError):
        return JsonResponse({'error': 'Invalid JSON'}, status=400)

    name = data.get('name', '').strip()
    if not name:
        return JsonResponse({'error': 'Введите название.'}, status=400)

    obj = Model.create_with_business_logic(name)
    _broadcast('something.created', {'something': serialize_something(obj)})
    return JsonResponse({'ok': True, 'something': serialize_something(obj)}, status=201)
```

**Правила:**
- `@login_required` + `@require_http_methods` на каждом endpoint
- Валидация через ранний `return`, не вложенные if
- `IntegrityError` → 400, не 500
- Всегда `{'ok': True, ...}` при успехе

---

## TDD — обязательный порядок

**Баг:** сначала тест (красный) → потом фикс → тест зелёный. Используй `/fix-bug`.
**Фича:** сначала тесты (красные) → потом реализация → тесты зелёные. Используй `/new-feature`.

Нельзя писать код, под который потом «дописываются» тесты — это не TDD, это документирование.

---

## Запрещено

- **Никакого DRF** — ни `APIView`, ни `Serializer`, ни `Router`
- **Никакого Celery** — Redis только для Channels
- **Никаких новых зависимостей** без явного ОК пользователя
- **Не импортировать `auth.User` напрямую** — только через `get_user_model()` или `AUTH_USER_MODEL`
- **Не писать логику в views** — только вызовы model-методов + broadcast

---

## БД: dev vs prod

| Env | DB |
|-----|----|
| Dev / тесты | SQLite (`db.sqlite3`) |
| Prod (Docker) | PostgreSQL — `DB_ENGINE=django.db.backends.postgresql` |

Поведенческая разница: PostgreSQL строго соблюдает типы и регистр. Если пишешь raw SQL или сложные аннотации — тестируй на PostgreSQL.

---

## Ключевые файлы

| Файл | Что делает |
|------|-----------|
| `apps/shop/models.py` | Category, Purchase, UnitOfMeasurement + вся бизнес-логика |
| `apps/shop/views.py` | Все API endpoints + `_broadcast()` |
| `apps/shop/serializers.py` | `serialize_category()`, `serialize_purchase()` |
| `apps/shop/consumers.py` | `ShopConsumer` + `WS_GROUP = 'shop'` |
| `apps/users/views.py` | login/logout |
| `config/settings.py` | Env через python-decouple, DB по `DB_ENGINE` |
