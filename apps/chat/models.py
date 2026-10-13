from django.db import models

from core.models import CoreModel
from apps.users.models import User
from apps.meetings.models import Meeting

class ConversationType(models.IntegerChoices):

   PRIVATE = 1, "Private"
   GROUP = 2, "Group"

class ContentType(models.IntegerChoices):
   TEXT = 1, "Text"
   IMAGE = 2, "Image"
   VIDEO = 3, "Video"
   AUDIO = 4, "Audio"
   FILE = 5, "File"
   URL = 6, "URL"
   OTHER = 99, "Other"


class Conversation(CoreModel):
   meeting = models.OneToOneField(Meeting, on_delete=models.CASCADE, related_name="conversation")
   is_active = models.BooleanField(default=True)
   conversation_type = models.SmallIntegerField(choices=ConversationType.choices)
   
   def __str__(self):
      return f"Conversation for {self.meeting.title}"


class ConversationParticipant(CoreModel):
   conversation = models.ForeignKey(Conversation, on_delete=models.CASCADE, related_name="members")
   participant = models.ForeignKey(User, on_delete=models.CASCADE, related_name="chat_memberships")
   joined_at = models.DateTimeField(auto_now_add=True)
   last_read_message = models.ForeignKey("Message", on_delete=models.SET_NULL, related_name="last_read_message", null=True, blank=True)
   is_muted = models.BooleanField(default=False)

   class Meta:
      unique_together = ("conversation", "participant")


class Message(CoreModel):
   conversation = models.ForeignKey(Conversation, on_delete=models.CASCADE, related_name="messages")
   sender = models.ForeignKey(User, on_delete=models.CASCADE, related_name="sent_messages")
   content = models.TextField()
   content_type = models.SmallIntegerField(choices=ContentType.choices)
   is_edited = models.BooleanField(default=False)
   edited_at = models.DateTimeField(null=True, blank=True)


   def __str__(self):
      return f"Message from {self.sender.first_name} to {self.conversation.meeting.title}"
