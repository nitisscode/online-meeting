from rest_framework import serializers
from rest_framework.exceptions import NotFound, PermissionDenied
from django.db import transaction
from django.utils import timezone

from apps.chat.models import Conversation, ConversationType
from apps.chat.services import ConversationService
from apps.users.models import User
from apps.users.serializers import UserResponseSerializer
from .models import Meeting, MeetingParticipant, MeetingSettings
from .models import ParticipantRole, ConnectionStatus, MeetingStatus


class MeetingSettingsSerializer(serializers.ModelSerializer):
   class Meta:
      model = MeetingSettings
      fields = [
         'id',
         'meeting',
         'allow_chat',
         'allow_screen_share',
         'allow_recording',
         'waiting_room_enabled',
         'allow_raise_hand',
      ]
      read_only_fields = ['id', 'meeting']


   # def create(self, validated_data):
   #    validated_data['meeting'] = self.context['request'].meeting
   #    return super().create(validated_data)

class MeetingListSerializer(serializers.ModelSerializer):
   class Meta:
      model = Meeting
      fields = [
         'id',
         'title',
         'status',
         'scheduled_at',
         'started_at',
         'ended_at',
         'meeting_code',
      ]
      read_only_fields = fields

class MeetingCreateSerializer(serializers.ModelSerializer):
   settings = MeetingSettingsSerializer(required=False)
   class Meta:
      model = Meeting
      fields = [
         'id',
         'title',
         'description',
         'meeting_code',
         'status',
         'scheduled_at',
         'started_at',
         'ended_at',
         'is_private',
         'pass_code',
         'created_by',
         'settings',
      ]
      read_only_fields = ['id', 'meeting_code', 'created_by', 'created_at', 'updated_at']

   def create(self, validated_data):
      settings_data = validated_data.pop("settings", {})
      user = self.context["request"].user
      
      with transaction.atomic():
         meeting = Meeting.objects.create(created_by=user, **validated_data)
         MeetingSettings.objects.create(meeting=meeting, **settings_data)
         MeetingParticipant.objects.create(
            meeting=meeting, user=user, role=ParticipantRole.HOST,
         )
      
      return meeting

   def to_representation(self, instance):
      data = super().to_representation(instance)
      data['settings'] = MeetingSettingsSerializer(instance.settings).data
      return data


class MeetingDetailSerializer(serializers.ModelSerializer):
   settings = MeetingSettingsSerializer(required=False)
   class Meta:
      model = Meeting
      fields = [
         'id',
         'title',
         'description',
         'meeting_code',
         'status',
         'scheduled_at',
         'started_at',
         'ended_at',
         'is_private',
         'pass_code',
         'created_by',
         'settings',
      ]
      read_only_fields = [
         'id',
         'title',
         'description',
         'meeting_code',
         'status',
         'scheduled_at',
         'started_at',
         'ended_at',
         'is_private',
         'pass_code',
         'created_by',
      ]

   def update(self, instance, validated_data):
      settings_data = validated_data.pop("settings", None)
      
      if settings_data:
         settings, _created = MeetingSettings.objects.get_or_create(meeting=instance)
         for attr, value in settings_data.items():
            setattr(settings, attr, value)
         settings.save()
         return instance

      




class MeetingParticipantsListSerializer(serializers.ModelSerializer):
   user = UserResponseSerializer(read_only=True)

   class Meta:
      model = MeetingParticipant
      fields = [
         'id',
         'user',
         'role',
         'connection_status',
         'joined_at',
         'left_at',
      ]
      read_only_fields = fields


class MeetingParticipantsSerializer(serializers.ModelSerializer):
   users = serializers.PrimaryKeyRelatedField(many=True, queryset=User.objects.all())
   
   class Meta:
      model = MeetingParticipant
      fields = [
         'id',
         'meeting',
         'users',
         'role',
      ]
      read_only_fields = ['id']

   def create(self, validated_data):
      meeting = Meeting.objects.get(pk=self.context['meeting_pk'])

      users = validated_data.pop('users')
      with transaction.atomic():
         MeetingParticipant.objects.bulk_create(
            [
               MeetingParticipant(
                  meeting=meeting, 
                  user=user, 
                  role=ParticipantRole.PARTICIPANT,
                  connection_status=ConnectionStatus.INVITED,
               ) for user in users
            ]
         )
      return meeting


class MeetingRoomSerializer(serializers.ModelSerializer):
   settings = MeetingSettingsSerializer(read_only=True)
   participants = MeetingParticipantsListSerializer(
      source='connected_participants', read_only=True, many=True
   )
   conversation_id = serializers.SerializerMethodField()

   class Meta:
      model = Meeting
      fields = [
         'id',
         'title',
         'meeting_code',
         'status',
         'started_at',
         'conversation_id',
         'settings',
         'participants',
      ]
      read_only_fields = fields

   def get_conversation_id(self, meeting):
      try:
         conversation = meeting.conversation
      except Conversation.DoesNotExist:
         return None
      if conversation.is_deleted or not conversation.is_active:
         return None
      return conversation.id


class JoinMeetingSerializer(serializers.Serializer):
   meeting_code = serializers.CharField(required=True)
   pass_code = serializers.CharField(required=False, allow_blank=True, allow_null=True)

   def validate(self, attrs):
      meeting_code = attrs.get("meeting_code")
      pass_code = attrs.get("pass_code") or ""

      try:
         meeting = Meeting.objects.select_related("settings").get(meeting_code=meeting_code)
      except Meeting.DoesNotExist:
         raise NotFound("Invalid meeting code.")

      meeting.ensure_joinable()

      if meeting.pass_code and meeting.pass_code != pass_code:
         raise PermissionDenied("Invalid pass code.")

      attrs["meeting"] = meeting
      return attrs

   def create(self, validated_data):
      meeting = validated_data["meeting"]
      user = self.context["request"].user
      MeetingParticipant.objects.update_or_create(
         meeting=meeting,
         user=user,
         defaults={
            "connection_status": ConnectionStatus.CONNECTED,
            "joined_at": timezone.now(),
            "left_at": None,
         },
      )
      conversation = ConversationService.create_conversation_and_participant(meeting.id, user)
      
      return meeting

   def to_representation(self, instance):
      return MeetingRoomSerializer(instance).data

