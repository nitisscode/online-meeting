from django.utils import timezone
from rest_framework.exceptions import NotFound, PermissionDenied, ValidationError

from .models import Message, ConversationParticipant, Conversation, ConversationType
from apps.meetings.models import MeetingParticipant
from .serializers import (
   MessageSerializer,
   SendMessageserializer, 
   EditMessageSerializer, 
   DeleteMessageSerializer, 
   MarkAsReadSerializer, 
   TypingSerializer
)


class MessageService:
   
   @staticmethod
   def is_member(conversation_id, user):
      return ConversationParticipant.objects.filter(
         conversation_id=conversation_id,
         participant=user,
      ).exists()

   @staticmethod
   def create_message(conversation_id, sender, content, content_type):
      if not MessageService.is_member(conversation_id, sender):
         raise PermissionDenied("You are not a member of this conversation.")

      message = Message.objects.create(
         conversation_id=conversation_id,
         sender=sender,
         content=content,
         content_type=content_type,
      )

      return MessageSerializer(message).data

   @staticmethod
   def edit_message(conversation_id, message_id, sender, content, content_type):
      message = MessageService.verify_message_and_owner(conversation_id, message_id, sender)

      message.content = content
      message.content_type = content_type
      message.is_edited = True
      message.edited_at = timezone.now()

      message.save(update_fields=["content", "content_type", "is_edited", "edited_at"])

      return MessageSerializer(message).data

   @staticmethod
   def delete_message(conversation_id, message_id, sender):
      message = MessageService.verify_message_and_owner(conversation_id, message_id, sender)
      message.soft_delete()

      return True


   @staticmethod
   def verify_message_and_owner(conversation_id, message_id, user):
      try:
         message = Message.objects.get(conversation_id=conversation_id, id=message_id, is_deleted=False)
      except Message.DoesNotExist:
         raise NotFound("Message not found")

      if message.sender != user:
         raise PermissionDenied("You are not the owner of this message.")

      return message


class ConversationService:

   @staticmethod
   
   def get_conversation(meeting_id):
      try:
         return Conversation.objects.get(meeting_id=meeting_id, is_active=True)
      except Conversation.DoesNotExist:
         raise NotFound("Conversation not found")

   @staticmethod
   def create_conversation(meeting_id, conversation_type=ConversationType.GROUP):
      conversation, _ = Conversation.objects.get_or_create(
         meeting_id=meeting_id, 
         conversation_type=conversation_type,
         is_active=True
         )
      return conversation

   @staticmethod
   def add_participant(conversation_id, participant):
      if not ConversationService.validate_meeting_participant(participant, conversation_id=conversation_id):
         raise PermissionDenied("You are not a participant of this conversation.")

      return ConversationParticipant.objects.get_or_create(
         conversation_id=conversation_id, 
         participant=participant
      )

   @staticmethod
   def create_conversation_and_participant(meeting_id, participant):
      conversation = ConversationService.create_conversation(meeting_id)
      ConversationService.add_participant(conversation.id, participant)
      return conversation
   
   @staticmethod
   def validate_conversation(conversation_id):
      try:
         return Conversation.objects.get(id=conversation_id, is_active=True).exists()
      except Conversation.DoesNotExist:
         raise NotFound("Conversation not found")

   @staticmethod
   def validate_meeting_participant(participant, meeting_id=None, conversation_id=None):
      if not meeting_id:
         if not conversation_id:
            raise ValidationError("Meeting ID or Conversation ID is required")
         
         meeting_id = Conversation.objects.get(id=conversation_id).meeting_id

      return MeetingParticipant.objects.filter(meeting_id=meeting_id, user=participant).exists()

   
   
