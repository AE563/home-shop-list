"""Shared utility functions for the Home Shop List project."""


def cascade_shift_order(model_class, from_order, exclude_pk=None):
    """
    Shift all instances of model_class with order >= from_order down by 1.
    Optionally exclude the instance with the given pk (used during updates).

    FR-04, FR-06: category priority conflict — cascade shift.
    """
    qs = model_class.objects.filter(order__gte=from_order)
    if exclude_pk is not None:
        qs = qs.exclude(pk=exclude_pk)
    qs.update(order=models.F('order') + 1)


try:
    from django.db import models  # noqa: F401 — imported for F() expression above
except ImportError:
    pass
