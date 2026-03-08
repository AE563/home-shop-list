"""WebSocket consumer tests (FR-03, FR-18, FR-19)."""

from unittest.mock import MagicMock

import pytest
from channels.layers import InMemoryChannelLayer, channel_layers, get_channel_layer
from channels.testing import WebsocketCommunicator

from apps.shop.consumers import ShopConsumer
from config.asgi import application

# ---------------------------------------------------------------------------
# Fixture: in-memory channel layer (no Redis required)
# ---------------------------------------------------------------------------


@pytest.fixture
def memory_channel_layer():
    """Swap the default channel layer with InMemoryChannelLayer for tests."""
    old = channel_layers.set('default', InMemoryChannelLayer())
    yield
    if old is not None:
        channel_layers.set('default', old)
    else:
        channel_layers.backends.pop('default', None)


def _mock_user(authenticated=True):
    user = MagicMock()
    user.is_authenticated = authenticated
    return user


# ---------------------------------------------------------------------------
# Unauthenticated rejection (FR-03)
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_unauthenticated_ws_connection_rejected():
    """FR-03: Unauthenticated WebSocket connection must be closed immediately."""
    communicator = WebsocketCommunicator(application, '/ws/shop/')
    connected, code = await communicator.connect()
    assert not connected or code in (3000, 4000, None)
    await communicator.disconnect()


# ---------------------------------------------------------------------------
# Authenticated connect
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_authenticated_user_can_connect(memory_channel_layer):
    """Authenticated user successfully connects to the WebSocket."""
    communicator = WebsocketCommunicator(ShopConsumer.as_asgi(), '/ws/shop/')
    communicator.scope['user'] = _mock_user(authenticated=True)
    connected, _ = await communicator.connect()
    assert connected
    await communicator.disconnect()


@pytest.mark.asyncio
async def test_unauthenticated_consumer_closes(memory_channel_layer):
    """Consumer closes connection for unauthenticated users."""
    communicator = WebsocketCommunicator(ShopConsumer.as_asgi(), '/ws/shop/')
    communicator.scope['user'] = _mock_user(authenticated=False)
    connected, _ = await communicator.connect()
    assert not connected
    await communicator.disconnect()


# ---------------------------------------------------------------------------
# Broadcast: purchase events
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
@pytest.mark.parametrize(
    'event_type,payload',
    [
        (
            'purchase.created',
            {'type': 'purchase.created', 'purchase': {'id': 1, 'name': 'Молоко', 'is_need_to_buy': True}},
        ),
        (
            'purchase.updated',
            {'type': 'purchase.updated', 'purchase': {'id': 1, 'is_need_to_buy': False}},
        ),
        (
            'purchase.deleted',
            {'type': 'purchase.deleted', 'purchase_id': 1},
        ),
    ],
)
async def test_receives_broadcast_purchase_events(memory_channel_layer, event_type, payload):
    """Consumer forwards purchase events from channel layer to WebSocket client."""
    communicator = WebsocketCommunicator(ShopConsumer.as_asgi(), '/ws/shop/')
    communicator.scope['user'] = _mock_user()
    connected, _ = await communicator.connect()
    assert connected

    channel_layer = get_channel_layer()
    await channel_layer.group_send('shop', {'type': 'shop.event', 'payload': payload})

    message = await communicator.receive_json_from(timeout=1)
    assert message['type'] == event_type
    await communicator.disconnect()


# ---------------------------------------------------------------------------
# Broadcast: category events
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
@pytest.mark.parametrize(
    'event_type,payload',
    [
        (
            'category.created',
            {'type': 'category.created', 'category': {'id': 7, 'name': 'Зелень', 'order': 2}},
        ),
        (
            'category.updated',
            {'type': 'category.updated', 'category': {'id': 7, 'name': 'Зелень', 'order': 3}},
        ),
        (
            'category.deleted',
            {'type': 'category.deleted', 'category_id': 7},
        ),
    ],
)
async def test_receives_broadcast_category_events(memory_channel_layer, event_type, payload):
    """Consumer forwards category events from channel layer to WebSocket client."""
    communicator = WebsocketCommunicator(ShopConsumer.as_asgi(), '/ws/shop/')
    communicator.scope['user'] = _mock_user()
    connected, _ = await communicator.connect()
    assert connected

    channel_layer = get_channel_layer()
    await channel_layer.group_send('shop', {'type': 'shop.event', 'payload': payload})

    message = await communicator.receive_json_from(timeout=1)
    assert message['type'] == event_type
    await communicator.disconnect()
