from rest_framework.viewsets import ModelViewSet
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework import status

from .models import Conversation, ConversationParticipant, Message
from .serializers import ConversationSerializer, ConversationParticipantSerializer, MessageSerializer
from .permissions import IsConversationParticipant, IsMessageSenderOrReadOnly

class ConversationViewSet(ModelViewSet):
   serializer_class = ConversationSerializer

   def get_queryset(self):
      return Conversation.objects.all()



class ConversationParticipantViewSet(ModelViewSet):
   serializer_class = ConversationParticipantSerializer

   def get_queryset(self):
      return ConversationParticipant.objects.all()


class MessageViewSet(ModelViewSet):
   serializer_class = MessageSerializer
   permission_classes = [IsMessageSenderOrReadOnly]

   def get_queryset(self):
      queryset = (
         Message.objects
         .filter(conversation__members__participant=self.request.user)
         .select_related("sender")
         .order_by("created_at")
      )
      conversation_id = self.request.query_params.get("conversation_id")
      if conversation_id:
         queryset = queryset.filter(conversation_id=conversation_id)
      return queryset
   
   def perform_create(self, serializer):
      serializer.save(sender=self.request.user)
   
   def perform_update(self, serializer):
      serializer.instance.update_edited()

   def perform_destroy(self, instance):
      instance.soft_delete()
      