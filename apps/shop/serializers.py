"""JSON helpers for WebSocket messages (PRD section 8.5)."""


def serialize_category(category):
    """Return a dict representation of a Category instance."""
    return {
        'id': category.pk,
        'name': category.name,
        'order': category.order,
    }


def serialize_purchase(purchase):
    """Return a dict representation of a Purchase instance."""
    return {
        'id': purchase.pk,
        'name': purchase.name,
        'is_need_to_buy': purchase.is_need_to_buy,
        'quantity': str(purchase.quantity),
        'unit_id': purchase.unit_id,
        'unit_name': purchase.unit.name,
        'unit_abbreviation': purchase.unit.abbreviation,
        'category_id': purchase.category_id,
        'category_name': purchase.category.name,
        'category_order': purchase.category.order,
    }