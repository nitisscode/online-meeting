from django.urls import path
from rest_framework.routers import DefaultRouter

from .views import ConversationViewSet, ConversationParticipantViewSet, MessageViewSet

router = DefaultRouter()
router.register(r'conversations', ConversationViewSet, basename='conversation')
router.register(r'conversation-participants', ConversationParticipantViewSet, basename='conversation-participant')
router.register(r'messages', MessageViewSet, basename='message')

urlpatterns = [] + router.urls

