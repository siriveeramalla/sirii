import json
from channels.generic.websocket import AsyncWebsocketConsumer
from django.core.exceptions import ObjectDoesNotExist
from .models import Room

class DocumentConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.room_id = self.scope['url_route']['kwargs']['room_id']
        self.room_group_name = f"document_{self.room_id}"
        self.user = self.scope["user"]

        await self.channel_layer.group_add(self.room_group_name, self.channel_name)
        await self.accept()

    async def disconnect(self, close_code):
        await self.channel_layer.group_discard(self.room_group_name, self.channel_name)

    async def receive(self, text_data):
        data = json.loads(text_data)
        content = data.get("content")
        cursor_position = data.get("cursor_position", 0)
        username = self.user.username if self.user.is_authenticated else "Anonymous"

        try:
            room = await self.get_room(self.room_id)
            room.content = content
            await self.save_room(room)

            await self.channel_layer.group_send(
                self.room_group_name,
                {
                    "type": "document_update",
                    "content": content,
                    "username": username,
                    "cursor_position": cursor_position,
                    "sender_channel": self.channel_name
                }
            )
        except ObjectDoesNotExist:
            await self.send(text_data=json.dumps({"error": "Room not found"}))

    async def document_update(self, event):
        if event["sender_channel"] != self.channel_name:
            await self.send(text_data=json.dumps({
                "content": event["content"],
                "username": event["username"],
                "cursor_position": event["cursor_position"]
            }))

    @staticmethod
    async def get_room(room_id):
        return await Room.objects.aget(pk=room_id)

    @staticmethod
    async def save_room(room):
        await room.asave(update_fields=["content"])
