---
name: pytest-selenium
description: Senior QA engineer expertise with pytest-django and Selenium. Use when writing any tests: unit tests for models/views, integration tests for AJAX endpoints, WebSocket consumer tests, or end-to-end browser tests with Selenium. Activates automatically for any task involving tests, test files, conftest.py, or QA.
---

# Тесты — решения этого проекта

---

## Фикстуры (conftest.py) — таблица

| Фикстура | Тип | Что даёт |
|----------|-----|----------|
| `user` | User | `testuser / testpass123` |
| `auth_client` | Client | Django test client, залогинен как `user` |
| `unit` | UnitOfMeasurement | `name='Штуки', abbreviation='шт.'` |
| `category` | Category | `name='Молочное', order=1` |
| `purchase` | Purchase | `name='Молоко', qty=2, is_need_to_buy=True` |

Не создавай объекты прямо в тестах — используй фикстуры.

---

## Паттерн: тест AJAX endpoint

```python
@pytest.mark.django_db
def test_toggle_sets_false(auth_client, purchase):
    # Act
    response = auth_client.patch(
        f'/api/purchases/{purchase.pk}/toggle/',
        data=json.dumps({'is_need_to_buy': False}),
        content_type='application/json',
    )
    # Assert HTTP
    assert response.status_code == 200
    # Assert DB
    purchase.refresh_from_db()
    assert purchase.is_need_to_buy is False
```

Каждый тест endpoint'а проверяет: статус + состояние БД. Не только статус.

---

## Паттерн: тест требует авторизации

```python
def test_requires_auth(client, purchase):
    response = client.patch(f'/api/purchases/{purchase.pk}/toggle/')
    assert response.status_code == 302  # redirect to /login/
```

---

## Паттерн: тест WS consumer

```python
@pytest.mark.asyncio
@pytest.mark.django_db(transaction=True)
async def test_receives_broadcast(user):
    communicator = WebsocketCommunicator(ShopConsumer.as_asgi(), '/ws/shop/')
    communicator.scope['user'] = user
    connected, _ = await communicator.connect()
    assert connected

    await get_channel_layer().group_send('shop', {
        'type': 'shop.event',
        'payload': {'type': 'purchase.updated', 'purchase_id': 42},
    })

    msg = await communicator.receive_json_from(timeout=3)
    assert msg['type'] == 'purchase.updated'
    await communicator.disconnect()  # обязательно — иначе утечка
```

`transaction=True` обязателен для async/WS тестов.

---

## Правила

- **`@pytest.mark.django_db`** на каждом тесте с БД
- **AAA**: Arrange → Act → Assert, явно разделяй
- **Имена**: `test_<действие>_<ожидаемый результат>` — `test_toggle_sets_false`, не `test_1`
- **Не тестируй Django**: не проверяй что `CharField` сохраняет строку
- **Один факт на тест**: если нужно проверить статус И тело — это один тест

---

## Что не тестировать

- Стандартное поведение Django ORM (save, delete, filter)
- Bootstrap/CSS рендеринг
- То что уже покрыто другим тестом в том же файле

---

## Запуск

```bash
pytest                          # все тесты, coverage report
pytest --no-cov -q              # быстро, без coverage
pytest tests/test_api.py -v     # только API
pytest -k "toggle"              # по имени
pytest --lf                     # только упавшие
npm test                        # JS тесты (Jest)
```
