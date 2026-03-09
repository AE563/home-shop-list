# /new-endpoint — Добавить новый API endpoint

Задай пользователю:
1. Метод (GET / POST / PATCH / DELETE)
2. URL (например `/api/purchases/<pk>/reorder/`)
3. Что делает (бизнес-логика)
4. Нужен ли broadcast через WebSocket?

---

## Реализация (порядок)

### 1. Модель (`apps/shop/models.py`)
Если нужна новая бизнес-логика — добавь метод в модель (fat models).
Не пиши логику во view.

### 2. View (`apps/shop/views.py`)

```python
@login_required
@require_http_methods(["PATCH"])
def my_action(request, pk):
    obj = get_object_or_404(ModelName, pk=pk)
    # ... логика через метод модели ...
    if broadcast_needed:
        _broadcast('event.type', {'key': value})
    return JsonResponse({'ok': True})
```

Правила:
- `@login_required` обязателен
- `@require_http_methods` явно указывает методы
- Ошибки: `JsonResponse({'error': '...'}, status=400/404/405)`
- Без DRF — чистый `JsonResponse`

### 3. URL (`config/urls.py`)

```python
path('api/resource/<int:pk>/action/', views.my_action),
```

### 4. Frontend (`static/js/ui.js`)
Если нужен AJAX-вызов — добавь через event delegation.
Используй `shopUtils.esc()` для любых пользовательских данных в innerHTML.

### 5. WebSocket (`static/js/websocket.js`)
Если endpoint делает broadcast — добавь обработчик нового события в `handleMessage`.

### 6. Тест (`tests/test_api.py`)

```python
@pytest.mark.django_db
def test_my_action_success(auth_client, purchase):
    response = auth_client.patch(f'/api/purchases/{purchase.pk}/action/', ...)
    assert response.status_code == 200
    purchase.refresh_from_db()
    assert purchase.field == expected

def test_my_action_requires_auth(client, purchase):
    response = client.patch(f'/api/purchases/{purchase.pk}/action/')
    assert response.status_code == 302
```

### 7. ARCHITECTURE.md
Добавь запись в Feature Backlog перед началом реализации.
