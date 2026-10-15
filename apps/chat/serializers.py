from rest_framework import serializers

from .models import Conversation, ConversationParticipant, Message, ContentType
from apps.users.serializers import UserResponseSerializer


class ConversationSerializer(serializers.ModelSerializer):
   class Meta:
      model = Conversation
      fields = "__all__"

class ConversationParticipantSerializer(serializers.ModelSerializer):
   class Meta:
      model = ConversationParticipant
      fields = "__all__"

class MessageSerializer(serializers.ModelSerializer):
   sender = UserResponseSerializer(read_only=True)
   class Meta:
      model = Message
      fields = "__all__"
      read_only_fields = ["id", "sender", "is_edited", "edited_at", "created_at"]

   def validate_conversation(self, conversation):
      user = self.context["request"].user
      
      if not conversation.members.filter(participant=user).exists():
         raise serializers.ValidationError("You are not a member of this conversation.")
      return conversation



#### Websocket Serializers

MAX_MSG_LENGTH = 1000

class SendMessageserializer(serializers.Serializer):
   content = serializers.CharField(max_length=MAX_MSG_LENGTH)
   content_type = serializers.ChoiceField(choices=ContentType.choices)


class EditMessageSerializer(serializers.Serializer):
   message_id = serializers.UUIDField()
   content = serializers.CharField(max_length=MAX_MSG_LENGTH)
   content_type = serializers.ChoiceField(choices=ContentType.choices)

class DeleteMessageSerializer(serializers.Serializer):
   message_id = serializers.UUIDField()

class MarkAsReadSerializer(serializers.Serializer):
   message_id = serializers.UUIDField()

class TypingSerializer(serializers.Serializer):
   is_typing = serializers.BooleanField()