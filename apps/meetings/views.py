from rest_framework import generics, status, viewsets
from rest_framework.permissions import IsAuthenticated
from .models import Meeting, MeetingParticipant, MeetingSettings

from .serializers import(
   MeetingListSerializer, 
   MeetingCreateSerializer,
   MeetingDetailSerializer, 
   MeetingParticipantsSerializer, 
   MeetingSettingsSerializer,
)


class MeetingViewSet(viewsets.ModelViewSet):
   
   def get_serializer_class(self):
      if self.action == 'create':
         return MeetingCreateSerializer
      elif self.action == 'retrieve':
         return MeetingDetailSerializer
      return MeetingListSerializer


   def get_queryset(self):
      return Meeting.objects.filter(created_by=self.request.user)

   def perform_create(self, serializer):
      serializer.save()


class MeetingParticipantViewSet(viewsets.ModelViewSet):
   serializer_class = MeetingParticipantsSerializer

   def get_queryset(self):
      return MeetingParticipant.objects.filter(meeting=self.kwargs['meeting_id'])

   def perform_create(self, serializer):
      meeting = Meeting.objects.get(pk=self.kwargs['meeting_pk'])
      serializer.save(meeting=meeting, user=self.request.user)



