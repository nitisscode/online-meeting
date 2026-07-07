import secrets
import string

from django.db import models

from apps.users.models import User
from core.models import CoreModel


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


