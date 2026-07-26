from django.contrib.auth import get_user_model
from django.contrib.auth.models import AnonymousUser
from datetime import timedelta
from unittest.mock import patch

from django.conf import settings
from django.core.cache import cache
from django.test import RequestFactory, TestCase, override_settings
from django.urls import reverse
from django.utils import timezone

from apps.AI.services import ModerationDecision
from apps.subscriptions.models import SubscriptionPlan, UserSubscription
from users.models import UserAgreementAcceptance

from .models import ChatMessage, ChatParticipant, ChatRoom
from .views import (
    ChatMessageDeleteAPIView,
    ChatMessageListAPIView,
    ChatMessageRetrieveAPIView,
    ChatMessageUpdateAPIView,
    ChatParticipantDeleteAPIView,
    ChatParticipantListAPIView,
    ChatParticipantRetrieveAPIView,
    ChatParticipantUpdateAPIView,
    ChatRoomDeleteAPIView,
    ChatRoomListAPIView,
    ChatRoomRetrieveAPIView,
    ChatRoomUpdateAPIView,
    available_messages_queryset,
    available_participants_queryset,
    available_rooms_queryset,
    manageable_participants_queryset,
    manageable_rooms_queryset,
)


class ChatQuerysetSafetyTests(TestCase):
    """
    Проверяет безопасное построение queryset для Swagger
    и сохранение правил доступа к объектам чата.
    """

    @classmethod
    def setUpTestData(cls):
        user_model = get_user_model()
        cls.owner = user_model.objects.create_user(
            email="owner@example.com",
            username="owner",
            password="test-password",
        )
        cls.member = user_model.objects.create_user(
            email="member@example.com",
            username="member",
            password="test-password",
        )
        cls.stranger = user_model.objects.create_user(
            email="stranger@example.com",
            username="stranger",
            password="test-password",
        )

        cls.public_room = ChatRoom.objects.create(
            name="Public room",
            created_by=cls.owner,
        )
        cls.private_room = ChatRoom.objects.create(
            name="Private room",
            is_private=True,
            created_by=cls.owner,
        )
        cls.membership = ChatParticipant.objects.create(
            room=cls.private_room,
            user=cls.member,
        )
        cls.message = ChatMessage.objects.create(
            room=cls.private_room,
            user=cls.member,
            message="Test message",
        )

    def test_anonymous_helpers_return_empty_querysets(self):
        anonymous = AnonymousUser()

        querysets = (
            available_rooms_queryset(anonymous),
            manageable_rooms_queryset(anonymous),
            available_participants_queryset(anonymous),
            manageable_participants_queryset(anonymous),
            available_messages_queryset(anonymous),
        )

        for queryset in querysets:
            with self.subTest(model=queryset.model.__name__):
                self.assertFalse(queryset.exists())

    def test_chat_views_return_empty_querysets_during_schema_inspection(self):
        view_models = (
            (ChatRoomListAPIView, ChatRoom),
            (ChatRoomRetrieveAPIView, ChatRoom),
            (ChatRoomUpdateAPIView, ChatRoom),
            (ChatRoomDeleteAPIView, ChatRoom),
            (ChatParticipantListAPIView, ChatParticipant),
            (ChatParticipantRetrieveAPIView, ChatParticipant),
            (ChatParticipantUpdateAPIView, ChatParticipant),
            (ChatParticipantDeleteAPIView, ChatParticipant),
            (ChatMessageListAPIView, ChatMessage),
            (ChatMessageRetrieveAPIView, ChatMessage),
            (ChatMessageUpdateAPIView, ChatMessage),
            (ChatMessageDeleteAPIView, ChatMessage),
        )

        request = RequestFactory().get("/swagger.json/")
        request.user = AnonymousUser()

        for view_class, model in view_models:
            with self.subTest(view=view_class.__name__):
                view = view_class()
                view.request = request
                view.swagger_fake_view = True

                queryset = view.get_queryset()

                self.assertIs(queryset.model, model)
                self.assertFalse(queryset.exists())

    def test_swagger_schema_is_generated_for_anonymous_user(self):
        response = self.client.get("/swagger.json/")

        self.assertEqual(response.status_code, 200)
        self.assertIn(
            response["Content-Type"],
            ("application/json; charset=utf-8", "application/yaml; charset=utf-8"),
        )
        self.assertTrue(response.content)

    def test_private_room_is_available_only_to_owner_and_participant(self):
        self.assertTrue(
            available_rooms_queryset(self.owner)
            .filter(pk=self.private_room.pk)
            .exists()
        )
        self.assertTrue(
            available_rooms_queryset(self.member)
            .filter(pk=self.private_room.pk)
            .exists()
        )
        self.assertFalse(
            available_rooms_queryset(self.stranger)
            .filter(pk=self.private_room.pk)
            .exists()
        )

    def test_only_owner_can_manage_room_and_participants(self):
        self.assertTrue(
            manageable_rooms_queryset(self.owner)
            .filter(pk=self.private_room.pk)
            .exists()
        )
        self.assertFalse(
            manageable_rooms_queryset(self.member)
            .filter(pk=self.private_room.pk)
            .exists()
        )
        self.assertTrue(
            manageable_participants_queryset(self.owner)
            .filter(pk=self.membership.pk)
            .exists()
        )
        self.assertFalse(
            manageable_participants_queryset(self.member)
            .filter(pk=self.membership.pk)
            .exists()
        )

    def test_participant_can_read_private_room_messages(self):
        self.assertTrue(
            available_messages_queryset(self.member)
            .filter(pk=self.message.pk)
            .exists()
        )
        self.assertFalse(
            available_messages_queryset(self.stranger)
            .filter(pk=self.message.pk)
            .exists()
        )


class ChatWebPageTests(TestCase):
    def setUp(self):
        self.user = get_user_model().objects.create_user(
            email="subscriber-chat@example.com",
            username="subscriber-chat",
            password="test-password",
        )
        UserAgreementAcceptance.objects.create(
            user=self.user,
            agreement_version=settings.USER_AGREEMENT_VERSION,
        )
        self.plan = SubscriptionPlan.objects.create(
            name="Чат-тест",
            price="100.00",
            duration_days=30,
            max_ai_requests=10,
            max_chat_requests=10,
            max_instruction_requests=0,
            max_image_analyses=0,
            has_chat_access=True,
            has_instruction_generation=False,
            has_image_analysis=False,
            is_public=False,
        )
        UserSubscription.objects.create(
            user=self.user,
            plan=self.plan,
            start_date=timezone.now() - timedelta(days=1),
            end_date=timezone.now() + timedelta(days=29),
        )
        self.room = ChatRoom.objects.create(
            name="Общий ремонт",
            created_by=self.user,
        )
        self.client.force_login(self.user)

    def test_subscriber_opens_chat_page(self):
        response = self.client.get(
            reverse("chat_web:rooms"),
            {"room": self.room.pk},
        )

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Общий ремонт")
        self.assertContains(response, "Чат автомобилистов")
        self.assertContains(response, 'id="chat-message"')
        self.assertContains(response, "community-chat__form")
        self.assertContains(response, "До 500 символов")

    @patch("apps.chat.views.SmartAutoPartsAIService")
    def test_message_is_moderated_before_creation(self, service_class):
        service_class.return_value.moderate_request.return_value = (
            ModerationDecision(
                allowed=True,
                category="safe",
                reason="Разрешено.",
            )
        )

        response = self.client.post(
            reverse(
                "chat_web:message_create",
                kwargs={"room_id": self.room.pk},
            ),
            {"message": "Как проверить крепёж?"},
        )

        self.assertEqual(response.status_code, 302)
        self.assertTrue(
            ChatMessage.objects.filter(
                room=self.room,
                user=self.user,
                message="Как проверить крепёж?",
            ).exists()
        )
        service_class.return_value.moderate_request.assert_called_once_with(
            user=self.user,
            text="Как проверить крепёж?",
        )

    @patch("apps.chat.views.SmartAutoPartsAIService")
    def test_rejected_message_is_not_created(self, service_class):
        service_class.return_value.moderate_request.return_value = (
            ModerationDecision(
                allowed=False,
                category="abuse",
                reason="Недопустимое сообщение.",
            )
        )

        self.client.post(
            reverse(
                "chat_web:message_create",
                kwargs={"room_id": self.room.pk},
            ),
            {"message": "Недопустимый текст"},
        )

        self.assertFalse(
            ChatMessage.objects.filter(
                room=self.room,
                message="Недопустимый текст",
            ).exists()
        )

    def test_message_cannot_exceed_500_characters(self):
        response = self.client.post(
            reverse(
                "chat_web:message_create",
                kwargs={"room_id": self.room.pk},
            ),
            {"message": "а" * 501},
        )

        self.assertEqual(response.status_code, 302)
        self.assertFalse(ChatMessage.objects.exists())

    @override_settings(
        COMMUNITY_CHAT_RATE_LIMIT=20,
        CHAT_BURST_RATE_LIMIT=1,
        CHAT_BURST_WINDOW_SECONDS=60,
    )
    @patch("apps.chat.views.SmartAutoPartsAIService")
    def test_burst_rate_limit_blocks_message_flood(self, service_class):
        cache.clear()
        service_class.return_value.moderate_request.return_value = (
            ModerationDecision(
                allowed=True,
                category="safe",
                reason="Разрешено.",
            )
        )
        url = reverse(
            "chat_web:message_create",
            kwargs={"room_id": self.room.pk},
        )

        self.client.post(url, {"message": "Первое сообщение"})
        self.client.post(url, {"message": "Второе сообщение"})

        self.assertEqual(
            ChatMessage.objects.filter(room=self.room).count(),
            1,
        )

    def test_user_without_subscription_can_open_community_chat(self):
        UserSubscription.objects.filter(user=self.user).delete()

        response = self.client.get(reverse("chat_web:rooms"))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Чат автомобилистов")
