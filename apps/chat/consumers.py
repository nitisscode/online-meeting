import asyncio
import time
import json
from django.core.serializers.json import DjangoJSONEncoder

from channels.db import database_sync_to_async
from channels.generic.websocket import AsyncJsonWebsocketConsumer
from rest_framework.exceptions import APIException
from apps.chat.handlers.messages import MessageHandler
from apps.chat.services import MessageService
from apps.constants.ws_status import WSStatusCodes, WSErrorCodes
from apps.constants.chat import ChatOperations

class ChatConsumer(AsyncJsonWebsocketConsumer):
   async def connect(self):
      self.user = self.scope["user"]
      self.conversation_id = self.scope["url_route"]["kwargs"]["conversation_id"]
      self.group_name = f"conversation_{self.conversation_id}"
      self.joined = False
      self.token_exp = None

      await self.accept()

      if not self.user.is_authenticated:
         await self.close(code=WSStatusCodes.UNAUTHORIZED, reason="Unauthorized")
         return

      if not await database_sync_to_async(MessageService.is_member)(self.conversation_id, self.user):
         await self.close(code=WSStatusCodes.FORBIDDEN, reason="You are not a member of this conversation")
         return

      await self.channel_layer.group_add(
         self.group_name,
         self.channel_name,
      )
      
      self.joined = True
      self.expiry_task = asyncio.create_task(self.expire_token())

      await MessageHandler(self, {}).chat_history()

   async def disconnect(self, close_code):
      if getattr(self, "expiry_task", None):
         self.expiry_task.cancel()
      
      if self.joined:
         await self.channel_layer.group_discard(
            self.group_name,
            self.channel_name,
         )

   async def expire_token(self):
      await asyncio.sleep(self.scope["token_exp"] - time.time())
      await self.close(code=WSStatusCodes.FORBIDDEN, reason="Token expired")

   async def receive(self, text_data=None, bytes_data=None, **kwargs):
      
      if text_data is None:
         await self.send_error(WSStatusCodes.INVALID_FORMAT, "Only JSON text frames are supported.")
         return
      
      try:
         content = await self.decode_json(text_data)
      except ValueError:
         await self.send_error(WSStatusCodes.INVALID_FORMAT, WSErrorCodes.INVALID_JSON)
         return
      
      if not isinstance(content, dict):
         await self.send_error(WSStatusCodes.INVALID_FORMAT, WSErrorCodes.INVALID_JSON)
         return
      
      try:
         await MessageHandler(self, content).handle()
      except APIException as e:
         await self.send_error(ChatOperations.ERROR, str(e))

   async def broadcast(self, payload, exclude_self=False):
      await self.channel_layer.group_send(
         self.group_name,
         {
            "type": "group.event",
            "payload": await self.encode_json(payload),
            "sender_channel": self.channel_name if exclude_self else None,
         }
      )

   async def send_error(self, code, reason):
      await self.send_json(
         {
            "op": ChatOperations.ERROR,
            "data": {
               "code": code,
               "reason": reason,
            }
         }
      )

   async def group_event(self, event):
      if event["sender_channel"] != self.channel_name:
         await self.send(text_data=event["payload"])
      

   async def encode_json(self, content):
      return json.dumps(content, cls=DjangoJSONEncoder)


