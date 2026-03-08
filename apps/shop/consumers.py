import json

from channels.generic.websocket import AsyncWebsocketConsumer


class ShopConsumer(AsyncWebsocketConsumer):
    """WebSocket consumer for real-time shop list synchronisation (FR-18, FR-19)."""

    GROUP_NAME = 'shop'

    async def connect(self):
        if not self.scope['user'].is_authenticated:
            await self.close()
            return
        await self.channel_layer.group_add(self.GROUP_NAME, self.channel_name)
        await self.accept()

    async def disconnect(self, code):
        await self.channel_layer.group_discard(self.GROUP_NAME, self.channel_name)

    # ------------------------------------------------------------------
    # Receive message from WebSocket client (not used in MVP — server-only push)
    # ------------------------------------------------------------------
    async def receive(self, text_data=None, bytes_data=None):
        pass

    # ------------------------------------------------------------------
    # Handlers for messages coming from the channel layer (group_send)
    # ------------------------------------------------------------------
    async def shop_event(self, event):
        """Forward any shop.* event payload to the WebSocket client."""
        await self.send(text_data=json.dumps(event['payload']))