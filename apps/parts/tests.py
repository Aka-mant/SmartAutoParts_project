import tempfile
from datetime import timedelta
from io import BytesIO
from urllib.parse import unquote
from types import SimpleNamespace
from unittest.mock import patch

from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase, override_settings
from django.urls import reverse
from django.utils import timezone
from PIL import Image as PILImage
from rest_framework.test import APIClient

from apps.AI.models import (
    AIImageAnalysis,
    AIRequest,
    AIToolRecommendation,
)
from apps.instructions.models import Instruction, InstructionStep
from apps.subscriptions.models import SubscriptionPlan, UserSubscription
from apps.tools.models import PartTool, Tool, ToolCategory
from users.models import UserAgreementAcceptance

from .models import (
    Compatibility,
    OEMNumber,
    Part,
    PartCategory,
    PartImage,
)


class PartDetailPageTests(TestCase):
    def setUp(self):
        self.media_directory = tempfile.TemporaryDirectory()
        self.media_override = override_settings(
            MEDIA_ROOT=self.media_directory.name
        )
        self.media_override.enable()
        self.addCleanup(self.media_override.disable)
        self.addCleanup(self.media_directory.cleanup)

        self.category = PartCategory.objects.create(
            name="Фильтры",
            slug="filters",
        )
        self.part = Part.objects.create(
            category=self.category,
            name="Масляный фильтр",
            slug="oil-filter",
            original_number="OEM-100",
            manufacturer="Smart",
            description="Фильтр для тестового автомобиля.",
            weight="0.45",
            dimensions={"Высота": "90 мм"},
        )
        image_buffer = BytesIO()
        PILImage.new("RGB", (80, 60), color="white").save(
            image_buffer,
            format="PNG",
        )
        self.image_bytes = image_buffer.getvalue()
        PartImage.objects.create(
            part=self.part,
            image=SimpleUploadedFile(
                "oil-filter.png",
                self.image_bytes,
                content_type="image/png",
            ),
            alt_text="Масляный фильтр",
            is_main=True,
        )
        OEMNumber.objects.create(
            part=self.part,
            number="OEM-100-ALT",
            manufacturer="Smart",
        )
        Compatibility.objects.create(
            part=self.part,
            brand="Lada",
            model="Vesta",
            generation="I",
            engine="1.6",
            year_from=2015,
            year_to=2022,
        )
        tool_category = ToolCategory.objects.create(
            name="Съёмники",
            slug="pullers",
        )
        tool = Tool.objects.create(
            category=tool_category,
            name="Съёмник фильтра",
            size="65 мм",
        )
        PartTool.objects.create(part=self.part, tool=tool)
        self.instruction = Instruction.objects.create(
            part=self.part,
            title="Замена масляного фильтра",
            slug="replace-oil-filter",
            short_description="Проверенная замена фильтра.",
            content="Остановите двигатель.",
            difficulty=Instruction.Difficulty.EASY,
            estimated_time=25,
            is_published=True,
        )
        InstructionStep.objects.create(
            instruction=self.instruction,
            step_number=1,
            title="Подготовка",
            description="Зафиксируйте автомобиль.",
        )
        self.user = get_user_model().objects.create_user(
            username="part-viewer",
            email="part-viewer@example.com",
            password="safe-test-password",
        )
        self.accept_agreement(self.user)
        self.plan = SubscriptionPlan.objects.create(
            name="Карточки деталей",
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
        self.activate_plan(self.user)
        self.client.force_login(self.user)

    @staticmethod
    def accept_agreement(user):
        UserAgreementAcceptance.objects.create(
            user=user,
            agreement_version=settings.USER_AGREEMENT_VERSION,
        )

    def activate_plan(self, user, *, expired=False):
        now = timezone.now()
        return UserSubscription.objects.create(
            user=user,
            plan=self.plan,
            start_date=now - timedelta(days=31 if expired else 1),
            end_date=now - timedelta(days=1) if expired else now + timedelta(days=29),
            is_active=True,
        )

    def test_absolute_url_uses_slug(self):
        self.assertEqual(
            self.part.get_absolute_url(),
            reverse(
                "parts_web:detail",
                kwargs={"slug": self.part.slug},
            ),
        )

    def test_detail_page_contains_integrated_part_data(self):
        response = self.client.get(self.part.get_absolute_url())

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, self.part.original_number)
        self.assertContains(response, "OEM-100-ALT")
        self.assertContains(response, "Lada")
        self.assertContains(response, "Съёмник фильтра")
        self.assertContains(response, self.instruction.title)
        self.assertContains(response, 'width="440"')
        self.assertContains(response, 'height="330"')
        self.assertContains(
            response,
            self.instruction.get_absolute_url(),
        )

    def test_inactive_part_returns_404(self):
        self.part.is_active = False
        self.part.save()

        response = self.client.get(self.part.get_absolute_url())

        self.assertEqual(response.status_code, 404)

    def test_search_result_links_to_part_card(self):
        response = self.client.get(
            reverse("users:part_search"),
            {"q": self.part.original_number},
        )

        self.assertEqual(response.status_code, 200)
        self.assertContains(
            response,
            f'href="{self.part.get_absolute_url()}"',
        )

    def test_anonymous_search_does_not_link_to_part_card(self):
        self.client.logout()

        response = self.client.get(
            reverse("users:part_search"),
            {"q": self.part.original_number},
        )

        self.assertEqual(response.status_code, 200)
        self.assertNotContains(
            response,
            f'href="{self.part.get_absolute_url()}"',
        )
        self.assertContains(response, "Войдите для просмотра")

    def test_anonymous_part_detail_redirects_to_login(self):
        self.client.logout()

        response = self.client.get(self.part.get_absolute_url())

        self.assertEqual(response.status_code, 302)
        self.assertIn(reverse("users:login"), response.url)

    def test_authenticated_user_without_plan_cannot_open_part_card(self):
        UserSubscription.objects.filter(user=self.user).update(
            is_active=False
        )

        response = self.client.get(self.part.get_absolute_url())

        self.assertRedirects(
            response,
            reverse("subscriptions_web:plans"),
            fetch_redirect_response=False,
        )

    def test_search_history_result_does_not_expose_card_without_plan(self):
        UserSubscription.objects.filter(user=self.user).update(
            is_active=False
        )

        response = self.client.get(
            reverse("users:part_search"),
            {"q": self.part.original_number},
        )

        self.assertEqual(response.status_code, 200)
        self.assertNotContains(
            response,
            f'href="{self.part.get_absolute_url()}"',
        )
        self.assertContains(response, "Выбрать тариф для просмотра")

    def test_part_detail_api_requires_active_plan(self):
        UserSubscription.objects.filter(user=self.user).update(
            is_active=False
        )
        client = APIClient()
        client.force_authenticate(self.user)

        response = client.get(
            reverse(
                "parts_api:part_detail",
                kwargs={"pk": self.part.pk},
            )
        )

        self.assertEqual(response.status_code, 403)

    def test_cyrillic_part_slug_reverses_and_opens(self):
        part = Part.objects.create(
            category=self.category,
            name="Передний амортизатор",
            slug="передний-амортизатор",
            original_number="SHOCK-001",
        )

        url = part.get_absolute_url()
        response = self.client.get(url)

        self.assertIn("передний-амортизатор", unquote(url))
        self.assertEqual(response.status_code, 200)

    def test_ai_request_endpoints_require_login(self):
        self.client.logout()
        instruction_response = self.client.post(
            reverse(
                "parts_web:request_instruction",
                kwargs={"slug": self.part.slug},
            ),
            {"goal": "Заменить фильтр"},
        )
        tools_response = self.client.post(
            reverse(
                "parts_web:request_tools",
                kwargs={"slug": self.part.slug},
            ),
            {"goal": "Подобрать инструменты"},
        )

        self.assertEqual(instruction_response.status_code, 302)
        self.assertIn(reverse("users:login"), instruction_response.url)
        self.assertEqual(tools_response.status_code, 302)
        self.assertIn(reverse("users:login"), tools_response.url)

    def test_superuser_sees_free_ai_actions_on_part_card(self):
        superuser = get_user_model().objects.create_superuser(
            username="part-root",
            email="part-root@example.com",
            password="safe-test-password",
        )
        self.accept_agreement(superuser)
        self.client.force_login(superuser)

        response = self.client.get(self.part.get_absolute_url())

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Безлимит")
        self.assertContains(response, "Запросить инструкцию")
        self.assertContains(response, "Подобрать инструменты")
        self.assertNotContains(response, "<textarea")
        self.assertNotContains(response, "<select")
        self.assertNotContains(
            response,
            "Свежая опубликованная инструкция будет загружена",
        )
        self.assertNotContains(
            response,
            "AI учтёт инструменты из каталога",
        )
        self.assertContains(
            response,
            reverse(
                "parts_web:request_instruction",
                kwargs={"slug": self.part.slug},
            ),
        )
        self.assertContains(
            response,
            reverse(
                "parts_web:request_tools",
                kwargs={"slug": self.part.slug},
            ),
        )

    @patch("apps.parts.views.SmartAutoPartsAIService")
    def test_instruction_action_calls_ai_service(self, service_class):
        superuser = get_user_model().objects.create_superuser(
            username="instruction-root",
            email="instruction-root@example.com",
            password="safe-test-password",
        )
        self.accept_agreement(superuser)
        service_class.return_value.generate_repair_instruction.return_value = (
            SimpleNamespace(
                cached=True,
                generated_instruction=SimpleNamespace(
                    instruction=self.instruction,
                ),
            )
        )
        self.client.force_login(superuser)

        response = self.client.post(
            reverse(
                "parts_web:request_instruction",
                kwargs={"slug": self.part.slug},
            ),
            {
                "instruction": self.instruction.pk,
                "goal": "Заменить масляный фильтр",
            },
        )

        self.assertRedirects(
            response,
            self.instruction.get_absolute_url(),
            fetch_redirect_response=False,
        )
        service_class.return_value.generate_repair_instruction.assert_called_once()
        call = (
            service_class.return_value
            .generate_repair_instruction.call_args.kwargs
        )
        self.assertEqual(call["user"], superuser)
        self.assertEqual(call["part"], self.part)
        self.assertEqual(call["instruction"], self.instruction)
        self.assertIn(f"ID {self.part.pk}", call["goal"])
        self.assertNotIn(
            "Заменить масляный фильтр",
            call["goal"],
        )

    @patch("apps.parts.views.SmartAutoPartsAIService")
    def test_tool_action_calls_ai_service(self, service_class):
        superuser = get_user_model().objects.create_superuser(
            username="tools-root",
            email="tools-root@example.com",
            password="safe-test-password",
        )
        self.accept_agreement(superuser)
        service_class.return_value.recommend_part_tools.return_value = (
            SimpleNamespace(answer="Набор ключей")
        )
        self.client.force_login(superuser)

        response = self.client.post(
            reverse(
                "parts_web:request_tools",
                kwargs={"slug": self.part.slug},
            ),
            {"goal": "Подобрать инструмент для снятия фильтра"},
        )

        self.assertEqual(response.status_code, 302)
        self.assertEqual(
            response.url,
            f"{self.part.get_absolute_url()}#ai-requests",
        )
        service_class.return_value.recommend_part_tools.assert_called_once()
        call = (
            service_class.return_value
            .recommend_part_tools.call_args.kwargs
        )
        self.assertEqual(call["user"], superuser)
        self.assertEqual(call["part"], self.part)
        self.assertIn(f"ID {self.part.pk}", call["goal"])
        self.assertIn("PartTool", call["goal"])
        self.assertNotIn(
            "Подобрать инструмент для снятия фильтра",
            call["goal"],
        )

    def test_image_analysis_page_requires_login(self):
        self.client.logout()
        response = self.client.get(
            reverse("parts_web:image_analysis")
        )

        self.assertEqual(response.status_code, 302)
        self.assertIn(reverse("users:login"), response.url)

    def test_superuser_can_open_image_analysis_upload(self):
        superuser = get_user_model().objects.create_superuser(
            username="image-root",
            email="image-root@example.com",
            password="safe-test-password",
        )
        self.accept_agreement(superuser)
        self.client.force_login(superuser)

        response = self.client.get(
            reverse("parts_web:image_analysis")
        )

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'enctype="multipart/form-data"')
        self.assertContains(response, 'name="image"')
        self.assertContains(
            response,
            'name="confirm_automotive_content"',
        )
        self.assertNotContains(response, "<textarea")
        self.assertContains(response, "Проверить и распознать")

    @patch("apps.parts.views.SmartAutoPartsAIService")
    def test_image_upload_requires_confirmation(self, service_class):
        superuser = get_user_model().objects.create_superuser(
            username="image-confirm-root",
            email="image-confirm-root@example.com",
            password="safe-test-password",
        )
        self.accept_agreement(superuser)
        self.client.force_login(superuser)

        response = self.client.post(
            reverse("parts_web:image_analysis"),
            {
                "image": SimpleUploadedFile(
                    "unconfirmed.png",
                    self.image_bytes,
                    content_type="image/png",
                )
            },
        )

        self.assertEqual(response.status_code, 200)
        self.assertContains(
            response,
            "Перед анализом подтвердите содержимое фотографии.",
        )
        service_class.return_value.analyze_part_image.assert_not_called()

    @patch("apps.parts.views.SmartAutoPartsAIService")
    def test_image_upload_calls_service_and_opens_result(
        self,
        service_class,
    ):
        superuser = get_user_model().objects.create_superuser(
            username="image-service-root",
            email="image-service-root@example.com",
            password="safe-test-password",
        )
        self.accept_agreement(superuser)
        analysis = AIImageAnalysis.objects.create(
            user=superuser,
            image=SimpleUploadedFile(
                "analysis.png",
                self.image_bytes,
                content_type="image/png",
            ),
            detected_part=self.part,
            confidence_score="94.50",
            analysis_result={
                "model_output": {
                    "description": "Тестовый результат.",
                    "part_category": "Фильтры",
                }
            },
            moderation_status="approved",
        )
        service_class.return_value.analyze_part_image.return_value = (
            SimpleNamespace(image_analysis=analysis)
        )
        self.client.force_login(superuser)
        upload = SimpleUploadedFile(
            "uploaded.png",
            self.image_bytes,
            content_type="image/png",
        )

        response = self.client.post(
            reverse("parts_web:image_analysis"),
            {
                "image": upload,
                "confirm_automotive_content": "on",
            },
        )

        self.assertRedirects(
            response,
            reverse(
                "parts_web:image_analysis_result",
                kwargs={"pk": analysis.pk},
            ),
            fetch_redirect_response=False,
        )
        service_class.return_value.analyze_part_image.assert_called_once()
        call = (
            service_class.return_value
            .analyze_part_image.call_args.kwargs
        )
        self.assertEqual(call["user"], superuser)
        self.assertEqual(call["image"].name, "uploaded.png")

    def test_image_result_is_visible_only_to_owner(self):
        owner = get_user_model().objects.create_user(
            username="image-owner",
            email="image-owner@example.com",
            password="safe-test-password",
        )
        stranger = get_user_model().objects.create_user(
            username="image-stranger",
            email="image-stranger@example.com",
            password="safe-test-password",
        )
        self.accept_agreement(owner)
        self.accept_agreement(stranger)
        analysis = AIImageAnalysis.objects.create(
            user=owner,
            image=SimpleUploadedFile(
                "private-analysis.png",
                self.image_bytes,
                content_type="image/png",
            ),
            detected_part=self.part,
            confidence_score="88.00",
            analysis_result={"model_output": {}},
            moderation_status="approved",
        )
        result_url = reverse(
            "parts_web:image_analysis_result",
            kwargs={"pk": analysis.pk},
        )

        self.client.force_login(stranger)
        forbidden_response = self.client.get(result_url)
        self.assertEqual(forbidden_response.status_code, 404)

        self.client.force_login(owner)
        owner_response = self.client.get(result_url)
        self.assertEqual(owner_response.status_code, 200)
        self.assertContains(
            owner_response,
            "Автоматическая модерация пройдена",
        )

    def test_part_card_shows_only_approved_tool_recommendation(self):
        user = get_user_model().objects.create_user(
            username="approved-tool-user",
            email="approved-tool-user@example.com",
            password="safe-test-password",
        )
        self.accept_agreement(user)
        self.activate_plan(user)
        pending_request = AIRequest.objects.create(
            user=user,
            part=self.part,
            prompt="Первый запрос.",
            response="Непроверенный инструмент.",
            request_type="tool_recommendation_moderation_pending",
        )
        AIToolRecommendation.objects.create(
            ai_request=pending_request,
            generated_content=pending_request.response,
        )
        approved_request = AIRequest.objects.create(
            user=user,
            part=self.part,
            prompt="Второй запрос.",
            response="Проверенный съёмник фильтра.",
            request_type="tool_recommendation_approved",
        )
        AIToolRecommendation.objects.create(
            ai_request=approved_request,
            generated_content=approved_request.response,
            moderation_status=(
                AIToolRecommendation.ModerationStatus.APPROVED
            ),
            reviewed_at=timezone.now(),
        )
        self.client.force_login(user)

        response = self.client.get(self.part.get_absolute_url())

        self.assertEqual(response.status_code, 200)
        self.assertContains(
            response,
            "Проверенный съёмник фильтра.",
        )
        self.assertNotContains(response, "Непроверенный инструмент.")
        rendered = response.content.decode()
        self.assertIn("catalog-tool-recommendation", rendered)
        self.assertGreater(
            rendered.index("catalog-tool-recommendation"),
            rendered.index("instruction-mini-grid"),
        )
