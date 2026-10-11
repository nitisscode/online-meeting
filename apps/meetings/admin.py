from django.contrib import admin
from unfold.admin import ModelAdmin, StackedInline, TabularInline

from apps.meetings.models import Meeting, MeetingParticipant, MeetingSettings


class MeetingSettingsInline(StackedInline):
    model = MeetingSettings
    extra = 0
    max_num = 1
    can_delete = False
    tab = True


class MeetingParticipantInline(TabularInline):
    model = MeetingParticipant
    extra = 0
    fields = ("user", "role", "connection_status", "joined_at", "left_at", "is_deleted")
    readonly_fields = ("joined_at", "left_at")
    autocomplete_fields = ("user",)
    show_change_link = True
    tab = True


@admin.register(Meeting)
class MeetingAdmin(ModelAdmin):
    list_display = (
        "title",
        "meeting_code",
        "created_by",
        "status",
        "is_private",
        "scheduled_at",
        "is_deleted",
        "created_at",
    )
    list_filter = ("status", "is_private", "is_deleted", "scheduled_at")
    search_fields = ("title", "meeting_code", "created_by__email", "created_by__username")
    readonly_fields = ("meeting_code", "created_at", "modified_at")
    autocomplete_fields = ("created_by",)
    inlines = (MeetingSettingsInline, MeetingParticipantInline)

    fieldsets = (
        (
            "General",
            {
                "classes": ["tab"],
                "fields": (
                    "title",
                    "description",
                    "meeting_code",
                    "created_by",
                    "status",
                ),
            },
        ),
        (
            "Schedule",
            {
                "classes": ["tab"],
                "fields": (
                    "scheduled_at",
                    "started_at",
                    "ended_at",
                ),
            },
        ),
        (
            "Access",
            {
                "classes": ["tab"],
                "fields": (
                    "is_private",
                    "pass_code",
                ),
            },
        ),
        (
            "Metadata",
            {
                "classes": ["tab"],
                "fields": (
                    "is_deleted",
                    "created_at",
                    "modified_at",
                ),
            },
        ),
    )

    def get_queryset(self, request):
        return (
            super()
            .get_queryset(request)
            .select_related("created_by", "settings")
            .prefetch_related("participants__user")
        )


@admin.register(MeetingParticipant)
class MeetingParticipantAdmin(ModelAdmin):
    list_display = (
        "meeting",
        "user",
        "role",
        "connection_status",
        "joined_at",
        "left_at",
        "is_deleted",
        "created_at",
    )
    list_filter = ("role", "connection_status", "is_deleted")
    search_fields = (
        "meeting__title",
        "meeting__meeting_code",
        "user__email",
        "user__username",
    )
    readonly_fields = ("created_at", "modified_at")
    autocomplete_fields = ("meeting", "user")

    def get_queryset(self, request):
        return super().get_queryset(request).select_related("meeting", "user")


@admin.register(MeetingSettings)
class MeetingSettingsAdmin(ModelAdmin):
    list_display = (
        "meeting",
        "allow_chat",
        "allow_screen_share",
        "allow_recording",
        "waiting_room_enabled",
        "allow_raise_hand",
        "is_deleted",
    )
    list_filter = (
        "allow_chat",
        "allow_screen_share",
        "allow_recording",
        "waiting_room_enabled",
        "allow_raise_hand",
        "is_deleted",
    )
    search_fields = ("meeting__title", "meeting__meeting_code")
    readonly_fields = ("created_at", "modified_at")
    autocomplete_fields = ("meeting",)

    def get_queryset(self, request):
        return super().get_queryset(request).select_related("meeting")
