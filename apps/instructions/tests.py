from datetime import timedelta
from urllib.parse import unquote

from django.conf import settings
from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone
from rest_framework.test import APIClient

from apps.AI.models import AIContentPurchase
from apps.parts.models import Part, PartCategory
from apps.subscriptions.models import SubscriptionPlan, UserSubscription

from apps.tools.models import Tool, ToolCategory
from users.models import RepairHistory, UserAgreementAcceptance

from .models import (
    Instruction,
    InstructionStep,
    InstructionTool,
    InstructionVersion,
)
from .serializers import InstructionSerializer, InstructionUpdateSerializer


class InstructionPageTests(TestCase):
    def setUp(self):
        self.category = PartCategory.objects.create(
            name="Тормозная система",
            slug="brakes",
        )
        self.part = Part.objects.create(
            category=self.category,
            name="Тормозные колодки",
            slug="brake-pads",
            original_number="BRAKE-001",
            manufacturer="Smart",
        )
        self.free_instruction = Instruction.objects.create(
            part=self.part,
            title="Проверка тормозных колодок",
            slug="check-brake-pads",
            short_description="Проверка толщины накладок.",
            content="Установите автомобиль на ровной площадке.",
            difficulty=Instruction.Difficulty.EASY,
            estimated_time=20,
            premium_only=False,
            is_published=True,
        )
        self.free_step = InstructionStep.objects.create(
            instruction=self.free_instruction,
            step_number=1,
            title="Зафиксируйте автомобиль",
            description="Включите стояночный тормоз.",
            warning="Не работайте под автомобилем без опор.",
        )
        self.premium_instruction = Instruction.objects.create(
            part=self.part,
            title="Полная замена тормозных колодок",
            slug="replace-brake-pads",
            short_description="Полная пошаговая замена.",
            content="Секретное содержимое premium-инструкции.",
            difficulty=Instruction.Difficulty.MEDIUM,
            estimated_time=60,
            premium_only=True,
            is_published=True,
        )
        self.premium_step = InstructionStep.objects.create(
            instruction=self.premium_instruction,
            step_number=1,
            title="Снимите колесо",
            description="Соблюдайте момент затяжки.",
        )
        self.draft = Instruction.objects.create(
            part=self.part,
            title="Черновик инструкции",
            slug="draft-instruction",
            content="Не опубликовано.",
            is_published=False,
        )
        self.viewer = self.create_user("viewer")
        subscription = self.activate_instruction_plan(self.viewer)
        self.purchase_instruction(
            self.viewer,
            self.free_instruction,
            subscription,
        )
        self.purchase_instruction(
            self.viewer,
            self.premium_instruction,
            subscription,
        )
        self.client.force_login(self.viewer)

    def create_user(self, suffix="user"):
        user = get_user_model().objects.create_user(
            username=suffix,
            email=f"{suffix}@example.com",
            password="test-password",
        )
        UserAgreementAcceptance.objects.create(
            user=user,
            agreement_version=settings.USER_AGREEMENT_VERSION,
        )
        return user

    def activate_instruction_plan(self, user, *, expired=False):
        plan = SubscriptionPlan.objects.create(
            name=f"Instruction-{user.pk}",
            description="Тестовый доступ.",
            price="100.00",
            duration_days=30,
            max_ai_requests=10,
            max_chat_requests=5,
            max_instruction_requests=5,
            max_image_analyses=0,
            has_chat_access=True,
            has_instruction_generation=True,
            has_image_analysis=False,
            is_public=False,
        )
        now = timezone.now()
        return UserSubscription.objects.create(
            user=user,
            plan=plan,
            start_date=now - timedelta(days=31 if expired else 1),
            end_date=now -
            timedelta(days=1) if expired else now + timedelta(days=29),
            is_active=True,
        )

    def purchase_instruction(
        self,
        user,
        instruction,
        subscription=None,
    ):
        return AIContentPurchase.objects.create(
            user=user,
            subscription=subscription,
            content_type=AIContentPurchase.ContentType.INSTRUCTION,
            content_key=f"instruction:{instruction.pk}",
            part=instruction.part,
            instruction=instruction,
            source=AIContentPurchase.Source.DATABASE,
        )

    def test_list_contains_published_and_hides_draft(self):
        response = self.client.get(reverse("instructions_web:list"))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, self.free_instruction.title)
        self.assertContains(response, self.premium_instruction.title)
        self.assertNotContains(response, self.draft.title)

    def test_list_filters_by_search_difficulty_and_category(self):
        response = self.client.get(
            reverse("instructions_web:list"),
            {
                "q": "замена",
                "difficulty": Instruction.Difficulty.MEDIUM,
                "category": self.category.slug,
            },
        )

        self.assertContains(response, self.premium_instruction.title)
        self.assertNotContains(response, self.free_instruction.title)

    def test_anonymous_user_cannot_open_free_instruction(self):
        self.client.logout()
        response = self.client.get(
            self.free_instruction.get_absolute_url()
        )

        self.assertEqual(response.status_code, 302)
        self.assertIn(reverse("users:login"), response.url)

    def test_anonymous_user_cannot_open_premium_instruction(self):
        self.client.logout()
        response = self.client.get(
            self.premium_instruction.get_absolute_url()
        )

        self.assertEqual(response.status_code, 302)
        self.assertIn(reverse("users:login"), response.url)

    def test_authenticated_user_without_plan_cannot_open_instructions(self):
        user = self.create_user("without-plan")
        self.client.force_login(user)

        list_response = self.client.get(
            reverse("instructions_web:list")
        )
        detail_response = self.client.get(
            self.free_instruction.get_absolute_url()
        )

        self.assertRedirects(
            list_response,
            reverse("subscriptions_web:plans"),
            fetch_redirect_response=False,
        )
        self.assertRedirects(
            detail_response,
            reverse("subscriptions_web:plans"),
            fetch_redirect_response=False,
        )

    def test_active_subscription_unlocks_premium_instruction(self):
        user = self.create_user("active")
        subscription = self.activate_instruction_plan(user)
        self.purchase_instruction(
            user,
            self.premium_instruction,
            subscription,
        )
        self.client.force_login(user)

        response = self.client.get(
            self.premium_instruction.get_absolute_url()
        )

        self.assertContains(response, self.premium_instruction.content)
        self.assertContains(response, self.premium_step.title)

    def test_expired_subscription_does_not_unlock_instruction(self):
        user = self.create_user("expired")
        self.activate_instruction_plan(user, expired=True)
        self.client.force_login(user)

        response = self.client.get(
            self.premium_instruction.get_absolute_url()
        )

        self.assertRedirects(
            response,
            reverse("subscriptions_web:plans"),
            fetch_redirect_response=False,
        )

    def test_draft_detail_returns_404(self):
        response = self.client.get(self.draft.get_absolute_url())
        self.assertEqual(response.status_code, 404)

    def test_cyrillic_slug_reverses_and_opens(self):
        instruction = Instruction.objects.create(
            part=self.part,
            title="Диагностика амортизатора",
            slug="диагностика-амортизатор-ngk-11",
            content="Проверьте амортизатор.",
            is_published=True,
        )
        self.purchase_instruction(
            self.viewer,
            instruction,
        )

        url = instruction.get_absolute_url()
        response = self.client.get(url)

        self.assertIn(
            "диагностика-амортизатор-ngk-11",
            unquote(url),
        )
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, instruction.title)

    def test_api_hides_all_instructions_without_subscription(self):
        user = self.create_user("api")
        client = APIClient()
        client.force_authenticate(user)

        detail_response = client.get(
            reverse(
                "instructions_api:instruction_detail",
                kwargs={"pk": self.premium_instruction.pk},
            )
        )
        list_response = client.get(
            reverse("instructions_api:instruction_list")
        )

        self.assertEqual(detail_response.status_code, 404)
        payload = list_response.json()
        self.assertEqual(payload.get("results", payload), [])

    def test_related_api_hides_premium_step_without_subscription(self):
        user = self.create_user("step-api")
        client = APIClient()
        client.force_authenticate(user)

        response = client.get(
            reverse(
                "instructions_api:instruction_step_detail",
                kwargs={"pk": self.premium_step.pk},
            )
        )

        self.assertEqual(response.status_code, 404)

    def test_version_model_tracks_author(self):
        user = self.create_user("editor")
        version = InstructionVersion.objects.create(
            instruction=self.free_instruction,
            version_number=1,
            content=self.free_instruction.content,
            changelog="Исходная версия.",
            created_by=user,
        )

        self.assertEqual(version.created_by, user)

    def test_manual_update_archives_previous_version(self):
        editor = self.create_user("manual-editor")
        old_content = self.free_instruction.content
        serializer = InstructionUpdateSerializer(
            self.free_instruction,
            data={"content": "Новая проверенная редакция."},
            partial=True,
        )
        self.assertTrue(serializer.is_valid(), serializer.errors)

        updated = serializer.save(updated_by=editor)

        snapshot = InstructionVersion.objects.get(
            instruction=updated,
            version_number=1,
        )
        self.assertEqual(snapshot.content, old_content)
        self.assertEqual(updated.version, 2)
        self.assertEqual(updated.updated_by, editor)

    def test_step_repair_requires_tools_and_supports_navigation(self):
        user = self.create_user("repair-session")
        subscription = self.activate_instruction_plan(user)
        self.purchase_instruction(
            user,
            self.free_instruction,
            subscription,
        )
        tool_category = ToolCategory.objects.create(
            name="Ключи",
            slug="repair-session-keys",
        )
        tool = Tool.objects.create(
            category=tool_category,
            name="Ключ 17 мм",
        )
        InstructionTool.objects.create(
            instruction=self.free_instruction,
            tool=tool,
            usage_description="Для крепежа.",
        )
        InstructionStep.objects.create(
            instruction=self.free_instruction,
            step_number=2,
            title="Проверка",
            description="Проверьте крепёж.",
        )
        self.client.force_login(user)

        start_response = self.client.post(
            reverse(
                "instructions_web:start_repair",
                kwargs={"slug": self.free_instruction.slug},
            )
        )
        repair = RepairHistory.objects.get(
            user=user,
            instruction=self.free_instruction,
        )

        self.assertRedirects(
            start_response,
            reverse("instructions_web:repair", kwargs={"pk": repair.pk}),
            fetch_redirect_response=False,
        )
        page = self.client.get(
            reverse("instructions_web:repair", kwargs={"pk": repair.pk})
        )
        self.assertContains(page, "Предыдущий шаг")
        self.assertContains(page, "Следующий шаг")
        self.assertContains(page, tool.name)

        self.client.post(
            reverse(
                "instructions_web:repair_navigate",
                kwargs={"pk": repair.pk},
            ),
            {"action": "next"},
        )
        repair.refresh_from_db()
        self.assertEqual(repair.current_step, 2)

    def test_active_plan_without_purchase_hides_instruction(self):
        user = self.create_user("not-purchased")
        self.activate_instruction_plan(user)
        self.client.force_login(user)

        list_response = self.client.get(
            reverse("instructions_web:list")
        )
        detail_response = self.client.get(
            self.free_instruction.get_absolute_url()
        )

        self.assertEqual(list_response.status_code, 200)
        self.assertNotContains(
            list_response,
            self.free_instruction.title,
        )
        self.assertEqual(detail_response.status_code, 404)

    def test_repair_navigation_error_and_completion_branches(self):
        user = self.create_user("repair-branches")
        subscription = self.activate_instruction_plan(user)
        self.purchase_instruction(
            user,
            self.free_instruction,
            subscription,
        )
        self.client.force_login(user)
        start_url = reverse(
            "instructions_web:start_repair",
            kwargs={"slug": self.free_instruction.slug},
        )

        self.free_instruction.steps.all().delete()
        without_steps = self.client.post(start_url)
        self.assertEqual(without_steps.status_code, 302)

        first_step = InstructionStep.objects.create(
            instruction=self.free_instruction,
            step_number=1,
            title="Первый",
            description="Первый шаг.",
        )
        without_tools = self.client.post(start_url)
        self.assertEqual(without_tools.status_code, 302)

        tool_category = ToolCategory.objects.create(
            name="Ветви ремонта",
            slug="repair-branches-tools",
        )
        tool = Tool.objects.create(
            category=tool_category,
            name="Тестовый ключ",
        )
        InstructionTool.objects.create(
            instruction=self.free_instruction,
            tool=tool,
        )
        InstructionStep.objects.create(
            instruction=self.free_instruction,
            step_number=2,
            title="Второй",
            description="Второй шаг.",
        )
        self.client.post(start_url)
        repair = RepairHistory.objects.get(
            user=user,
            instruction=self.free_instruction,
        )
        navigation_url = reverse(
            "instructions_web:repair_navigate",
            kwargs={"pk": repair.pk},
        )

        premature = self.client.post(
            navigation_url,
            {"action": "complete"},
        )
        self.assertEqual(premature.status_code, 302)
        invalid = self.client.post(
            navigation_url,
            {"action": "unknown"},
        )
        self.assertEqual(invalid.status_code, 302)
        self.client.post(navigation_url, {"action": "previous"})
        self.client.post(navigation_url, {"action": "next"})
        completed = self.client.post(
            navigation_url,
            {"action": "complete"},
        )
        repair.refresh_from_db()
        self.assertEqual(completed.status_code, 302)
        self.assertTrue(repair.completed)
        self.assertEqual(first_step.step_number, 1)

    def test_instruction_api_create_and_update_assigns_editor(self):
        editor = get_user_model().objects.create_superuser(
            username="instruction-api-editor",
            email="instruction-api-editor@example.com",
            password="password",
        )
        client = APIClient()
        client.force_authenticate(editor)
        created = client.post(
            reverse("instructions_api:instruction_create"),
            {
                "part": self.part.pk,
                "title": "Создано через API",
                "slug": "created-through-api",
                "content": "Полный текст инструкции.",
                "difficulty": "easy",
                "is_published": True,
            },
            format="json",
        )
        self.assertEqual(created.status_code, 201)
        instruction = Instruction.objects.get(slug="created-through-api")
        self.assertEqual(instruction.created_by, editor)

        updated = client.patch(
            reverse(
                "instructions_api:instruction_update",
                kwargs={"pk": instruction.pk},
            ),
            {"content": "Исправленный полный текст."},
            format="json",
        )
        self.assertEqual(updated.status_code, 200)
        instruction.refresh_from_db()
        self.assertEqual(instruction.updated_by, editor)

    def test_api_representation_hides_restricted_content(self):
        user = self.create_user("restricted-serializer")
        request = type("Request", (), {"user": user})()
        data = InstructionSerializer(
            self.free_instruction,
            context={"request": request},
        ).data
        self.assertTrue(data["access_restricted"])
        self.assertEqual(data["content"], "")
        self.assertEqual(data["steps"], [])


class HeaderIntegrationTests(TestCase):
    def test_authenticated_header_uses_russian_dashboard_name(self):
        user = get_user_model().objects.create_user(
            username="header-user",
            email="header@example.com",
            password="test-password",
        )
        self.client.force_login(user)

        response = self.client.get(reverse("home"))

        self.assertContains(response, "Панель управления")
        self.assertNotContains(response, ">Dashboard<")
        self.assertContains(
            response,
            reverse("instructions_web:list"),
        )
        self.assertContains(
            response,
            reverse("subscriptions_web:plans"),
        )
