"""Tests for apps/core/utils.py — cascade_shift_order helper."""

import pytest

from apps.core.utils import cascade_shift_order
from apps.shop.models import Category


@pytest.mark.django_db
def test_cascade_shift_order_shifts_all_matching(db):
    """cascade_shift_order increments order for all instances >= from_order."""
    cat1 = Category.objects.create(name='Первый', order=1)
    cat2 = Category.objects.create(name='Второй', order=2)
    cat3 = Category.objects.create(name='Третий', order=3)

    cascade_shift_order(Category, from_order=2)

    cat1.refresh_from_db()
    cat2.refresh_from_db()
    cat3.refresh_from_db()

    assert cat1.order == 1  # below threshold — unchanged
    assert cat2.order == 3  # shifted
    assert cat3.order == 4  # shifted


@pytest.mark.django_db
def test_cascade_shift_order_excludes_pk(db):
    """cascade_shift_order with exclude_pk skips that instance."""
    cat1 = Category.objects.create(name='Первый', order=1)
    cat2 = Category.objects.create(name='Второй', order=2)

    cascade_shift_order(Category, from_order=1, exclude_pk=cat1.pk)

    cat1.refresh_from_db()
    cat2.refresh_from_db()

    assert cat1.order == 1  # excluded — unchanged
    assert cat2.order == 3  # shifted


@pytest.mark.django_db
def test_cascade_shift_order_no_matches_does_nothing(db):
    """cascade_shift_order with no matching rows is a no-op."""
    cat = Category.objects.create(name='Один', order=5)

    cascade_shift_order(Category, from_order=10)

    cat.refresh_from_db()
    assert cat.order == 5  # unchanged
