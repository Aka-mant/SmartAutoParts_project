from django.urls import path

from .apps import ChatConfig
from .views import (
    # ChatRoom
    ChatRoomListAPIView,
    ChatRoomCreateAPIView,
    ChatRoomRetrieveAPIView,
    ChatRoomUpdateAPIView,
    ChatRoomDeleteAPIView,

    # ChatParticipant
    ChatParticipantListAPIView,
    ChatParticipantCreateAPIView,
    ChatParticipantRetrieveAPIView,
    ChatParticipantUpdateAPIView,
    ChatParticipantDeleteAPIView,

    # ChatMessage
    ChatMessageListAPIView,
    ChatMessageCreateAPIView,
    ChatMessageRetrieveAPIView,
    ChatMessageUpdateAPIView,
    ChatMessageDeleteAPIView,
)

app_name = ChatConfig.name

urlpatterns = [
    # ==========================
    # Комнаты чата
    # ==========================
    path(
        "rooms/",
        ChatRoomListAPIView.as_view(),
        name="chat_room_list",
    ),
    path(
        "rooms/create/",
        ChatRoomCreateAPIView.as_view(),
        name="chat_room_create",
    ),
    path(
        "rooms/<int:pk>/",
        ChatRoomRetrieveAPIView.as_view(),
        name="chat_room_detail",
    ),
    path(
        "rooms/<int:pk>/update/",
        ChatRoomUpdateAPIView.as_view(),
        name="chat_room_update",
    ),
    path(
        "rooms/<int:pk>/delete/",
        ChatRoomDeleteAPIView.as_view(),
        name="chat_room_delete",
    ),

    # ==========================
    # Участники чата
    # ==========================
    path(
        "participants/",
        ChatParticipantListAPIView.as_view(),
        name="chat_participant_list",
    ),
    path(
        "participants/create/",
        ChatParticipantCreateAPIView.as_view(),
        name="chat_participant_create",
    ),
    path(
        "participants/<int:pk>/",
        ChatParticipantRetrieveAPIView.as_view(),
        name="chat_participant_detail",
    ),
    path(
        "participants/<int:pk>/update/",
        ChatParticipantUpdateAPIView.as_view(),
        name="chat_participant_update",
    ),
    path(
        "participants/<int:pk>/delete/",
        ChatParticipantDeleteAPIView.as_view(),
        name="chat_participant_delete",
    ),

    # ==========================
    # Сообщения чата
    # ==========================
    path(
        "messages/",
        ChatMessageListAPIView.as_view(),
        name="chat_message_list",
    ),
    path(
        "messages/create/",
        ChatMessageCreateAPIView.as_view(),
        name="chat_message_create",
    ),
    path(
        "messages/<int:pk>/",
        ChatMessageRetrieveAPIView.as_view(),
        name="chat_message_detail",
    ),
    path(
        "messages/<int:pk>/update/",
        ChatMessageUpdateAPIView.as_view(),
        name="chat_message_update",
    ),
    path(
        "messages/<int:pk>/delete/",
        ChatMessageDeleteAPIView.as_view(),
        name="chat_message_delete",
    ),
]
