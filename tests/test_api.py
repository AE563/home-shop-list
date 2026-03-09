"""API tests: Category и Purchase CRUD + toggle (FR-04, FR-06, FR-07, FR-08, FR-10, FR-11, FR-15)."""

import json
from unittest.mock import patch as mock_patch

import pytest

from apps.shop.models import Category, Purchase

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def patch(client, url, data):
    return client.patch(url, json.dumps(data), content_type='application/json')


def post(client, url, data):
    return client.post(url, json.dumps(data), content_type='application/json')


# ---------------------------------------------------------------------------
# Category: create (FR-04)
# ---------------------------------------------------------------------------


@pytest.mark.django_db
def test_create_category_returns_201(auth_client):
    """FR-04: POST /api/categories/ создаёт категорию и возвращает 201."""
    response = post(auth_client, '/api/categories/', {'name': 'Молочное', 'order': 1})
    assert response.status_code == 201
    data = response.json()
    assert data['ok'] is True
    assert data['category']['name'] == 'Молочное'
    assert Category.objects.filter(name='Молочное').exists()


@pytest.mark.django_db
def test_create_category_empty_name_returns_400(auth_client):
    """FR-04: Пустое имя → 400."""
    response = post(auth_client, '/api/categories/', {'name': '  ', 'order': 1})
    assert response.status_code == 400
    assert 'error' in response.json()


@pytest.mark.django_db
def test_create_category_invalid_json_returns_400(auth_client):
    """FR-04: Невалидный JSON → 400."""
    response = auth_client.post('/api/categories/', 'not json', content_type='application/json')
    assert response.status_code == 400


@pytest.mark.django_db
def test_create_category_duplicate_name_returns_400(auth_client):
    """FR-04: Дублирующееся имя → 400."""
    Category.objects.create(name='Молочное', order=1)
    response = post(auth_client, '/api/categories/', {'name': 'Молочное', 'order': 2})
    assert response.status_code == 400
    assert 'уже существует' in response.json()['error']


@pytest.mark.django_db
def test_create_category_shifts_existing_order(auth_client):
    """FR-04: create_with_order_shift сдвигает категории при вставке на занятую позицию."""
    existing = Category.objects.create(name='Мясо', order=1)
    post(auth_client, '/api/categories/', {'name': 'Молочное', 'order': 1})

    existing.refresh_from_db()
    new_cat = Category.objects.get(name='Молочное')
    assert new_cat.order == 1
    assert existing.order == 2


@pytest.mark.django_db
def test_create_category_requires_login(client):
    """FR-03: Создание категории без авторизации → 302."""
    response = post(client, '/api/categories/', {'name': 'Молочное', 'order': 1})
    assert response.status_code == 302


# ---------------------------------------------------------------------------
# Category: update (FR-06)
# ---------------------------------------------------------------------------


@pytest.mark.django_db
def test_update_category_returns_200(auth_client, category):
    """FR-06: PATCH /api/categories/<pk>/ обновляет категорию."""
    response = patch(auth_client, f'/api/categories/{category.pk}/', {'name': 'Новое имя'})
    assert response.status_code == 200
    data = response.json()
    assert data['ok'] is True
    assert data['category']['name'] == 'Новое имя'
    category.refresh_from_db()
    assert category.name == 'Новое имя'


@pytest.mark.django_db
def test_update_category_empty_name_returns_400(auth_client, category):
    """FR-06: Пустое имя при обновлении → 400."""
    response = patch(auth_client, f'/api/categories/{category.pk}/', {'name': ''})
    assert response.status_code == 400


@pytest.mark.django_db
def test_update_category_duplicate_name_returns_400(auth_client, category):
    """FR-06: Дублирующееся имя при обновлении → 400."""
    Category.objects.create(name='Зелень', order=2)
    response = patch(auth_client, f'/api/categories/{category.pk}/', {'name': 'Зелень'})
    assert response.status_code == 400


@pytest.mark.django_db
def test_update_category_not_found_returns_404(auth_client):
    """FR-06: Несуществующая категория → 404."""
    response = patch(auth_client, '/api/categories/9999/', {'name': 'Что-то'})
    assert response.status_code == 404


@pytest.mark.django_db
def test_update_category_requires_login(client, category):
    """FR-03: Обновление категории без авторизации → 302."""
    response = patch(client, f'/api/categories/{category.pk}/', {'name': 'X'})
    assert response.status_code == 302


# ---------------------------------------------------------------------------
# Category: delete (FR-07)
# ---------------------------------------------------------------------------


@pytest.mark.django_db
def test_delete_category_returns_200(auth_client, category):
    """FR-07: DELETE /api/categories/<pk>/ удаляет категорию."""
    pk = category.pk
    response = auth_client.delete(f'/api/categories/{pk}/')
    assert response.status_code == 200
    assert response.json()['ok'] is True
    assert not Category.objects.filter(pk=pk).exists()


@pytest.mark.django_db
def test_delete_category_cascades_purchases(auth_client, category, purchase):
    """FR-07: Удаление категории каскадно удаляет её товары."""
    pk = category.pk
    auth_client.delete(f'/api/categories/{pk}/')
    assert not Purchase.objects.filter(category_id=pk).exists()


@pytest.mark.django_db
def test_delete_category_requires_login(client, category):
    """FR-03: Удаление без авторизации → 302."""
    response = client.delete(f'/api/categories/{category.pk}/')
    assert response.status_code == 302


# ---------------------------------------------------------------------------
# Purchase: create (FR-08)
# ---------------------------------------------------------------------------


@pytest.mark.django_db
def test_create_purchase_returns_201(auth_client, category, unit):
    """FR-08: POST /api/purchases/ создаёт товар и возвращает 201."""
    response = post(
        auth_client,
        '/api/purchases/',
        {
            'name': 'Молоко',
            'quantity': 2,
            'category_id': category.pk,
            'unit_id': unit.pk,
        },
    )
    assert response.status_code == 201
    data = response.json()
    assert data['ok'] is True
    assert data['purchase']['name'] == 'Молоко'
    assert Purchase.objects.filter(name='Молоко').exists()


@pytest.mark.django_db
def test_create_purchase_empty_name_returns_400(auth_client, category, unit):
    """FR-08: Пустое имя товара → 400."""
    response = post(
        auth_client,
        '/api/purchases/',
        {
            'name': '',
            'quantity': 1,
            'category_id': category.pk,
            'unit_id': unit.pk,
        },
    )
    assert response.status_code == 400


@pytest.mark.django_db
def test_create_purchase_invalid_json_returns_400(auth_client):
    """FR-08: Невалидный JSON → 400."""
    response = auth_client.post('/api/purchases/', 'bad', content_type='application/json')
    assert response.status_code == 400


@pytest.mark.django_db
@pytest.mark.parametrize('quantity', [0, -1, -0.5])
def test_create_purchase_non_positive_quantity_returns_400(auth_client, category, unit, quantity):
    """FR-08: Количество ≤ 0 → 400.

    Args:
        quantity: Недопустимое количество.
    """
    response = post(
        auth_client,
        '/api/purchases/',
        {
            'name': 'Молоко',
            'quantity': quantity,
            'category_id': category.pk,
            'unit_id': unit.pk,
        },
    )
    assert response.status_code == 400
    assert 'больше 0' in response.json()['error']


@pytest.mark.django_db
def test_create_purchase_unknown_category_returns_404(auth_client, unit):
    """FR-08: Несуществующая категория → 404."""
    response = post(
        auth_client,
        '/api/purchases/',
        {
            'name': 'Молоко',
            'quantity': 1,
            'category_id': 9999,
            'unit_id': unit.pk,
        },
    )
    assert response.status_code == 404


@pytest.mark.django_db
def test_create_purchase_requires_login(client, category, unit):
    """FR-03: Создание товара без авторизации → 302."""
    response = post(
        client,
        '/api/purchases/',
        {
            'name': 'Молоко',
            'quantity': 1,
            'category_id': category.pk,
            'unit_id': unit.pk,
        },
    )
    assert response.status_code == 302


# ---------------------------------------------------------------------------
# Purchase: update (FR-10)
# ---------------------------------------------------------------------------


@pytest.mark.django_db
def test_update_purchase_returns_200(auth_client, purchase, unit):
    """FR-10: PATCH /api/purchases/<pk>/ обновляет товар."""
    response = patch(
        auth_client,
        f'/api/purchases/{purchase.pk}/',
        {
            'name': 'Сыр',
            'quantity': 0.3,
            'unit_id': unit.pk,
        },
    )
    assert response.status_code == 200
    data = response.json()
    assert data['ok'] is True
    assert data['purchase']['name'] == 'Сыр'
    purchase.refresh_from_db()
    assert purchase.name == 'Сыр'
    assert float(purchase.quantity) == 0.3


@pytest.mark.django_db
def test_update_purchase_empty_name_returns_400(auth_client, purchase):
    """FR-10: Пустое имя при обновлении → 400."""
    response = patch(auth_client, f'/api/purchases/{purchase.pk}/', {'name': ''})
    assert response.status_code == 400


@pytest.mark.django_db
@pytest.mark.parametrize('quantity', [0, -1])
def test_update_purchase_non_positive_quantity_returns_400(auth_client, purchase, unit, quantity):
    """FR-10: Количество ≤ 0 при обновлении → 400.

    Args:
        quantity: Недопустимое количество.
    """
    response = patch(
        auth_client,
        f'/api/purchases/{purchase.pk}/',
        {
            'name': 'Молоко',
            'quantity': quantity,
            'unit_id': unit.pk,
        },
    )
    assert response.status_code == 400


@pytest.mark.django_db
def test_update_purchase_not_found_returns_404(auth_client):
    """FR-10: Несуществующий товар → 404."""
    response = patch(auth_client, '/api/purchases/9999/', {'name': 'Что-то'})
    assert response.status_code == 404


@pytest.mark.django_db
def test_update_purchase_requires_login(client, purchase, unit):
    """FR-03: Обновление товара без авторизации → 302."""
    response = patch(client, f'/api/purchases/{purchase.pk}/', {'name': 'X', 'unit_id': unit.pk})
    assert response.status_code == 302


# ---------------------------------------------------------------------------
# Purchase: delete (FR-11)
# ---------------------------------------------------------------------------


@pytest.mark.django_db
def test_delete_purchase_returns_200(auth_client, purchase):
    """FR-11: DELETE /api/purchases/<pk>/ удаляет товар."""
    pk = purchase.pk
    response = auth_client.delete(f'/api/purchases/{pk}/')
    assert response.status_code == 200
    assert response.json()['ok'] is True
    assert not Purchase.objects.filter(pk=pk).exists()


@pytest.mark.django_db
def test_delete_purchase_not_found_returns_404(auth_client):
    """FR-11: Несуществующий товар → 404."""
    response = auth_client.delete('/api/purchases/9999/')
    assert response.status_code == 404


@pytest.mark.django_db
def test_delete_purchase_requires_login(client, purchase):
    """FR-03: Удаление товара без авторизации → 302."""
    response = client.delete(f'/api/purchases/{purchase.pk}/')
    assert response.status_code == 302


# ---------------------------------------------------------------------------
# Purchase: toggle (FR-15)
# ---------------------------------------------------------------------------


@pytest.mark.django_db
@pytest.mark.parametrize('initial,new_value', [(True, False), (False, True)])
def test_toggle_purchase_changes_status(auth_client, purchase, initial, new_value):
    """FR-15: PATCH /api/purchases/<pk>/toggle/ переключает статус.

    Args:
        initial: Начальный статус покупки.
        new_value: Ожидаемый статус после переключения.
    """
    purchase.is_need_to_buy = initial
    purchase.save(update_fields=['is_need_to_buy', 'updated_at'])

    response = patch(
        auth_client,
        f'/api/purchases/{purchase.pk}/toggle/',
        {
            'is_need_to_buy': new_value,
        },
    )
    assert response.status_code == 200
    data = response.json()
    assert data['ok'] is True
    assert data['is_need_to_buy'] == new_value

    purchase.refresh_from_db()
    assert purchase.is_need_to_buy == new_value


@pytest.mark.django_db
def test_toggle_purchase_invalid_json_returns_400(auth_client, purchase):
    """FR-15: Невалидный JSON при toggle → 400."""
    response = auth_client.patch(f'/api/purchases/{purchase.pk}/toggle/', 'bad', content_type='application/json')
    assert response.status_code == 400


@pytest.mark.django_db
def test_toggle_purchase_not_found_returns_404(auth_client):
    """FR-15: Несуществующий товар → 404."""
    response = patch(auth_client, '/api/purchases/9999/toggle/', {'is_need_to_buy': False})
    assert response.status_code == 404


@pytest.mark.django_db
def test_toggle_purchase_requires_login(client, purchase):
    """FR-03: Toggle без авторизации → 302."""
    response = patch(client, f'/api/purchases/{purchase.pk}/toggle/', {'is_need_to_buy': False})
    assert response.status_code == 302


# ---------------------------------------------------------------------------
# Edge cases: wrong HTTP method (405)
# ---------------------------------------------------------------------------


@pytest.mark.django_db
def test_category_detail_wrong_method_returns_405(auth_client, category):
    """GET /api/categories/<pk>/ → 405 (only PATCH/DELETE allowed)."""
    response = auth_client.get(f'/api/categories/{category.pk}/')
    assert response.status_code == 405


@pytest.mark.django_db
def test_purchase_detail_wrong_method_returns_405(auth_client, purchase):
    """GET /api/purchases/<pk>/ → 405 (only PATCH/DELETE allowed)."""
    response = auth_client.get(f'/api/purchases/{purchase.pk}/')
    assert response.status_code == 405


@pytest.mark.django_db
def test_delete_category_not_found_returns_404(auth_client):
    """FR-07: DELETE несуществующей категории → 404."""
    response = auth_client.delete('/api/categories/9999/')
    assert response.status_code == 404


# ---------------------------------------------------------------------------
# Bug #1 fix: broadcast shifted categories on order shift
# ---------------------------------------------------------------------------


@pytest.mark.django_db
def test_create_category_broadcasts_shifted_categories(auth_client):
    """Bug #1: category.updated broadcast sent for each shifted category after create."""
    existing = Category.objects.create(name='Мясо', order=1)
    with mock_patch('apps.shop.views._broadcast') as mock_broadcast:
        post(auth_client, '/api/categories/', {'name': 'Молочное', 'order': 1})

    calls = mock_broadcast.call_args_list
    assert calls[0][0][0] == 'category.created'
    assert calls[1][0][0] == 'category.updated'
    shifted_cat = calls[1][0][1]['category']
    assert shifted_cat['id'] == existing.pk
    assert shifted_cat['order'] == 2


@pytest.mark.django_db
def test_create_category_no_shift_no_extra_broadcasts(auth_client):
    """Bug #1: no extra broadcast when new category order doesn't displace others."""
    with mock_patch('apps.shop.views._broadcast') as mock_broadcast:
        post(auth_client, '/api/categories/', {'name': 'Молочное', 'order': 99})

    assert mock_broadcast.call_count == 1
    assert mock_broadcast.call_args[0][0] == 'category.created'


@pytest.mark.django_db
def test_update_category_broadcasts_shifted_categories(auth_client):
    """Bug #1: category.updated broadcast sent for shifted categories after order change."""
    cat1 = Category.objects.create(name='Мясо', order=1)
    cat2 = Category.objects.create(name='Молочное', order=2)
    with mock_patch('apps.shop.views._broadcast') as mock_broadcast:
        patch(auth_client, f'/api/categories/{cat2.pk}/', {'name': 'Молочное', 'order': 1})

    event_types = [c[0][0] for c in mock_broadcast.call_args_list]
    assert event_types.count('category.updated') == 2
    broadcast_ids = {c[0][1]['category']['id'] for c in mock_broadcast.call_args_list}
    assert cat1.pk in broadcast_ids
    assert cat2.pk in broadcast_ids


@pytest.mark.django_db
def test_update_category_name_only_no_extra_broadcasts(auth_client, category):
    """Bug #1: no extra broadcasts when only name changes (order unchanged)."""
    with mock_patch('apps.shop.views._broadcast') as mock_broadcast:
        patch(auth_client, f'/api/categories/{category.pk}/', {'name': 'Новое имя', 'order': category.order})

    assert mock_broadcast.call_count == 1
    assert mock_broadcast.call_args[0][0] == 'category.updated'
