# sorties/consumers.py
import json
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
from django.contrib.auth.models import User
from .models import GroupeAmis, Message

class ChatConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.group_name = self.scope['url_route']['kwargs']['group_name']
        self.group_channel_name = f'chat_{self.group_name}'

        await self.channel_layer.group_add(
            self.group_channel_name,
            self.channel_name
        )

        await self.accept()

    async def disconnect(self, close_code):
        await self.channel_layer.group_discard(
            self.group_channel_name,
            self.channel_name
        )

    async def receive(self, text_data):
        text_data_json = json.loads(text_data)
        message = text_data_json['message']

        user = self.scope["user"]
        group = await self.get_group(self.group_name)

        await self.create_message(group, user, message)

        await self.channel_layer.group_send(
            self.group_channel_name,
            {
                'type': 'chat_message',
                'message': message,
                'user': user.username,
            }
        )

    async def chat_message(self, event):
        message = event['message']
        user = event['user']

        await self.send(text_data=json.dumps({
            'message': message,
            'user': user,
        }))

    @database_sync_to_async
    def get_group(self, group_name):
        return GroupeAmis.objects.get(nom=group_name)

    @database_sync_to_async
    def create_message(self, group, user, message):
        return Message.objects.create(group=group, user=user, content=message)
