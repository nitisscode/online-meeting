from rest_framework import serializers
from django.db import transaction

from apps.users.models import User
from .models import Meeting, MeetingParticipant, MeetingSettings
from .models import ParticipantRole


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
                  role=ParticipantRole.PARTICIPANT
               ) for user in users
            ]
         )
      return meeting



