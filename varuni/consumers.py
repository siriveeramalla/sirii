import json
from channels.generic.websocket import AsyncWebsocketConsumer
from django.contrib.auth.models import User
from channels.db import database_sync_to_async
from .models import Room, RoomContent

active_users = {}  

class DocumentConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.room_id = self.scope['url_route']['kwargs']['room_id']
        self.room_group_name = f'document_{self.room_id}'
        self.user = self.scope['user']
        self.username = self.user.username

        await self.channel_layer.group_add(self.room_group_name, self.channel_name)
        await self.accept()

        
        if self.room_id not in active_users:
            active_users[self.room_id] = {}
        active_users[self.room_id][self.username] = self.channel_name

        
        await self.channel_layer.group_send(
            self.room_group_name,
            {
                'type': 'user_join',
                'username': self.username,
                'users': list(active_users[self.room_id].keys())
            }
        )

        
        content = await self.get_room_content(self.room_id)
        await self.send(text_data=json.dumps({
            'type': 'load',
            'content': content
        }))

    async def disconnect(self, close_code):
        await self.channel_layer.group_discard(self.room_group_name, self.channel_name)

        if self.room_id in active_users and self.username in active_users[self.room_id]:
            del active_users[self.room_id][self.username]

            
            await self.channel_layer.group_send(
                self.room_group_name,
                {
                    'type': 'user_leave',
                    'username': self.username,
                    'users': list(active_users[self.room_id].keys())
                }
            )

    async def receive(self, text_data):
        data = json.loads(text_data)
        msg_type = data.get("type")

        if msg_type == "edit":
            await self.channel_layer.group_send(
                self.room_group_name,
                {
                    "type": "document_edit",
                    "username": self.username,
                    "content": data["content"],
                    "cursor": data.get("cursor")
                }
            )

        elif msg_type == "save":
            await self.save_room_content(self.room_id, data["content"])
            await self.send(text_data=json.dumps({
                "type": "save",
                "message": "Document saved successfully."
            }))

        elif msg_type == "join-call":
            
            for user, channel in active_users[self.room_id].items():
                if user != self.username:
                    await self.channel_layer.send(channel, {
                        "type": "call_joined",
                        "username": self.username
                    })

        elif msg_type in ["offer", "answer", "ice-candidate"]:
            target = data.get("target")
            if not target:
                return
            target_channel = active_users[self.room_id].get(target)
            if target_channel:
                await self.channel_layer.send(target_channel, {
                    "type": "webrtc_signal",
                    "message_type": msg_type,
                    "username": self.username,
                    "payload": data.get("offer") or data.get("answer") or data.get("candidate")
                })

    

    async def document_edit(self, event):
        if event["username"] != self.username:
            await self.send(text_data=json.dumps({
                "type": "edit",
                "username": event["username"],
                "content": event["content"],
                "cursor": event.get("cursor")
            }))

    async def user_join(self, event):
        await self.send(text_data=json.dumps({
            "type": "user_join",
            "username": event["username"],
            "users": event["users"]
        }))

    async def user_leave(self, event):
        await self.send(text_data=json.dumps({
            "type": "user_leave",
            "username": event["username"],
            "users": event["users"]
        }))

    async def call_joined(self, event):
        await self.send(text_data=json.dumps({
            "type": "join-call",
            "username": event["username"]
        }))

    async def webrtc_signal(self, event):
        await self.send(text_data=json.dumps({
            "type": event["message_type"],
            "username": event["username"],
            **({"offer": event["payload"]} if event["message_type"] == "offer" else {}),
            **({"answer": event["payload"]} if event["message_type"] == "answer" else {}),
            **({"candidate": event["payload"]} if event["message_type"] == "ice-candidate" else {}),
        }))

   
    @database_sync_to_async
    def get_room_content(self, room_id):
        room = Room.objects.get(id=room_id)
        content, _ = RoomContent.objects.get_or_create(room=room)
        return content.content

    @database_sync_to_async
    def save_room_content(self, room_id, content):
        room = Room.objects.get(id=room_id)
        room_content, _ = RoomContent.objects.get_or_create(room=room)
        room_content.content = content
        room_content.save()