import json
from channels.generic.websocket import AsyncWebsocketConsumer
from django.core.exceptions import ObjectDoesNotExist
from .models import Room,RoomContent
active_users = {}
class DocumentConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.room_id = self.scope['url_route']['kwargs']['room_id']
        self.username = self.scope["user"].username
        self.room_group_name = f"document_{self.room_id}"

        await self.channel_layer.group_add(self.room_group_name, self.channel_name)
        await self.accept()

        if self.room_id not in active_users:
            active_users[self.room_id] = {}
        active_users[self.room_id][self.channel_name] = self.username

        await self.channel_layer.group_send(
            self.room_group_name,
            {
                "type": "user_list_update",
                "users": list(active_users[self.room_id].values())
            }
        )

    async def disconnect(self, close_code):
        await self.channel_layer.group_discard(self.room_group_name, self.channel_name)
        if self.room_id in active_users and self.channel_name in active_users[self.room_id]:
            del active_users[self.room_id][self.channel_name]
            await self.channel_layer.group_send(
                self.room_group_name,
                {
                    "type": "user_list_update",
                    "users": list(active_users[self.room_id].values())
                }
            )

    async def receive(self, text_data):
        data = json.loads(text_data)
        content = data.get("content", "")
        caret = data.get("caret", None)
        username = data.get("username", self.username)

        try:
            room = await self.get_room(self.room_id)
            room_content, _ = await RoomContent.objects.aget_or_create(room=room)
            room_content.content = content
            await room_content.asave(update_fields=["content"])

            await self.channel_layer.group_send(
                self.room_group_name,
                {
                    "type": "document_update",
                    "content": content,
                    "caret": caret,
                    "username": username
                }
            )
        except ObjectDoesNotExist:
            await self.send(text_data=json.dumps({"error": "Room not found"}))

    async def document_update(self, event):
        await self.send(text_data=json.dumps({
            "content": event["content"],
            "caret": event.get("caret", None),
            "username": event.get("username", "")
        }))

    async def user_list_update(self, event):
        await self.send(text_data=json.dumps({
            "type": "user_list",
            "users": event["users"]
        }))

    @staticmethod
    async def get_room_content(room_id):
        room = await Room.objects.aget(pk=room_id)
        content, _ = await RoomContent.objects.aget_or_create(room=room)
        return content

    @staticmethod
    async def save_room_content(room_content, content):
        room_content.content = content
        await room_content.asave(update_fields=["content"])
