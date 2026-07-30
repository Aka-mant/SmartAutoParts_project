import tempfile
from datetime import timedelta
from io import BytesIO
from types import SimpleNamespace
from unittest.mock import patch

from django.conf import settings
from django.contrib import admin
from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from django.core.cache import cache
from django.test import TestCase, override_settings
from django.urls import reverse
from django.utils import timezone
from PIL import Image
from rest_framework.test import APIClient

from apps.AI.models import (
    AIContentPurchase,
    AIGeneratedInstruction,
    AIImageAnalysis,
    AIRequest,
    AIToolRecommendation,
)
from apps.AI.serializers import (
    AIGeneratedInstructionCreateSerializer,
    AIRequestSerializer,
)
from apps.AI.admin import PrettyJSONWidget
from apps.AI.services import (
    AIAccessDenied,
    AIConfigurationError,
    AIContentBlocked,
    AIImageValidationError,
    AIProviderError,
    AIQuotaService,
    AIInstructionModerationService,
    AIQuotaExceeded,
    AIRequestRejected,
    AIServiceError,
    DomainModerationOutput,
    ImageCatalogContext,
    ImageCatalogBuilder,
    ImageInputValidator,
    LocalAutomotivePolicy,
    ModerationDecision,
    OpenAIGateway,
    PartImageAnalysisOutput,
    ProviderModerationResult,
    ProviderResponse,
    ProjectContextBuilder,
    RepairInstructionOutput,
    RepairStepOutput,
    RepairToolOutput,
    RequestModerationService,
    SmartAutoPartsAIService,
    StructuredProviderResponse,
    record_content_purchase,
)
from apps.instructions.models import Instruction, InstructionVersion
from apps.chat.models import ChatMessage, ChatParticipant, ChatRoom
from apps.parts.models import Part, PartCategory
from apps.subscriptions.models import SubscriptionPlan, UserSubscription
from apps.tools.models import PartTool, Tool, ToolCategory
from users.models import Profile, UserAgreementAcceptance


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


class OpenAIGatewayEdgeCaseTests(TestCase):
    """Проверяет защитные ветви шлюза и локальной модерации."""

    @override_settings(OPENAI_API_KEY="")
    @patch.dict("os.environ", {"OPENAI_API_KEY": ""})
    def test_gateway_requires_api_key_without_injected_client(self):
        with self.assertRaises(AIConfigurationError):
            OpenAIGateway()

    def test_moderation_parsing_and_multimodal_request(self):
        result = SimpleNamespace(
            flagged=True,
            categories=SimpleNamespace(
                model_dump=lambda: {"violence": True, "sexual": False}
            ),
        )
        moderations = SimpleNamespace(
            create=lambda **kwargs: SimpleNamespace(results=[result])
        )
        gateway = OpenAIGateway(
            client=SimpleNamespace(moderations=moderations)
        )

        text_result = gateway.moderate_text("текст")
        image_result = gateway.moderate_multimodal(
            text="фото",
            image_data_url="data:image/png;base64,AA==",
        )

        self.assertTrue(text_result.flagged)
        self.assertEqual(text_result.categories, ("violence",))
        self.assertTrue(image_result.flagged)
        with self.assertRaises(AIProviderError):
            gateway._parse_moderation_response(
                SimpleNamespace(results=[])
            )

    def test_gateway_helper_methods_cover_all_response_shapes(self):
        self.assertEqual(OpenAIGateway._model_dump({"a": 1}), {"a": 1})
        self.assertEqual(OpenAIGateway._model_dump(object()), {})
        self.assertEqual(
            OpenAIGateway._total_tokens(SimpleNamespace(usage=None)),
            0,
        )
        self.assertEqual(
            OpenAIGateway._total_tokens(
                SimpleNamespace(
                    usage=SimpleNamespace(
                        total_tokens=None,
                        input_tokens=4,
                        output_tokens=6,
                    )
                )
            ),
            10,
        )
        self.assertFalse(OpenAIGateway._moderation_flagged(None))
        self.assertTrue(
            OpenAIGateway._moderation_flagged(
                SimpleNamespace(flagged=True)
            )
        )
        self.assertTrue(
            OpenAIGateway._moderation_flagged(
                SimpleNamespace(
                    flagged=None,
                    results=[SimpleNamespace(flagged=True)],
                )
            )
        )
        with self.assertRaises(AIProviderError):
            OpenAIGateway._moderation_flagged(
                SimpleNamespace(type="error")
            )

    def test_embedded_moderation_and_refusal_are_enforced(self):
        for field, expected in (
            ("input", "Запрос заблокирован"),
            ("output", "Ответ заблокирован"),
        ):
            moderation = SimpleNamespace(input=None, output=None)
            setattr(moderation, field, SimpleNamespace(flagged=True))
            with self.subTest(field=field):
                with self.assertRaisesRegex(AIContentBlocked, expected):
                    OpenAIGateway._assert_generation_moderation(
                        SimpleNamespace(moderation=moderation)
                    )

        response = SimpleNamespace(
            output=[
                SimpleNamespace(
                    content=[SimpleNamespace(refusal="Отказ модели")]
                )
            ]
        )
        self.assertEqual(
            OpenAIGateway._extract_refusal(response),
            "Отказ модели",
        )
        self.assertEqual(
            OpenAIGateway._extract_refusal(SimpleNamespace(output=[])),
            "",
        )

    def test_empty_text_and_structured_responses_raise_precise_errors(self):
        responses = SimpleNamespace(
            create=lambda **kwargs: SimpleNamespace(
                output_text="",
                output=[],
                moderation=None,
                usage=None,
            ),
            parse=lambda **kwargs: SimpleNamespace(
                output_parsed=None,
                output=[],
                moderation=None,
                usage=None,
            ),
        )
        gateway = OpenAIGateway(
            client=SimpleNamespace(responses=responses)
        )
        common = {
            "system_prompt": "system",
            "user_prompt": "user",
            "reasoning_effort": "low",
            "max_output_tokens": 10,
            "safety_identifier": None,
            "verbosity": "low",
        }

        with self.assertRaisesRegex(AIProviderError, "пустой ответ"):
            gateway.generate_text(**common)
        with self.assertRaisesRegex(
            AIProviderError,
            "не соответствующий схеме",
        ):
            gateway.generate_structured(
                response_model=DomainModerationOutput,
                **common,
            )
        with self.assertRaisesRegex(
            AIProviderError,
            "не соответствующий схеме",
        ):
            gateway.generate_structured_image(
                response_model=DomainModerationOutput,
                image_data_url="data:image/png;base64,AA==",
                image_detail="low",
                **common,
            )

    def test_refusals_are_exposed_for_every_generation_mode(self):
        refusal_response = SimpleNamespace(
            output_text="",
            output_parsed=None,
            moderation=None,
            usage=None,
            output=[
                SimpleNamespace(
                    content=[SimpleNamespace(refusal="Запрос отклонён")]
                )
            ],
        )
        gateway = OpenAIGateway(
            client=SimpleNamespace(
                responses=SimpleNamespace(
                    create=lambda **kwargs: refusal_response,
                    parse=lambda **kwargs: refusal_response,
                )
            )
        )
        common = {
            "system_prompt": "system",
            "user_prompt": "user",
            "reasoning_effort": "low",
            "max_output_tokens": 10,
            "safety_identifier": None,
            "verbosity": "low",
        }
        operations = (
            lambda: gateway.generate_text(**common),
            lambda: gateway.generate_structured(
                response_model=DomainModerationOutput,
                **common,
            ),
            lambda: gateway.generate_structured_image(
                response_model=DomainModerationOutput,
                image_data_url="data:image/png;base64,AA==",
                image_detail="low",
                **common,
            ),
        )
        for operation in operations:
            with self.assertRaisesRegex(
                AIContentBlocked,
                "Запрос отклонён",
            ):
                operation()

    def test_local_policy_decisions_and_combined_moderation(self):
        policy = LocalAutomotivePolicy()
        self.assertEqual(policy.evaluate("").category, "empty")
        with override_settings(AI_MAX_PROMPT_LENGTH=3):
            self.assertEqual(policy.evaluate("длинно").category, "too_long")
        self.assertEqual(
            policy.evaluate("как обойти иммобилайзер").category,
            "vehicle_theft",
        )
        risky = policy.evaluate("ремонт SRS")
        self.assertTrue(risky.allowed)
        self.assertTrue(risky.requires_professional)
        self.assertEqual(policy.evaluate("замена лампы").category, "safe")

        blocked_gateway = FakeOpenAIGateway()
        blocked_gateway.moderate_text = lambda text: (
            ProviderModerationResult(True, ("violence",))
        )
        decision = RequestModerationService(
            blocked_gateway
        ).moderate("замена детали", safety_identifier=None)
        self.assertFalse(decision.allowed)
        self.assertEqual(decision.category, "openai_safety")

        local_only = RequestModerationService(
            FakeOpenAIGateway(),
            enable_domain_moderation=False,
        ).moderate("замена детали", safety_identifier=None)
        self.assertTrue(local_only.allowed)

        enabled = RequestModerationService(FakeOpenAIGateway()).moderate(
            "замена детали",
            safety_identifier="user",
        )
        self.assertTrue(enabled.allowed)
        self.assertEqual(enabled.tokens_used, 15)

        blocked_domain = FakeOpenAIGateway()
        blocked_domain.generate_structured = lambda **kwargs: (
            (_ for _ in ()).throw(AIContentBlocked("Отказ"))
        )
        decision = RequestModerationService(blocked_domain).moderate(
            "замена детали",
            safety_identifier=None,
        )
        self.assertFalse(decision.allowed)

    def test_image_validator_rejects_invalid_inputs_and_compresses_png(self):
        validator = ImageInputValidator()
        with self.assertRaisesRegex(
            AIImageValidationError,
            "не передано",
        ):
            validator.validate(None)
        with self.assertRaisesRegex(
            AIImageValidationError,
            "прочитать",
        ):
            validator.validate(BytesIO())
        invalid = SimpleUploadedFile("bad.png", b"not-an-image")
        with self.assertRaisesRegex(
            AIImageValidationError,
            "повреждён",
        ):
            validator.validate(invalid)

        buffer = BytesIO()
        Image.new("RGBA", (120, 80), "red").save(buffer, format="PNG")
        uploaded = SimpleUploadedFile("деталь.png", buffer.getvalue())
        validated = validator.validate(uploaded)

        self.assertEqual(validated.mime_type, "image/png")
        self.assertEqual((validated.width, validated.height), (120, 80))
        self.assertTrue(validated.data_url.startswith("data:image/png"))

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
            max_chat_requests=max_ai_requests,
            max_image_analyses=max_ai_requests,
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
        purchase = AIContentPurchase.objects.get(
            source_request=result.ai_request
        )
        self.assertEqual(
            purchase.content_type,
            AIContentPurchase.ContentType.CHAT,
        )
        self.assertEqual(purchase.content_key, f"chat:{result.ai_request.pk}")

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
        purchase = AIContentPurchase.objects.get(
            source_request=result.ai_request
        )
        self.assertEqual(
            purchase.content_key,
            f"tools:{self.part.pk}",
        )

    def test_stored_tools_are_charged_without_openai_generation(self):
        category = ToolCategory.objects.create(
            name="Диагностические инструменты",
            slug="diagnostic-tools",
        )
        tool = Tool.objects.create(
            category=category,
            name="Мультиметр",
            size="CAT III",
        )
        PartTool.objects.create(
            part=self.part,
            tool=tool,
            required=True,
        )

        ai_request = self.service.purchase_stored_part_tools(
            user=self.user,
            part=self.part,
        )

        self.assertIsNotNone(ai_request)
        self.assertEqual(
            ai_request.request_type,
            "tool_recommendation_cached",
        )
        self.assertIn(tool.name, ai_request.response)
        purchase = AIContentPurchase.objects.get(
            source_request=ai_request
        )
        self.assertEqual(purchase.source, AIContentPurchase.Source.DATABASE)

    def test_superuser_requests_instruction_and_tools_without_subscription(
            self):
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
        purchase = AIContentPurchase.objects.get(
            source_request=result.ai_request
        )
        self.assertEqual(purchase.instruction, instruction)
        self.assertEqual(purchase.source, AIContentPurchase.Source.DATABASE)

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

    def test_provider_safety_block_is_saved_for_all_generation_types(self):
        def blocked(**kwargs):
            raise AIContentBlocked(
                "Заблокировано провайдером.",
                categories=("safety",),
            )

        scenarios = (
            (
                "chat",
                "generate_text",
                lambda: self.service.answer_chat(
                    user=self.user,
                    message="Проверь безопасную деталь.",
                    part=self.part,
                ),
            ),
            (
                "tool_recommendation",
                "generate_text",
                lambda: self.service.recommend_part_tools(
                    user=self.user,
                    part=self.part,
                    goal="Подбери обычный ключ.",
                ),
            ),
            (
                "repair_instruction",
                "generate_structured",
                lambda: self.service.generate_repair_instruction(
                    user=self.user,
                    part=self.part,
                    goal="Подготовь новую инструкцию.",
                ),
            ),
            (
                "image_analysis",
                "generate_structured_image",
                lambda: self.service.analyze_part_image(
                    user=self.user,
                    image=self.image_file(),
                ),
            ),
        )
        for prefix, method_name, operation in scenarios:
            with self.subTest(prefix=prefix):
                with patch.object(
                    self.gateway,
                    method_name,
                    side_effect=blocked,
                ):
                    with self.assertRaises(AIRequestRejected):
                        operation()
                self.assertTrue(
                    AIRequest.objects.filter(
                        request_type=f"{prefix}_blocked"
                    ).exists()
                )

    def test_blocked_moderation_and_empty_tool_goal_are_saved(self):
        blocked_decision = ModerationDecision(
            allowed=False,
            category="blocked",
            reason="Локально запрещено.",
            risk_level="critical",
            requires_professional=True,
        )
        with patch.object(
            self.service.moderation,
            "moderate",
            return_value=blocked_decision,
        ):
            with self.assertRaises(AIRequestRejected):
                self.service.recommend_part_tools(
                    user=self.user,
                    part=self.part,
                    goal="Проверяемый запрос",
                )
            with self.assertRaises(AIRequestRejected):
                self.service.generate_repair_instruction(
                    user=self.user,
                    part=self.part,
                    goal="Проверяемая инструкция",
                )

        with self.assertRaises(ValueError):
            self.service.recommend_part_tools(
                user=self.user,
                part=self.part,
                goal=" ",
            )
        empty_part = Part.objects.create(
            name="Без инструментов",
            slug="without-tools",
            original_number="NO-TOOLS",
        )
        self.assertIsNone(
            self.service.purchase_stored_part_tools(
                user=self.user,
                part=empty_part,
            )
        )

    def test_instruction_resolution_rejects_foreign_part(self):
        other_part = Part.objects.create(
            name="Другая",
            slug="other-ai-part",
            original_number="OTHER-AI",
        )
        instruction = self.published_instruction()

        with self.assertRaises(ValueError):
            self.service.generate_repair_instruction(
                user=self.user,
                part=other_part,
                instruction=instruction,
                goal="Обнови инструкцию другой детали.",
            )

    def test_image_local_moderation_configuration_and_stored_tool_quota(
        self,
    ):
        blocked = ModerationDecision(
            allowed=False,
            category="blocked",
            reason="Отклонено",
        )
        with patch.object(
            self.service.moderation,
            "moderate",
            return_value=blocked,
        ):
            with self.assertRaises(AIRequestRejected):
                self.service.analyze_part_image(
                    user=self.user,
                    image=self.image_file(),
                )

        with override_settings(OPENAI_IMAGE_DETAIL="invalid"):
            with self.assertRaises(AIConfigurationError):
                self.service.analyze_part_image(
                    user=self.user,
                    image=self.image_file(),
                )

        tool_category = ToolCategory.objects.create(
            name="Тарифные ключи",
            slug="quota-tools",
        )
        tool = Tool.objects.create(
            category=tool_category,
            name="Ключ тарифа",
        )
        PartTool.objects.create(part=self.part, tool=tool)
        self.active_subscription(has_image_analysis=True)
        enforced = SmartAutoPartsAIService(
            gateway=self.gateway,
            enforce_access=True,
            enable_domain_moderation=False,
        )
        request = enforced.purchase_stored_part_tools(
            user=self.user,
            part=self.part,
        )
        self.assertEqual(request.request_type, "tool_recommendation_cached")


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

    @patch("apps.AI.views.SmartAutoPartsAIService")
    def test_create_api_maps_service_errors_to_http_errors(
        self,
        service_class,
    ):
        decision = ModerationDecision(
            allowed=False,
            category="blocked",
            reason="Фото отклонено.",
        )
        scenarios = (
            (
                AIRequestRejected("Фото отклонено.", decision=decision),
                400,
            ),
            (AIAccessDenied("Нет доступа."), 403),
            (AIImageValidationError("Повреждённое фото."), 400),
            (AIProviderError("Сервис недоступен."), 503),
        )
        for error, expected_status in scenarios:
            with self.subTest(error=error.__class__.__name__):
                service_class.return_value.analyze_part_image.side_effect = (
                    error
                )
                response = self.client.post(
                    reverse("apps.AI:image_analysis_create"),
                    {
                        "image": self.image_file(),
                        "confirm_automotive_content": True,
                    },
                    format="multipart",
                )
                self.assertEqual(response.status_code, expected_status)

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

    def test_ai_serializer_owner_duplicate_and_response_branches(self):
        from rest_framework import serializers

        other = get_user_model().objects.create_user(
            username="serializer-other",
            email="serializer-other@example.com",
            password="password",
        )
        ai_request = AIRequest.objects.create(
            user=other,
            part=self.part,
            prompt="Запрос",
            response="Ответ",
            request_type="chat",
        )
        regular = get_user_model().objects.create_user(
            username="serializer-regular",
            email="serializer-regular@example.com",
            password="password",
        )
        foreign_serializer = AIGeneratedInstructionCreateSerializer(
            context={"request": SimpleNamespace(user=regular)}
        )
        with self.assertRaises(serializers.ValidationError):
            foreign_serializer.validate_ai_request(ai_request)

        request = SimpleNamespace(user=self.user)
        serializer = AIGeneratedInstructionCreateSerializer(
            context={"request": request}
        )
        self.assertEqual(
            serializer.validate_ai_request(ai_request),
            ai_request,
        )
        AIGeneratedInstruction.objects.create(
            ai_request=ai_request,
            generated_content="Текст",
        )
        with self.assertRaises(serializers.ValidationError):
            serializer.validate_ai_request(ai_request)
        with self.assertRaises(serializers.ValidationError):
            serializer.validate_generated_content(" ")

        representation = AIRequestSerializer(
            context={"request": SimpleNamespace(user=other)}
        )
        self.assertEqual(
            representation.get_response(ai_request),
            ai_request.response,
        )

    def test_ai_request_and_generated_instruction_api_write_paths(self):
        request_response = self.client.post(
            reverse("apps.AI:ai_request_create"),
            {
                "part": self.part.pk,
                "prompt": "Проверяемый запрос API",
                "response": "Ответ API",
                "request_type": "chat",
            },
            format="json",
        )
        self.assertEqual(request_response.status_code, 201)
        ai_request = AIRequest.objects.latest("pk")
        self.assertEqual(ai_request.user, self.user)

        generated_response = self.client.post(
            reverse("apps.AI:generated_instruction_create"),
            {
                "ai_request": ai_request.pk,
                "generated_content": "Новая подробная инструкция.",
            },
            format="json",
        )
        self.assertEqual(generated_response.status_code, 201)
        generated = AIGeneratedInstruction.objects.latest("pk")

        update_response = self.client.patch(
            reverse(
                "apps.AI:generated_instruction_update",
                kwargs={"pk": generated.pk},
            ),
            {"generated_content": "Исправленная инструкция."},
            format="json",
        )
        self.assertEqual(update_response.status_code, 200)


class AIChatWebPageTests(TestCase):
    def setUp(self):
        cache.clear()
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
        self.assertNotContains(response, 'id="ai-part"')
        self.assertContains(response, 'name="part_query"')
        self.assertContains(response, "Безлимит", count=2)
        self.assertContains(response, 'maxlength="500"')
        self.assertNotContains(response, "data-confirm=")

    @patch("apps.AI.views.SmartAutoPartsAIService")
    def test_rejection_reason_is_rendered_inside_ai_chat(
        self,
        service_class,
    ):
        service_class.return_value.answer_chat.side_effect = (
            AIRequestRejected(
                "Запрос содержит небезопасную рекомендацию.",
                decision=ModerationDecision(
                    allowed=False,
                    category="unsafe",
                    reason="Запрос содержит небезопасную рекомендацию.",
                ),
            )
        )

        self.client.post(
            reverse("ai_web:chat"),
            {"message": "Проверь этот небезопасный запрос"},
        )
        response = self.client.get(reverse("ai_web:chat"))

        self.assertContains(response, "assistant-message--moderator")
        self.assertContains(
            response,
            "Запрос содержит небезопасную рекомендацию.",
        )

    def test_administrator_without_tariff_has_no_unlimited_ai_access(self):
        administrator = get_user_model().objects.create_user(
            username="ai-chat-admin",
            email="ai-chat-admin@example.com",
            password="safe-test-password",
            role="admin",
            is_staff=True,
        )
        self.client.force_login(administrator)

        response = self.client.get(reverse("ai_web:chat"))

        self.assertRedirects(
            response,
            reverse("subscriptions_web:plans"),
            fetch_redirect_response=False,
        )

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

    @patch("apps.AI.views.SmartAutoPartsAIService")
    def test_part_query_is_resolved_from_database_before_ai(
        self,
        service_class,
    ):
        part = Part.objects.create(
            name="Генератор",
            slug="chat-alternator",
            original_number="ALT-42-001",
            manufacturer="Smart",
        )

        self.client.post(
            reverse("ai_web:chat"),
            {
                "message": "Как проверить этот генератор?",
                "part_query": "ALT-42-001",
            },
        )

        service_class.return_value.answer_chat.assert_called_once_with(
            user=self.superuser,
            message="Как проверить этот генератор?",
            part=part,
        )

    @patch("apps.AI.views.SmartAutoPartsAIService")
    def test_unknown_part_query_sends_message_without_link(
        self,
        service_class,
    ):
        self.client.post(
            reverse("ai_web:chat"),
            {
                "message": "Проверь номер UNKNOWN-55 из сообщения.",
                "part_query": "UNKNOWN-55",
            },
        )

        service_class.return_value.answer_chat.assert_called_once_with(
            user=self.superuser,
            message="Проверь номер UNKNOWN-55 из сообщения.",
            part=None,
        )

    @patch("apps.AI.views.SmartAutoPartsAIService")
    def test_chat_form_validates_length_and_handles_service_errors(
        self,
        service_class,
    ):
        url = reverse("ai_web:chat")
        invalid = self.client.post(url, {"message": "x"})
        self.assertEqual(invalid.status_code, 302)
        service_class.return_value.answer_chat.assert_not_called()

        for error in (
            AIAccessDenied("Нет доступа"),
            AIProviderError("Провайдер недоступен"),
        ):
            service_class.return_value.answer_chat.side_effect = error
            response = self.client.post(
                url,
                {"message": "Корректный вопрос"},
            )
            self.assertEqual(response.status_code, 302)

    def test_part_query_resolver_handles_empty_and_name_lookup(self):
        from apps.AI.views import AIChatPageView

        self.assertIsNone(AIChatPageView.resolve_part_query(" "))
        part = Part.objects.create(
            name="Редкий стартер",
            slug="rare-starter",
            original_number="START-77",
            manufacturer="Smart",
        )
        self.assertEqual(
            AIChatPageView.resolve_part_query("Редкий стартер"),
            part,
        )

    def test_regular_user_sees_only_purchased_chat_answers(self):
        user = get_user_model().objects.create_user(
            username="paid-chat-user",
            email="paid-chat-user@example.com",
            password="safe-test-password",
        )
        UserAgreementAcceptance.objects.create(
            user=user,
            agreement_version=settings.USER_AGREEMENT_VERSION,
        )
        plan = SubscriptionPlan.objects.create(
            name="AI chat test",
            price="100.00",
            duration_days=30,
            max_ai_requests=10,
            max_chat_requests=10,
            has_chat_access=True,
            is_public=False,
        )
        subscription = UserSubscription.objects.create(
            user=user,
            plan=plan,
            start_date=timezone.now() - timedelta(days=1),
            end_date=timezone.now() + timedelta(days=29),
            is_active=True,
        )
        bought = AIRequest.objects.create(
            user=user,
            prompt="Купленный вопрос",
            response="Купленный ответ",
            request_type="chat",
        )
        AIContentPurchase.objects.create(
            user=user,
            subscription=subscription,
            content_type=AIContentPurchase.ContentType.CHAT,
            content_key=f"chat:{bought.pk}",
            source_request=bought,
            source=AIContentPurchase.Source.AI,
        )
        AIRequest.objects.create(
            user=user,
            prompt="Старый вопрос без списания",
            response="Не купленный ответ",
            request_type="chat",
        )
        self.client.force_login(user)

        response = self.client.get(reverse("ai_web:chat"))

        self.assertContains(response, "Купленный ответ")
        self.assertNotContains(response, "Не купленный ответ")

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

    def test_admin_rejects_unknown_moderation_decision(self):
        recommendation = self.create_recommendation()
        response = self.client.post(
            self.moderation_url(recommendation, "unknown"),
            {"moderation_note": "Текст"},
        )
        self.assertEqual(response.status_code, 302)
        recommendation.refresh_from_db()
        self.assertEqual(
            recommendation.moderation_status,
            AIToolRecommendation.ModerationStatus.PENDING,
        )

    def test_moderator_readonly_fields_and_completed_action(self):
        moderator = get_user_model().objects.create_user(
            username="tool-readonly-moderator",
            email="tool-readonly-moderator@example.com",
            password="password",
            role="moderator",
            is_staff=True,
        )
        recommendation = self.create_recommendation()
        model_admin = admin.site._registry[AIToolRecommendation]
        request = SimpleNamespace(user=moderator)

        readonly = model_admin.get_readonly_fields(
            request,
            recommendation,
        )
        concrete_names = {
            field.name
            for field in AIToolRecommendation._meta.concrete_fields
        }
        self.assertTrue(concrete_names.issubset(set(readonly)))

        recommendation.moderation_status = (
            AIToolRecommendation.ModerationStatus.APPROVED
        )
        self.assertEqual(
            model_admin.moderation_actions(recommendation),
            recommendation.get_moderation_status_display(),
        )


class AIServiceHelperCoverageTests(TestCase):
    """Проверяет нормализацию и вспомогательные правила AI-сервиса."""

    @classmethod
    def setUpTestData(cls):
        cls.user = get_user_model().objects.create_user(
            username="helper-user",
            email="helper@example.com",
            password="password",
        )
        cls.other = get_user_model().objects.create_user(
            username="helper-other",
            email="other-helper@example.com",
            password="password",
        )
        category = PartCategory.objects.create(
            name="Вспомогательная",
            slug="helper-category",
        )
        cls.part = Part.objects.create(
            category=category,
            name="Фильтр",
            slug="helper-filter",
            original_number="OEM-H-1",
            manufacturer="Производитель",
            description="Описание",
        )

    @staticmethod
    def instruction_output():
        """Создаёт полный структурированный результат инструкции."""
        return RepairInstructionOutput(
            title="  Замена фильтра  ",
            summary="  Описание ремонта  ",
            difficulty="easy",
            estimated_time_minutes=-5,
            safety_warnings=["Остановите двигатель"],
            preconditions=["Охладите узел"],
            tools=[
                RepairToolOutput(
                    name="Ключ",
                    size="10 мм",
                    required=False,
                    usage="Ослабить крепёж",
                )
            ],
            steps=[
                RepairStepOutput(
                    number=9,
                    title=" ",
                    description=" Первый шаг ",
                    warning=" Осторожно ",
                    estimated_minutes=-1,
                ),
                RepairStepOutput(
                    number=8,
                    title="Второй",
                    description="Второй шаг",
                    warning="",
                    estimated_minutes=2,
                ),
                RepairStepOutput(
                    number=7,
                    title="Третий",
                    description="Третий шаг",
                    warning="",
                    estimated_minutes=3,
                ),
            ],
            final_checks=["Проверить герметичность"],
            professional_service_required=False,
            professional_service_reason="",
            assumptions=["Сверить момент затяжки"],
        )

    def test_instruction_normalisation_rendering_and_validation(self):
        decision = ModerationDecision(
            True,
            "automotive_risk",
            "Риск",
            requires_professional=True,
        )
        output = SmartAutoPartsAIService._normalise_instruction(
            self.instruction_output(),
            decision=decision,
        )
        self.assertEqual(output.title, "Замена фильтра")
        self.assertEqual(output.steps[0].number, 1)
        self.assertEqual(output.steps[0].title, "Шаг 1")
        self.assertTrue(output.professional_service_required)
        rendered = SmartAutoPartsAIService._render_instruction(output)
        self.assertIn("## Пошаговая инструкция", rendered)
        self.assertIn("Когда нужен профессиональный сервис", rendered)

        invalid = self.instruction_output()
        invalid.title = ""
        with self.assertRaises(AIProviderError):
            SmartAutoPartsAIService._normalise_instruction(
                invalid,
                decision=decision,
            )
        too_short = self.instruction_output()
        too_short.steps = too_short.steps[:2]
        with self.assertRaises(AIProviderError):
            SmartAutoPartsAIService._normalise_instruction(
                too_short,
                decision=decision,
            )
        blank_step = self.instruction_output()
        blank_step.steps[1].description = " "
        with self.assertRaises(AIProviderError):
            SmartAutoPartsAIService._normalise_instruction(
                blank_step,
                decision=decision,
            )

    def test_instruction_moderation_defensive_branches(self):
        moderator = get_user_model().objects.create_user(
            username="helper-moderator",
            email="helper-moderator@example.com",
            password="password",
            role="moderator",
            is_staff=True,
        )
        service = AIInstructionModerationService()

        with self.assertRaises(ValueError):
            service.reject(
                moderator=moderator,
                generated_instruction=1,
                moderation_note=" ",
            )
        with self.assertRaises(AIServiceError):
            service._assert_pending(
                SimpleNamespace(
                    is_cached=True,
                    moderation_status="pending",
                )
            )
        with self.assertRaises(AIServiceError):
            service._assert_pending(
                SimpleNamespace(
                    is_cached=False,
                    moderation_status="approved",
                )
            )
        with self.assertRaises(AIServiceError):
            service._create_published_instruction(
                generated=SimpleNamespace(
                    ai_request=SimpleNamespace(part=None),
                ),
                moderator=moderator,
            )

        Instruction.objects.create(
            part=self.part,
            title="Занятый адрес",
            slug="занятый-адрес",
            content="Существующий материал.",
        )
        self.assertEqual(
            service._unique_slug("Занятый адрес", 77),
            "занятый-адрес-2",
        )

    def test_tool_response_visibility_and_purchase_string(self):
        without_recommendation = AIRequest.objects.create(
            user=self.user,
            part=self.part,
            prompt="Подбери инструмент.",
            response="Исходный ответ.",
            request_type="tool_recommendation",
        )
        serializer = AIRequestSerializer(
            context={"request": SimpleNamespace(user=self.user)}
        )
        self.assertEqual(
            serializer.get_response(without_recommendation),
            "Исходный ответ.",
        )

        rejected_request = AIRequest.objects.create(
            user=self.user,
            part=self.part,
            prompt="Повторный подбор.",
            response="Скрытый ответ.",
            request_type="tool_recommendation_moderation_rejected",
        )
        AIToolRecommendation.objects.create(
            ai_request=rejected_request,
            generated_content="Скрытый ответ.",
            moderation_status="rejected",
            moderation_note="Недостаточно данных.",
        )
        self.assertIn(
            "Недостаточно данных",
            serializer.get_response(rejected_request),
        )

        purchase = AIContentPurchase.objects.create(
            user=self.user,
            part=self.part,
            content_type=AIContentPurchase.ContentType.TOOLS,
            content_key=f"tools:{self.part.pk}",
        )
        self.assertIn(purchase.content_key, str(purchase))

    def test_image_normalisation_and_rendering(self):
        alternative = Part.objects.create(
            category=self.part.category,
            name="Альтернативный фильтр",
            slug="helper-alternative-filter",
            original_number="OEM-H-2",
        )
        output = PartImageAnalysisOutput(
            is_automotive_part=True,
            is_automotive_tool=False,
            part_name=" Фильтр ",
            part_category=" Категория ",
            manufacturer=" Завод ",
            visible_oem_numbers=[" OEM-H-1 ", ""],
            visible_markings=[" M "],
            condition="used_good",
            observed_damage=[],
            confidence_score=float("nan"),
            description=" Описание ",
            safety_notes=[" Проверить "],
            matched_part_id=self.part.pk,
            alternative_part_ids=[
                self.part.pk,
                alternative.pk,
                999,
                alternative.pk,
            ],
            match_basis=" OEM ",
            limitations=[" Ракурс "],
        )
        catalog = ImageCatalogContext(
            payload={},
            parts_by_id={
                self.part.pk: self.part,
                alternative.pk: alternative,
            },
            oem_index={"OEMH1": self.part.pk},
        )
        normalised = SmartAutoPartsAIService._normalise_image_analysis(
            output,
            catalog=catalog,
        )
        self.assertEqual(normalised.confidence_score, 0)
        self.assertEqual(
            normalised.alternative_part_ids,
            [alternative.pk],
        )
        rendered = SmartAutoPartsAIService._render_image_analysis(
            normalised,
            detected_part=self.part,
        )
        self.assertIn("OEM-H-1", rendered)

        normalised.is_automotive_part = False
        normalised.is_automotive_tool = False
        self.assertIn(
            "не обнаружена",
            SmartAutoPartsAIService._render_image_analysis(
                normalised,
                detected_part=None,
            ),
        )

    def test_access_identifier_part_and_private_chat_history(self):
        anonymous = SimpleNamespace(is_authenticated=False)
        with self.assertRaises(AIAccessDenied):
            SmartAutoPartsAIService._assert_can_moderate(anonymous)
        with self.assertRaises(AIAccessDenied):
            SmartAutoPartsAIService._assert_can_moderate(self.user)
        self.user.is_superuser = True
        SmartAutoPartsAIService._assert_can_moderate(self.user)
        self.user.is_superuser = False

        self.assertIsNone(
            SmartAutoPartsAIService._safety_identifier(
                SimpleNamespace(pk=None)
            )
        )
        self.assertEqual(
            len(SmartAutoPartsAIService._safety_identifier(self.user)),
            64,
        )
        self.assertIs(
            SmartAutoPartsAIService._part_instance(self.part),
            self.part,
        )
        self.assertEqual(
            SmartAutoPartsAIService._part_instance(self.part.pk),
            self.part,
        )
        self.assertIsNone(SmartAutoPartsAIService._part_instance(None))
        self.assertEqual(
            SmartAutoPartsAIService._chat_history(
                user=self.user,
                room=None,
                limit=10,
            ),
            [],
        )

        room = ChatRoom.objects.create(
            name="Закрытая",
            is_private=True,
            created_by=self.other,
        )
        with self.assertRaises(AIAccessDenied):
            SmartAutoPartsAIService._chat_history(
                user=self.user,
                room=room,
                limit=10,
            )
        ChatParticipant.objects.create(room=room, user=self.user)
        ChatMessage.objects.create(
            room=room,
            user=self.other,
            message="Сообщение истории",
        )
        history = SmartAutoPartsAIService._chat_history(
            user=self.user,
            room=room.pk,
            limit=100,
        )
        self.assertEqual(history[0]["content"], "Сообщение истории")

    def test_image_validator_rejects_limits_formats_and_animation(self):
        validator = ImageInputValidator()
        oversized = SimpleNamespace(
            size=100,
            read=lambda count: b"x",
            seek=lambda offset: None,
        )
        with override_settings(AI_IMAGE_MAX_BYTES=10):
            with self.assertRaises(AIImageValidationError):
                validator.validate(oversized)

        non_bytes = SimpleNamespace(
            size=0,
            read=lambda count: "text",
            seek=lambda offset: None,
        )
        with self.assertRaises(AIImageValidationError):
            validator.validate(non_bytes)

        def uploaded(format_name, size=(100, 100), **save_kwargs):
            buffer = BytesIO()
            Image.new("RGB", size, "green").save(
                buffer,
                format=format_name,
                **save_kwargs,
            )
            return SimpleUploadedFile(
                f"part.{format_name.lower()}",
                buffer.getvalue(),
            )

        with self.assertRaises(AIImageValidationError):
            validator.validate(uploaded("BMP"))
        with override_settings(AI_IMAGE_MIN_SIDE=64):
            with self.assertRaises(AIImageValidationError):
                validator.validate(uploaded("PNG", (20, 20)))
        with override_settings(AI_IMAGE_MAX_PIXELS=100):
            with self.assertRaises(AIImageValidationError):
                validator.validate(uploaded("PNG"))

        jpeg = BytesIO()
        Image.new("RGBA", (100, 100), "red").save(jpeg, format="PNG")
        source = SimpleUploadedFile("rgba.png", jpeg.getvalue())
        self.assertEqual(validator.validate(source).format_name, "PNG")
        self.assertEqual(
            validator.validate(uploaded("WEBP")).format_name,
            "WEBP",
        )

        first = Image.new("RGB", (100, 100), "red")
        second = Image.new("RGB", (100, 100), "blue")
        animated = BytesIO()
        first.save(
            animated,
            format="GIF",
            save_all=True,
            append_images=[second],
            duration=100,
            loop=0,
        )
        with self.assertRaises(AIImageValidationError):
            validator.validate(
                SimpleUploadedFile("animated.gif", animated.getvalue())
            )

    def test_quota_service_rejects_each_access_state(self):
        quota = AIQuotaService()
        with self.assertRaises(AIAccessDenied):
            quota.check(
                SimpleNamespace(
                    is_authenticated=False,
                    is_active=True,
                ),
                feature="chat",
            )
        inactive = get_user_model().objects.create_user(
            username="inactive-quota",
            email="inactive-quota@example.com",
            password="password",
            is_active=False,
        )
        with self.assertRaises(AIAccessDenied):
            quota.check(inactive, feature="chat")
        with self.assertRaises(AIAccessDenied):
            quota.check(self.user, feature="chat")

        UserAgreementAcceptance.objects.create(
            user=self.user,
            agreement_version=settings.USER_AGREEMENT_VERSION,
        )
        with self.assertRaises(AIAccessDenied):
            quota.check(self.user, feature="chat")

        plan = SubscriptionPlan.objects.create(
            name="Ограниченный",
            price="1.00",
            duration_days=30,
            max_ai_requests=0,
            max_chat_requests=0,
            max_instruction_requests=0,
            max_image_analyses=0,
            has_chat_access=False,
            has_instruction_generation=False,
            has_image_analysis=False,
            is_public=False,
        )
        UserSubscription.objects.create(
            user=self.user,
            plan=plan,
            start_date=timezone.now() - timedelta(days=1),
            end_date=timezone.now() + timedelta(days=1),
        )
        for feature in ("chat", "instruction", "image_analysis"):
            with self.subTest(feature=feature):
                with self.assertRaises(AIAccessDenied):
                    quota.check(self.user, feature=feature)

        plan.has_chat_access = True
        plan.save(update_fields=["has_chat_access"])
        with self.assertRaises(AIQuotaExceeded):
            quota.check(self.user, feature="chat")

    def test_context_and_catalog_helpers_cover_empty_and_thresholds(self):
        context_builder = ProjectContextBuilder()
        self.assertIsNone(context_builder._user_vehicle(self.user))
        profile = Profile.objects.create(
            user=self.user,
            car_brand="Lada",
            car_model="Vesta",
            car_year=2024,
            preferred_language="Русский",
            country="Россия",
        )
        self.assertEqual(
            context_builder._user_vehicle(self.user)["brand"],
            profile.car_brand,
        )
        self.assertIsNone(
            context_builder.build(user=self.user, part=None)["part"]
        )
        self.assertEqual(
            context_builder._trim(" abc ", 10),
            "abc",
        )
        self.assertEqual(
            context_builder._trim("abcdefgh", 4),
            "abcd…",
        )
        self.assertIsNone(
            ImageCatalogBuilder().resolve_detected_part(
                output=PartImageAnalysisOutput(
                    is_automotive_part=False,
                    is_automotive_tool=True,
                    part_name="Ключ",
                    part_category="Инструменты",
                    manufacturer="",
                    visible_oem_numbers=[],
                    visible_markings=[],
                    condition="unknown",
                    observed_damage=[],
                    confidence_score=99,
                    description="",
                    safety_notes=[],
                    matched_part_id=0,
                    alternative_part_ids=[],
                    match_basis="",
                    limitations=[],
                ),
                catalog=ImageCatalogContext({}, {}, {}),
            )
        )

        catalog = ImageCatalogContext(
            {},
            {self.part.pk: self.part},
            {},
        )
        low_confidence = PartImageAnalysisOutput(
            is_automotive_part=True,
            is_automotive_tool=False,
            part_name="Фильтр",
            part_category="",
            manufacturer="",
            visible_oem_numbers=[],
            visible_markings=[],
            condition="unknown",
            observed_damage=[],
            confidence_score=10,
            description="",
            safety_notes=[],
            matched_part_id=self.part.pk,
            alternative_part_ids=[],
            match_basis="",
            limitations=[],
        )
        matcher = ImageCatalogBuilder()
        self.assertIsNone(
            matcher.resolve_detected_part(
                output=low_confidence,
                catalog=catalog,
            )
        )
        low_confidence.confidence_score = 90
        self.assertEqual(
            matcher.resolve_detected_part(
                output=low_confidence,
                catalog=catalog,
            ),
            self.part,
        )

    def test_existing_purchase_is_enriched_and_saved(self):
        purchase = AIContentPurchase.objects.create(
            user=self.user,
            content_type=AIContentPurchase.ContentType.TOOLS,
            content_key=f"tools:{self.part.pk}",
        )
        request = AIRequest.objects.create(
            user=self.user,
            part=self.part,
            prompt="Запрос",
            response="Ответ",
            request_type="tool_recommendation_cached",
        )
        enriched = record_content_purchase(
            user=self.user,
            content_type=AIContentPurchase.ContentType.TOOLS,
            content_key=f"tools:{self.part.pk}",
            part=self.part,
            source_request=request,
            subscription=None,
            source=AIContentPurchase.Source.DATABASE,
        )
        enriched.refresh_from_db()
        self.assertEqual(enriched.pk, purchase.pk)
        self.assertEqual(enriched.part, self.part)
        self.assertEqual(enriched.source_request, request)

    def test_instruction_moderation_parsers_and_rejections(self):
        service = AIInstructionModerationService()
        self.assertEqual(
            service._extract_title("Текст", fallback="Запасной"),
            "Запасной",
        )
        self.assertEqual(service._extract_summary("# Заголовок"), "")
        self.assertEqual(service._extract_difficulty("Текст"), "")
        self.assertIsNone(service._extract_estimated_time("Текст"))
        self.assertTrue(
            service._unique_slug("", 77).startswith("ai-instruction-77")
        )
        with self.assertRaises(AIAccessDenied):
            service._assert_can_moderate(
                SimpleNamespace(is_authenticated=False)
            )
        with self.assertRaises(AIAccessDenied):
            service._assert_can_moderate(self.user)

    def test_pretty_json_widget_formats_supported_values(self):
        widget = PrettyJSONWidget()
        self.assertEqual(widget.format_value(None), "")
        self.assertEqual(widget.format_value("not-json"), "not-json")
        formatted = widget.format_value({"b": 2, "a": 1})
        self.assertIn('"a": 1', formatted)
        self.assertLess(formatted.index('"a"'), formatted.index('"b"'))

    def test_service_moderation_delegates_enforce_permissions(self):
        service = SmartAutoPartsAIService(
            gateway=FakeOpenAIGateway(),
            enforce_access=False,
        )
        operations = (
            lambda: service.reject_generated_instruction(
                moderator=self.user,
                generated_instruction=1,
                moderation_note="Причина",
            ),
            lambda: service.approve_tool_recommendation(
                moderator=self.user,
                recommendation=1,
            ),
            lambda: service.reject_tool_recommendation(
                moderator=self.user,
                recommendation=1,
                moderation_note="Причина",
            ),
        )
        for operation in operations:
            with self.assertRaises(AIAccessDenied):
                operation()
