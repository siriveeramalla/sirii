'''import json
from channels.generic.websocket import AsyncWebsocketConsumer
from .models import Room, RoomContent
from asgiref.sync import async_to_sync

class DocumentConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.room_id = self.scope['url_route']['kwargs']['room_id']
        self.room_group_name = f'document_{self.room_id}'

        # Join room group
        await self.channel_layer.group_add(
            self.room_group_name,
            self.channel_name
        )

        await self.accept()

    async def disconnect(self, close_code):
        # Leave room group
        await self.channel_layer.group_discard(
            self.room_group_name,
            self.channel_name
        )

    async def receive(self, text_data):
        text_data_json = json.loads(text_data)
        content = text_data_json['content']

        # Broadcast the content to the group (all users in the room)
        await self.channel_layer.group_send(
            self.room_group_name,
            {
                'type': 'document_update',
                'content': content
            }
        )
    async def receive(self, text_data):
        data = json.loads(text_data)

        if data.get('type') == 'save_document':
            await self.save_document(data['content'])
        else:
            content = data['content']
            await self.channel_layer.group_send(
                self.room_group_name,
                {
                    'type': 'document_update',
                    'content': content
                }
            )

    @database_sync_to_async
    def save_document(self, content):
        room = Room.objects.get(id=self.room_id)
        room_content, created = RoomContent.objects.get_or_create(room=room)
        room_content.content = content
        room_content.save()
    # Receive message from room group
    async def document_update(self, event):
        content = event['content']

        # Send the document content to WebSocket
        await self.send(text_data=json.dumps({
            'content': content
        }))'''
import json
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
from django.contrib.sessions.models import Session
from django.utils import timezone
from varuni.models import Document, UserStatus,Room

active_users = {}
editing_users = {}

class DocumentConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.room_id = self.scope['url_route']['kwargs']['room_id']
        self.room_group_name = f'document_{self.room_id}'
        self.user = self.scope['user']

        await self.channel_layer.group_add(self.room_group_name, self.channel_name)
        await self.accept()

        if self.user.is_authenticated:
            username = self.user.username

            if self.room_id not in active_users:
                active_users[self.room_id] = set()
            active_users[self.room_id].add(username)

            await self.set_user_status(active=True)

            await self.send_active_users()

    async def disconnect(self, close_code):
        if self.user.is_authenticated:
            username = self.user.username

            # Remove from active_users
            if self.room_id in active_users and username in active_users[self.room_id]:
                active_users[self.room_id].remove(username)
                if not active_users[self.room_id]:
                    del active_users[self.room_id]

            # Remove from editing_users
            if self.room_id in editing_users and username in editing_users[self.room_id]:
                editing_users[self.room_id].remove(username)
                if not editing_users[self.room_id]:
                    del editing_users[self.room_id]

            await self.set_user_status(active=False)

            # Optional: force logout
         #   await self.force_logout(self.user)

            await self.send_active_users()

        await self.channel_layer.group_discard(self.room_group_name, self.channel_name)

    async def receive(self, text_data):
        data = json.loads(text_data)
        message_type = data.get('type')

        if message_type == 'send_edit':
            # Broadcast the edit to others
            await self.channel_layer.group_send(
                self.room_group_name,
                {
                    'type': 'edit_message',
                    'message': data['message'],
                    'username': data['username']
                }
            )

        elif message_type == 'save_document':
            room_id = self.scope['url_route']['kwargs']['room_id']
            content = data['content']
            await self.save_document(room_id, content)

    async def broadcast_edit(self, event):
        await self.send(text_data=json.dumps(event['data']))

    async def send_active_users(self):
        await self.channel_layer.group_send(self.room_group_name, {
            'type': 'active_users_update',
            'active_users': list(active_users.get(self.room_id, []))
        })

    async def active_users_update(self, event):
        await self.send(text_data=json.dumps({
            'type': 'active_users',
            'users': event['active_users']
        }))

    async def add_editing_user(self):
        username = self.user.username
        if self.room_id not in editing_users:
            editing_users[self.room_id] = set()
        editing_users[self.room_id].add(username)

        await self.channel_layer.group_send(self.room_group_name, {
            'type': 'editing_users_update',
            'editing_users': list(editing_users[self.room_id])
        })

    async def editing_users_update(self, event):
        await self.send(text_data=json.dumps({
            'type': 'editing_users',
            'users': event['editing_users']
        }))

    @database_sync_to_async
    def save_document(self, content):
        room_id = self.scope['url_route']['kwargs']['room_id']
        try:
            room = Room.objects.get(id=room_id)
            room.document = content
            room.save()
            print("Document saved successfully.")
        except Room.DoesNotExist:
            print("Room not found.")


    @database_sync_to_async
    def set_user_status(self, active=True):
        try:
            status, created = UserStatus.objects.get_or_create(user=self.user)
            status.is_active = active
            status.room_id = self.room_id if active else None
            status.save()
        except:
            pass