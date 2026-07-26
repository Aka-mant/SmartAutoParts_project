import tempfile
from datetime import timedelta
from io import BytesIO
from types import SimpleNamespace
from unittest.mock import patch

from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase, override_settings
from django.urls import reverse
from django.utils import timezone
from PIL import Image
from rest_framework.test import APIClient

from apps.AI.models import (
    AIGeneratedInstruction,
    AIImageAnalysis,
    AIRequest,
    AIToolRecommendation,
)
from apps.AI.services import (
    AIAccessDenied,
    AIQuotaExceeded,
    AIRequestRejected,
    DomainModerationOutput,
    OpenAIGateway,
    PartImageAnalysisOutput,
    ProviderModerationResult,
    ProviderResponse,
    RepairInstructionOutput,
    RepairStepOutput,
    RepairToolOutput,
    SmartAutoPartsAIService,
    StructuredProviderResponse,
)
from apps.instructions.models import Instruction, InstructionVersion
from apps.parts.models import Part, PartCategory
from apps.subscriptions.models import SubscriptionPlan, UserSubscription
from users.models import UserAgreementAcceptance


class FakeOpenAIGateway:
    """Детерминированный шлюз для тестов без реального API-ключа."""

    model = "gpt-5.6-sol"
    moderation_model = "omni-moderation-latest"

    def __init__(
        self,
        *,
        matched_part_id=0,
        image_flagged=False,
        image_is_part=True,
        image_is_tool=False,
        image_confidence=92.5,
    ):
        self.matched_part_id = matched_part_id
        self.image_flagged = image_flagged
        self.image_is_part = image_is_part
        self.image_is_tool = image_is_tool
        self.image_confidence = image_confidence
        self.repair_generation_calls = 0

    def moderate_text(self, text):
        return ProviderModerationResult(flagged=False, categories=())

    def moderate_multimodal(self, **kwargs):
        return ProviderModerationResult(
            flagged=self.image_flagged,
            categories=("sexual",) if self.image_flagged else (),
        )

    def generate_text(self, **kwargs):
        return ProviderResponse(
            text="Проверенный тестовый ответ AI.",
            tokens_used=120,
        )

    def generate_structured(self, *, response_model, **kwargs):
        if response_model is DomainModerationOutput:
            parsed = DomainModerationOutput(
                allowed=True,
                category="safe",
                reason="Запрос разрешён.",
                risk_level="low",
                requires_professional=False,
            )
            return StructuredProviderResponse(
                parsed=parsed,
                tokens_used=15,
            )

        self.repair_generation_calls += 1
        parsed = RepairInstructionOutput(
            title="Замена тестовой детали",
            summary="Пошаговая проверяемая инструкция.",
            difficulty="medium",
            estimated_time_minutes=45,
            safety_warnings=[
                "Зафиксируйте автомобиль перед началом работ."
            ],
            preconditions=[
                "Сверьте деталь и автомобиль по VIN."
            ],
            tools=[
                RepairToolOutput(
                    name="Набор ключей",
                    size="",
                    required=True,
                    usage="Демонтаж крепежа.",
                )
            ],
            steps=[
                RepairStepOutput(
                    number=8,
                    title="Подготовка",
                    description="Установите автомобиль на ровной площадке.",
                    warning="Используйте стояночный тормоз.",
                    estimated_minutes=5,
                ),
                RepairStepOutput(
                    number=2,
                    title="Демонтаж",
                    description="Снимите старую деталь по руководству.",
                    warning="Не повреждайте соседние узлы.",
                    estimated_minutes=20,
                ),
                RepairStepOutput(
                    number=5,
                    title="Установка",
                    description="Установите новую деталь и проверьте крепёж.",
                    warning="Момент затяжки сверьте по VIN.",
                    estimated_minutes=20,
                ),
            ],
            final_checks=[
                "Проверьте крепёж и отсутствие посторонних шумов."
            ],
            professional_service_required=False,
            professional_service_reason="",
            assumptions=[
                "Точный момент затяжки отсутствует в базе."
            ],
        )
        return StructuredProviderResponse(
            parsed=parsed,
            tokens_used=640,
        )

    def generate_structured_image(self, **kwargs):
        parsed = PartImageAnalysisOutput(
            is_automotive_part=self.image_is_part,
            is_automotive_tool=self.image_is_tool,
            part_name="Тестовая деталь",
            part_category="Тестовая категория",
            manufacturer="SmartAutoParts",
            visible_oem_numbers=["OEM-TEST-001"],
            visible_markings=["SmartAutoParts"],
            condition="used_good",
            observed_damage=[],
            confidence_score=self.image_confidence,
            description="На фотографии видна тестовая деталь.",
            safety_notes=["Проверьте совместимость по VIN."],
            matched_part_id=self.matched_part_id,
            alternative_part_ids=[],
            match_basis="Совпали маркировка и OEM-номер.",
            limitations=["Не видна обратная сторона детали."],
        )
        return StructuredProviderResponse(
            parsed=parsed,
            tokens_used=420,
        )


class OpenAIGatewayContractTests(TestCase):
    """Проверяет параметры реального OpenAI Responses API шлюза."""

    def test_text_request_uses_configured_model_and_server_safety_fields(self):
        class FakeResponses:
            def __init__(self):
                self.kwargs = None

            def create(self, **kwargs):
                self.kwargs = kwargs
                return SimpleNamespace(
                    output_text="Ответ OpenAI",
                    usage=SimpleNamespace(total_tokens=25),
                    moderation=None,
                )

        responses = FakeResponses()
        gateway = OpenAIGateway(
            client=SimpleNamespace(responses=responses),
            model="gpt-5.6-sol",
        )

        result = gateway.generate_text(
            system_prompt="Системные правила",
            user_prompt="Подбери инструмент",
            reasoning_effort="low",
            max_output_tokens=500,
            safety_identifier="safe-user-id",
            verbosity="medium",
        )

        self.assertEqual(result.text, "Ответ OpenAI")
        self.assertEqual(result.tokens_used, 25)
        self.assertEqual(responses.kwargs["model"], "gpt-5.6-sol")
        self.assertEqual(
            responses.kwargs["moderation"]["model"],
            "omni-moderation-latest",
        )
        self.assertEqual(
            responses.kwargs["safety_identifier"],
            "safe-user-id",
        )
        self.assertFalse(responses.kwargs["store"])

    def test_structured_requests_put_verbosity_inside_text(self):
        class FakeResponses:
            def __init__(self):
                self.calls = []

            def parse(self, **kwargs):
                self.calls.append(kwargs)
                return SimpleNamespace(
                    output_parsed=DomainModerationOutput(
                        allowed=True,
                        category="safe",
                        reason="Запрос разрешён.",
                        risk_level="low",
                        requires_professional=False,
                    ),
                    usage=SimpleNamespace(total_tokens=30),
                    moderation=None,
                )

        responses = FakeResponses()
        gateway = OpenAIGateway(
            client=SimpleNamespace(responses=responses),
            model="gpt-5.6-sol",
        )

        gateway.generate_structured(
            system_prompt="Системные правила",
            user_prompt="Проверь запрос",
            response_model=DomainModerationOutput,
            reasoning_effort="low",
            max_output_tokens=500,
            safety_identifier="safe-user-id",
            verbosity="low",
        )
        gateway.generate_structured_image(
            system_prompt="Системные правила",
            user_prompt="Проверь изображение",
            image_data_url="data:image/png;base64,AA==",
            image_detail="low",
            response_model=DomainModerationOutput,
            reasoning_effort="low",
            max_output_tokens=500,
            safety_identifier="safe-user-id",
            verbosity="medium",
        )

        self.assertEqual(len(responses.calls), 2)
        self.assertEqual(
            responses.calls[0]["text"],
            {"verbosity": "low"},
        )
        self.assertEqual(
            responses.calls[1]["text"],
            {"verbosity": "medium"},
        )
        self.assertNotIn("verbosity", responses.calls[0])
        self.assertNotIn("verbosity", responses.calls[1])


class SmartAutoPartsAIServiceTests(TestCase):
    def setUp(self):
        self.media_directory = tempfile.TemporaryDirectory()
        self.media_override = override_settings(
            MEDIA_ROOT=self.media_directory.name
        )
        self.media_override.enable()
        self.addCleanup(self.media_override.disable)
        self.addCleanup(self.media_directory.cleanup)

        user_model = get_user_model()
        self.user = user_model.objects.create_user(
            username="driver",
            email="driver@example.com",
            password="safe-test-password",
        )
        UserAgreementAcceptance.objects.create(
            user=self.user,
            agreement_version=settings.USER_AGREEMENT_VERSION,
        )
        category = PartCategory.objects.create(
            name="Тестовая категория",
            slug="test-category",
        )
        self.part = Part.objects.create(
            category=category,
            name="Тестовая деталь",
            slug="test-part",
            original_number="OEM-TEST-001",
            manufacturer="SmartAutoParts",
            description="Описание тестовой детали.",
        )
        self.gateway = FakeOpenAIGateway(
            matched_part_id=self.part.pk
        )
        self.service = SmartAutoPartsAIService(
            gateway=self.gateway,
            enforce_access=False,
            enable_domain_moderation=False,
        )

    @staticmethod
    def image_file(name="part.jpg"):
        buffer = BytesIO()
        Image.new("RGB", (96, 96), color="gray").save(
            buffer,
            format="JPEG",
        )
        return SimpleUploadedFile(
            name,
            buffer.getvalue(),
            content_type="image/jpeg",
        )

    def active_subscription(
        self,
        *,
        has_image_analysis,
        max_ai_requests=5,
    ):
        plan = SubscriptionPlan.objects.create(
            name=f"Plan-{SubscriptionPlan.objects.count()}",
            description="Тестовый тариф.",
            price="10.00",
            duration_days=30,
            max_ai_requests=max_ai_requests,
            has_chat_access=True,
            has_image_analysis=has_image_analysis,
        )
        return UserSubscription.objects.create(
            user=self.user,
            plan=plan,
            start_date=timezone.now() - timedelta(days=1),
            end_date=timezone.now() + timedelta(days=29),
            is_active=True,
        )

    def published_instruction(self, *, version=1):
        return Instruction.objects.create(
            part=self.part,
            title="Опубликованная инструкция",
            slug=f"published-instruction-{Instruction.objects.count()}",
            short_description="Проверенная редактором инструкция.",
            content="# Проверенная инструкция\n\nСохранённый текст.",
            difficulty="medium",
            estimated_time=30,
            version=version,
            created_by=self.user,
        )

    def test_answer_chat_saves_ai_request(self):
        result = self.service.answer_chat(
            user=self.user,
            message="Как проверить эту деталь?",
            part=self.part,
        )

        self.assertEqual(result.answer, "Проверенный тестовый ответ AI.")
        self.assertEqual(result.ai_request.request_type, "chat")
        self.assertEqual(result.ai_request.tokens_used, 120)
        self.assertEqual(result.ai_request.part, self.part)

    def test_recommend_part_tools_uses_ai_and_saves_request(self):
        result = self.service.recommend_part_tools(
            user=self.user,
            part=self.part,
            goal="Подбери безопасные инструменты для замены детали.",
        )

        self.assertEqual(result.answer, "Проверенный тестовый ответ AI.")
        self.assertEqual(
            result.ai_request.request_type,
            "tool_recommendation_moderation_pending",
        )
        self.assertEqual(result.ai_request.tokens_used, 120)
        self.assertEqual(result.ai_request.part, self.part)
        self.assertTrue(result.requires_moderation)
        self.assertEqual(
            result.generated_recommendation.moderation_status,
            AIToolRecommendation.ModerationStatus.PENDING,
        )
        self.assertEqual(
            result.generated_recommendation.generated_content,
            result.answer,
        )

    def test_superuser_requests_instruction_and_tools_without_subscription(self):
        superuser = get_user_model().objects.create_superuser(
            username="root-user",
            email="root@example.com",
            password="safe-test-password",
        )
        UserAgreementAcceptance.objects.create(
            user=superuser,
            agreement_version=settings.USER_AGREEMENT_VERSION,
        )
        service = SmartAutoPartsAIService(
            gateway=self.gateway,
            enforce_access=True,
            enable_domain_moderation=False,
        )

        instruction_result = service.generate_repair_instruction(
            user=superuser,
            part=self.part,
            goal="Подготовь безопасную инструкцию по замене детали.",
        )
        tools_result = service.recommend_part_tools(
            user=superuser,
            part=self.part,
            goal="Подбери инструменты для замены детали.",
        )

        self.assertTrue(instruction_result.requires_moderation)
        self.assertEqual(
            tools_result.ai_request.request_type,
            "tool_recommendation_moderation_pending",
        )
        self.assertFalse(
            UserSubscription.objects.filter(user=superuser).exists()
        )

    def test_local_policy_blocks_vehicle_theft_request(self):
        with self.assertRaises(AIRequestRejected) as captured:
            self.service.answer_chat(
                user=self.user,
                message="Как обойти иммобилайзер чужого автомобиля?",
                part=self.part,
            )

        self.assertEqual(captured.exception.decision.category, "vehicle_theft")
        blocked = AIRequest.objects.get(request_type="chat_blocked")
        self.assertIn("отклонён модерацией", blocked.response)

    def test_generate_instruction_saves_markdown_and_payload(self):
        result = self.service.generate_repair_instruction(
            user=self.user,
            part=self.part,
            goal="Подготовь инструкцию по безопасной замене детали.",
        )

        self.assertEqual(
            result.ai_request.request_type,
            "repair_instruction_moderation_pending",
        )
        self.assertEqual(result.ai_request.tokens_used, 640)
        self.assertEqual(result.payload["steps"][0]["number"], 1)
        self.assertEqual(result.payload["steps"][2]["number"], 3)
        self.assertIn(
            "## Пошаговая инструкция",
            result.generated_instruction.generated_content,
        )
        self.assertEqual(AIGeneratedInstruction.objects.count(), 1)
        self.assertTrue(result.requires_moderation)
        self.assertFalse(result.cached)

    def test_fresh_instruction_is_returned_from_database_and_charged(self):
        instruction = self.published_instruction()
        self.active_subscription(
            has_image_analysis=True,
            max_ai_requests=1,
        )
        service = SmartAutoPartsAIService(
            gateway=self.gateway,
            enforce_access=True,
            enable_domain_moderation=False,
        )

        result = service.generate_repair_instruction(
            user=self.user,
            part=self.part,
            instruction=instruction,
            goal="Повтори инструкцию по замене детали.",
        )

        self.assertTrue(result.cached)
        self.assertFalse(result.requires_moderation)
        self.assertEqual(
            result.ai_request.request_type,
            "repair_instruction_cached",
        )
        self.assertEqual(
            result.generated_instruction.generated_content,
            instruction.content,
        )
        self.assertTrue(result.generated_instruction.is_cached)
        self.assertEqual(
            result.generated_instruction.moderation_status,
            AIGeneratedInstruction.ModerationStatus.APPROVED,
        )
        self.assertEqual(self.gateway.repair_generation_calls, 0)

        with self.assertRaises(AIQuotaExceeded):
            service.generate_repair_instruction(
                user=self.user,
                part=self.part,
                instruction=instruction,
                goal="Повтори инструкцию по замене детали.",
            )

    @override_settings(AI_INSTRUCTION_CACHE_TTL_DAYS=365)
    def test_stale_instruction_creates_pending_next_version(self):
        instruction = self.published_instruction(version=3)
        old_timestamp = timezone.now() - timedelta(days=366)
        Instruction.objects.filter(pk=instruction.pk).update(
            updated_at=old_timestamp
        )
        instruction.refresh_from_db()

        result = self.service.generate_repair_instruction(
            user=self.user,
            part=self.part,
            instruction=instruction,
            goal="Обнови инструкцию по безопасной замене детали.",
        )

        instruction.refresh_from_db()
        generated = result.generated_instruction
        snapshot = InstructionVersion.objects.get(
            instruction=instruction,
            version_number=3,
        )

        self.assertFalse(result.cached)
        self.assertTrue(result.requires_moderation)
        self.assertEqual(generated.version_number, 4)
        self.assertEqual(
            generated.moderation_status,
            AIGeneratedInstruction.ModerationStatus.PENDING,
        )
        self.assertEqual(instruction.version, 3)
        self.assertEqual(
            instruction.content,
            "# Проверенная инструкция\n\nСохранённый текст.",
        )
        self.assertEqual(snapshot.content, instruction.content)
        self.assertEqual(self.gateway.repair_generation_calls, 1)

    @override_settings(AI_INSTRUCTION_CACHE_TTL_DAYS=365)
    def test_moderator_approves_pending_instruction_version(self):
        instruction = self.published_instruction(version=1)
        Instruction.objects.filter(pk=instruction.pk).update(
            updated_at=timezone.now() - timedelta(days=366)
        )
        instruction.refresh_from_db()
        result = self.service.generate_repair_instruction(
            user=self.user,
            part=self.part,
            instruction=instruction,
            goal="Обнови опубликованную инструкцию.",
        )
        moderator = get_user_model().objects.create_user(
            username="moderator",
            email="moderator@example.com",
            password="safe-test-password",
            role="moderator",
        )

        approved = self.service.approve_generated_instruction(
            moderator=moderator,
            generated_instruction=result.generated_instruction,
            moderation_note="Технические данные проверены.",
        )

        instruction.refresh_from_db()
        self.assertEqual(instruction.version, 2)
        self.assertIn("## Пошаговая инструкция", instruction.content)
        self.assertEqual(
            approved.moderation_status,
            AIGeneratedInstruction.ModerationStatus.APPROVED,
        )
        self.assertEqual(approved.reviewed_by, moderator)

    def test_analyze_part_image_saves_result_and_ai_request(self):
        result = self.service.analyze_part_image(
            user=self.user,
            image=self.image_file(),
            note="Определи эту деталь.",
        )

        self.assertEqual(result.detected_part, self.part)
        self.assertEqual(result.ai_request.request_type, "image_analysis")
        self.assertEqual(result.ai_request.tokens_used, 420)
        self.assertEqual(result.image_analysis.detected_part, self.part)
        self.assertEqual(
            str(result.image_analysis.confidence_score),
            "92.50",
        )
        self.assertEqual(
            result.payload["verified_detected_part_id"],
            self.part.pk,
        )
        self.assertEqual(
            result.payload["suggested_original_number"],
            self.part.original_number,
        )
        self.assertEqual(AIImageAnalysis.objects.count(), 1)
        self.assertTrue(result.image_analysis.image.name.endswith(".jpg"))
        self.assertEqual(
            result.image_analysis.moderation_status,
            "approved",
        )
        self.assertEqual(
            result.image_analysis.moderation_categories,
            [],
        )
        self.assertEqual(
            result.image_analysis.moderation_model,
            "omni-moderation-latest",
        )
        self.assertIsNotNone(
            result.image_analysis.moderation_checked_at
        )

    def test_image_analysis_requires_tariff_feature(self):
        self.active_subscription(has_image_analysis=False)
        service = SmartAutoPartsAIService(
            gateway=self.gateway,
            enforce_access=True,
            enable_domain_moderation=False,
        )

        with self.assertRaises(AIAccessDenied):
            service.analyze_part_image(
                user=self.user,
                image=self.image_file(),
            )

        self.assertEqual(AIImageAnalysis.objects.count(), 0)

    def test_image_analysis_respects_ai_request_limit(self):
        self.active_subscription(
            has_image_analysis=True,
            max_ai_requests=1,
        )
        AIRequest.objects.create(
            user=self.user,
            part=self.part,
            prompt="Предыдущий запрос",
            response="Ответ",
            tokens_used=10,
            request_type="chat",
        )
        service = SmartAutoPartsAIService(
            gateway=self.gateway,
            enforce_access=True,
            enable_domain_moderation=False,
        )

        with self.assertRaises(AIQuotaExceeded):
            service.analyze_part_image(
                user=self.user,
                image=self.image_file(),
            )

        self.assertEqual(AIImageAnalysis.objects.count(), 0)

    def test_image_moderation_blocks_before_storage(self):
        service = SmartAutoPartsAIService(
            gateway=FakeOpenAIGateway(
                matched_part_id=self.part.pk,
                image_flagged=True,
            ),
            enforce_access=False,
            enable_domain_moderation=False,
        )

        with self.assertRaises(AIRequestRejected) as captured:
            service.analyze_part_image(
                user=self.user,
                image=self.image_file(),
            )

        self.assertEqual(
            captured.exception.decision.category,
            "openai_image_safety",
        )
        self.assertEqual(AIImageAnalysis.objects.count(), 0)
        self.assertTrue(
            AIRequest.objects.filter(
                request_type="image_analysis_blocked"
            ).exists()
        )

    def test_non_automotive_image_is_rejected_after_recognition(self):
        service = SmartAutoPartsAIService(
            gateway=FakeOpenAIGateway(
                matched_part_id=self.part.pk,
                image_is_part=False,
                image_is_tool=False,
            ),
            enforce_access=False,
            enable_domain_moderation=False,
        )

        with self.assertRaises(AIRequestRejected) as captured:
            service.analyze_part_image(
                user=self.user,
                image=self.image_file(),
            )

        self.assertEqual(
            captured.exception.decision.category,
            "non_automotive_image",
        )
        self.assertEqual(AIImageAnalysis.objects.count(), 0)
        self.assertTrue(
            AIRequest.objects.filter(
                request_type="image_analysis_rejected"
            ).exists()
        )


class AIImageAnalysisAPITests(TestCase):
    """Проверяет, что API загрузки вызывает безопасный AI-сервис."""

    def setUp(self):
        self.media_directory = tempfile.TemporaryDirectory()
        self.media_override = override_settings(
            MEDIA_ROOT=self.media_directory.name
        )
        self.media_override.enable()
        self.addCleanup(self.media_override.disable)
        self.addCleanup(self.media_directory.cleanup)

        self.user = get_user_model().objects.create_superuser(
            username="image-api-root",
            email="image-api-root@example.com",
            password="safe-test-password",
        )
        category = PartCategory.objects.create(
            name="API фото",
            slug="api-image",
        )
        self.part = Part.objects.create(
            category=category,
            name="API деталь",
            slug="api-image-part",
            original_number="API-IMAGE-001",
        )
        self.client = APIClient()
        self.client.force_authenticate(self.user)

    @staticmethod
    def image_file(name="api-image.jpg"):
        buffer = BytesIO()
        Image.new("RGB", (96, 96), color="gray").save(
            buffer,
            format="JPEG",
        )
        return SimpleUploadedFile(
            name,
            buffer.getvalue(),
            content_type="image/jpeg",
        )

    @patch("apps.AI.views.SmartAutoPartsAIService")
    def test_create_api_delegates_moderation_and_recognition_to_service(
        self,
        service_class,
    ):
        analysis = AIImageAnalysis.objects.create(
            user=self.user,
            image=self.image_file("stored.jpg"),
            detected_part=self.part,
            confidence_score="91.00",
            analysis_result={"model_output": {}},
            moderation_status="approved",
            moderation_categories=[],
            moderation_model="omni-moderation-latest",
            moderation_checked_at=timezone.now(),
        )
        service_class.return_value.analyze_part_image.return_value = (
            SimpleNamespace(image_analysis=analysis)
        )

        response = self.client.post(
            reverse("apps.AI:image_analysis_create"),
            {
                "image": self.image_file(),
                "confirm_automotive_content": True,
            },
            format="multipart",
        )

        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.json()["id"], analysis.pk)
        self.assertEqual(
            response.json()["moderation_status"],
            "approved",
        )
        service_class.return_value.analyze_part_image.assert_called_once()

    @patch("apps.AI.views.SmartAutoPartsAIService")
    def test_create_api_requires_photo_confirmation(self, service_class):
        response = self.client.post(
            reverse("apps.AI:image_analysis_create"),
            {"image": self.image_file()},
            format="multipart",
        )

        self.assertEqual(response.status_code, 400)
        self.assertIn("confirm_automotive_content", response.json())
        service_class.return_value.analyze_part_image.assert_not_called()

    def test_pending_tool_recommendation_is_hidden_until_approval(self):
        user = get_user_model().objects.create_user(
            username="tool-api-user",
            email="tool-api-user@example.com",
            password="safe-test-password",
        )
        ai_request = AIRequest.objects.create(
            user=user,
            part=self.part,
            prompt="Подбери инструменты.",
            response="Непроверенный ключ на 17 мм.",
            request_type="tool_recommendation_moderation_pending",
        )
        recommendation = AIToolRecommendation.objects.create(
            ai_request=ai_request,
            generated_content=ai_request.response,
        )
        client = APIClient()
        client.force_authenticate(user)
        detail_url = reverse(
            "apps.AI:ai_request_detail",
            kwargs={"pk": ai_request.pk},
        )

        pending_response = client.get(detail_url)

        self.assertEqual(pending_response.status_code, 200)
        self.assertEqual(
            pending_response.json()["response"],
            "Рекомендация ожидает технической модерации.",
        )

        recommendation.moderation_status = (
            AIToolRecommendation.ModerationStatus.APPROVED
        )
        recommendation.save(update_fields=("moderation_status",))

        approved_response = client.get(detail_url)

        self.assertEqual(approved_response.status_code, 200)
        self.assertEqual(
            approved_response.json()["response"],
            "Непроверенный ключ на 17 мм.",
        )


class AIChatWebPageTests(TestCase):
    def setUp(self):
        self.superuser = get_user_model().objects.create_superuser(
            username="ai-chat-root",
            email="ai-chat-root@example.com",
            password="safe-test-password",
        )
        UserAgreementAcceptance.objects.create(
            user=self.superuser,
            agreement_version=settings.USER_AGREEMENT_VERSION,
        )
        self.client.force_login(self.superuser)

    def test_superuser_opens_ai_helper(self):
        response = self.client.get(reverse("ai_web:chat"))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "AI-помощник SmartAutoParts")
        self.assertContains(response, "ai-request-status")
        self.assertContains(response, reverse("chat_web:rooms"))
        self.assertContains(response, 'id="ai-part-search"')
        self.assertContains(response, "Безлимит", count=2)
        self.assertContains(response, 'maxlength="500"')

    @patch("apps.AI.views.SmartAutoPartsAIService")
    def test_ai_helper_delegates_chat_request(self, service_class):
        response = self.client.post(
            reverse("ai_web:chat"),
            {"message": "Как проверить деталь?"},
        )

        self.assertRedirects(
            response,
            reverse("ai_web:chat"),
            fetch_redirect_response=False,
        )
        service_class.return_value.answer_chat.assert_called_once_with(
            user=self.superuser,
            message="Как проверить деталь?",
            part=None,
        )

    def test_moderator_cannot_open_ai_helper(self):
        moderator = get_user_model().objects.create_user(
            username="ai-chat-moderator",
            email="ai-chat-moderator@example.com",
            password="safe-test-password",
            role="moderator",
            is_staff=True,
        )
        UserAgreementAcceptance.objects.create(
            user=moderator,
            agreement_version=settings.USER_AGREEMENT_VERSION,
        )
        self.client.force_login(moderator)

        response = self.client.get(reverse("ai_web:chat"))

        self.assertRedirects(
            response,
            reverse("users:dashboard"),
            fetch_redirect_response=False,
        )


class AIGeneratedInstructionAdminTests(TestCase):
    """Проверяет полноценную модерацию AI-инструкций в Django Admin."""

    def setUp(self):
        self.superuser = get_user_model().objects.create_superuser(
            username="ai-admin",
            email="ai-admin@example.com",
            password="safe-test-password",
        )
        category = PartCategory.objects.create(
            name="Админ-тест",
            slug="admin-test",
        )
        self.part = Part.objects.create(
            category=category,
            name="Тестовая ступица",
            slug="admin-test-hub",
            original_number="HUB-ADMIN-001",
        )
        self.client.force_login(self.superuser)

    def create_generated(
        self,
        *,
        instruction=None,
        version_number=1,
        content=None,
    ):
        request = AIRequest.objects.create(
            user=self.superuser,
            part=self.part,
            prompt="Создай проверяемую инструкцию из данных проекта.",
            response="AI-черновик",
            request_type="repair_instruction_moderation_pending",
        )
        return AIGeneratedInstruction.objects.create(
            ai_request=request,
            instruction=instruction,
            generated_content=content or (
                "# Замена тестовой ступицы\n\n"
                "Проверенная последовательность ремонта.\n\n"
                "**Сложность:** medium\n"
                "**Ориентировочное время:** 55 мин.\n\n"
                "## Пошаговая инструкция\n\n"
                "### 1. Подготовка\n\nЗафиксируйте автомобиль."
            ),
            version_number=version_number,
            moderation_status=(
                AIGeneratedInstruction.ModerationStatus.PENDING
            ),
        )

    @staticmethod
    def moderation_url(generated, decision):
        return reverse(
            "admin:AI_aigeneratedinstruction_moderate",
            args=(generated.pk, decision),
        )

    def test_admin_approves_and_publishes_existing_instruction_version(self):
        instruction = Instruction.objects.create(
            part=self.part,
            title="Старая инструкция",
            slug="old-admin-instruction",
            content="Старая проверенная редакция.",
            version=1,
            is_published=False,
            created_by=self.superuser,
        )
        generated = self.create_generated(
            instruction=instruction,
            version_number=2,
        )

        response = self.client.post(
            self.moderation_url(generated, "approve"),
            {"moderation_note": "Техническая проверка выполнена."},
        )

        self.assertEqual(response.status_code, 302)
        generated.refresh_from_db()
        instruction.refresh_from_db()
        self.assertEqual(
            generated.moderation_status,
            AIGeneratedInstruction.ModerationStatus.APPROVED,
        )
        self.assertEqual(generated.reviewed_by, self.superuser)
        self.assertEqual(
            generated.moderation_note,
            "Техническая проверка выполнена.",
        )
        self.assertEqual(instruction.version, 2)
        self.assertTrue(instruction.is_published)
        self.assertEqual(
            instruction.content,
            generated.generated_content,
        )
        self.assertTrue(
            InstructionVersion.objects.filter(
                instruction=instruction,
                version_number=1,
                content="Старая проверенная редакция.",
            ).exists()
        )

    def test_admin_approval_creates_and_publishes_new_instruction(self):
        generated = self.create_generated()

        response = self.client.post(
            self.moderation_url(generated, "approve"),
            {"moderation_note": "Новая инструкция проверена."},
        )

        self.assertEqual(response.status_code, 302)
        generated.refresh_from_db()
        instruction = generated.instruction
        self.assertIsNotNone(instruction)
        self.assertEqual(instruction.part, self.part)
        self.assertEqual(instruction.title, "Замена тестовой ступицы")
        self.assertEqual(instruction.difficulty, "medium")
        self.assertEqual(instruction.estimated_time, 55)
        self.assertEqual(instruction.version, 1)
        self.assertTrue(instruction.is_published)
        self.assertEqual(instruction.created_by, self.superuser)
        self.assertEqual(
            generated.moderation_status,
            AIGeneratedInstruction.ModerationStatus.APPROVED,
        )

    def test_admin_rejection_requires_and_saves_reason(self):
        generated = self.create_generated()
        url = self.moderation_url(generated, "reject")

        invalid_response = self.client.post(
            url,
            {"moderation_note": ""},
        )

        self.assertEqual(invalid_response.status_code, 200)
        self.assertContains(
            invalid_response,
            "Укажите причину отклонения инструкции.",
        )
        generated.refresh_from_db()
        self.assertEqual(
            generated.moderation_status,
            AIGeneratedInstruction.ModerationStatus.PENDING,
        )

        response = self.client.post(
            url,
            {"moderation_note": "Не подтверждены технические значения."},
        )

        self.assertEqual(response.status_code, 302)
        generated.refresh_from_db()
        self.assertEqual(
            generated.moderation_status,
            AIGeneratedInstruction.ModerationStatus.REJECTED,
        )
        self.assertEqual(
            generated.moderation_note,
            "Не подтверждены технические значения.",
        )
        self.assertEqual(generated.reviewed_by, self.superuser)

    def test_admin_list_displays_moderation_buttons(self):
        generated = self.create_generated()

        response = self.client.get(
            reverse("admin:AI_aigeneratedinstruction_changelist")
        )

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Одобрить")
        self.assertContains(response, "Отклонить")
        self.assertContains(
            response,
            self.moderation_url(generated, "approve"),
        )

    def test_moderator_role_can_only_review_ai_instruction(self):
        generated = self.create_generated()
        moderator = get_user_model().objects.create_user(
            username="instruction-moderator",
            email="instruction-moderator@example.com",
            password="safe-test-password",
            role="moderator",
        )
        self.assertTrue(moderator.is_staff)
        self.client.force_login(moderator)

        list_response = self.client.get(
            reverse("admin:AI_aigeneratedinstruction_changelist")
        )
        add_response = self.client.get(
            reverse("admin:AI_aigeneratedinstruction_add")
        )
        moderate_response = self.client.post(
            self.moderation_url(generated, "approve"),
            {"moderation_note": "Проверено модератором."},
        )

        self.assertEqual(list_response.status_code, 200)
        self.assertEqual(add_response.status_code, 403)
        self.assertEqual(moderate_response.status_code, 302)
        generated.refresh_from_db()
        self.assertEqual(
            generated.moderation_status,
            AIGeneratedInstruction.ModerationStatus.APPROVED,
        )
        self.assertEqual(generated.reviewed_by, moderator)


class AIToolRecommendationAdminTests(TestCase):
    """Проверяет модерацию AI-рекомендаций инструментов в админке."""

    def setUp(self):
        self.superuser = get_user_model().objects.create_superuser(
            username="tool-admin",
            email="tool-admin@example.com",
            password="safe-test-password",
        )
        category = PartCategory.objects.create(
            name="Инструменты",
            slug="admin-tools",
        )
        self.part = Part.objects.create(
            category=category,
            name="Тестовый суппорт",
            slug="admin-test-caliper",
            original_number="CALIPER-ADMIN-001",
        )
        self.client.force_login(self.superuser)

    def create_recommendation(self):
        ai_request = AIRequest.objects.create(
            user=self.superuser,
            part=self.part,
            prompt="Подбери инструменты из данных проекта.",
            response="Ключ на 17 мм; защитные очки.",
            request_type="tool_recommendation_moderation_pending",
        )
        return AIToolRecommendation.objects.create(
            ai_request=ai_request,
            generated_content=ai_request.response,
        )

    @staticmethod
    def moderation_url(recommendation, decision):
        return reverse(
            "admin:AI_aitoolrecommendation_moderate",
            args=(recommendation.pk, decision),
        )

    def test_admin_approves_tool_recommendation(self):
        recommendation = self.create_recommendation()

        response = self.client.post(
            self.moderation_url(recommendation, "approve"),
            {"moderation_note": "Размер сверен с каталогом."},
        )

        self.assertEqual(response.status_code, 302)
        recommendation.refresh_from_db()
        recommendation.ai_request.refresh_from_db()
        self.assertEqual(
            recommendation.moderation_status,
            AIToolRecommendation.ModerationStatus.APPROVED,
        )
        self.assertEqual(recommendation.reviewed_by, self.superuser)
        self.assertEqual(
            recommendation.ai_request.request_type,
            "tool_recommendation_approved",
        )

    def test_admin_rejects_tool_recommendation_with_required_reason(self):
        recommendation = self.create_recommendation()
        url = self.moderation_url(recommendation, "reject")

        invalid_response = self.client.post(
            url,
            {"moderation_note": ""},
        )

        self.assertEqual(invalid_response.status_code, 200)
        self.assertContains(
            invalid_response,
            "Укажите причину отклонения рекомендации инструментов.",
        )
        recommendation.refresh_from_db()
        self.assertEqual(
            recommendation.moderation_status,
            AIToolRecommendation.ModerationStatus.PENDING,
        )

        response = self.client.post(
            url,
            {"moderation_note": "Размер инструмента не подтверждён."},
        )

        self.assertEqual(response.status_code, 302)
        recommendation.refresh_from_db()
        recommendation.ai_request.refresh_from_db()
        self.assertEqual(
            recommendation.moderation_status,
            AIToolRecommendation.ModerationStatus.REJECTED,
        )
        self.assertEqual(
            recommendation.ai_request.request_type,
            "tool_recommendation_rejected",
        )

    def test_admin_list_displays_tool_moderation_buttons(self):
        recommendation = self.create_recommendation()

        response = self.client.get(
            reverse("admin:AI_aitoolrecommendation_changelist")
        )

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Одобрить")
        self.assertContains(response, "Отклонить")
        self.assertContains(
            response,
            self.moderation_url(recommendation, "approve"),
        )
