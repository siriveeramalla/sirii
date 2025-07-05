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

        await self.channel_layer.group_add(self.room_group_name, self.channel_name)
        await self.accept()

        if self.room_id not in active_users:
            active_users[self.room_id] = {}
        active_users[self.room_id][self.user.username] = self.channel_name

        await self.channel_layer.group_send(
            self.room_group_name,
            {
                'type': 'user_join',
                'username': self.user.username,
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

        if self.room_id in active_users and self.user.username in active_users[self.room_id]:
            del active_users[self.room_id][self.user.username]
            await self.channel_layer.group_send(
                self.room_group_name,
                {
                    'type': 'user_leave',
                    'username': self.user.username,
                    'users': list(active_users[self.room_id].keys())
                }
            )

    async def receive(self, text_data):
        data = json.loads(text_data)
        message_type = data.get('type')

        if message_type == 'edit':
            content = data['content']
            cursor = data.get('cursor', None)
            await self.channel_layer.group_send(
                self.room_group_name,
                {
                    'type': 'document_edit',
                    'username': self.user.username,
                    'content': content,
                    'cursor': cursor
                }
            )

        elif message_type == 'save':
            content = data['content']
            await self.save_room_content(self.room_id, content)
            await self.send(text_data=json.dumps({
                'type': 'save',
                'message': 'Document saved successfully.'
            }))

        elif message_type in ['offer', 'answer', 'ice-candidate']:
            await self.channel_layer.group_send(
                self.room_group_name,
                {
                    'type': 'webrtc_signal',
                    'username': self.user.username,
                    'message_type': message_type,
                    'data': data['data']
                }
            )

    async def document_edit(self, event):
        if self.user.username != event['username']:
            await self.send(text_data=json.dumps({
                'type': 'edit',
                'username': event['username'],
                'content': event['content'],
                'cursor': event.get('cursor')
            }))

    async def user_join(self, event):
        await self.send(text_data=json.dumps({
            'type': 'user_join',
            'username': event['username'],
            'users': event['users']
        }))

    async def user_leave(self, event):
        await self.send(text_data=json.dumps({
            'type': 'user_leave',
            'username': event['username'],
            'users': event['users']
        }))

    async def webrtc_signal(self, event):
        if self.user.username != event['username']:
            await self.send(text_data=json.dumps({
                'type': event['message_type'],
                'username': event['username'],
                'data': event['data']
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
