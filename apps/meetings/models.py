import secrets

from django.db import models
from django.utils import timezone

from apps.users.models import User
from core.models import CoreModel

from .exceptions import MeetingStateError

MEETING_CODE_LENGTH = 10
MEETING_CODE_ALPHABET = "ABCDEFGHJKLMNPQRSTUVWXYZ23456789"

class MeetingStatus(models.IntegerChoices):
   SCHEDULED = 0, "Scheduled"
   LIVE = 1, "Live"
   ENDED = 2, "Ended"
   CANCELLED = 3, "Cancelled"


class ParticipantRole(models.IntegerChoices):
   HOST = 0, "Host"
   CO_HOST = 1, "Co Host"
   PARTICIPANT = 2, "Participant"


class ConnectionStatus(models.IntegerChoices):
   CONNECTING = 0, "Connecting"
   CONNECTED = 1, "Connected"
   DISCONNECTED = 2, "Disconnected"
   LEFT = 3, "Left"
   INVITED = 4, "Invited"



def generate_meeting_code() -> str:
   return "".join(secrets.choice(MEETING_CODE_ALPHABET) for _ in range(MEETING_CODE_LENGTH))


class Meeting(CoreModel):
   meeting_code = models.CharField(max_length=10, unique=True, default=generate_meeting_code)
   created_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name='meetings')
   title = models.CharField(max_length=255)
   description = models.TextField(blank=True, null=True)
   status = models.PositiveSmallIntegerField(choices=MeetingStatus.choices, default=MeetingStatus.SCHEDULED)
   scheduled_at = models.DateTimeField(blank=True, null=True)
   started_at = models.DateTimeField(blank=True, null=True)
   ended_at = models.DateTimeField(blank=True, null=True)
   is_private = models.BooleanField(default=False)
   pass_code = models.CharField(max_length=10, blank=True, null=True)


   def __str__(self):
      return self.title

   def is_ongoing(self):
      return self.status == MeetingStatus.LIVE

   def ensure_not_closed(self):
      if self.status == MeetingStatus.ENDED:
         raise MeetingStateError("Meeting has ended")
      if self.status == MeetingStatus.CANCELLED:
         raise MeetingStateError("Meeting has been cancelled")
   
   def ensure_joinable(self):
      self.ensure_not_closed()

      if not self.is_ongoing():
         raise MeetingStateError("Meeting is not ongoing")

   def start(self):
      self.ensure_not_closed()
      if self.is_ongoing():
         raise MeetingStateError("Meeting is already ongoing")
      self.status = MeetingStatus.LIVE
      self.started_at = timezone.now()
      self.save()

   def end(self):
      if not self.is_ongoing():
         raise MeetingStateError("Meeting is not ongoing")

      self.status = MeetingStatus.ENDED
      self.ended_at = timezone.now()
      self.save()

   def connected_participants(self):
      return self.participants.connected().select_related("user").order_by("role", "created_at")


class MeetingParticipantQuerySet(models.QuerySet):
   def connected(self):
      return self.filter(connection_status=ConnectionStatus.CONNECTED)

class MeetingParticipant(CoreModel):
   meeting = models.ForeignKey(Meeting, on_delete=models.CASCADE, related_name="participants")
   user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="meeting_participations")

   role = models.PositiveSmallIntegerField(choices=ParticipantRole.choices, default=ParticipantRole.PARTICIPANT)

   connection_status = models.PositiveSmallIntegerField(
      null=True,
      blank=True,
      choices=ConnectionStatus.choices,
   )

   joined_at = models.DateTimeField(null=True, blank=True)
   left_at = models.DateTimeField(null=True, blank=True)

   objects = MeetingParticipantQuerySet.as_manager()

   class Meta:
      unique_together = ("meeting", "user")

   def __str__(self):
      return f"{self.user} - {self.meeting}"



class MeetingSettings(CoreModel):
   meeting = models.OneToOneField(Meeting, on_delete=models.CASCADE, related_name="settings")
   allow_chat = models.BooleanField(default=True)
   allow_screen_share = models.BooleanField(default=True)
   allow_recording = models.BooleanField(default=False)
   waiting_room_enabled = models.BooleanField(default=False)
   allow_raise_hand = models.BooleanField(default=True)

   def __str__(self):
      return f"{self.meeting}"


