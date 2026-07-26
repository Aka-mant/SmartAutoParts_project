from django.contrib import admin

from .models import ChatMessage, ChatParticipant, ChatRoom


@admin.register(ChatRoom)
class ChatRoomAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "name",
        "is_private",
        "created_by",
        "created_at",
    )
    list_filter = ("is_private", "created_at")
    search_fields = ("name", "created_by__email")
    autocomplete_fields = ("created_by",)
    readonly_fields = ("created_at",)


@admin.register(ChatParticipant)
class ChatParticipantAdmin(admin.ModelAdmin):
    list_display = ("id", "room", "user", "joined_at")
    search_fields = ("room__name", "user__email")
    autocomplete_fields = ("room", "user")
    readonly_fields = ("joined_at",)


@admin.register(ChatMessage)
class ChatMessageAdmin(admin.ModelAdmin):
    list_display = ("id", "room", "user", "message_preview", "created_at")
    list_filter = ("is_edited", "created_at")
    search_fields = ("room__name", "user__email", "message")
    autocomplete_fields = ("room", "user")
    readonly_fields = ("created_at",)

    @admin.display(description="Сообщение")
    def message_preview(self, obj):
        return obj.message[:80]
