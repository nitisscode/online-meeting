from django.urls import path

from rest_framework.routers import DefaultRouter

from .views import MeetingViewSet, MeetingParticipantViewSet


router = DefaultRouter()
router.register(r'', MeetingViewSet, basename='meeting')
router.register(r'participants', MeetingParticipantViewSet, basename='meeting-participant')


urlpatterns = [] + router.urls
