from django.contrib.auth import get_user_model
from django.contrib.auth.models import AnonymousUser
from datetime import timedelta
from types import SimpleNamespace
from unittest.mock import patch

from django.conf import settings
from django.core.cache import cache
from django.test import RequestFactory, TestCase, override_settings
from django.urls import reverse
from django.utils import timezone
from rest_framework.test import APIClient

from apps.AI.services import (
    AIAccessDenied,
    AIProviderError,
    AIRequestRejected,
    ModerationDecision,
)
from apps.subscriptions.models import SubscriptionPlan, UserSubscription
from users.models import UserAgreementAcceptance

from .models import ChatMessage, ChatParticipant, ChatRoom
from .views import (
    ChatMessageDeleteAPIView,
    ChatMessageCreateAPIView,
    ChatMessageListAPIView,
    ChatMessageRetrieveAPIView,
    ChatMessageUpdateAPIView,
    ChatParticipantDeleteAPIView,
    ChatParticipantCreateAPIView,
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
    is_chat_rate_limited,
)
from .serializers import (
    ChatMessageCreateSerializer,
    ChatMessageUpdateSerializer,
    ChatParticipantCreateSerializer,
    ChatParticipantUpdateSerializer,
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
            ("application/json; charset=utf-8",
             "application/yaml; charset=utf-8"),
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

    def test_serializer_duplicate_access_and_update_branches(self):
        from rest_framework import serializers

        with self.assertRaises(serializers.ValidationError):
            ChatParticipantCreateSerializer().validate(
                {"room": self.private_room, "user": self.member}
            )
        duplicate = ChatParticipant.objects.create(
            room=self.public_room,
            user=self.stranger,
        )
        with self.assertRaises(serializers.ValidationError):
            ChatParticipantUpdateSerializer(
                instance=duplicate
            ).validate(
                {"room": self.private_room, "user": self.member}
            )

        request = RequestFactory().post("/")
        request.user = self.stranger
        message_serializer = ChatMessageCreateSerializer(
            context={"request": request}
        )
        with self.assertRaises(serializers.ValidationError):
            message_serializer.validate_room(self.private_room)
        request.user = AnonymousUser()
        self.assertEqual(
            message_serializer.validate_room(self.private_room),
            self.private_room,
        )

        update_serializer = ChatMessageUpdateSerializer()
        updated = update_serializer.update(
            self.message,
            {"message": "Исправленный текст"},
        )
        self.assertTrue(updated.is_edited)
        self.assertEqual(updated.message, "Исправленный текст")

    @patch("apps.chat.views.cache.incr", side_effect=ValueError)
    @patch("apps.chat.views.cache.add", return_value=False)
    def test_rate_limit_recovers_from_missing_cache_key(
        self,
        cache_add,
        cache_incr,
    ):
        request = RequestFactory().post(
            "/",
            REMOTE_ADDR="127.0.0.1",
        )
        request.user = self.member
        self.assertFalse(
            is_chat_rate_limited(
                request,
                scope="test",
                limit=1,
                window_seconds=60,
            )
        )
        cache_add.assert_called_once()
        cache_incr.assert_called_once()

    def test_view_permission_and_queryset_edge_branches(self):
        from rest_framework.exceptions import (
            PermissionDenied,
            ValidationError,
        )

        request = RequestFactory().post("/")
        request.user = self.stranger
        serializer = SimpleNamespace(
            validated_data={
                "room": self.private_room,
                "user": self.stranger,
                "message": "Сообщение",
            },
            save=lambda **kwargs: None,
        )
        participant_view = ChatParticipantCreateAPIView()
        participant_view.request = request
        with self.assertRaises(ValidationError):
            participant_view.perform_create(serializer)

        UserAgreementAcceptance.objects.create(
            user=self.stranger,
            agreement_version=settings.USER_AGREEMENT_VERSION,
        )
        with self.assertRaises(PermissionDenied):
            participant_view.perform_create(serializer)

        message_view = ChatMessageCreateAPIView()
        message_view.request = request
        with self.assertRaises(PermissionDenied):
            message_view.perform_create(serializer)

        for view_class in (
            ChatParticipantDeleteAPIView,
            ChatMessageUpdateAPIView,
            ChatMessageDeleteAPIView,
        ):
            view = view_class()
            request.user = AnonymousUser()
            view.request = request
            self.assertFalse(view.get_queryset().exists())
            request.user = self.owner
            self.owner.is_superuser = True
            view.request = request
            self.assertGreaterEqual(view.get_queryset().count(), 1)
            self.owner.is_superuser = False

    @patch("apps.chat.views.SmartAutoPartsAIService")
    def test_message_update_permission_and_moderation_errors(
        self,
        service_class,
    ):
        from rest_framework.exceptions import (
            PermissionDenied,
            ValidationError,
        )

        request = RequestFactory().patch("/")
        request.user = self.stranger
        view = ChatMessageUpdateAPIView()
        view.request = request
        view.get_object = lambda: self.message
        serializer = SimpleNamespace(
            validated_data={
                "room": self.private_room,
                "message": "Исправление",
            },
            save=lambda **kwargs: None,
        )
        with self.assertRaises(ValidationError):
            view.perform_update(serializer)

        UserAgreementAcceptance.objects.create(
            user=self.stranger,
            agreement_version=settings.USER_AGREEMENT_VERSION,
        )
        with self.assertRaises(PermissionDenied):
            view.perform_update(serializer)

        serializer.validated_data["room"] = self.public_room
        service_class.return_value.moderate_request.side_effect = (
            AIProviderError("Ошибка")
        )
        with self.assertRaises(ValidationError):
            view.perform_update(serializer)

        service_class.return_value.moderate_request.side_effect = None
        service_class.return_value.moderate_request.return_value = (
            ModerationDecision(
                allowed=False,
                category="blocked",
                reason="Отклонено",
            )
        )
        with self.assertRaises(ValidationError):
            view.perform_update(serializer)


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
        response = self.client.get(
            reverse("chat_web:rooms"),
            {"room": self.room.pk},
        )

        self.assertFalse(
            ChatMessage.objects.filter(
                room=self.room,
                message="Недопустимый текст",
            ).exists()
        )
        self.assertContains(response, "community-message--moderator")
        self.assertContains(response, "Недопустимое сообщение.")

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

    def test_room_creation_validates_name_and_adds_owner(self):
        url = reverse("chat_web:room_create")
        invalid = self.client.post(url, {"name": "x"})
        self.assertEqual(invalid.status_code, 302)

        response = self.client.post(
            url,
            {"name": "Закрытая комната", "is_private": "on"},
        )
        room = ChatRoom.objects.get(name="Закрытая комната")
        self.assertEqual(response.status_code, 302)
        self.assertTrue(room.is_private)
        self.assertTrue(
            ChatParticipant.objects.filter(
                room=room,
                user=self.user,
            ).exists()
        )

    def test_private_room_owner_can_manage_participants(self):
        member = get_user_model().objects.create_user(
            email="member-web@example.com",
            username="member-web",
            password="test-password",
        )
        private_room = ChatRoom.objects.create(
            name="Закрытый гараж",
            is_private=True,
            created_by=self.user,
        )
        owner_participant = ChatParticipant.objects.create(
            room=private_room,
            user=self.user,
        )

        page = self.client.get(
            reverse("chat_web:rooms"),
            {"room": private_room.pk},
        )
        self.assertContains(page, "Управление участниками")
        self.assertContains(page, member.username)

        added = self.client.post(
            reverse(
                "chat_web:participant_add",
                kwargs={"room_id": private_room.pk},
            ),
            {"user_identifier": member.email.upper()},
        )
        self.assertEqual(added.status_code, 302)
        participant = ChatParticipant.objects.get(
            room=private_room,
            user=member,
        )

        removed = self.client.post(
            reverse(
                "chat_web:participant_remove",
                kwargs={
                    "room_id": private_room.pk,
                    "participant_id": participant.pk,
                },
            )
        )
        self.assertEqual(removed.status_code, 302)
        self.assertFalse(
            ChatParticipant.objects.filter(pk=participant.pk).exists()
        )

        creator_removal = self.client.post(
            reverse(
                "chat_web:participant_remove",
                kwargs={
                    "room_id": private_room.pk,
                    "participant_id": owner_participant.pk,
                },
            )
        )
        self.assertEqual(creator_removal.status_code, 302)
        self.assertTrue(
            ChatParticipant.objects.filter(pk=owner_participant.pk).exists()
        )

    def test_private_room_participant_management_validates_access(self):
        member = get_user_model().objects.create_user(
            email="private-member@example.com",
            username="private-member",
            password="test-password",
        )
        inactive = get_user_model().objects.create_user(
            email="inactive-member@example.com",
            username="inactive-member",
            password="test-password",
            is_active=False,
        )
        private_room = ChatRoom.objects.create(
            name="Приватный бокс",
            is_private=True,
            created_by=self.user,
        )
        ChatParticipant.objects.create(room=private_room, user=self.user)

        empty = self.client.post(
            reverse(
                "chat_web:participant_add",
                kwargs={"room_id": private_room.pk},
            ),
            {"user_identifier": ""},
        )
        self.assertEqual(empty.status_code, 302)

        missing = self.client.post(
            reverse(
                "chat_web:participant_add",
                kwargs={"room_id": private_room.pk},
            ),
            {"user_identifier": inactive.username},
        )
        self.assertEqual(missing.status_code, 302)
        self.assertFalse(
            ChatParticipant.objects.filter(
                room=private_room,
                user=inactive,
            ).exists()
        )

        ChatParticipant.objects.create(room=private_room, user=member)
        UserAgreementAcceptance.objects.create(
            user=member,
            agreement_version=settings.USER_AGREEMENT_VERSION,
        )
        self.client.force_login(member)
        forbidden = self.client.post(
            reverse(
                "chat_web:participant_add",
                kwargs={"room_id": private_room.pk},
            ),
            {"user_identifier": inactive.email},
        )
        self.assertEqual(forbidden.status_code, 404)

        page = self.client.get(
            reverse("chat_web:rooms"),
            {"room": private_room.pk},
        )
        self.assertNotContains(page, "Управление участниками")

    @patch("apps.chat.views.SmartAutoPartsAIService")
    def test_web_message_handles_moderation_exceptions(self, service_class):
        url = reverse(
            "chat_web:message_create",
            kwargs={"room_id": self.room.pk},
        )
        decision = ModerationDecision(
            allowed=False,
            category="blocked",
            reason="Запрещено.",
        )
        service_class.return_value.moderate_request.side_effect = (
            AIRequestRejected("Запрещено.", decision=decision)
        )
        rejected = self.client.post(url, {"message": "Первый текст"})
        self.assertEqual(rejected.status_code, 302)
        self.assertIn(
            "Запрещено.",
            self.client.session["community_chat_moderation_notice"],
        )

        service_class.return_value.moderate_request.side_effect = (
            AIAccessDenied("Недоступно")
        )
        unavailable = self.client.post(url, {"message": "Второй текст"})
        self.assertEqual(unavailable.status_code, 302)

    @patch("apps.chat.views.SmartAutoPartsAIService")
    def test_chat_api_crud_and_access_rules(self, service_class):
        service_class.return_value.moderate_request.return_value = (
            ModerationDecision(
                allowed=True,
                category="safe",
                reason="Разрешено.",
            )
        )
        api_client = APIClient()
        api_client.force_authenticate(self.user)
        room_create = api_client.post(
            reverse("apps.chat:chat_room_create"),
            {
                "name": "API-комната",
                "is_private": False,
                "created_by": self.user.pk,
            },
        )
        self.assertEqual(room_create.status_code, 201)
        api_room = ChatRoom.objects.get(name="API-комната")

        participant_create = api_client.post(
            reverse("apps.chat:chat_participant_create"),
            {"room": api_room.pk, "user": self.user.pk},
        )
        self.assertEqual(participant_create.status_code, 201)

        message_create = api_client.post(
            reverse("apps.chat:chat_message_create"),
            {"room": api_room.pk, "message": "Сообщение API"},
        )
        self.assertEqual(message_create.status_code, 201)
        message = ChatMessage.objects.get(message="Сообщение API")

        update = api_client.patch(
            reverse(
                "apps.chat:chat_message_update",
                kwargs={"pk": message.pk},
            ),
            {"message": "Изменённое сообщение"},
            content_type="application/json",
        )
        self.assertEqual(update.status_code, 200)
        delete = api_client.delete(
            reverse(
                "apps.chat:chat_message_delete",
                kwargs={"pk": message.pk},
            )
        )
        self.assertEqual(delete.status_code, 204)

    def test_chat_api_requires_user_agreement(self):
        UserAgreementAcceptance.objects.filter(user=self.user).delete()
        api_client = APIClient()
        api_client.force_authenticate(self.user)
        response = api_client.post(
            reverse("apps.chat:chat_message_create"),
            {"room": self.room.pk, "message": "Без соглашения"},
        )
        self.assertEqual(response.status_code, 400)

    @patch("apps.chat.views.SmartAutoPartsAIService")
    def test_chat_api_rejects_private_access_and_moderation_errors(
        self,
        service_class,
    ):
        other = get_user_model().objects.create_user(
            email="private-owner@example.com",
            username="private-owner",
            password="password",
        )
        private_room = ChatRoom.objects.create(
            name="Чужая приватная",
            is_private=True,
            created_by=other,
        )
        api_client = APIClient()
        api_client.force_authenticate(self.user)

        participant = api_client.post(
            reverse("apps.chat:chat_participant_create"),
            {"room": private_room.pk, "user": self.user.pk},
        )
        self.assertEqual(participant.status_code, 403)
        message = api_client.post(
            reverse("apps.chat:chat_message_create"),
            {"room": private_room.pk, "message": "Нет доступа"},
        )
        self.assertEqual(message.status_code, 400)

        service_class.return_value.moderate_request.side_effect = (
            AIProviderError("Ошибка")
        )
        failed = api_client.post(
            reverse("apps.chat:chat_message_create"),
            {"room": self.room.pk, "message": "Проверяемое сообщение"},
        )
        self.assertEqual(failed.status_code, 400)

        service_class.return_value.moderate_request.side_effect = None
        service_class.return_value.moderate_request.return_value = (
            ModerationDecision(
                allowed=False,
                category="blocked",
                reason="Отклонено",
            )
        )
        blocked = api_client.post(
            reverse("apps.chat:chat_message_create"),
            {"room": self.room.pk, "message": "Ещё сообщение"},
        )
        self.assertEqual(blocked.status_code, 400)
