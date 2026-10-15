from channels.db import database_sync_to_async

from apps.constants.chat import ChatOperations
from apps.chat.services import MessageService
from apps.chat.serializers import (
   SendMessageserializer, 
   EditMessageSerializer, 
   DeleteMessageSerializer, 
   TypingSerializer
)

class MessageHandler:
   def __init__(self, consumer, payload):
      self.consumer = consumer
      self.payload = payload
      self.op = payload.get("op")
      self.data = payload.get("data")


   async def handle(self):
      match self.op:
         case ChatOperations.MESSAGE_SENT:
            return await self.send_message()
         
         case ChatOperations.MESSAGE_EDITED:
            return await self.edit_message()
         
         case ChatOperations.MESSAGE_DELETED:
            return await self.delete_message()
         
         case ChatOperations.MESSAGE_TYPING:
            return await self.typing()
         
         case _:
            raise ValueError(f"Invalid operation: {self.op}")
        
   async def validate(self, serializer_class):
      serializer = serializer_class(data=self.data)
      serializer.is_valid(raise_exception=True)
      return serializer.validated_data


   async def send_message(self):
      data = await self.validate(SendMessageserializer)

      message = await database_sync_to_async(MessageService.create_message)(
         conversation_id=self.consumer.conversation_id,
         sender=self.consumer.user,
         **data,
      )

      await self.consumer.broadcast({"op": ChatOperations.MESSAGE_RECEIVED, "data": message})


   async def edit_message(self):
      data = await self.validate(EditMessageSerializer)

      message = await database_sync_to_async(MessageService.edit_message)(
         conversation_id=self.consumer.conversation_id,
         sender=self.consumer.user,
         **data,
      )

      await self.consumer.broadcast({"op": ChatOperations.MESSAGE_EDITED, "data": message})

   async def delete_message(self):
      data = await self.validate(DeleteMessageSerializer)
      
      await database_sync_to_async(MessageService.delete_message)(
         conversation_id=self.consumer.conversation_id,
         sender=self.consumer.user,
         **data,
      )

      await self.consumer.broadcast(
         {
            "op": ChatOperations.MESSAGE_DELETED, 
            "data": data,
         }
      )


   async def typing(self):
      data = await self.validate(TypingSerializer)

      await self.consumer.broadcast(
         {
            "op": ChatOperations.MESSAGE_TYPING,
            "data": {
               "user_id": str(self.consumer.user.id),
               "is_typing": data.get("is_typing"),
            }
         },
         exclude_self=True,
      )