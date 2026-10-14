from channels.generic.websocket import AsyncJsonWebsocketConsumer
from channels.db import database_sync_to_async

from apps.chat.models import Conversation, ConversationParticipant



class ChatConsumer(AsyncJsonWebsocketConsumer):
   async def connect(self):
      self.user = self.scope["user"]
      self.conversation_id = self.scope["url_route"]["kwargs"]["conversation_id"]
      self.group_name = f"conversation_{self.conversation_id}"

      if not self.user.is_authenticated:
         await self.close(code=4001, reason="Unauthorized")
         return

      if not await self.is_conversation_member():
         await self.close(code=4002, reason="You are not a member of this conversation")
         return

      await self.channel_layer.group_add(
         self.group_name,
         self.channel_name,
      )

      await self.accept()

   async def disconnect(self, close_code):
      if hasattr(self, "group_name"):
         await self.channel_layer.group_discard(
            self.group_name,
            self.channel_name,
         )

   

   @database_sync_to_async
   def is_conversation_member(self):
      return ConversationParticipant.objects.filter(
         conversation_id=self.conversation_id,
         participant=self.user,
      ).exists()

