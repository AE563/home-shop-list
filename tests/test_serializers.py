"""Direct unit tests for apps/shop/serializers.py."""
import pytest

from apps.shop.serializers import serialize_category, serialize_purchase


@pytest.mark.django_db
def test_serialize_category_returns_all_fields(category):
    """serialize_category returns id, name, order."""
    data = serialize_category(category)
    assert data == {
        'id': category.pk,
        'name': category.name,
        'order': category.order,
    }


@pytest.mark.django_db
def test_serialize_category_reflects_actual_values(db):
    """serialize_category reflects the exact field values of the instance."""
    from apps.shop.models import Category
    cat = Category.objects.create(name='Зелень', order=5)
    data = serialize_category(cat)
    assert data['name'] == 'Зелень'
    assert data['order'] == 5
    assert data['id'] == cat.pk


@pytest.mark.django_db
def test_serialize_purchase_returns_all_fields(purchase, category, unit):
    """serialize_purchase returns all expected fields with correct values."""
    data = serialize_purchase(purchase)

    assert data['id'] == purchase.pk
    assert data['name'] == purchase.name
    assert data['is_need_to_buy'] == purchase.is_need_to_buy
    assert data['quantity'] == str(purchase.quantity)
    assert data['unit_id'] == unit.pk
    assert data['unit_name'] == unit.name
    assert data['unit_abbreviation'] == unit.abbreviation
    assert data['category_id'] == category.pk
    assert data['category_name'] == category.name
    assert data['category_order'] == category.order


@pytest.mark.django_db
def test_serialize_purchase_quantity_is_string(purchase):
    """serialize_purchase returns quantity as a string (Decimal -> str)."""
    data = serialize_purchase(purchase)
    assert isinstance(data['quantity'], str)


@pytest.mark.django_db
def test_serialize_purchase_is_need_to_buy_false(db, category, unit):
    """serialize_purchase correctly serializes is_need_to_buy=False."""
    from apps.shop.models import Purchase
    p = Purchase.objects.create(
        name='Кефир', category=category, unit=unit, quantity=1, is_need_to_buy=False,
    )
    data = serialize_purchase(p)
    assert data['is_need_to_buy'] is False
