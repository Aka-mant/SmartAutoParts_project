from io import StringIO
from tempfile import TemporaryDirectory
from urllib.parse import urlencode
from unittest.mock import patch

from django.apps import apps
from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.management import call_command
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone
from rest_framework.test import APIClient

from apps.instructions.models import Instruction, InstructionStep
from apps.parts.models import Part
from users.models import (
    Profile,
    RepairHistory,
    SearchHistory,
    UserAgreementAcceptance,
    UserRole,
)

from apps.AI.models import AIGeneratedInstruction, AIRequest
from apps.analytics.models import UserActivity
from apps.chat.models import ChatParticipant, ChatRoom
from apps.subscriptions.models import SubscriptionPlan, UserSubscription
from apps.tools.models import Tool


class UserRegistrationPageTests(TestCase):
    """Проверяет все серверные ветви страницы регистрации."""

    def test_registration_page_is_available_to_guest(self):
        response = self.client.get(reverse("users:register"))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Регистрация")

    def test_registration_rejects_different_passwords(self):
        response = self.client.post(
            reverse("users:register"),
            {
                "username": "different-passwords",
                "email": "different@example.com",
                "password": "Strong-password-123",
                "password_confirm": "Another-password-123",
            },
        )

        self.assertEqual(response.status_code, 400)
        self.assertContains(
            response,
            "Пароли не совпадают.",
            status_code=400,
        )

    def test_registration_renders_serializer_errors(self):
        response = self.client.post(
            reverse("users:register"),
            {
                "username": "x",
                "email": "not-an-email",
                "password": "123",
                "password_confirm": "123",
            },
        )

        self.assertEqual(response.status_code, 400)
        self.assertFalse(
            get_user_model().objects.filter(username="x").exists()
        )

    def test_registration_creates_user_and_redirects_to_login(self):
        response = self.client.post(
            reverse("users:register"),
            {
                "username": "new-registration-user",
                "email": "new-registration@example.com",
                "password": "Strong-registration-password-123",
                "password_confirm": "Strong-registration-password-123",
            },
        )

        self.assertRedirects(
            response,
            reverse("users:login"),
            fetch_redirect_response=False,
        )
        user = get_user_model().objects.get(
            username="new-registration-user"
        )
        self.assertTrue(
            user.check_password("Strong-registration-password-123")
        )

    def test_administrator_cannot_delete_self_but_can_delete_user(self):
        administrator = get_user_model().objects.create_superuser(
            username="delete-admin",
            email="delete-admin@example.com",
            password="safe-test-password",
        )
        removable_user = get_user_model().objects.create_user(
            username="removable-user",
            email="removable-user@example.com",
            password="safe-test-password",
        )
        api_client = APIClient()
        api_client.force_authenticate(administrator)

        self_delete = api_client.delete(
            reverse(
                "users:user_delete",
                kwargs={"pk": administrator.pk},
            )
        )
        self.assertEqual(self_delete.status_code, 403)
        self.assertTrue(
            get_user_model().objects.filter(pk=administrator.pk).exists()
        )

        user_delete = api_client.delete(
            reverse(
                "users:user_delete",
                kwargs={"pk": removable_user.pk},
            )
        )
        self.assertEqual(user_delete.status_code, 204)
        self.assertFalse(
            get_user_model().objects.filter(pk=removable_user.pk).exists()
        )

    def test_search_with_only_punctuation_is_recorded_as_empty(self):
        user = get_user_model().objects.create_user(
            username="punctuation-search-user",
            email="punctuation-search@example.com",
            password="safe-test-password",
        )
        UserAgreementAcceptance.objects.create(
            user=user,
            agreement_version=settings.USER_AGREEMENT_VERSION,
        )
        self.client.force_login(user)

        response = self.client.get(
            reverse("users:part_search"),
            {"q": "!!!"},
        )

        self.assertEqual(response.status_code, 200)
        self.assertFalse(response.context["parts"])
        self.assertTrue(
            SearchHistory.objects.filter(
                user=user,
                search_query="!!!",
                result_found=False,
            ).exists()
        )


class UserAgreementTests(TestCase):
    """Проверяет обязательное и версионируемое принятие соглашения."""

    def setUp(self):
        self.user = get_user_model().objects.create_user(
            username="agreement-user",
            email="agreement@example.com",
            password="safe-test-password",
        )
        self.client.force_login(self.user)

    def test_first_service_page_redirects_to_agreement(self):
        response = self.client.get(reverse("users:dashboard"))

        self.assertEqual(response.status_code, 302)
        self.assertTrue(
            response.url.startswith(reverse("users:user_agreement"))
        )
        self.assertIn("next=", response.url)

    def test_acceptance_is_recorded_and_allows_service_page(self):
        response = self.client.post(
            reverse("users:user_agreement"),
            {
                "agreement_accepted": "on",
                "next": reverse("users:dashboard"),
            },
        )

        self.assertRedirects(
            response,
            reverse("users:dashboard"),
            fetch_redirect_response=False,
        )
        self.assertTrue(
            UserAgreementAcceptance.objects.filter(
                user=self.user,
                agreement_version=settings.USER_AGREEMENT_VERSION,
            ).exists()
        )

        dashboard = self.client.get(reverse("users:dashboard"))
        self.assertEqual(dashboard.status_code, 200)

    def test_acceptance_requires_checkbox(self):
        response = self.client.post(
            reverse("users:user_agreement"),
            {"next": reverse("users:dashboard")},
        )

        self.assertEqual(response.status_code, 200)
        self.assertFalse(
            UserAgreementAcceptance.objects.filter(
                user=self.user,
            ).exists()
        )

    def test_administrator_and_superuser_do_not_accept_agreement(self):
        for suffix, kwargs in (
            ("admin", {"role": "admin", "is_staff": True}),
            (
                "superuser",
                {
                    "is_staff": True,
                    "is_superuser": True,
                },
            ),
        ):
            user = get_user_model().objects.create_user(
                username=f"agreement-{suffix}",
                email=f"agreement-{suffix}@example.com",
                password="safe-test-password",
                **kwargs,
            )
            self.client.force_login(user)

            dashboard = self.client.get(reverse("users:dashboard"))
            agreement = self.client.get(
                reverse("users:user_agreement")
            )

            self.assertEqual(dashboard.status_code, 200)
            self.assertContains(
                agreement,
                "Для вашей роли принятие не требуется",
            )
            self.assertNotContains(
                agreement,
                'name="agreement_accepted"',
            )


class ProfileLanguageTests(TestCase):
    def test_profile_language_is_select_with_ten_languages(self):
        user = get_user_model().objects.create_user(
            username="language-user",
            email="language-user@example.com",
            password="safe-test-password",
        )
        UserAgreementAcceptance.objects.create(
            user=user,
            agreement_version=settings.USER_AGREEMENT_VERSION,
        )
        self.client.force_login(user)

        response = self.client.get(reverse("users:profile_update"))

        self.assertEqual(response.status_code, 200)
        self.assertContains(
            response,
            '<select name="preferred_language"',
            html=False,
        )
        for language in (
            "Китайский (мандарин)",
            "Английский",
            "Хинди",
            "Испанский",
            "Арабский",
            "Бенгальский",
            "Португальский",
            "Русский",
            "Урду",
            "Индонезийский",
        ):
            self.assertContains(response, language)


class DashboardAccessPresentationTests(TestCase):
    """Проверяет счётчики и служебные состояния личного кабинета."""

    def accept(self, user):
        UserAgreementAcceptance.objects.create(
            user=user,
            agreement_version=settings.USER_AGREEMENT_VERSION,
        )

    def test_free_card_has_no_ai_counter(self):
        user = get_user_model().objects.create_user(
            username="free-dashboard",
            email="free-dashboard@example.com",
            password="safe-test-password",
        )
        self.accept(user)
        self.client.force_login(user)

        response = self.client.get(reverse("users:dashboard"))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Без подписки")
        self.assertNotContains(response, "AI-запросы</span>")
        self.assertContains(response, "Выбрать тариф")

    def test_superuser_counters_are_unlimited_without_purchase_banner(self):
        user = get_user_model().objects.create_superuser(
            username="unlimited-dashboard",
            email="unlimited-dashboard@example.com",
            password="safe-test-password",
        )
        self.accept(user)
        self.client.force_login(user)

        response = self.client.get(reverse("users:dashboard"))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Безлимит", count=5)
        self.assertNotContains(
            response,
            "card-body p-4 p-lg-5 position-relative",
        )
        self.assertNotContains(response, "Выбрать тариф")


class SearchHistoryLinkTests(TestCase):
    """Проверяет повторный поиск из истории пользователя."""

    def setUp(self):
        self.user = get_user_model().objects.create_user(
            username="history-user",
            email="history@example.com",
            password="safe-test-password",
        )
        UserAgreementAcceptance.objects.create(
            user=self.user,
            agreement_version=settings.USER_AGREEMENT_VERSION,
        )
        self.part = Part.objects.create(
            name="Тестовый масляный фильтр",
            slug="test-oil-filter",
            original_number="OEM-TEST-001",
            manufacturer="SmartAutoParts",
            description="Деталь для проверки истории поиска.",
        )
        self.history = SearchHistory.objects.create(
            user=self.user,
            original_number=self.part.original_number,
            search_query="масляный фильтр",
            result_found=True,
        )
        self.client.force_login(self.user)

    def test_history_item_builds_url_for_displayed_oem_number(self):
        expected_url = (
            f"{reverse('users:part_search')}?"
            f"{urlencode({'q': self.part.original_number})}"
        )

        self.assertEqual(
            self.history.get_search_results_url(),
            expected_url,
        )

    def test_history_page_contains_link_to_saved_search_results(self):
        response = self.client.get(reverse("users:search_history"))

        self.assertEqual(response.status_code, 200)
        self.assertContains(
            response,
            f'href="{self.history.get_search_results_url()}"',
            html=False,
        )

    def test_history_link_opens_results_for_displayed_part(self):
        response = self.client.get(
            self.history.get_search_results_url(),
        )

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, self.part.name)
        self.assertEqual(
            response.context["search_query"],
            self.part.original_number,
        )


class RepairStepNavigationTests(TestCase):
    """Проверяет сохранение и безопасную навигацию по шагам ремонта."""

    def setUp(self):
        user_model = get_user_model()
        self.user = user_model.objects.create_user(
            username="repair-user",
            email="repair@example.com",
            password="safe-test-password",
        )
        self.other_user = user_model.objects.create_user(
            username="other-repair-user",
            email="other-repair@example.com",
            password="safe-test-password",
        )
        self.superuser = user_model.objects.create_superuser(
            username="repair-root",
            email="repair-root@example.com",
            password="safe-test-password",
        )
        for accepted_user in (
            self.user,
            self.other_user,
            self.superuser,
        ):
            UserAgreementAcceptance.objects.create(
                user=accepted_user,
                agreement_version=settings.USER_AGREEMENT_VERSION,
            )
        self.part = Part.objects.create(
            name="Тестовый амортизатор",
            slug="repair-test-shock",
            original_number="SHOCK-TEST-001",
        )
        self.instruction = Instruction.objects.create(
            part=self.part,
            title="Замена тестового амортизатора",
            slug="replace-repair-test-shock",
            content="Проверенная инструкция.",
            is_published=True,
        )
        for number in range(1, 4):
            InstructionStep.objects.create(
                instruction=self.instruction,
                step_number=number,
                title=f"Шаг {number}",
                description=f"Описание шага {number}.",
            )
        self.repair = RepairHistory.objects.create(
            user=self.user,
            instruction=self.instruction,
        )
        self.url = reverse(
            "users:repair_step_navigation",
            kwargs={"pk": self.repair.pk},
        )

    def test_new_repair_starts_at_first_step(self):
        self.assertEqual(self.repair.current_step, 1)

    def test_owner_can_move_to_next_and_previous_step(self):
        self.client.force_login(self.user)

        self.client.post(self.url, {"action": "next"})
        self.repair.refresh_from_db()
        self.assertEqual(self.repair.current_step, 2)

        self.client.post(self.url, {"action": "previous"})
        self.repair.refresh_from_db()
        self.assertEqual(self.repair.current_step, 1)

    def test_navigation_does_not_cross_first_or_last_step(self):
        self.client.force_login(self.user)

        self.client.post(self.url, {"action": "previous"})
        self.repair.refresh_from_db()
        self.assertEqual(self.repair.current_step, 1)

        self.repair.current_step = 3
        self.repair.save()
        self.client.post(self.url, {"action": "next"})
        self.repair.refresh_from_db()
        self.assertEqual(self.repair.current_step, 3)

    def test_user_cannot_change_another_users_repair(self):
        self.client.force_login(self.other_user)

        response = self.client.post(self.url, {"action": "next"})

        self.assertEqual(response.status_code, 404)
        self.repair.refresh_from_db()
        self.assertEqual(self.repair.current_step, 1)

    def test_superuser_can_change_any_repair(self):
        self.client.force_login(self.superuser)

        response = self.client.post(self.url, {"action": "next"})

        self.assertEqual(response.status_code, 302)
        self.repair.refresh_from_db()
        self.assertEqual(self.repair.current_step, 2)

    def test_owner_can_complete_repair(self):
        self.client.force_login(self.user)

        response = self.client.post(
            self.url,
            {"action": "complete"},
        )

        self.assertEqual(response.status_code, 302)
        self.repair.refresh_from_db()
        self.assertTrue(self.repair.completed)
        self.assertEqual(self.repair.current_step, 3)

    def test_completed_repair_cannot_be_navigated(self):
        self.repair.completed = True
        self.repair.save()
        self.client.force_login(self.user)

        response = self.client.post(self.url, {"action": "next"})

        self.assertEqual(response.status_code, 404)

    def test_dashboard_shows_previous_and_next_buttons(self):
        self.client.force_login(self.user)

        response = self.client.get(reverse("users:dashboard"))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Предыдущий шаг")
        self.assertContains(response, "Следующий шаг")
        self.assertContains(response, "Завершить ремонт")
        self.assertContains(response, "Шаг 1")
        self.assertContains(response, "Распознать запчасть")
        self.assertContains(
            response,
            reverse("parts_web:image_analysis"),
        )

    def test_repair_history_shows_navigation_for_unfinished_repair(self):
        self.client.force_login(self.user)

        response = self.client.get(
            reverse("users:repair_history_list")
        )

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Предыдущий шаг")
        self.assertContains(response, "Следующий шаг")
        self.assertContains(response, "Завершить ремонт")
        self.assertContains(response, "из 3")


class CreateConnectedObjectsCommandTests(TestCase):
    """Проверяет генерацию полного набора связанных тестовых данных."""

    def test_command_rejects_invalid_count_ranges(self):
        stderr = StringIO()

        call_command(
            "ccu",
            min_count=0,
            max_count=1,
            stderr=stderr,
        )
        self.assertIn("должен быть больше нуля", stderr.getvalue())

        stderr = StringIO()
        call_command(
            "ccu",
            min_count=2,
            max_count=1,
            stderr=stderr,
        )
        self.assertIn("не может быть меньше", stderr.getvalue())

    def test_command_helper_generates_participants_and_ai_instructions(self):
        from users.management.commands.ccu import Command

        command = Command(stdout=StringIO())
        command.min_count = 4
        command.max_count = 4
        users = [
            get_user_model().objects.create_user(
                username=f"ccu-helper-{index}",
                email=f"ccu-helper-{index}@example.com",
                password="password",
            )
            for index in range(2)
        ]
        rooms = [
            ChatRoom.objects.create(
                name=f"Комната {index}",
                created_by=users[index],
            )
            for index in range(2)
        ]
        participants = command.create_chat_participants(rooms, users)
        self.assertGreaterEqual(len(participants), 2)
        self.assertGreaterEqual(ChatParticipant.objects.count(), 2)
        self.assertEqual(command.create_chat_messages([], users), [])

        part = Part.objects.create(
            name="CCU AI деталь",
            slug="ccu-ai-part",
            original_number="CCU-AI",
        )
        instruction = Instruction.objects.create(
            part=part,
            title="CCU инструкция",
            slug="ccu-ai-instruction",
            content="Текст",
        )
        ai_request = AIRequest.objects.create(
            user=users[0],
            part=part,
            prompt="Создай инструкцию",
            response="Ответ",
            request_type="instruction_generation",
        )
        generated = command.create_ai_generated_instructions(
            [ai_request],
            [instruction],
        )
        self.assertEqual(len(generated), 1)
        self.assertEqual(AIGeneratedInstruction.objects.count(), 1)

    def test_command_creates_active_user_subscription(self):
        from users.management.commands.ccu import Command

        user = get_user_model().objects.create_user(
            username="ccu-subscriber",
            email="ccu-subscriber@example.com",
            password="password",
        )
        plan = SubscriptionPlan.objects.create(
            name="CCU тариф",
            price=100,
            duration_days=30,
        )
        command = Command(stdout=StringIO())
        command.min_count = 1
        command.max_count = 1

        with patch(
            "users.management.commands.ccu.random.random",
            return_value=0.1,
        ):
            subscriptions = command.create_user_subscriptions(
                [user],
                [plan],
            )

        user.refresh_from_db()
        self.assertEqual(len(subscriptions), 1)
        self.assertTrue(subscriptions[0].is_active)
        self.assertEqual(user.role, UserRole.PREMIUM)

    def test_command_creates_connected_objects(self):
        stdout = StringIO()

        with TemporaryDirectory() as media_root:
            with self.settings(MEDIA_ROOT=media_root):
                call_command(
                    "ccu",
                    min_count=2,
                    max_count=2,
                    password="Strong-test-password-1!",
                    stdout=stdout,
                )

        self.assertGreater(get_user_model().objects.count(), 0)
        self.assertGreater(Part.objects.count(), 0)
        self.assertGreater(Instruction.objects.count(), 0)
        self.assertGreater(Tool.objects.count(), 0)
        self.assertGreater(SubscriptionPlan.objects.count(), 0)
        self.assertGreater(ChatRoom.objects.count(), 0)
        self.assertGreater(UserActivity.objects.count(), 0)
        self.assertGreater(AIRequest.objects.count(), 0)
        self.assertIn(
            "Все тестовые данные успешно созданы",
            stdout.getvalue(),
        )

        superuser = get_user_model().objects.filter(
            is_superuser=True,
        ).first()
        api_client = APIClient()
        api_client.force_authenticate(superuser)

        api_resources = (
            ("parts_api", "part_category", "parts.PartCategory"),
            ("parts_api", "part", "parts.Part"),
            ("parts_api", "oem_number", "parts.OEMNumber"),
            ("parts_api", "compatibility", "parts.Compatibility"),
            ("parts_api", "part_image", "parts.PartImage"),
            ("apps.tools", "tool_category", "tools.ToolCategory"),
            ("apps.tools", "tool", "tools.Tool"),
            ("apps.tools", "part_tool", "tools.PartTool"),
            (
                "instructions_api",
                "instruction",
                "instructions.Instruction",
            ),
            (
                "instructions_api",
                "instruction_version",
                "instructions.InstructionVersion",
            ),
            (
                "instructions_api",
                "instruction_step",
                "instructions.InstructionStep",
            ),
            (
                "instructions_api",
                "instruction_image",
                "instructions.InstructionImage",
            ),
            (
                "instructions_api",
                "instruction_tool",
                "instructions.InstructionTool",
            ),
            (
                "subscriptions_api",
                "subscription_plan",
                "subscriptions.SubscriptionPlan",
            ),
            (
                "subscriptions_api",
                "user_subscription",
                "subscriptions.UserSubscription",
            ),
            (
                "subscriptions_api",
                "subscription_payment",
                "subscriptions.SubscriptionPayment",
            ),
            ("apps.AI", "ai_request", "AI.AIRequest"),
            (
                "apps.AI",
                "generated_instruction",
                "AI.AIGeneratedInstruction",
            ),
            (
                "apps.AI",
                "image_analysis",
                "AI.AIImageAnalysis",
            ),
            ("apps.chat", "chat_room", "chat.ChatRoom"),
            (
                "apps.chat",
                "chat_participant",
                "chat.ChatParticipant",
            ),
            ("apps.chat", "chat_message", "chat.ChatMessage"),
            (
                "apps.analytics",
                "user_activity",
                "analytics.UserActivity",
            ),
            (
                "apps.analytics",
                "search_log",
                "analytics.SearchLog",
            ),
            (
                "apps.analytics",
                "popular_part",
                "analytics.PopularPart",
            ),
        )

        for namespace, resource, model_label in api_resources:
            with self.subTest(resource=resource):
                model = apps.get_model(model_label)
                instance = model.objects.first()

                list_response = api_client.get(
                    reverse(f"{namespace}:{resource}_list")
                )
                self.assertEqual(list_response.status_code, 200)

                create_response = api_client.post(
                    reverse(f"{namespace}:{resource}_create"),
                    {},
                    format="json",
                )
                self.assertIn(
                    create_response.status_code,
                    (201, 400),
                )

                if instance is None:
                    continue

                detail_response = api_client.get(
                    reverse(
                        f"{namespace}:{resource}_detail",
                        kwargs={"pk": instance.pk},
                    )
                )
                self.assertEqual(detail_response.status_code, 200)

                if resource == "chat_message":
                    continue

                update_response = api_client.patch(
                    reverse(
                        f"{namespace}:{resource}_update",
                        kwargs={"pk": instance.pk},
                    ),
                    {},
                    format="json",
                )
                self.assertEqual(update_response.status_code, 200)

        project_apps = {
            "AI",
            "analytics",
            "chat",
            "instructions",
            "parts",
            "subscriptions",
            "tools",
            "users",
        }
        for model in apps.get_models():
            if model._meta.app_label not in project_apps:
                continue
            for instance in model.objects.all()[:2]:
                self.assertIsInstance(str(instance), str)
                get_absolute_url = getattr(
                    instance,
                    "get_absolute_url",
                    None,
                )
                if get_absolute_url is not None:
                    self.assertIsInstance(get_absolute_url(), str)

        self.client.force_login(superuser)
        part = Part.objects.first()
        instruction = apps.get_model(
            "instructions",
            "Instruction",
        ).objects.first()
        image_analysis = apps.get_model(
            "AI",
            "AIImageAnalysis",
        ).objects.first()
        chat_room = apps.get_model("chat", "ChatRoom").objects.first()
        plan = apps.get_model(
            "subscriptions",
            "SubscriptionPlan",
        ).objects.first()

        page_urls = (
            reverse("users:dashboard"),
            reverse("users:user_agreement"),
            reverse("users:profile_detail"),
            reverse("users:profile_update"),
            reverse("users:search_history"),
            reverse("users:repair_history_list"),
            reverse("users:part_search"),
            reverse("instructions_web:list"),
            reverse(
                "instructions_web:detail",
                kwargs={"slug": instruction.slug},
            ),
            reverse(
                "instructions_web:repair",
                kwargs={"pk": instruction.pk},
            ),
            reverse(
                "parts_web:detail",
                kwargs={"slug": part.slug},
            ),
            reverse("parts_web:image_analysis"),
            reverse(
                "parts_web:image_analysis_result",
                kwargs={"pk": image_analysis.pk},
            ),
            reverse("subscriptions_web:plans"),
            reverse(
                "subscriptions_web:payment",
                kwargs={"plan_id": plan.pk},
            ),
            reverse("ai_web:chat"),
            reverse("chat_web:rooms"),
            reverse("chat_web:room_create"),
        )

        for url in page_urls:
            with self.subTest(url=url):
                response = self.client.get(url)
                self.assertLess(response.status_code, 500)

        message_url = reverse(
            "chat_web:message_create",
            kwargs={"room_id": chat_room.pk},
        )
        response = self.client.get(message_url)
        self.assertIn(response.status_code, (302, 405))

    def test_cross_app_serializer_validation_rules(self):
        from datetime import timedelta
        from decimal import Decimal

        from django.utils import timezone
        from rest_framework.exceptions import ValidationError

        from apps.AI.serializers import (
            AIGeneratedInstructionCreateSerializer,
            AIGeneratedInstructionUpdateSerializer,
            AIImageAnalysisCreateSerializer,
            AIImageAnalysisUpdateSerializer,
            AIRequestCreateSerializer,
            AIRequestUpdateSerializer,
        )
        from apps.analytics.serializers import (
            PopularPartCreateSerializer,
            PopularPartUpdateSerializer,
            SearchLogCreateSerializer,
            SearchLogUpdateSerializer,
            UserActivityCreateSerializer,
            UserActivityUpdateSerializer,
        )
        from apps.chat.serializers import (
            ChatMessageCreateSerializer,
            ChatMessageUpdateSerializer,
            ChatRoomCreateSerializer,
            ChatRoomUpdateSerializer,
        )
        from apps.parts.serializers import (
            PartCategoryCreateSerializer,
            PartCategoryUpdateSerializer,
            PartCreateSerializer,
            PartUpdateSerializer,
        )
        from apps.subscriptions.serializers import (
            SubscriptionPaymentCreateSerializer,
            SubscriptionPaymentUpdateSerializer,
            SubscriptionPlanCreateSerializer,
            SubscriptionPlanUpdateSerializer,
            UserSubscriptionCreateSerializer,
            UserSubscriptionUpdateSerializer,
            validate_plan_limits,
        )
        from apps.tools.serializers import (
            PartToolCreateSerializer,
            ToolCategoryCreateSerializer,
            ToolCategoryUpdateSerializer,
        )

        call_command(
            "ccu",
            min_count=1,
            max_count=1,
            stdout=StringIO(),
        )

        prompt_serializers = (
            AIRequestCreateSerializer(),
            AIRequestUpdateSerializer(),
        )
        for serializer in prompt_serializers:
            self.assertEqual(serializer.validate_prompt(" запрос "), "запрос")
            with self.assertRaises(ValidationError):
                serializer.validate_prompt(" ")
            with self.assertRaises(ValidationError):
                serializer.validate_prompt("x" * 501)

        content_serializers = (
            AIGeneratedInstructionCreateSerializer(),
            AIGeneratedInstructionUpdateSerializer(),
        )
        for serializer in content_serializers:
            self.assertEqual(
                serializer.validate_generated_content(" текст "),
                "текст",
            )
            with self.assertRaises(ValidationError):
                serializer.validate_generated_content(" ")

        confirmation = AIImageAnalysisCreateSerializer()
        self.assertTrue(
            confirmation.validate_confirm_automotive_content(True)
        )
        with self.assertRaises(ValidationError):
            confirmation.validate_confirm_automotive_content(False)

        confidence = AIImageAnalysisUpdateSerializer()
        self.assertIsNone(confidence.validate_confidence_score(None))
        self.assertEqual(
            confidence.validate_confidence_score(Decimal("70")),
            Decimal("70"),
        )
        for value in (Decimal("-1"), Decimal("101")):
            with self.assertRaises(ValidationError):
                confidence.validate_confidence_score(value)

        text_validators = (
            (
                UserActivityCreateSerializer(),
                "validate_action",
            ),
            (
                UserActivityUpdateSerializer(),
                "validate_action",
            ),
            (
                SearchLogCreateSerializer(),
                "validate_query",
            ),
            (
                SearchLogUpdateSerializer(),
                "validate_query",
            ),
        )
        for serializer, method_name in text_validators:
            validator = getattr(serializer, method_name)
            self.assertEqual(validator(" значение "), "значение")
            with self.assertRaises(ValidationError):
                validator(" ")

        search_log_update = SearchLogUpdateSerializer()
        self.assertEqual(search_log_update.validate_results_count(0), 0)
        with self.assertRaises(ValidationError):
            search_log_update.validate_results_count(-1)

        for serializer in (
            PopularPartCreateSerializer(),
            PopularPartUpdateSerializer(),
        ):
            self.assertEqual(serializer.validate_searches_count(0), 0)
            self.assertEqual(serializer.validate_views_count(0), 0)
            with self.assertRaises(ValidationError):
                serializer.validate_searches_count(-1)
            with self.assertRaises(ValidationError):
                serializer.validate_views_count(-1)

        message_serializers = (
            ChatMessageCreateSerializer(),
            ChatMessageUpdateSerializer(),
        )
        for serializer in message_serializers:
            self.assertEqual(
                serializer.validate_message(" сообщение "),
                "сообщение",
            )
            with self.assertRaises(ValidationError):
                serializer.validate_message(" ")
            with self.assertRaises(ValidationError):
                serializer.validate_message("x" * 501)

        room_serializers = (
            ChatRoomCreateSerializer(),
            ChatRoomUpdateSerializer(),
        )
        for serializer in room_serializers:
            self.assertEqual(serializer.validate_name(" Комната "), "Комната")
            with self.assertRaises(ValidationError):
                serializer.validate_name(" ")

        part_category = apps.get_model(
            "parts",
            "PartCategory",
        ).objects.first()
        duplicate_category = PartCategoryCreateSerializer()
        with self.assertRaises(ValidationError):
            duplicate_category.validate_slug(part_category.slug)

        update_category = PartCategoryUpdateSerializer(
            instance=part_category,
        )
        self.assertEqual(
            update_category.validate_slug(part_category.slug),
            part_category.slug,
        )

        part = apps.get_model("parts", "Part").objects.first()
        duplicate_part = PartCreateSerializer()
        with self.assertRaises(ValidationError):
            duplicate_part.validate_original_number(
                part.original_number
            )
        with self.assertRaises(ValidationError):
            duplicate_part.validate_slug(part.slug)

        update_part = PartUpdateSerializer(instance=part)
        self.assertEqual(
            update_part.validate_original_number(part.original_number),
            part.original_number,
        )
        self.assertEqual(update_part.validate_slug(part.slug), part.slug)

        tool_category = apps.get_model(
            "tools",
            "ToolCategory",
        ).objects.first()
        with self.assertRaises(ValidationError):
            ToolCategoryCreateSerializer().validate_slug(
                tool_category.slug
            )
        self.assertEqual(
            ToolCategoryUpdateSerializer(
                instance=tool_category,
            ).validate_slug(tool_category.slug),
            tool_category.slug,
        )

        part_tool = apps.get_model("tools", "PartTool").objects.first()
        with self.assertRaises(ValidationError):
            PartToolCreateSerializer().validate(
                {
                    "part": part_tool.part,
                    "tool": part_tool.tool,
                }
            )

        valid_limits = {
            "max_ai_requests": 10,
            "max_chat_requests": 3,
            "max_instruction_requests": 3,
            "max_image_analyses": 3,
            "has_chat_access": True,
            "has_instruction_generation": True,
            "has_image_analysis": True,
        }
        self.assertEqual(validate_plan_limits(valid_limits), valid_limits)
        with self.assertRaises(ValidationError):
            validate_plan_limits(
                {
                    **valid_limits,
                    "max_chat_requests": 11,
                }
            )

        for serializer in (
            SubscriptionPlanCreateSerializer(),
            SubscriptionPlanUpdateSerializer(),
        ):
            self.assertEqual(serializer.validate_price(Decimal("1")), 1)
            self.assertEqual(serializer.validate_duration_days(1), 1)
            with self.assertRaises(ValidationError):
                serializer.validate_price(Decimal("0"))
            with self.assertRaises(ValidationError):
                serializer.validate_duration_days(0)

        now = timezone.now()
        invalid_period = {
            "start_date": now,
            "end_date": now - timedelta(days=1),
        }
        with self.assertRaises(ValidationError):
            UserSubscriptionCreateSerializer().validate(invalid_period)

        subscription = apps.get_model(
            "subscriptions",
            "UserSubscription",
        ).objects.first()
        with self.assertRaises(ValidationError):
            UserSubscriptionUpdateSerializer(
                instance=subscription,
            ).validate(invalid_period)

        for serializer in (
            SubscriptionPaymentCreateSerializer(),
            SubscriptionPaymentUpdateSerializer(),
        ):
            self.assertEqual(serializer.validate_amount(Decimal("1")), 1)
            self.assertEqual(serializer.validate_currency(" rub "), "RUB")
            with self.assertRaises(ValidationError):
                serializer.validate_amount(Decimal("0"))
            with self.assertRaises(ValidationError):
                serializer.validate_currency("ru")


class UserUtilityCoverageTests(TestCase):
    """Проверяет формы, сериализаторы, права и служебные классы."""

    def setUp(self):
        self.user = get_user_model().objects.create_user(
            username="utility-user",
            email="utility@example.com",
            password="Strong-test-password-1!",
        )
        self.other_user = get_user_model().objects.create_user(
            username="utility-other",
            email="other-utility@example.com",
            password="Strong-test-password-1!",
        )
        Profile.objects.create(user=self.user)
        Profile.objects.create(user=self.other_user)

    def test_profile_forms_cover_valid_and_invalid_values(self):
        from users.forms import ProfileUpdateForm, UserProfileUpdateForm

        duplicate_form = UserProfileUpdateForm(
            {
                "username": self.other_user.username,
                "email": self.other_user.email,
            },
            instance=self.user,
        )
        self.assertFalse(duplicate_form.is_valid())
        self.assertIn("username", duplicate_form.errors)
        self.assertIn("email", duplicate_form.errors)

        valid_form = UserProfileUpdateForm(
            {
                "username": "utility-renamed",
                "email": "RENAMED@example.com",
            },
            instance=self.user,
        )
        self.assertTrue(valid_form.is_valid())
        self.assertEqual(
            valid_form.cleaned_data["email"],
            "renamed@example.com",
        )

        for year, expected_valid in (
            ("", True),
            (1885, False),
            (2101, False),
            (2020, True),
        ):
            with self.subTest(year=year):
                form = ProfileUpdateForm(
                    {
                        "preferred_language": "Русский",
                        "car_year": year,
                    },
                    instance=self.user.profile,
                )
                self.assertEqual(form.is_valid(), expected_valid)

    def test_user_serializers_create_user_and_token_claims(self):
        from users.pagination import DefaultPagination, SmallPagination
        from users.serializers import (
            ProfileSerializer,
            UserCreateSerializer,
            UserTokenObtainSerializer,
        )

        serializer = UserCreateSerializer(
            data={
                "username": "serializer-user",
                "email": "serializer@example.com",
                "password": "Strong-serializer-password-1!",
                "first_name": "Иван",
                "last_name": "Иванов",
                "phone": "+79990000000",
            }
        )
        self.assertTrue(serializer.is_valid(), serializer.errors)
        created_user = serializer.save()
        Profile.objects.create(user=created_user)
        self.assertTrue(
            created_user.check_password(
                "Strong-serializer-password-1!"
            )
        )

        token = UserTokenObtainSerializer.get_token(created_user)
        self.assertEqual(token["email"], created_user.email)
        self.assertEqual(token["username"], created_user.username)
        self.assertEqual(token["role"], created_user.role)

        profile_data = ProfileSerializer(created_user.profile).data
        self.assertEqual(profile_data["user_email"], created_user.email)
        self.assertEqual(DefaultPagination.page_size, 20)
        self.assertEqual(SmallPagination.max_page_size, 50)

    def test_permissions_and_owned_queryset_mixin(self):
        from django.contrib.auth.models import AnonymousUser
        from rest_framework.test import APIRequestFactory

        from users.mixins.mixins import UserOwnedQuerySetMixin
        from users.permissions import (
            CanAdministrate,
            CanModerate,
            HasPaidAccess,
            IsAdmin,
            IsModerator,
            IsOwner,
            IsSuperuser,
        )

        request = APIRequestFactory().get("/")
        request.user = self.user

        for permission_class in (
            IsModerator,
            IsAdmin,
            IsSuperuser,
            HasPaidAccess,
            CanModerate,
            CanAdministrate,
        ):
            self.assertFalse(
                permission_class().has_permission(request, None)
            )

        owner_permission = IsOwner()
        self.assertTrue(owner_permission.has_permission(request, None))
        self.assertTrue(
            owner_permission.has_object_permission(
                request,
                None,
                self.user,
            )
        )
        self.assertFalse(
            owner_permission.has_object_permission(
                request,
                None,
                self.other_user,
            )
        )

        history = SearchHistory.objects.create(
            user=self.user,
            original_number="OEM-UTILITY",
            search_query="OEM-UTILITY",
        )
        self.assertTrue(
            owner_permission.has_object_permission(
                request,
                None,
                history,
            )
        )
        self.assertFalse(
            owner_permission.has_object_permission(
                request,
                None,
                object(),
            )
        )
        self.assertTrue(
            owner_permission.has_object_permission(
                request,
                None,
                type(
                    "OwnedAIObject",
                    (),
                    {"ai_request": type(
                        "OwnedRequest",
                        (),
                        {"user": self.user},
                    )()},
                )(),
            )
        )

        request.user = AnonymousUser()
        self.assertFalse(owner_permission.has_permission(request, None))
        self.assertFalse(
            owner_permission.has_object_permission(
                request,
                None,
                history,
            )
        )

        class QuerySetBase:
            def get_queryset(inner_self):
                return SearchHistory.objects.all()

        class OwnedView(UserOwnedQuerySetMixin, QuerySetBase):
            pass

        view = OwnedView()
        view.request = request
        self.assertFalse(view.get_queryset().exists())

        request.user = self.user
        view.request = request
        self.assertEqual(view.get_queryset().count(), 1)

        self.user.is_superuser = True
        self.user.is_staff = True
        self.user.save(update_fields=["is_superuser", "is_staff"])
        self.assertEqual(view.get_queryset().count(), 1)
        self.assertTrue(
            owner_permission.has_object_permission(
                request,
                None,
                self.other_user,
            )
        )


class UserPageBranchCoverageTests(TestCase):
    """Проверяет ролевые и тарифные ветви пользовательских страниц."""

    def setUp(self):
        self.user = get_user_model().objects.create_user(
            username="page-branches",
            email="page-branches@example.com",
            password="safe-test-password",
        )
        UserAgreementAcceptance.objects.create(
            user=self.user,
            agreement_version=settings.USER_AGREEMENT_VERSION,
        )
        self.client.force_login(self.user)

    def test_dashboard_with_active_subscription_and_usage(self):
        plan = SubscriptionPlan.objects.create(
            name="Полный тест",
            price="300.00",
            duration_days=30,
            max_ai_requests=12,
            max_chat_requests=5,
            max_instruction_requests=4,
            max_image_analyses=3,
            has_chat_access=True,
            has_instruction_generation=True,
            has_image_analysis=True,
            is_public=False,
        )
        UserSubscription.objects.create(
            user=self.user,
            plan=plan,
            start_date=timezone.now() - timezone.timedelta(days=1),
            end_date=timezone.now() + timezone.timedelta(days=5),
        )
        for request_type in (
            "chat",
            "tool_recommendation_approved",
            "repair_instruction_cached",
            "image_analysis",
        ):
            AIRequest.objects.create(
                user=self.user,
                prompt=request_type,
                response="Ответ",
                request_type=request_type,
            )
        profile, _ = Profile.objects.get_or_create(user=self.user)
        profile.car_brand = "Несуществующая марка"
        profile.car_model = "Модель"
        profile.car_year = 2020
        profile.save()

        response = self.client.get(reverse("users:dashboard"))

        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.context["has_active_subscription"])
        self.assertEqual(response.context["ai_requests_used"], 4)
        self.assertTrue(response.context["subscription_is_expiring"])

    def test_moderator_dashboard_has_no_ai_access(self):
        self.user.role = UserRole.MODERATOR
        self.user.save(update_fields=["role"])

        response = self.client.get(reverse("users:dashboard"))

        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.context["is_ai_moderator"])
        self.assertFalse(response.context["has_chat_access"])

    def test_agreement_anonymous_admin_and_unsafe_next_branches(self):
        self.client.logout()
        anonymous = self.client.post(reverse("users:user_agreement"))
        self.assertEqual(anonymous.status_code, 302)

        self.user.is_superuser = True
        self.user.is_staff = True
        self.user.save(update_fields=["is_superuser", "is_staff"])
        self.client.force_login(self.user)
        privileged = self.client.post(reverse("users:user_agreement"))
        self.assertRedirects(
            privileged,
            reverse("users:dashboard"),
            fetch_redirect_response=False,
        )

        self.user.is_superuser = False
        self.user.is_staff = False
        self.user.save(update_fields=["is_superuser", "is_staff"])
        self.client.force_login(self.user)
        response = self.client.post(
            reverse("users:user_agreement"),
            {
                "agreement_accepted": "on",
                "next": "https://malicious.example/",
            },
        )
        self.assertRedirects(
            response,
            reverse("users:dashboard"),
            fetch_redirect_response=False,
        )

    def test_profile_update_valid_and_invalid_posts(self):
        url = reverse("users:profile_update")
        valid = self.client.post(
            url,
            {
                "username": "page-branches-updated",
                "email": self.user.email,
                "first_name": "Иван",
                "last_name": "Тестов",
                "preferred_language": "Русский",
                "country": "Россия",
                "car_brand": "Lada",
                "car_model": "Vesta",
                "car_year": 2022,
            },
        )
        self.assertEqual(valid.status_code, 302)
        self.user.refresh_from_db()
        self.assertEqual(self.user.first_name, "Иван")

        invalid = self.client.post(
            url,
            {"username": "", "email": "not-an-email"},
        )
        self.assertEqual(invalid.status_code, 200)

    def test_dashboard_helper_edge_cases(self):
        from users.views import UserDashboardView

        self.assertEqual(
            UserDashboardView.get_instruction_steps_count(
                object()
            ),
            0,
        )
        broken = type(
            "BrokenInstruction",
            (),
            {
                "steps": type(
                    "Manager",
                    (),
                    {
                        "count": lambda self: (_ for _ in ()).throw(
                            TypeError()
                        )
                    },
                )()
            },
        )()
        self.assertEqual(
            UserDashboardView.get_instruction_steps_count(broken),
            0,
        )
        self.assertEqual(
            UserDashboardView.get_current_repair_step(
                type("Repair", (), {"current_step": 8})(),
                0,
            ),
            0,
        )
        self.assertEqual(
            UserDashboardView.get_current_repair_step(
                type("Repair", (), {"current_step": None})(),
                3,
            ),
            1,
        )

        view = UserDashboardView()
        view.request = type("Request", (), {"user": self.user})()
        self.assertEqual(
            view.get_feature_requests_used(None, "unknown"),
            0,
        )
        acceptance = UserAgreementAcceptance.objects.get(user=self.user)
        self.assertIn(self.user.email, str(acceptance))
        empty_history = SearchHistory.objects.create(
            user=self.user,
            original_number="",
            search_query="",
            result_found=False,
        )
        self.assertEqual(
            empty_history.get_search_results_url(),
            reverse("users:part_search"),
        )

    def test_registration_login_and_search_pagination_branches(self):
        authenticated = self.client.get(reverse("users:register"))
        self.assertEqual(authenticated.status_code, 302)

        self.client.logout()
        login = self.client.get(reverse("users:login"))
        self.assertEqual(login.status_code, 200)
        self.assertContains(login, "form-control-lg")

        self.client.force_login(self.user)
        before = SearchHistory.objects.count()
        response = self.client.get(
            reverse("users:part_search"),
            {"q": "NOT-FOUND", "page": 1},
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(SearchHistory.objects.count(), before)

    def test_repair_api_and_navigation_edge_cases(self):
        part = Part.objects.create(
            name="Ремонтная деталь",
            slug="repair-user-branch",
            original_number="USER-REPAIR",
        )
        instruction = Instruction.objects.create(
            part=part,
            title="Ремонтная инструкция",
            slug="user-repair-instruction",
            content="Текст",
        )
        api_client = APIClient()
        api_client.force_authenticate(self.user)
        created = api_client.post(
            reverse("users:repair_history_create"),
            {
                "user": self.user.pk,
                "instruction": instruction.pk,
                "completed": False,
                "notes": "Начало",
            },
            format="json",
        )
        self.assertEqual(created.status_code, 201)
        repair = RepairHistory.objects.get(
            user=self.user,
            instruction=instruction,
        )
        updated = api_client.patch(
            reverse(
                "users:repair_history_update",
                kwargs={"pk": repair.pk},
            ),
            {"notes": "Обновлено"},
            format="json",
        )
        self.assertEqual(updated.status_code, 200)

        navigation_url = reverse(
            "users:repair_step_navigation",
            kwargs={"pk": repair.pk},
        )
        no_steps = self.client.post(navigation_url, {"action": "next"})
        self.assertEqual(no_steps.status_code, 302)

        InstructionStep.objects.create(
            instruction=instruction,
            step_number=1,
            title="Шаг",
            description="Описание",
        )
        unknown = self.client.post(
            navigation_url,
            {"action": "unknown"},
        )
        self.assertEqual(unknown.status_code, 302)
        safe_next = self.client.post(
            navigation_url,
            {
                "action": "next",
                "next": reverse("users:repair_history_list"),
            },
        )
        self.assertRedirects(
            safe_next,
            reverse("users:repair_history_list"),
            fetch_redirect_response=False,
        )
