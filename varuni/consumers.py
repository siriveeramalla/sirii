import json
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

    # Receive message from room group
    async def document_update(self, event):
        content = event['content']

        # Send the document content to WebSocket
        await self.send(text_data=json.dumps({
            'content': content
        }))