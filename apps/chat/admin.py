from django.contrib import admin
from unfold.admin import ModelAdmin, TabularInline

from .models import Conversation, ConversationParticipant, Message


class ConversationParticipantInline(TabularInline):
    model = ConversationParticipant
    extra = 0
    fields = ("participant", "joined_at", "last_read_message", "is_muted", "is_deleted")
    readonly_fields = ("joined_at",)
    autocomplete_fields = ("participant", "last_read_message")
    tab = True


class MessageInline(TabularInline):
    model = Message
    extra = 0
    fields = ("sender", "content_type", "content", "is_edited", "edited_at", "is_deleted", "created_at")
    readonly_fields = ("is_edited", "edited_at", "created_at")
    autocomplete_fields = ("sender",)
    ordering = ("created_at",)
    show_change_link = True
    tab = True


@admin.register(Conversation)
class ConversationAdmin(ModelAdmin):
    list_display = ("meeting", "conversation_type", "is_active", "is_deleted", "created_at")
    list_filter = ("conversation_type", "is_active", "is_deleted")
    search_fields = ("meeting__title", "meeting__meeting_code")
    readonly_fields = ("created_at", "modified_at")
    autocomplete_fields = ("meeting",)
    inlines = (ConversationParticipantInline, MessageInline)

    def get_queryset(self, request):
        return super().get_queryset(request).select_related("meeting")


@admin.register(Message)
class MessageAdmin(ModelAdmin):
    list_display = ("conversation", "sender", "content_type", "short_content", "is_edited", "is_deleted", "created_at")
    list_filter = ("content_type", "is_edited", "is_deleted")
    search_fields = ("content", "sender__email", "sender__username", "conversation__meeting__title")
    readonly_fields = ("is_edited", "edited_at", "created_at", "modified_at")
    autocomplete_fields = ("conversation", "sender")

    @admin.display(description="Content")
    def short_content(self, obj):
        return obj.content[:50]

    def get_queryset(self, request):
        return super().get_queryset(request).select_related("conversation__meeting", "sender")

        