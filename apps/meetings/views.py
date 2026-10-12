from django.core.exceptions import ValidationError

from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response
from .models import ConnectionStatus, Meeting, MeetingParticipant

from .serializers import(
   MeetingListSerializer, 
   MeetingCreateSerializer,
   MeetingDetailSerializer, 
   MeetingParticipantsSerializer, 
   JoinMeetingSerializer,
   MeetingRoomSerializer,
)

class MeetingViewSet(viewsets.ModelViewSet):
   
   def get_serializer_class(self):
      if self.action == 'create':
         return MeetingCreateSerializer
      elif self.action in ('retrieve', 'update', 'partial_update'):
         return MeetingDetailSerializer
      return MeetingListSerializer


   def get_queryset(self):
      return Meeting.objects.filter(created_by=self.request.user)

   def perform_create(self, serializer):
      serializer.save()

   def perform_update(self, serializer):
      serializer.save()

   @action(detail=True, methods=["get"])
   def participants(self, request, pk=None):
      try:
         meeting = Meeting.objects.select_related("settings").get(pk=pk)
      except (Meeting.DoesNotExist, ValidationError, ValueError):
         return Response({"detail": "Not found."}, status=status.HTTP_404_NOT_FOUND)

      joined = MeetingParticipant.objects.filter(
         meeting=meeting,
         user=request.user,
         connection_status=ConnectionStatus.CONNECTED,
      ).exists()
      if meeting.created_by_id != request.user.id and not joined:
         return Response({"detail": "Not found."}, status=status.HTTP_404_NOT_FOUND)

      return Response(MeetingRoomSerializer(meeting).data)



   @action(detail=True, methods=["post"])
   def start(self, request, pk=None):
      try:
         meeting = Meeting.objects.get(pk=pk)
      except (Meeting.DoesNotExist, ValidationError, ValueError):
         return Response({"detail": "Not found."}, status=status.HTTP_404_NOT_FOUND)

      meeting.start()
      return Response({"detail": "Meeting started."}, status=status.HTTP_200_OK)

   
   @action(detail=True, methods=["post"])
   def end(self, request, pk=None):
      try:
         meeting = Meeting.objects.get(pk=pk)
      except (Meeting.DoesNotExist, ValidationError, ValueError):
         return Response({"detail": "Not found."}, status=status.HTTP_404_NOT_FOUND)

      meeting.end()
      return Response({"detail": "Meeting ended."}, status=status.HTTP_200_OK)

   @action(detail=False, methods=["post"])
   def join(self, request):
      serializer = JoinMeetingSerializer(data=request.data, context={"request": request})
      serializer.is_valid(raise_exception=True)
      serializer.save()
      return Response(serializer.data, status=status.HTTP_200_OK)


class MeetingParticipantViewSet(viewsets.ModelViewSet):
   serializer_class = MeetingParticipantsSerializer

   def get_queryset(self):
      return MeetingParticipant.objects.filter(meeting=self.kwargs['meeting_id'])

   def perform_create(self, serializer):
      meeting = Meeting.objects.get(pk=self.kwargs['meeting_pk'])
      serializer.save(meeting=meeting, user=self.request.user)


      
