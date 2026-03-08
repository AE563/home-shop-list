from django.db import models
from django.db.models import F, Prefetch


class CategoryQuerySet(models.QuerySet):
    def with_active_purchases(self):
        """FR-12: Categories with is_need_to_buy=True purchases prefetched."""
        need_to_buy_qs = (
            Purchase.objects
            .filter(is_need_to_buy=True)
            .select_related('unit')
            .order_by('name')
        )
        return (
            self
            .prefetch_related(
                Prefetch('purchases', queryset=need_to_buy_qs, to_attr='active_purchases')
            )
            .filter(purchases__is_need_to_buy=True)
            .distinct()
            .order_by('order', 'name')
        )

    def with_all_purchases(self):
        """FR-13: All categories with all purchases prefetched."""
        all_qs = Purchase.objects.select_related('unit').order_by('name')
        return (
            self
            .prefetch_related(
                Prefetch('purchases', queryset=all_qs, to_attr='all_purchases')
            )
            .order_by('order', 'name')
        )


class Category(models.Model):
    name = models.CharField(max_length=255, unique=True)
    order = models.PositiveSmallIntegerField(default=1)  # priority; 1 = highest

    objects = CategoryQuerySet.as_manager()

    class Meta:
        ordering = ['order', 'name']

    def __str__(self):
        return self.name

    @classmethod
    def create_with_order_shift(cls, name: str, order: int) -> 'Category':
        """FR-04: Shift existing categories down, then insert new one at given position."""
        cls.objects.filter(order__gte=order).update(order=F('order') + 1)
        return cls.objects.create(name=name, order=order)

    def update_with_order_shift(self, name: str, order: int) -> None:
        """FR-06: Shift other categories if order changes, then save."""
        if order != self.order:
            Category.objects.filter(order__gte=order).exclude(pk=self.pk).update(order=F('order') + 1)
        self.name = name
        self.order = order
        self.save()


class UnitOfMeasurement(models.Model):
    name = models.CharField(max_length=50, unique=True)
    abbreviation = models.CharField(max_length=10)

    class Meta:
        ordering = ['name']

    def __str__(self):
        return self.abbreviation


class Purchase(models.Model):
    name = models.CharField(max_length=255)
    is_need_to_buy = models.BooleanField(default=True)
    quantity = models.DecimalField(max_digits=8, decimal_places=2, default=1)
    category = models.ForeignKey(
        Category,
        on_delete=models.CASCADE,
        related_name='purchases',
    )
    unit = models.ForeignKey(
        UnitOfMeasurement,
        on_delete=models.PROTECT,
        related_name='purchases',
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['category__order', 'name']
        indexes = [models.Index(fields=['is_need_to_buy'])]

    def __str__(self):
        return f"{self.name} ({self.quantity:.2f} {self.unit.abbreviation})"

    def set_need_to_buy(self, value: bool) -> None:
        """FR-15: Set buy status and persist only relevant fields."""
        self.is_need_to_buy = value
        self.save(update_fields=['is_need_to_buy', 'updated_at'])

    def update_fields(self, name: str, quantity: float, unit: 'UnitOfMeasurement') -> None:
        """FR-10: Update editable fields and persist."""
        self.name = name
        self.quantity = quantity
        self.unit = unit
        self.save()
