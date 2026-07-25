import tempfile
from datetime import timedelta
from io import BytesIO

from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase, override_settings
from django.utils import timezone
from PIL import Image

from apps.AI.models import (
    AIGeneratedInstruction,
    AIImageAnalysis,
    AIRequest,
)
from apps.AI.services import (
    AIAccessDenied,
    AIQuotaExceeded,
    AIRequestRejected,
    DomainModerationOutput,
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


class FakeOpenAIGateway:
    """Детерминированный шлюз для тестов без реального API-ключа."""

    model = "gpt-5.6-sol"

    def __init__(self, *, matched_part_id=0, image_flagged=False):
        self.matched_part_id = matched_part_id
        self.image_flagged = image_flagged
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
            is_automotive_part=True,
            part_name="Тестовая деталь",
            part_category="Тестовая категория",
            manufacturer="SmartAutoParts",
            visible_oem_numbers=["OEM-TEST-001"],
            visible_markings=["SmartAutoParts"],
            condition="used_good",
            observed_damage=[],
            confidence_score=92.5,
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
        self.assertEqual(AIImageAnalysis.objects.count(), 1)
        self.assertTrue(result.image_analysis.image.name.endswith(".jpg"))

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
