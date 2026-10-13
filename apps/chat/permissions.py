from rest_framework.permissions import BasePermission, SAFE_METHODS

from .models import Conversation, ConversationParticipant

class IsConversationParticipant(BasePermission):
   def has_permission(self, request, view):
      if not request.user or not request.user.is_authenticated:
         return False

      conversation_id = view.query_params.get("conversation_id")

      if conversation_id is None:
         return False

      return ConversationParticipant.objects.filter(
            conversation_id=conversation_id,
            participant=request.user,
        ).exists()


class IsMessageSenderOrReadOnly(BasePermission):
   def has_object_permission(self, request, view, obj):
      return request.method in SAFE_METHODS or obj.sender_id == request.user.id

