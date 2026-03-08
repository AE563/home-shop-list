import pytest


@pytest.fixture
def user(db, django_user_model):
    """A regular authenticated user for use in tests."""
    return django_user_model.objects.create_user(
        username='testuser',
        password='testpass123',
    )


@pytest.fixture
def auth_client(client, user):
    """Django test client pre-logged in as `user`."""
    client.force_login(user)
    return client


@pytest.fixture
def unit(db):
    """Default unit of measurement for tests."""
    from apps.shop.models import UnitOfMeasurement
    return UnitOfMeasurement.objects.create(name='Штуки', abbreviation='шт.')


@pytest.fixture
def category(db):
    """Default category for tests."""
    from apps.shop.models import Category
    return Category.objects.create(name='Молочное', order=1)


@pytest.fixture
def purchase(db, category, unit):
    """Default purchase for tests."""
    from apps.shop.models import Purchase
    return Purchase.objects.create(
        name='Молоко', category=category, unit=unit, quantity=2, is_need_to_buy=True,
    )