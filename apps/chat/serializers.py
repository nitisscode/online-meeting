from rest_framework import serializers

from .models import Conversation, ConversationParticipant, Message
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

