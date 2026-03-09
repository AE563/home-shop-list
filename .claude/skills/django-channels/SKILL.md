---
name: django-channels
description: Django Channels and WebSocket expertise. Use when implementing real-time features, WebSocket consumers, channel layers, ASGI configuration, or Redis message broker. Activates for tasks involving real-time sync, live updates, or WebSocket connections.
---

# Django Channels + WebSocket

You are an expert in Django Channels 4, ASGI, and real-time communication patterns. You write correct, efficient WebSocket consumers and client-side connection logic.

## Key distinction

- **Redis** = channel layer (message broker between consumers). Required.
- **Celery** = background task queue (cron jobs, async tasks). NOT needed for WebSockets.

## ASGI setup (config/asgi.py)

```python
import os
from django.core.asgi import get_asgi_application
from channels.routing import ProtocolTypeRouter, URLRouter
from channels.auth import AuthMiddlewareStack
import apps.shop.routing

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')

application = ProtocolTypeRouter({
    'http': get_asgi_application(),
    'websocket': AuthMiddlewareStack(
        URLRouter(apps.shop.routing.websocket_urlpatterns)
    ),
})
```

## Channel layer (settings.py)

```python
CHANNEL_LAYERS = {
    'default': {
        'BACKEND': 'channels_redis.core.RedisChannelLayer',
        'CONFIG': {
            'hosts': [config('REDIS_URL', default='redis://127.0.0.1:6379/0')],
        },
    },
}
```

## WebSocket routing (apps/shop/routing.py)

```python
from django.urls import re_path
from . import consumers

websocket_urlpatterns = [
    re_path(r'ws/shop/$', consumers.ShopConsumer.as_asgi()),
]
```

## Consumer (apps/shop/consumers.py)

```python
import json
from channels.generic.websocket import AsyncWebsocketConsumer

class ShopConsumer(AsyncWebsocketConsumer):
    GROUP_NAME = 'shop'  # All users share one group = one shared list

    async def connect(self):
        # Reject unauthenticated connections
        if not self.scope['user'].is_authenticated:
            await self.close()
            return
        await self.channel_layer.group_add(self.GROUP_NAME, self.channel_name)
        await self.accept()

    async def disconnect(self, close_code):
        await self.channel_layer.group_discard(self.GROUP_NAME, self.channel_name)

    async def receive(self, text_data):
        # Clients do NOT send WS messages -- changes go through REST API
        # Consumer only broadcasts, does not receive actions from client
        pass

    # Handler called by channel layer when a broadcast is sent
    async def shop_update(self, event):
        await self.send(text_data=json.dumps(event['payload']))
```

## Broadcasting from a view (apps/shop/views.py)

```python
from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer

channel_layer = get_channel_layer()

def broadcast(payload: dict):
    """Send a message to all connected WebSocket clients."""
    async_to_sync(channel_layer.group_send)(
        'shop',
        {
            'type': 'shop.update',  # Maps to consumer method shop_update()
            'payload': payload,
        }
    )

# Call after any data change:
broadcast({'type': 'purchase.updated', 'purchase_id': item.pk, 'is_need_to_buy': False})
```

## Event type naming convention

```
purchase.created   -- new item added
purchase.updated   -- item fields changed (name, quantity, is_need_to_buy)
purchase.deleted   -- item removed
category.created
category.updated
category.deleted
```

## Client-side (static/js/websocket.js)

```javascript
(function () {
  const WS_URL = `ws://${window.location.host}/ws/shop/`;
  const RECONNECT_DELAY_MS = 3000;
  let socket;

  function connect() {
    socket = new WebSocket(WS_URL);

    socket.onopen = () => {
      hideBanner();
    };

    socket.onmessage = (event) => {
      const data = JSON.parse(event.data);
      handleEvent(data);
    };

    socket.onclose = () => {
      showBanner('Соединение потеряно, переподключение...');
      setTimeout(connect, RECONNECT_DELAY_MS);
    };

    socket.onerror = () => {
      socket.close(); // triggers onclose -> retry
    };
  }

  function handleEvent(data) {
    switch (data.type) {
      case 'purchase.updated': onPurchaseUpdated(data); break;
      case 'purchase.created': onPurchaseCreated(data); break;
      case 'purchase.deleted': onPurchaseDeleted(data); break;
      case 'category.created': onCategoryCreated(data); break;
      case 'category.updated': onCategoryUpdated(data); break;
      case 'category.deleted': onCategoryDeleted(data); break;
    }
  }

  connect();
})();
```

## Common mistakes

- Do NOT run `manage.py runserver` for Channels in production -- use Daphne or Uvicorn
- For local dev `runserver` works fine with Channels 4
- Do NOT put business logic in consumers -- keep consumers thin, logic in views/services
- Do NOT forget `AuthMiddlewareStack` -- without it `scope['user']` is anonymous
- The `type` field in `group_send` maps to a consumer method: dots become underscores (`shop.update` → `shop_update`)

## Local Redis start

```bash
# Check Redis is running before starting Django
redis-cli ping   # expected: PONG

# Start Redis if not running
sudo systemctl start redis-server
```
