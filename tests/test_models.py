import pytest
from django.db import IntegrityError
from django.db.models.deletion import ProtectedError

from apps.shop.models import Category, Purchase, UnitOfMeasurement


# ---------------------------------------------------------------------------
# __str__ методы
# ---------------------------------------------------------------------------

@pytest.mark.django_db
@pytest.mark.parametrize("name", ["Молочное", "Мясо и рыба", "Напитки"])
def test_category_str(name):
    """Category.__str__ возвращает имя категории."""
    assert str(Category(name=name, order=1)) == name


@pytest.mark.django_db
@pytest.mark.parametrize("name,abbreviation", [
    ("Штуки", "шт."),
    ("Килограммы", "кг"),
    ("Литры", "л"),
])
def test_unit_str(name, abbreviation):
    """UnitOfMeasurement.__str__ возвращает аббревиатуру единицы измерения."""
    assert str(UnitOfMeasurement(name=name, abbreviation=abbreviation)) == abbreviation


@pytest.mark.django_db
@pytest.mark.parametrize("quantity,expected_str", [
    (1,    "Молоко (1.00 шт.)"),
    (2,    "Молоко (2.00 шт.)"),
    (2.5,  "Молоко (2.50 шт.)"),
    (0.33, "Молоко (0.33 шт.)"),
])
def test_purchase_str(quantity, expected_str):
    """Purchase.__str__ содержит название, количество (2 знака) и аббревиатуру единицы.

    Args:
        quantity: Количество товара для сохранения в БД.
        expected_str: Ожидаемое строковое представление.
    """
    unit = UnitOfMeasurement.objects.create(name="Штуки", abbreviation="шт.")
    cat = Category.objects.create(name="Молочное", order=1)
    purchase = Purchase.objects.create(
        name="Молоко", category=cat, unit=unit, quantity=quantity
    )
    assert str(purchase) == expected_str


# ---------------------------------------------------------------------------
# Значения по умолчанию
# ---------------------------------------------------------------------------

@pytest.mark.django_db
def test_purchase_default_is_need_to_buy():
    """FR-08: При создании товара is_need_to_buy равен True по умолчанию."""
    unit = UnitOfMeasurement.objects.create(name="Штуки", abbreviation="шт.")
    cat = Category.objects.create(name="Молочное", order=1)
    purchase = Purchase.objects.create(name="Кефир", category=cat, unit=unit)
    assert purchase.is_need_to_buy is True


# ---------------------------------------------------------------------------
# Сортировка (Meta.ordering)
# ---------------------------------------------------------------------------

@pytest.mark.django_db
@pytest.mark.parametrize("categories,expected_names", [
    (
        [(2, "Молочное"), (1, "Зелень"), (1, "Выпечка")],
        ["Выпечка", "Зелень", "Молочное"],
    ),
    (
        [(3, "Фрукты"), (1, "Хлеб"), (2, "Мясо")],
        ["Хлеб", "Мясо", "Фрукты"],
    ),
    (
        [(1, "Один"), (1, "Два"), (1, "Три")],
        ["Два", "Один", "Три"],
    ),
])
def test_category_default_ordering(categories, expected_names):
    """Категории сортируются по приоритету (order asc), затем по имени (asc) — Meta.ordering.

    Args:
        categories: Список пар (order, name) для создания категорий.
        expected_names: Ожидаемый порядок имён в QuerySet.
    """
    for order, name in categories:
        Category.objects.create(name=name, order=order)
    names = list(Category.objects.values_list("name", flat=True))
    assert names == expected_names


@pytest.mark.django_db
@pytest.mark.parametrize("names,expected", [
    (["Сыр", "Кефир", "Молоко"], ["Кефир", "Молоко", "Сыр"]),
    (["Яйца", "Апельсины", "Бананы"], ["Апельсины", "Бананы", "Яйца"]),
    (["Хлеб", "Масло"], ["Масло", "Хлеб"]),
])
def test_purchase_alphabetical_ordering(names, expected):
    """Товары в категории сортируются по алфавиту — Meta.ordering.

    Args:
        names: Список названий товаров в случайном порядке.
        expected: Ожидаемый алфавитный порядок.
    """
    unit = UnitOfMeasurement.objects.create(name="Штуки", abbreviation="шт.")
    cat = Category.objects.create(name="Молочное", order=1)
    for name in names:
        Purchase.objects.create(name=name, category=cat, unit=unit)
    assert list(cat.purchases.values_list("name", flat=True)) == expected


# ---------------------------------------------------------------------------
# Ограничения целостности
# ---------------------------------------------------------------------------

@pytest.mark.django_db
def test_category_name_unique():
    """Category.name уникально — дубликат вызывает IntegrityError."""
    Category.objects.create(name="Молочное", order=1)
    with pytest.raises(IntegrityError):
        Category.objects.create(name="Молочное", order=2)


@pytest.mark.django_db
@pytest.mark.parametrize("purchase_count", [1, 2, 5])
def test_purchase_cascade_delete_when_category_deleted(purchase_count):
    """FR-07: Удаление категории каскадно удаляет все её товары (on_delete=CASCADE).

    Args:
        purchase_count: Количество товаров в категории перед удалением.
    """
    unit = UnitOfMeasurement.objects.create(name="Штуки", abbreviation="шт.")
    cat = Category.objects.create(name="Молочное", order=1)
    for i in range(purchase_count):
        Purchase.objects.create(name=f"Товар {i}", category=cat, unit=unit)

    cat.delete()

    assert Purchase.objects.count() == 0


@pytest.mark.django_db
def test_unit_protected_from_deletion_when_referenced():
    """UnitOfMeasurement нельзя удалить, пока на него ссылается товар (on_delete=PROTECT)."""
    unit = UnitOfMeasurement.objects.create(name="Штуки", abbreviation="шт.")
    cat = Category.objects.create(name="Молочное", order=1)
    Purchase.objects.create(name="Молоко", category=cat, unit=unit)

    with pytest.raises(ProtectedError):
        unit.delete()


# ---------------------------------------------------------------------------
# FR-12: страница просмотра
# ---------------------------------------------------------------------------

@pytest.mark.django_db
@pytest.mark.parametrize("is_need_to_buy,should_appear", [
    (True, True),
    (False, False),
])
def test_purchase_visibility_on_view_page(auth_client, is_need_to_buy, should_appear):
    """FR-12: Страница просмотра показывает товар только если is_need_to_buy=True.

    Args:
        auth_client: Авторизованный тестовый клиент Django.
        is_need_to_buy: Статус товара («нужно купить»).
        should_appear: Ожидается ли товар в HTML-ответе.
    """
    unit = UnitOfMeasurement.objects.create(name="Штуки", abbreviation="шт.")
    cat = Category.objects.create(name="Молочное", order=1)
    Purchase.objects.create(
        name="Молоко", category=cat, unit=unit, is_need_to_buy=is_need_to_buy
    )

    response = auth_client.get("/")
    content = response.content.decode()

    assert response.status_code == 200
    if should_appear:
        assert "Молоко" in content
    else:
        assert "Молоко" not in content


@pytest.mark.django_db
def test_category_hidden_from_view_when_all_purchases_bought(auth_client):
    """FR-12: Категория не отображается, если все её товары куплены."""
    unit = UnitOfMeasurement.objects.create(name="Штуки", abbreviation="шт.")
    cat = Category.objects.create(name="Молочное", order=1)
    Purchase.objects.create(name="Молоко", category=cat, unit=unit, is_need_to_buy=False)
    Purchase.objects.create(name="Кефир", category=cat, unit=unit, is_need_to_buy=False)

    response = auth_client.get("/")
    assert response.status_code == 200
    assert "Молочное" not in response.content.decode()


@pytest.mark.django_db
def test_view_page_shows_only_needed_purchases(auth_client):
    """FR-12: Страница просмотра одновременно показывает нужные и скрывает купленные товары."""
    unit = UnitOfMeasurement.objects.create(name="Штуки", abbreviation="шт.")
    cat = Category.objects.create(name="Молочное", order=1)
    Purchase.objects.create(name="Молоко", category=cat, unit=unit, is_need_to_buy=True)
    Purchase.objects.create(name="Кефир", category=cat, unit=unit, is_need_to_buy=False)

    response = auth_client.get("/")
    content = response.content.decode()
    assert "Молоко" in content
    assert "Кефир" not in content


# ---------------------------------------------------------------------------
# Category.create_with_order_shift (FR-04)
# ---------------------------------------------------------------------------

@pytest.mark.django_db
def test_category_create_with_order_shift_inserts_at_position():
    """FR-04: create_with_order_shift сдвигает существующие категории вниз."""
    existing = Category.objects.create(name="Мясо", order=1)
    new_cat = Category.create_with_order_shift(name="Молочное", order=1)

    existing.refresh_from_db()
    assert new_cat.order == 1
    assert existing.order == 2


@pytest.mark.django_db
def test_category_create_with_order_shift_does_not_shift_lower_orders():
    """FR-04: Категории с порядком ниже целевого не сдвигаются."""
    lower = Category.objects.create(name="Хлеб", order=3)
    Category.create_with_order_shift(name="Молочное", order=5)

    lower.refresh_from_db()
    assert lower.order == 3


# ---------------------------------------------------------------------------
# Category.update_with_order_shift (FR-06)
# ---------------------------------------------------------------------------

@pytest.mark.django_db
def test_category_update_with_order_shift_changes_order():
    """FR-06: update_with_order_shift сдвигает категории при смене позиции."""
    cat_a = Category.objects.create(name="А", order=1)
    cat_b = Category.objects.create(name="Б", order=2)

    cat_b.update_with_order_shift(name="Б", order=1)

    cat_a.refresh_from_db()
    assert cat_b.order == 1
    assert cat_a.order == 2


@pytest.mark.django_db
def test_category_update_with_order_shift_same_order_no_shift():
    """FR-06: Если порядок не меняется, другие категории не сдвигаются."""
    cat_a = Category.objects.create(name="А", order=1)
    cat_b = Category.objects.create(name="Б", order=2)

    cat_b.update_with_order_shift(name="Б обновлённая", order=2)

    cat_a.refresh_from_db()
    assert cat_a.order == 1
    assert cat_b.name == "Б обновлённая"


# ---------------------------------------------------------------------------
# CategoryQuerySet.with_active_purchases (FR-12)
# ---------------------------------------------------------------------------

@pytest.mark.django_db
def test_qs_with_active_purchases_returns_only_needed_categories():
    """FR-12: with_active_purchases возвращает только категории с нужными товарами."""
    unit = UnitOfMeasurement.objects.create(name="Штуки", abbreviation="шт.")
    cat_active = Category.objects.create(name="Молочное", order=1)
    cat_empty = Category.objects.create(name="Зелень", order=2)
    Purchase.objects.create(name="Молоко", category=cat_active, unit=unit, is_need_to_buy=True)
    Purchase.objects.create(name="Укроп", category=cat_empty, unit=unit, is_need_to_buy=False)

    qs = Category.objects.with_active_purchases()
    names = list(qs.values_list('name', flat=True))
    assert "Молочное" in names
    assert "Зелень" not in names


@pytest.mark.django_db
def test_qs_with_active_purchases_prefetches_only_needed():
    """FR-12: active_purchases содержит только is_need_to_buy=True."""
    unit = UnitOfMeasurement.objects.create(name="Штуки", abbreviation="шт.")
    cat = Category.objects.create(name="Молочное", order=1)
    Purchase.objects.create(name="Молоко", category=cat, unit=unit, is_need_to_buy=True)
    Purchase.objects.create(name="Кефир", category=cat, unit=unit, is_need_to_buy=False)

    cat_result = Category.objects.with_active_purchases().get(pk=cat.pk)
    purchase_names = [p.name for p in cat_result.active_purchases]
    assert "Молоко" in purchase_names
    assert "Кефир" not in purchase_names


# ---------------------------------------------------------------------------
# CategoryQuerySet.with_all_purchases (FR-13)
# ---------------------------------------------------------------------------

@pytest.mark.django_db
def test_qs_with_all_purchases_includes_all_statuses():
    """FR-13: with_all_purchases возвращает все товары независимо от статуса."""
    unit = UnitOfMeasurement.objects.create(name="Штуки", abbreviation="шт.")
    cat = Category.objects.create(name="Молочное", order=1)
    Purchase.objects.create(name="Молоко", category=cat, unit=unit, is_need_to_buy=True)
    Purchase.objects.create(name="Кефир", category=cat, unit=unit, is_need_to_buy=False)

    cat_result = Category.objects.with_all_purchases().get(pk=cat.pk)
    purchase_names = [p.name for p in cat_result.all_purchases]
    assert "Молоко" in purchase_names
    assert "Кефир" in purchase_names


# ---------------------------------------------------------------------------
# Purchase.set_need_to_buy (FR-15)
# ---------------------------------------------------------------------------

@pytest.mark.django_db
@pytest.mark.parametrize("initial,new_value", [(True, False), (False, True)])
def test_purchase_set_need_to_buy(initial, new_value):
    """FR-15: set_need_to_buy устанавливает значение и сохраняет в БД.

    Args:
        initial: Начальное значение is_need_to_buy.
        new_value: Новое значение для установки.
    """
    unit = UnitOfMeasurement.objects.create(name="Штуки", abbreviation="шт.")
    cat = Category.objects.create(name="Молочное", order=1)
    purchase = Purchase.objects.create(
        name="Молоко", category=cat, unit=unit, is_need_to_buy=initial,
    )

    purchase.set_need_to_buy(new_value)

    purchase.refresh_from_db()
    assert purchase.is_need_to_buy == new_value


# ---------------------------------------------------------------------------
# Purchase.update_fields (FR-10)
# ---------------------------------------------------------------------------

@pytest.mark.django_db
def test_purchase_update_fields_persists_changes():
    """FR-10: update_fields сохраняет новое название, количество и единицу измерения."""
    unit_a = UnitOfMeasurement.objects.create(name="Штуки", abbreviation="шт.")
    unit_b = UnitOfMeasurement.objects.create(name="Килограммы", abbreviation="кг")
    cat = Category.objects.create(name="Молочное", order=1)
    purchase = Purchase.objects.create(name="Молоко", category=cat, unit=unit_a, quantity=1)

    purchase.update_fields(name="Масло", quantity=0.5, unit=unit_b)

    purchase.refresh_from_db()
    assert purchase.name == "Масло"
    assert float(purchase.quantity) == 0.5
    assert purchase.unit == unit_b
