from django.conf import settings
from django.db import models
from django.utils.translation import gettext_lazy as _


class ChatRoom(models.Model):
    """
    Модель комнаты чата.

    Представляет отдельный чат, в котором пользователи могут
    обмениваться сообщениями. Комната может быть публичной
    или приватной и содержит информацию о создателе и дате
    создания.
    """

    name = models.CharField(
        max_length=255,
        verbose_name=_("Name"),
    )

    is_private = models.BooleanField(
        default=False,
        verbose_name=_("Private"),
        help_text=_("Indicates whether the chat room is private."),
    )

    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        related_name="created_chat_rooms",
        null=True,
        blank=True,
        verbose_name=_("Created by"),
    )

    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name=_("Created at"),
    )

    class Meta:
        db_table = "chat_chatroom"
        ordering = ("name",)
        verbose_name = _("Chat room")
        verbose_name_plural = _("Chat rooms")

    def __str__(self):
        return self.name


class ChatParticipant(models.Model):
    """
    Модель участника чата.

    Хранит информацию об участниках комнат чата.
    Реализует связь между пользователем и комнатой,
    а также фиксирует дату присоединения пользователя
    к чату.
    """

    room = models.ForeignKey(
        ChatRoom,
        on_delete=models.CASCADE,
        related_name="participants",
        verbose_name=_("Chat room"),
    )

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="chat_participations",
        verbose_name=_("User"),
    )

    joined_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name=_("Joined at"),
    )

    class Meta:
        db_table = "chat_chatparticipant"
        ordering = ("room", "user")
        verbose_name = _("Chat participant")
        verbose_name_plural = _("Chat participants")
        constraints = [
            models.UniqueConstraint(
                fields=("room", "user"),
                name="uq_room_user",
            ),
        ]

    def __str__(self):
        return f"{self.user.email} → {self.room.name}"


class ChatMessage(models.Model):
    """
    Модель сообщения чата.

    Хранит сообщения пользователей, отправленные в комнаты
    чата. Содержит текст сообщения, автора, комнату,
    информацию о редактировании и дату отправки.
    """

    room = models.ForeignKey(
        ChatRoom,
        on_delete=models.CASCADE,
        related_name="messages",
        verbose_name=_("Chat room"),
    )

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="chat_messages",
        verbose_name=_("User"),
    )

    message = models.TextField(
        verbose_name=_("Message"),
    )

    is_edited = models.BooleanField(
        default=False,
        verbose_name=_("Edited"),
        help_text=_("Indicates whether the message has been edited."),
    )

    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name=_("Created at"),
    )

    class Meta:
        db_table = "chat_chatmessage"
        ordering = ("created_at",)
        verbose_name = _("Chat message")
        verbose_name_plural = _("Chat messages")

    def __str__(self):
        return (
            f"{self.user.email}: "
            f"{self.message[:50]}"
            f"{'...' if len(self.message) > 50 else ''}"
        )
