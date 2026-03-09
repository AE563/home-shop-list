import json
import logging

from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer
from django.contrib.auth.decorators import login_required
from django.db import IntegrityError
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, render
from django.views.decorators.http import require_http_methods

from .consumers import WS_GROUP
from .models import Category, Purchase, UnitOfMeasurement
from .serializers import serialize_category, serialize_purchase

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# WebSocket broadcast helper (FR-18)
# ---------------------------------------------------------------------------


def _broadcast(event_type, payload):
    """Push a JSON event to all WS clients in the shop group.
    No-ops when Redis is unavailable — logs a warning instead of crashing."""
    channel_layer = get_channel_layer()
    if channel_layer is None:
        return
    try:
        async_to_sync(channel_layer.group_send)(
            WS_GROUP,
            {'type': 'shop.event', 'payload': {'type': event_type, **payload}},
        )
    except Exception as e:
        logger.warning('WebSocket broadcast failed (%s): %s', event_type, e)


# ---------------------------------------------------------------------------
# Pages
# ---------------------------------------------------------------------------


@login_required
def view_page(request):
    """FR-12: Show only categories that have at least one is_need_to_buy=True purchase."""
    categories = Category.objects.with_active_purchases()
    return render(request, 'shop/view.html', {'categories': categories})


@login_required
def edit_page(request):
    """FR-13: Show all categories and all purchases."""
    categories = Category.objects.with_all_purchases()
    units = UnitOfMeasurement.objects.order_by('name')
    return render(request, 'shop/edit.html', {'categories': categories, 'units': units})


# ---------------------------------------------------------------------------
# Purchase: toggle (FR-15)
# ---------------------------------------------------------------------------


@login_required
@require_http_methods(['PATCH'])
def toggle_purchase(request, pk):
    """FR-15: Toggle is_need_to_buy for a purchase via AJAX PATCH."""
    purchase = get_object_or_404(Purchase.objects.select_related('unit', 'category'), pk=pk)
    try:
        data = json.loads(request.body)
    except (json.JSONDecodeError, ValueError):
        return JsonResponse({'error': 'Invalid JSON'}, status=400)

    purchase.set_need_to_buy(bool(data.get('is_need_to_buy', purchase.is_need_to_buy)))

    _broadcast('purchase.updated', {'purchase': serialize_purchase(purchase)})
    return JsonResponse({'ok': True, 'is_need_to_buy': purchase.is_need_to_buy})


# ---------------------------------------------------------------------------
# Category CRUD (FR-04, FR-06, FR-07)
# ---------------------------------------------------------------------------


@login_required
@require_http_methods(['POST'])
def create_category(request):
    """FR-04: Create category with cascade priority shift."""
    try:
        data = json.loads(request.body)
    except (json.JSONDecodeError, ValueError):
        return JsonResponse({'error': 'Invalid JSON'}, status=400)

    name = data.get('name', '').strip()
    if not name:
        return JsonResponse({'error': 'Введите название категории.'}, status=400)

    try:
        order = max(1, int(data.get('order', 1)))
    except (TypeError, ValueError):
        order = 1

    try:
        category = Category.create_with_order_shift(name, order)
    except IntegrityError:
        return JsonResponse({'error': 'Категория с таким названием уже существует.'}, status=400)

    _broadcast('category.created', {'category': serialize_category(category)})
    return JsonResponse({'ok': True, 'category': serialize_category(category)}, status=201)


@login_required
@require_http_methods(['PATCH', 'DELETE'])
def category_detail(request, pk):
    """FR-06/07: Update or delete a category."""
    category = get_object_or_404(Category, pk=pk)

    if request.method == 'DELETE':
        pk_int = category.pk
        category.delete()
        _broadcast('category.deleted', {'category_id': pk_int})
        return JsonResponse({'ok': True})

    # PATCH
    try:
        data = json.loads(request.body)
    except (json.JSONDecodeError, ValueError):
        return JsonResponse({'error': 'Invalid JSON'}, status=400)

    name = data.get('name', category.name).strip()
    if not name:
        return JsonResponse({'error': 'Введите название категории.'}, status=400)

    try:
        order = max(1, int(data.get('order', category.order)))
    except (TypeError, ValueError):
        order = category.order

    try:
        category.update_with_order_shift(name, order)
    except IntegrityError:
        return JsonResponse({'error': 'Категория с таким названием уже существует.'}, status=400)

    _broadcast('category.updated', {'category': serialize_category(category)})
    return JsonResponse({'ok': True, 'category': serialize_category(category)})


# ---------------------------------------------------------------------------
# Purchase CRUD (FR-08, FR-10, FR-11)
# ---------------------------------------------------------------------------


@login_required
@require_http_methods(['POST'])
def create_purchase(request):
    """FR-08: Create a new purchase inside a category."""
    try:
        data = json.loads(request.body)
    except (json.JSONDecodeError, ValueError):
        return JsonResponse({'error': 'Invalid JSON'}, status=400)

    name = data.get('name', '').strip()
    if not name:
        return JsonResponse({'error': 'Введите название товара.'}, status=400)

    try:
        quantity = float(data.get('quantity', 1))
    except (TypeError, ValueError):
        quantity = 1.0

    if quantity <= 0:
        return JsonResponse({'error': 'Количество должно быть больше 0.'}, status=400)

    category = get_object_or_404(Category, pk=data.get('category_id'))
    unit = get_object_or_404(UnitOfMeasurement, pk=data.get('unit_id'))

    purchase = Purchase.objects.create(
        name=name,
        quantity=quantity,
        category=category,
        unit=unit,
        is_need_to_buy=True,
    )
    payload = serialize_purchase(purchase)
    _broadcast('purchase.created', {'purchase': payload})
    return JsonResponse({'ok': True, 'purchase': payload}, status=201)


@login_required
@require_http_methods(['PATCH', 'DELETE'])
def purchase_detail(request, pk):
    """FR-10/11: Update or delete a purchase."""
    purchase = get_object_or_404(Purchase.objects.select_related('unit', 'category'), pk=pk)

    if request.method == 'DELETE':
        pk_int = purchase.pk
        category_id = purchase.category_id
        purchase.delete()
        _broadcast('purchase.deleted', {'purchase_id': pk_int, 'category_id': category_id})
        return JsonResponse({'ok': True})

    # PATCH
    try:
        data = json.loads(request.body)
    except (json.JSONDecodeError, ValueError):
        return JsonResponse({'error': 'Invalid JSON'}, status=400)

    name = data.get('name', purchase.name).strip()
    if not name:
        return JsonResponse({'error': 'Введите название товара.'}, status=400)

    try:
        quantity = float(data.get('quantity', purchase.quantity))
    except (TypeError, ValueError):
        quantity = float(purchase.quantity)

    if quantity <= 0:
        return JsonResponse({'error': 'Количество должно быть больше 0.'}, status=400)

    unit = get_object_or_404(UnitOfMeasurement, pk=data.get('unit_id', purchase.unit_id))

    purchase.update_fields(name, quantity, unit)

    payload = serialize_purchase(purchase)
    _broadcast('purchase.updated', {'purchase': payload})
    return JsonResponse({'ok': True, 'purchase': payload})
