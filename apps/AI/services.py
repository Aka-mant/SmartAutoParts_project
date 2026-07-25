"""
Сервисный слой AI-приложения SmartAutoParts.

Основная модель — GPT-5.6 Sol через OpenAI Responses API. Модуль:

* модерирует входящие запросы;
* отвечает в AI-чате с контекстом моделей проекта;
* распознаёт запчасти на пользовательских фотографиях;
* генерирует структурированные пошаговые инструкции;
* контролирует доступ и лимиты подписки;
* сохраняет историю в AI-моделях проекта.

Сервис намеренно не публикует AI-инструкции как ``Instruction`` автоматически:
перед публикацией технический материал должен проверить человек.
"""

from __future__ import annotations

import base64
import hashlib
import logging
import math
import os
import re
import warnings
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from datetime import timedelta
from decimal import Decimal
from io import BytesIO
from typing import Any, Generic, Literal, Protocol, TypeVar

from django.conf import settings
from django.core.exceptions import ObjectDoesNotExist
from django.core.files.base import ContentFile
from django.db import transaction
from django.db.models import Prefetch
from django.utils import timezone
from django.utils.text import get_valid_filename
from PIL import Image, UnidentifiedImageError
from pydantic import BaseModel, ConfigDict

from apps.AI.models import AIGeneratedInstruction, AIImageAnalysis, AIRequest
from apps.AI.prompts import (
    CHAT_SYSTEM_PROMPT,
    IMAGE_ANALYSIS_SYSTEM_PROMPT,
    INSTRUCTION_SYSTEM_PROMPT,
    MODERATION_SYSTEM_PROMPT,
    build_chat_prompt,
    build_image_analysis_prompt,
    build_instruction_prompt,
    build_moderation_prompt,
)
from apps.chat.models import ChatMessage, ChatParticipant, ChatRoom
from apps.instructions.models import (
    Instruction,
    InstructionTool,
    InstructionVersion,
)
from apps.parts.models import Part
from apps.subscriptions.models import UserSubscription
from apps.tools.models import PartTool

logger = logging.getLogger(__name__)


class AIServiceError(Exception):
    """Базовая ошибка сервисного слоя AI."""


class AIConfigurationError(AIServiceError):
    """AI-провайдер не настроен."""


class AIProviderError(AIServiceError):
    """OpenAI API вернул ошибку или некорректный ответ."""


class AIAccessDenied(AIServiceError):
    """Пользователь не имеет доступа к запрошенной AI-функции."""


class AIQuotaExceeded(AIAccessDenied):
    """Лимит AI-запросов по подписке исчерпан."""


class AIImageValidationError(AIServiceError):
    """Загруженное изображение не прошло проверку."""


class AIContentBlocked(AIServiceError):
    """OpenAI или локальная политика заблокировали содержимое."""

    def __init__(
        self,
        message: str,
        *,
        categories: Sequence[str] = (),
    ) -> None:
        super().__init__(message)
        self.categories = tuple(categories)


class AIRequestRejected(AIServiceError):
    """Запрос отклонён модерацией и записан в историю."""

    def __init__(
        self,
        message: str,
        *,
        decision: "ModerationDecision",
        ai_request: AIRequest | None = None,
    ) -> None:
        super().__init__(message)
        self.decision = decision
        self.ai_request = ai_request


class StrictOutputModel(BaseModel):
    """Базовая схема OpenAI Structured Outputs."""

    model_config = ConfigDict(extra="forbid")


class DomainModerationOutput(StrictOutputModel):
    """Смысловое решение по автомобильной политике проекта."""

    allowed: bool
    category: Literal["safe", "automotive_risk", "blocked"]
    reason: str
    risk_level: Literal["low", "medium", "high", "critical"]
    requires_professional: bool


class RepairToolOutput(StrictOutputModel):
    """Инструмент в сгенерированной инструкции."""

    name: str
    size: str
    required: bool
    usage: str


class RepairStepOutput(StrictOutputModel):
    """Один шаг сгенерированной инструкции."""

    number: int
    title: str
    description: str
    warning: str
    estimated_minutes: int


class RepairInstructionOutput(StrictOutputModel):
    """Структурированный результат генерации ремонтной инструкции."""

    title: str
    summary: str
    difficulty: Literal["easy", "medium", "hard", "expert"]
    estimated_time_minutes: int
    safety_warnings: list[str]
    preconditions: list[str]
    tools: list[RepairToolOutput]
    steps: list[RepairStepOutput]
    final_checks: list[str]
    professional_service_required: bool
    professional_service_reason: str
    assumptions: list[str]


class PartImageAnalysisOutput(StrictOutputModel):
    """Структурированный результат визуального анализа детали."""

    is_automotive_part: bool
    part_name: str
    part_category: str
    manufacturer: str
    visible_oem_numbers: list[str]
    visible_markings: list[str]
    condition: Literal[
        "new",
        "used_good",
        "worn",
        "damaged",
        "unknown",
    ]
    observed_damage: list[str]
    confidence_score: float
    description: str
    safety_notes: list[str]
    matched_part_id: int
    alternative_part_ids: list[int]
    match_basis: str
    limitations: list[str]


@dataclass(frozen=True)
class ProviderResponse:
    """Текстовый ответ AI-провайдера."""

    text: str
    tokens_used: int


OutputT = TypeVar("OutputT", bound=BaseModel)


@dataclass(frozen=True)
class StructuredProviderResponse(Generic[OutputT]):
    """Валидированный структурированный ответ AI-провайдера."""

    parsed: OutputT
    tokens_used: int


@dataclass(frozen=True)
class ProviderModerationResult:
    """Результат OpenAI Moderation API."""

    flagged: bool
    categories: tuple[str, ...]


@dataclass(frozen=True)
class ModerationDecision:
    """Итог объединённой модерации запроса."""

    allowed: bool
    category: str
    reason: str
    risk_level: str = "low"
    requires_professional: bool = False
    tokens_used: int = 0


@dataclass(frozen=True)
class ChatServiceResult:
    """Результат ответа AI-чата."""

    ai_request: AIRequest
    answer: str
    moderation: ModerationDecision


@dataclass(frozen=True)
class InstructionServiceResult:
    """Результат генерации AI-инструкции."""

    ai_request: AIRequest
    generated_instruction: AIGeneratedInstruction
    payload: dict[str, Any]
    moderation: ModerationDecision
    cached: bool = False
    requires_moderation: bool = False


@dataclass(frozen=True)
class ImageAnalysisServiceResult:
    """Результат визуального анализа пользовательской фотографии."""

    ai_request: AIRequest
    image_analysis: AIImageAnalysis
    payload: dict[str, Any]
    detected_part: Part | None
    moderation: ModerationDecision


@dataclass(frozen=True)
class ValidatedImage:
    """Проверенные байты и метаданные изображения."""

    content: bytes
    data_url: str
    filename: str
    mime_type: str
    width: int
    height: int
    format_name: str


@dataclass(frozen=True)
class ImageCatalogContext:
    """Каталог-кандидат и индекс OEM-номеров для сопоставления."""

    payload: dict[str, Any]
    parts_by_id: dict[int, Part]
    oem_index: dict[str, int]


class AIGateway(Protocol):
    """Контракт шлюза, позволяющий тестировать сервис без реального API."""

    def moderate_text(self, text: str) -> ProviderModerationResult:
        """Проверить текст через OpenAI Moderation API."""

    def moderate_multimodal(
        self,
        *,
        text: str,
        image_data_url: str,
    ) -> ProviderModerationResult:
        """Проверить текст и изображение через OpenAI Moderation API."""

    def generate_text(
        self,
        *,
        system_prompt: str,
        user_prompt: str,
        reasoning_effort: str,
        max_output_tokens: int,
        safety_identifier: str | None,
        verbosity: str,
    ) -> ProviderResponse:
        """Получить обычный текстовый ответ."""

    def generate_structured(
        self,
        *,
        system_prompt: str,
        user_prompt: str,
        response_model: type[OutputT],
        reasoning_effort: str,
        max_output_tokens: int,
        safety_identifier: str | None,
        verbosity: str,
    ) -> StructuredProviderResponse[OutputT]:
        """Получить ответ по Pydantic-схеме."""

    def generate_structured_image(
        self,
        *,
        system_prompt: str,
        user_prompt: str,
        image_data_url: str,
        image_detail: str,
        response_model: type[OutputT],
        reasoning_effort: str,
        max_output_tokens: int,
        safety_identifier: str | None,
        verbosity: str,
    ) -> StructuredProviderResponse[OutputT]:
        """Получить структурированный ответ по изображению."""


class OpenAIGateway:
    """Шлюз OpenAI Responses API для GPT-5.6 Sol."""

    def __init__(
        self,
        *,
        api_key: str | None = None,
        model: str | None = None,
        moderation_model: str | None = None,
        timeout: float | None = None,
        client: Any | None = None,
    ) -> None:
        resolved_key = (
            api_key
            or getattr(settings, "OPENAI_API_KEY", "")
            or os.getenv("OPENAI_API_KEY", "")
        )

        if client is None and not resolved_key:
            raise AIConfigurationError(
                "Не задан OPENAI_API_KEY для работы AI-сервиса."
            )

        self.model = (
            model
            or getattr(settings, "OPENAI_AI_MODEL", "")
            or "gpt-5.6-sol"
        )
        self.moderation_model = (
            moderation_model
            or getattr(settings, "OPENAI_MODERATION_MODEL", "")
            or "omni-moderation-latest"
        )

        if client is not None:
            self.client = client
            return

        try:
            from openai import OpenAI
        except ImportError as exc:  # pragma: no cover - зависит от окружения.
            raise AIConfigurationError(
                "Установите пакет openai из requirements/base.txt."
            ) from exc

        self.client = OpenAI(
            api_key=resolved_key,
            timeout=timeout
            or float(getattr(settings, "OPENAI_TIMEOUT_SECONDS", 90)),
            max_retries=int(getattr(settings, "OPENAI_MAX_RETRIES", 2)),
        )

    def moderate_text(self, text: str) -> ProviderModerationResult:
        try:
            response = self.client.moderations.create(
                model=self.moderation_model,
                input=text,
            )
        except Exception as exc:  # pragma: no cover - сетевой код.
            logger.exception("OpenAI moderation request failed")
            raise AIProviderError(
                "Не удалось выполнить модерацию запроса."
            ) from exc

        return self._parse_moderation_response(response)

    def moderate_multimodal(
        self,
        *,
        text: str,
        image_data_url: str,
    ) -> ProviderModerationResult:
        try:
            response = self.client.moderations.create(
                model=self.moderation_model,
                input=[
                    {"type": "text", "text": text},
                    {
                        "type": "image_url",
                        "image_url": {"url": image_data_url},
                    },
                ],
            )
        except Exception as exc:  # pragma: no cover - сетевой код.
            logger.exception("OpenAI multimodal moderation request failed")
            raise AIProviderError(
                "Не удалось выполнить модерацию изображения."
            ) from exc

        return self._parse_moderation_response(response)

    @classmethod
    def _parse_moderation_response(
        cls,
        response: Any,
    ) -> ProviderModerationResult:
        if not getattr(response, "results", None):
            raise AIProviderError("OpenAI вернул пустой результат модерации.")

        result = response.results[0]
        categories_data = cls._model_dump(getattr(result, "categories", {}))
        categories = tuple(
            name
            for name, is_flagged in categories_data.items()
            if bool(is_flagged)
        )
        return ProviderModerationResult(
            flagged=bool(getattr(result, "flagged", False)),
            categories=categories,
        )

    def generate_text(
        self,
        *,
        system_prompt: str,
        user_prompt: str,
        reasoning_effort: str,
        max_output_tokens: int,
        safety_identifier: str | None,
        verbosity: str,
    ) -> ProviderResponse:
        try:
            response = self.client.responses.create(
                model=self.model,
                instructions=system_prompt,
                input=[{"role": "user", "content": user_prompt}],
                reasoning={"effort": reasoning_effort},
                max_output_tokens=max_output_tokens,
                moderation={"model": self.moderation_model},
                safety_identifier=safety_identifier,
                store=False,
                text={"verbosity": verbosity},
            )
        except Exception as exc:  # pragma: no cover - сетевой код.
            logger.exception("OpenAI text generation failed")
            raise AIProviderError(
                "OpenAI не смог сформировать ответ."
            ) from exc

        self._assert_generation_moderation(response)
        text = (getattr(response, "output_text", "") or "").strip()
        if not text:
            refusal = self._extract_refusal(response)
            if refusal:
                raise AIContentBlocked(refusal)
            raise AIProviderError("OpenAI вернул пустой ответ.")

        return ProviderResponse(
            text=text,
            tokens_used=self._total_tokens(response),
        )

    def generate_structured(
        self,
        *,
        system_prompt: str,
        user_prompt: str,
        response_model: type[OutputT],
        reasoning_effort: str,
        max_output_tokens: int,
        safety_identifier: str | None,
        verbosity: str,
    ) -> StructuredProviderResponse[OutputT]:
        try:
            response = self.client.responses.parse(
                model=self.model,
                instructions=system_prompt,
                input=[{"role": "user", "content": user_prompt}],
                text_format=response_model,
                reasoning={"effort": reasoning_effort},
                max_output_tokens=max_output_tokens,
                moderation={"model": self.moderation_model},
                safety_identifier=safety_identifier,
                store=False,
                verbosity=verbosity,
            )
        except Exception as exc:  # pragma: no cover - сетевой код.
            logger.exception("OpenAI structured generation failed")
            raise AIProviderError(
                "OpenAI не смог сформировать структурированный ответ."
            ) from exc

        self._assert_generation_moderation(response)
        parsed = getattr(response, "output_parsed", None)
        if parsed is None:
            refusal = self._extract_refusal(response)
            if refusal:
                raise AIContentBlocked(refusal)
            raise AIProviderError(
                "OpenAI вернул ответ, не соответствующий схеме."
            )

        return StructuredProviderResponse(
            parsed=parsed,
            tokens_used=self._total_tokens(response),
        )

    def generate_structured_image(
        self,
        *,
        system_prompt: str,
        user_prompt: str,
        image_data_url: str,
        image_detail: str,
        response_model: type[OutputT],
        reasoning_effort: str,
        max_output_tokens: int,
        safety_identifier: str | None,
        verbosity: str,
    ) -> StructuredProviderResponse[OutputT]:
        try:
            response = self.client.responses.parse(
                model=self.model,
                instructions=system_prompt,
                input=[
                    {
                        "role": "user",
                        "content": [
                            {
                                "type": "input_text",
                                "text": user_prompt,
                            },
                            {
                                "type": "input_image",
                                "image_url": image_data_url,
                                "detail": image_detail,
                            },
                        ],
                    }
                ],
                text_format=response_model,
                reasoning={"effort": reasoning_effort},
                max_output_tokens=max_output_tokens,
                moderation={"model": self.moderation_model},
                safety_identifier=safety_identifier,
                store=False,
                verbosity=verbosity,
            )
        except Exception as exc:  # pragma: no cover - сетевой код.
            logger.exception("OpenAI image analysis failed")
            raise AIProviderError(
                "OpenAI не смог проанализировать изображение."
            ) from exc

        self._assert_generation_moderation(response)
        parsed = getattr(response, "output_parsed", None)
        if parsed is None:
            refusal = self._extract_refusal(response)
            if refusal:
                raise AIContentBlocked(refusal)
            raise AIProviderError(
                "OpenAI вернул анализ, не соответствующий схеме."
            )

        return StructuredProviderResponse(
            parsed=parsed,
            tokens_used=self._total_tokens(response),
        )

    @staticmethod
    def _model_dump(value: Any) -> dict[str, Any]:
        if hasattr(value, "model_dump"):
            return value.model_dump()
        if isinstance(value, Mapping):
            return dict(value)
        return {}

    @staticmethod
    def _total_tokens(response: Any) -> int:
        usage = getattr(response, "usage", None)
        if usage is None:
            return 0
        total = getattr(usage, "total_tokens", None)
        if total is not None:
            return max(0, int(total))
        return max(
            0,
            int(getattr(usage, "input_tokens", 0) or 0)
            + int(getattr(usage, "output_tokens", 0) or 0),
        )

    @classmethod
    def _moderation_flagged(cls, result: Any) -> bool:
        if result is None:
            return False
        if getattr(result, "type", "") == "error":
            raise AIProviderError(
                "OpenAI вернул ошибку встроенной модерации."
            )
        flagged = getattr(result, "flagged", None)
        if flagged is not None:
            return bool(flagged)
        results = getattr(result, "results", ()) or ()
        return any(bool(getattr(item, "flagged", False)) for item in results)

    @classmethod
    def _assert_generation_moderation(cls, response: Any) -> None:
        moderation = getattr(response, "moderation", None)
        if moderation is None:
            return
        if cls._moderation_flagged(getattr(moderation, "input", None)):
            raise AIContentBlocked(
                "Запрос заблокирован встроенной модерацией OpenAI."
            )
        if cls._moderation_flagged(getattr(moderation, "output", None)):
            raise AIContentBlocked(
                "Ответ заблокирован встроенной модерацией OpenAI."
            )

    @staticmethod
    def _extract_refusal(response: Any) -> str:
        for item in getattr(response, "output", ()) or ():
            for content in getattr(item, "content", ()) or ():
                refusal = getattr(content, "refusal", None)
                if refusal:
                    return str(refusal)
        return ""


class LocalAutomotivePolicy:
    """Быстрые детерминированные правила до обращения к OpenAI."""

    _BLOCK_PATTERNS: tuple[tuple[str, re.Pattern[str]], ...] = (
        (
            "vehicle_theft",
            re.compile(
                r"(обойт|взлом|эмулир|удалить).{0,45}"
                r"(иммобилайзер|сигнализац|противоугон)"
                r"|(?:immobilizer|alarm).{0,35}(?:bypass|hack)",
                re.IGNORECASE | re.DOTALL,
            ),
        ),
        (
            "odometer_fraud",
            re.compile(
                r"(скрут|уменьш|поддел|измен).{0,35}(пробег|одометр)"
                r"|(?:rollback|tamper).{0,25}(?:odometer|mileage)",
                re.IGNORECASE | re.DOTALL,
            ),
        ),
        (
            "safety_bypass",
            re.compile(
                r"(обманк|эмулятор|навсегда отключ|ездить без).{0,45}"
                r"(подушк|srs|abs|esp|тормозн)"
                r"|(?:bypass|defeat).{0,35}(?:airbag|brake|abs|esp)",
                re.IGNORECASE | re.DOTALL,
            ),
        ),
        (
            "weapon_or_sabotage",
            re.compile(
                r"(сделать|изготовить|собрать).{0,35}"
                r"(бомб|взрыв|оруж)"
                r"|(?:build|make).{0,30}(?:bomb|weapon)"
                r"|(?:сломать|повредить|саботир).{0,35}"
                r"(чуж|автомоб|машин)",
                re.IGNORECASE | re.DOTALL,
            ),
        ),
    )

    _PROFESSIONAL_RISK = re.compile(
        r"\b(srs|airbag|abs|esp|высоковольт|hybrid battery|"
        r"подушк\w*\s+безопасност|тормозн\w*\s+систем|"
        r"рулев\w*\s+управлен|топливн\w*\s+магистрал)\b",
        re.IGNORECASE,
    )

    def evaluate(self, text: str) -> ModerationDecision:
        cleaned = text.strip()
        if not cleaned:
            return ModerationDecision(
                allowed=False,
                category="empty",
                reason="Запрос не может быть пустым.",
            )

        max_length = int(getattr(settings, "AI_MAX_PROMPT_LENGTH", 8_000))
        if len(cleaned) > max_length:
            return ModerationDecision(
                allowed=False,
                category="too_long",
                reason=f"Запрос превышает лимит {max_length} символов.",
            )

        for category, pattern in self._BLOCK_PATTERNS:
            if pattern.search(cleaned):
                return ModerationDecision(
                    allowed=False,
                    category=category,
                    reason=(
                        "Запрос противоречит правилам безопасности "
                        "SmartAutoParts."
                    ),
                    risk_level="critical",
                    requires_professional=True,
                )

        requires_professional = bool(self._PROFESSIONAL_RISK.search(cleaned))
        return ModerationDecision(
            allowed=True,
            category=(
                "automotive_risk" if requires_professional else "safe"
            ),
            reason=(
                "Запрос требует усиленного предупреждения о безопасности."
                if requires_professional
                else "Локальные правила нарушений не обнаружили."
            ),
            risk_level="high" if requires_professional else "low",
            requires_professional=requires_professional,
        )


class RequestModerationService:
    """Объединяет локальные правила, Moderation API и GPT-классификацию."""

    def __init__(
        self,
        gateway: AIGateway,
        *,
        enable_domain_moderation: bool | None = None,
    ) -> None:
        self.gateway = gateway
        self.local_policy = LocalAutomotivePolicy()
        self.enable_domain_moderation = (
            bool(
                getattr(settings, "AI_ENABLE_DOMAIN_MODERATION", True)
            )
            if enable_domain_moderation is None
            else enable_domain_moderation
        )

    def moderate(
        self,
        text: str,
        *,
        safety_identifier: str | None,
    ) -> ModerationDecision:
        local = self.local_policy.evaluate(text)
        if not local.allowed:
            return local

        provider = self.gateway.moderate_text(text)
        if provider.flagged:
            return ModerationDecision(
                allowed=False,
                category="openai_safety",
                reason="Запрос заблокирован политикой безопасности.",
                risk_level="critical",
                requires_professional=True,
            )

        if not self.enable_domain_moderation:
            return local

        try:
            result = self.gateway.generate_structured(
                system_prompt=MODERATION_SYSTEM_PROMPT,
                user_prompt=build_moderation_prompt(text),
                response_model=DomainModerationOutput,
                reasoning_effort=str(
                    getattr(
                        settings,
                        "OPENAI_MODERATION_REASONING_EFFORT",
                        "low",
                    )
                ),
                max_output_tokens=int(
                    getattr(
                        settings,
                        "OPENAI_MODERATION_MAX_OUTPUT_TOKENS",
                        700,
                    )
                ),
                safety_identifier=safety_identifier,
                verbosity="low",
            )
        except AIContentBlocked as exc:
            return ModerationDecision(
                allowed=False,
                category="openai_safety",
                reason=str(exc),
                risk_level="critical",
                requires_professional=True,
            )
        parsed = result.parsed

        return ModerationDecision(
            allowed=parsed.allowed,
            category=parsed.category,
            reason=parsed.reason.strip() or local.reason,
            risk_level=parsed.risk_level,
            requires_professional=(
                parsed.requires_professional
                or local.requires_professional
            ),
            tokens_used=result.tokens_used,
        )


class AIQuotaService:
    """Проверяет роли, активную подписку и лимит AI-запросов."""

    def check(self, user: Any, *, feature: str) -> UserSubscription | None:
        if not getattr(user, "is_authenticated", False):
            raise AIAccessDenied("Для AI-функций необходимо войти в аккаунт.")
        if not getattr(user, "is_active", False):
            raise AIAccessDenied("Аккаунт пользователя неактивен.")

        if bool(getattr(user, "has_paid_access", False)):
            return None

        now = timezone.now()
        subscription = (
            UserSubscription.objects.select_related("plan")
            .filter(
                user=user,
                is_active=True,
                start_date__lte=now,
                end_date__gt=now,
            )
            .order_by("-end_date")
            .first()
        )
        if subscription is None:
            raise AIAccessDenied(
                "Для этой AI-функции требуется активная подписка."
            )

        if feature == "chat" and not subscription.plan.has_chat_access:
            raise AIAccessDenied(
                "Текущий тариф не включает доступ к AI-чату."
            )
        if (
            feature == "image_analysis"
            and not subscription.plan.has_image_analysis
        ):
            raise AIAccessDenied(
                "Текущий тариф не включает анализ изображений."
            )

        maximum = int(subscription.plan.max_ai_requests)
        zero_is_unlimited = bool(
            getattr(settings, "AI_ZERO_QUOTA_IS_UNLIMITED", False)
        )
        if maximum == 0 and not zero_is_unlimited:
            raise AIQuotaExceeded(
                "На текущем тарифе не предусмотрены AI-запросы."
            )

        if maximum > 0:
            used = (
                AIRequest.objects.filter(
                    user=user,
                    created_at__gte=subscription.start_date,
                    created_at__lt=subscription.end_date,
                )
                .exclude(request_type__endswith="_blocked")
                .count()
            )
            if used >= maximum:
                raise AIQuotaExceeded(
                    "Лимит AI-запросов по подписке исчерпан."
                )

        return subscription


class ProjectContextBuilder:
    """Собирает компактный и проверяемый контекст моделей проекта."""

    MAX_EXISTING_INSTRUCTIONS = 3
    MAX_STEPS_PER_INSTRUCTION = 24
    MAX_COMPATIBILITIES = 60
    MAX_TEXT_LENGTH = 6_000

    def build(
        self,
        *,
        user: Any,
        part: Part | int | None = None,
        linked_instruction: Instruction | None = None,
    ) -> dict[str, Any]:
        resolved_part = self._load_part(part) if part is not None else None

        context: dict[str, Any] = {
            "source_policy": {
                "database_is_authoritative": True,
                "missing_exact_values_must_not_be_invented": True,
                "compatibility_requires_vin_confirmation": True,
            },
            "user_vehicle": self._user_vehicle(user),
            "part": None,
            "recent_repairs_for_part": [],
        }

        if resolved_part is None:
            return context

        context["part"] = self._serialize_part(resolved_part)
        context["recent_repairs_for_part"] = self._repair_history(
            user,
            resolved_part,
        )

        if linked_instruction is not None:
            if linked_instruction.part_id != resolved_part.pk:
                raise ValueError(
                    "Связанная инструкция относится к другой запчасти."
                )
            context["linked_instruction"] = self._serialize_instruction(
                self._load_instruction(linked_instruction.pk)
            )

        return context

    def _load_part(self, part: Part | int) -> Part:
        part_id = part.pk if isinstance(part, Part) else part
        instruction_queryset = (
            Instruction.objects.select_related("part")
            .prefetch_related(
                "steps",
                Prefetch(
                    "instruction_tools",
                    queryset=InstructionTool.objects.select_related(
                        "tool__category"
                    ),
                ),
            )
            .order_by("-updated_at")
        )
        return (
            Part.objects.select_related("category")
            .prefetch_related(
                "oem_numbers",
                "compatibilities",
                Prefetch(
                    "part_tools",
                    queryset=PartTool.objects.select_related(
                        "tool__category"
                    ),
                ),
                Prefetch("instructions", queryset=instruction_queryset),
            )
            .get(pk=part_id, is_active=True)
        )

    @staticmethod
    def _load_instruction(instruction_id: int) -> Instruction:
        return (
            Instruction.objects.select_related("part")
            .prefetch_related(
                "steps",
                Prefetch(
                    "instruction_tools",
                    queryset=InstructionTool.objects.select_related(
                        "tool__category"
                    ),
                ),
            )
            .get(pk=instruction_id)
        )

    def _serialize_part(self, part: Part) -> dict[str, Any]:
        compatibilities = [
            {
                "brand": item.brand,
                "model": item.model,
                "generation": item.generation,
                "engine": item.engine,
                "year_from": item.year_from,
                "year_to": item.year_to,
            }
            for item in list(part.compatibilities.all())[
                : self.MAX_COMPATIBILITIES
            ]
        ]
        tools = [
            {
                "name": relation.tool.name,
                "category": (
                    relation.tool.category.name
                    if relation.tool.category_id
                    else ""
                ),
                "size": relation.tool.size,
                "description": self._trim(relation.tool.description, 900),
                "required": relation.required,
            }
            for relation in part.part_tools.all()
        ]
        instructions = [
            self._serialize_instruction(instruction)
            for instruction in list(part.instructions.all())[
                : self.MAX_EXISTING_INSTRUCTIONS
            ]
        ]

        return {
            "id": part.pk,
            "name": part.name,
            "category": part.category.name if part.category_id else "",
            "original_number": part.original_number,
            "manufacturer": part.manufacturer,
            "description": self._trim(part.description),
            "weight": str(part.weight) if part.weight is not None else None,
            "dimensions": part.dimensions,
            "oem_numbers": [
                {
                    "number": oem.number,
                    "manufacturer": oem.manufacturer,
                }
                for oem in part.oem_numbers.all()
            ],
            "compatibilities": compatibilities,
            "compatibilities_truncated": (
                part.compatibilities.count() > len(compatibilities)
            ),
            "required_tools": tools,
            "existing_instructions": instructions,
        }

    def _serialize_instruction(
        self,
        instruction: Instruction,
    ) -> dict[str, Any]:
        return {
            "id": instruction.pk,
            "title": instruction.title,
            "short_description": self._trim(
                instruction.short_description,
                1_500,
            ),
            "content": self._trim(instruction.content),
            "difficulty": instruction.difficulty,
            "estimated_time_minutes": instruction.estimated_time,
            "version": instruction.version,
            "steps": [
                {
                    "number": step.step_number,
                    "title": step.title,
                    "description": self._trim(step.description, 2_000),
                    "warning": self._trim(step.warning, 1_000),
                    "estimated_minutes": step.estimated_minutes,
                }
                for step in list(instruction.steps.all())[
                    : self.MAX_STEPS_PER_INSTRUCTION
                ]
            ],
            "tools": [
                {
                    "name": relation.tool.name,
                    "size": relation.tool.size,
                    "usage": self._trim(
                        relation.usage_description,
                        1_000,
                    ),
                }
                for relation in instruction.instruction_tools.all()
            ],
        }

    @staticmethod
    def _user_vehicle(user: Any) -> dict[str, Any] | None:
        try:
            profile = user.profile
        except ObjectDoesNotExist:
            return None

        return {
            "brand": profile.car_brand,
            "model": profile.car_model,
            "year": profile.car_year,
            "preferred_language": profile.preferred_language,
            "country": profile.country,
        }

    @staticmethod
    def _repair_history(user: Any, part: Part) -> list[dict[str, Any]]:
        try:
            from users.models import RepairHistory
        except ImportError:
            return []

        return [
            {
                "instruction": item.instruction.title,
                "completed": item.completed,
                "notes": ProjectContextBuilder._trim(item.notes, 1_000),
                "created_at": item.created_at.isoformat(),
            }
            for item in RepairHistory.objects.select_related(
                "instruction"
            ).filter(
                user=user,
                instruction__part=part,
            )[:5]
        ]

    @staticmethod
    def _trim(value: str, limit: int | None = None) -> str:
        text = (value or "").strip()
        resolved_limit = limit or ProjectContextBuilder.MAX_TEXT_LENGTH
        if len(text) <= resolved_limit:
            return text
        return f"{text[:resolved_limit].rstrip()}…"


class ImageInputValidator:
    """Проверяет файл до отправки изображения внешнему API."""

    _FORMAT_MAP = {
        "JPEG": ("image/jpeg", "jpg"),
        "PNG": ("image/png", "png"),
        "WEBP": ("image/webp", "webp"),
        "GIF": ("image/gif", "gif"),
    }

    def validate(self, image: Any) -> ValidatedImage:
        if image is None or not hasattr(image, "read"):
            raise AIImageValidationError("Изображение не передано.")

        max_bytes = int(
            getattr(settings, "AI_IMAGE_MAX_BYTES", 10 * 1024 * 1024)
        )
        if int(getattr(image, "size", 0) or 0) > max_bytes:
            raise AIImageValidationError(
                f"Размер изображения превышает {max_bytes // 1024 // 1024} МБ."
            )

        try:
            image.seek(0)
        except (AttributeError, OSError):
            pass

        content = image.read(max_bytes + 1)
        if not isinstance(content, bytes) or not content:
            raise AIImageValidationError(
                "Не удалось прочитать изображение."
            )
        if len(content) > max_bytes:
            raise AIImageValidationError(
                f"Размер изображения превышает {max_bytes // 1024 // 1024} МБ."
            )

        try:
            with warnings.catch_warnings():
                warnings.simplefilter(
                    "error",
                    Image.DecompressionBombWarning,
                )
                with Image.open(BytesIO(content)) as opened:
                    format_name = (opened.format or "").upper()
                    width, height = opened.size
                    is_animated = bool(
                        getattr(opened, "is_animated", False)
                    )
                    opened.verify()
        except (
            Image.DecompressionBombError,
            Image.DecompressionBombWarning,
            UnidentifiedImageError,
            OSError,
            ValueError,
        ) as exc:
            raise AIImageValidationError(
                "Файл повреждён или не является поддерживаемым изображением."
            ) from exc

        if format_name not in self._FORMAT_MAP:
            raise AIImageValidationError(
                "Поддерживаются только JPEG, PNG, WEBP и статический GIF."
            )
        if format_name == "GIF" and is_animated:
            raise AIImageValidationError(
                "Анимированный GIF не поддерживается."
            )

        min_side = int(getattr(settings, "AI_IMAGE_MIN_SIDE", 64))
        if width < min_side or height < min_side:
            raise AIImageValidationError(
                f"Минимальный размер изображения — {min_side}×{min_side}."
            )

        max_pixels = int(
            getattr(settings, "AI_IMAGE_MAX_PIXELS", 40_000_000)
        )
        if width * height > max_pixels:
            raise AIImageValidationError(
                "Разрешение изображения превышает безопасный лимит."
            )

        mime_type, extension = self._FORMAT_MAP[format_name]
        original_name = os.path.basename(
            str(getattr(image, "name", "part"))
        )
        stem = get_valid_filename(os.path.splitext(original_name)[0])[:80]
        filename = f"{stem or 'part'}.{extension}"
        encoded = base64.b64encode(content).decode("ascii")

        return ValidatedImage(
            content=content,
            data_url=f"data:{mime_type};base64,{encoded}",
            filename=filename,
            mime_type=mime_type,
            width=width,
            height=height,
            format_name=format_name,
        )


class ImageCatalogBuilder:
    """Готовит ограниченный каталог и проверяет выбранный моделью ID."""

    @staticmethod
    def _normalize_oem(value: str) -> str:
        return re.sub(r"[^A-Z0-9]", "", (value or "").upper())

    def build(self) -> ImageCatalogContext:
        configured_limit = int(
            getattr(settings, "AI_IMAGE_CATALOG_LIMIT", 250)
        )
        limit = min(max(configured_limit, 1), 2_000)
        queryset = (
            Part.objects.filter(is_active=True)
            .select_related("category")
            .prefetch_related("oem_numbers", "compatibilities")
            .order_by("id")
        )
        total = queryset.count()
        parts = list(queryset[:limit])
        parts_by_id = {part.pk: part for part in parts}
        oem_index: dict[str, int] = {}
        entries: list[dict[str, Any]] = []

        for part in parts:
            numbers = [part.original_number]
            numbers.extend(oem.number for oem in part.oem_numbers.all())
            for number in numbers:
                normalized = self._normalize_oem(number)
                if normalized:
                    oem_index[normalized] = part.pk

            entries.append(
                {
                    "id": part.pk,
                    "name": part.name,
                    "category": (
                        part.category.name if part.category_id else ""
                    ),
                    "manufacturer": part.manufacturer,
                    "original_number": part.original_number,
                    "oem_numbers": [
                        {
                            "number": oem.number,
                            "manufacturer": oem.manufacturer,
                        }
                        for oem in part.oem_numbers.all()
                    ],
                    "compatibilities": [
                        {
                            "brand": item.brand,
                            "model": item.model,
                            "generation": item.generation,
                            "engine": item.engine,
                            "year_from": item.year_from,
                            "year_to": item.year_to,
                        }
                        for item in list(part.compatibilities.all())[:12]
                    ],
                }
            )

        return ImageCatalogContext(
            payload={
                "parts": entries,
                "total_active_parts": total,
                "catalog_truncated": total > len(entries),
                "matching_rule": (
                    "matched_part_id должен быть ID из этого списка; "
                    "если данных недостаточно, вернуть 0."
                ),
            },
            parts_by_id=parts_by_id,
            oem_index=oem_index,
        )

    def resolve_detected_part(
        self,
        *,
        output: PartImageAnalysisOutput,
        catalog: ImageCatalogContext,
    ) -> Part | None:
        if not output.is_automotive_part:
            return None

        threshold = float(
            getattr(settings, "AI_IMAGE_MIN_MATCH_CONFIDENCE", 65)
        )
        if output.confidence_score < threshold:
            return None

        for visible_number in output.visible_oem_numbers:
            part_id = catalog.oem_index.get(
                self._normalize_oem(visible_number)
            )
            if part_id is not None:
                return catalog.parts_by_id.get(part_id)

        return catalog.parts_by_id.get(output.matched_part_id)


class SmartAutoPartsAIService:
    """Публичный фасад AI-функций проекта."""

    def __init__(
        self,
        *,
        gateway: AIGateway | None = None,
        enforce_access: bool = True,
        enable_domain_moderation: bool | None = None,
    ) -> None:
        self.gateway = gateway or OpenAIGateway()
        self.enforce_access = enforce_access
        self.quota = AIQuotaService()
        self.moderation = RequestModerationService(
            self.gateway,
            enable_domain_moderation=enable_domain_moderation,
        )
        self.context_builder = ProjectContextBuilder()
        self.image_validator = ImageInputValidator()
        self.image_catalog = ImageCatalogBuilder()

    def moderate_request(
        self,
        *,
        user: Any,
        text: str,
    ) -> ModerationDecision:
        """Публичная проверка запроса без генерации ответа."""

        return self.moderation.moderate(
            text,
            safety_identifier=self._safety_identifier(user),
        )

    def answer_chat(
        self,
        *,
        user: Any,
        message: str,
        part: Part | int | None = None,
        room: ChatRoom | int | None = None,
        history_limit: int = 12,
    ) -> ChatServiceResult:
        """Модерирует запрос, отвечает в чате и сохраняет ``AIRequest``."""

        if self.enforce_access:
            self.quota.check(user, feature="chat")

        safety_identifier = self._safety_identifier(user)
        decision = self.moderation.moderate(
            message,
            safety_identifier=safety_identifier,
        )
        if not decision.allowed:
            ai_request = self._save_blocked_request(
                user=user,
                part=part,
                prompt=message,
                request_type="chat_blocked",
                decision=decision,
            )
            raise AIRequestRejected(
                decision.reason,
                decision=decision,
                ai_request=ai_request,
            )

        project_context = self.context_builder.build(
            user=user,
            part=part,
        )
        history = self._chat_history(
            user=user,
            room=room,
            limit=history_limit,
        )

        try:
            provider = self.gateway.generate_text(
                system_prompt=CHAT_SYSTEM_PROMPT,
                user_prompt=build_chat_prompt(
                    user_text=message,
                    project_context=project_context,
                    history=history,
                ),
                reasoning_effort=str(
                    getattr(settings, "OPENAI_CHAT_REASONING_EFFORT", "low")
                ),
                max_output_tokens=int(
                    getattr(settings, "OPENAI_CHAT_MAX_OUTPUT_TOKENS", 2_500)
                ),
                safety_identifier=safety_identifier,
                verbosity=str(
                    getattr(settings, "OPENAI_CHAT_VERBOSITY", "medium")
                ),
            )
        except AIContentBlocked as exc:
            blocked = ModerationDecision(
                allowed=False,
                category="openai_generation_safety",
                reason=str(exc),
                risk_level="critical",
                requires_professional=True,
                tokens_used=decision.tokens_used,
            )
            ai_request = self._save_blocked_request(
                user=user,
                part=part,
                prompt=message,
                request_type="chat_blocked",
                decision=blocked,
            )
            raise AIRequestRejected(
                str(exc),
                decision=blocked,
                ai_request=ai_request,
            ) from exc

        ai_request = AIRequest.objects.create(
            user=user,
            part=self._part_instance(part),
            prompt=message.strip(),
            response=provider.text,
            tokens_used=decision.tokens_used + provider.tokens_used,
            request_type="chat",
        )
        return ChatServiceResult(
            ai_request=ai_request,
            answer=provider.text,
            moderation=decision,
        )

    def analyze_part_image(
        self,
        *,
        user: Any,
        image: Any,
        note: str = "",
    ) -> ImageAnalysisServiceResult:
        """
        Проверяет тариф и изображение, распознаёт деталь и сохраняет результат.

        Фотография проходит локальную валидацию, текстовую модерацию и
        мультимодальную модерацию OpenAI до визуального анализа.
        """

        if self.enforce_access:
            self.quota.check(user, feature="image_analysis")

        validated = self.image_validator.validate(image)
        prompt_text = (
            note.strip()
            or "Определи автомобильную запчасть на фотографии."
        )
        safety_identifier = self._safety_identifier(user)
        decision = self.moderation.moderate(
            prompt_text,
            safety_identifier=safety_identifier,
        )
        if not decision.allowed:
            ai_request = self._save_blocked_request(
                user=user,
                part=None,
                prompt=prompt_text,
                request_type="image_analysis_blocked",
                decision=decision,
            )
            raise AIRequestRejected(
                decision.reason,
                decision=decision,
                ai_request=ai_request,
            )

        image_moderation = self.gateway.moderate_multimodal(
            text=prompt_text,
            image_data_url=validated.data_url,
        )
        if image_moderation.flagged:
            blocked = ModerationDecision(
                allowed=False,
                category="openai_image_safety",
                reason="Изображение заблокировано политикой безопасности.",
                risk_level="critical",
                requires_professional=False,
                tokens_used=decision.tokens_used,
            )
            ai_request = self._save_blocked_request(
                user=user,
                part=None,
                prompt=prompt_text,
                request_type="image_analysis_blocked",
                decision=blocked,
            )
            raise AIRequestRejected(
                blocked.reason,
                decision=blocked,
                ai_request=ai_request,
            )

        catalog = self.image_catalog.build()
        image_detail = str(
            getattr(settings, "OPENAI_IMAGE_DETAIL", "high")
        )
        if image_detail not in {"low", "high", "original", "auto"}:
            raise AIConfigurationError(
                "OPENAI_IMAGE_DETAIL должен быть low, high, original или auto."
            )

        try:
            provider = self.gateway.generate_structured_image(
                system_prompt=IMAGE_ANALYSIS_SYSTEM_PROMPT,
                user_prompt=build_image_analysis_prompt(
                    user_note=note.strip(),
                    catalog_context=catalog.payload,
                    user_vehicle=ProjectContextBuilder._user_vehicle(user),
                ),
                image_data_url=validated.data_url,
                image_detail=image_detail,
                response_model=PartImageAnalysisOutput,
                reasoning_effort=str(
                    getattr(
                        settings,
                        "OPENAI_IMAGE_REASONING_EFFORT",
                        "low",
                    )
                ),
                max_output_tokens=int(
                    getattr(
                        settings,
                        "OPENAI_IMAGE_MAX_OUTPUT_TOKENS",
                        2_500,
                    )
                ),
                safety_identifier=safety_identifier,
                verbosity=str(
                    getattr(settings, "OPENAI_IMAGE_VERBOSITY", "medium")
                ),
            )
        except AIContentBlocked as exc:
            blocked = ModerationDecision(
                allowed=False,
                category="openai_generation_safety",
                reason=str(exc),
                risk_level="critical",
                requires_professional=False,
                tokens_used=decision.tokens_used,
            )
            ai_request = self._save_blocked_request(
                user=user,
                part=None,
                prompt=prompt_text,
                request_type="image_analysis_blocked",
                decision=blocked,
            )
            raise AIRequestRejected(
                str(exc),
                decision=blocked,
                ai_request=ai_request,
            ) from exc

        claimed_part_id = provider.parsed.matched_part_id
        output = self._normalise_image_analysis(
            provider.parsed,
            catalog=catalog,
        )
        detected_part = self.image_catalog.resolve_detected_part(
            output=output,
            catalog=catalog,
        )
        output.matched_part_id = (
            detected_part.pk if detected_part is not None else 0
        )
        response_text = self._render_image_analysis(
            output,
            detected_part=detected_part,
        )
        confidence = Decimal(
            str(round(output.confidence_score, 2))
        ).quantize(Decimal("0.01"))

        with transaction.atomic():
            ai_request = AIRequest.objects.create(
                user=user,
                part=detected_part,
                prompt=prompt_text,
                response=response_text,
                tokens_used=decision.tokens_used + provider.tokens_used,
                request_type="image_analysis",
            )
            payload = {
                "model_output": output.model_dump(mode="json"),
                "model_claimed_part_id": claimed_part_id,
                "verified_detected_part_id": (
                    detected_part.pk if detected_part is not None else None
                ),
                "image": {
                    "filename": validated.filename,
                    "mime_type": validated.mime_type,
                    "format": validated.format_name,
                    "width": validated.width,
                    "height": validated.height,
                    "size_bytes": len(validated.content),
                },
                "moderation_categories": list(
                    image_moderation.categories
                ),
                "catalog_truncated": bool(
                    catalog.payload["catalog_truncated"]
                ),
                "ai_request_id": ai_request.pk,
                "model": getattr(
                    self.gateway,
                    "model",
                    "gpt-5.6-sol",
                ),
            }
            analysis = AIImageAnalysis.objects.create(
                user=user,
                image=ContentFile(
                    validated.content,
                    name=validated.filename,
                ),
                detected_part=detected_part,
                confidence_score=confidence,
                analysis_result=payload,
            )

        return ImageAnalysisServiceResult(
            ai_request=ai_request,
            image_analysis=analysis,
            payload=payload,
            detected_part=detected_part,
            moderation=decision,
        )

    def generate_repair_instruction(
        self,
        *,
        user: Any,
        part: Part | int,
        goal: str,
        instruction: Instruction | None = None,
    ) -> InstructionServiceResult:
        """
        Возвращает сохранённую или генерирует новую ремонтную инструкцию.

        Пока опубликованная инструкция моложе
        ``AI_INSTRUCTION_CACHE_TTL_DAYS``, пользователю возвращается её
        содержимое без повторной генерации. При этом создаётся новый
        ``AIRequest``, поэтому запрос учитывается в лимите тарифа.

        После истечения TTL предыдущая опубликованная версия архивируется в
        ``InstructionVersion``, а новая AI-версия сохраняется со статусом
        ``pending``. Публичная ``Instruction`` меняется только после решения
        модератора через ``approve_generated_instruction``.
        """

        if self.enforce_access:
            self.quota.check(user, feature="instruction")

        resolved_part = self._part_instance(part)
        resolved_instruction = self._resolve_saved_instruction(
            part=resolved_part,
            instruction=instruction,
            goal=goal,
        )
        safety_identifier = self._safety_identifier(user)
        decision = self.moderation.moderate(
            goal,
            safety_identifier=safety_identifier,
        )
        if not decision.allowed:
            ai_request = self._save_blocked_request(
                user=user,
                part=resolved_part,
                prompt=goal,
                request_type="repair_instruction_blocked",
                decision=decision,
            )
            raise AIRequestRejected(
                decision.reason,
                decision=decision,
                ai_request=ai_request,
            )

        if (
            resolved_instruction is not None
            and self._instruction_is_fresh(resolved_instruction)
        ):
            return self._return_cached_instruction(
                user=user,
                part=resolved_part,
                goal=goal,
                instruction=resolved_instruction,
                decision=decision,
            )

        source_version = (
            resolved_instruction.version
            if resolved_instruction is not None
            else None
        )
        project_context = self.context_builder.build(
            user=user,
            part=resolved_part,
            linked_instruction=resolved_instruction,
        )

        try:
            provider = self.gateway.generate_structured(
                system_prompt=INSTRUCTION_SYSTEM_PROMPT,
                user_prompt=build_instruction_prompt(
                    goal=goal,
                    project_context=project_context,
                ),
                response_model=RepairInstructionOutput,
                reasoning_effort=str(
                    getattr(
                        settings,
                        "OPENAI_INSTRUCTION_REASONING_EFFORT",
                        "medium",
                    )
                ),
                max_output_tokens=int(
                    getattr(
                        settings,
                        "OPENAI_INSTRUCTION_MAX_OUTPUT_TOKENS",
                        12_000,
                    )
                ),
                safety_identifier=safety_identifier,
                verbosity=str(
                    getattr(
                        settings,
                        "OPENAI_INSTRUCTION_VERBOSITY",
                        "high",
                    )
                ),
            )
        except AIContentBlocked as exc:
            blocked = ModerationDecision(
                allowed=False,
                category="openai_generation_safety",
                reason=str(exc),
                risk_level="critical",
                requires_professional=True,
                tokens_used=decision.tokens_used,
            )
            ai_request = self._save_blocked_request(
                user=user,
                part=resolved_part,
                prompt=goal,
                request_type="repair_instruction_blocked",
                decision=blocked,
            )
            raise AIRequestRejected(
                str(exc),
                decision=blocked,
                ai_request=ai_request,
            ) from exc

        output = self._normalise_instruction(
            provider.parsed,
            decision=decision,
        )
        payload = output.model_dump(mode="json")
        markdown = self._render_instruction(output)

        with transaction.atomic():
            locked_instruction = None
            proposed_version = 1

            if resolved_instruction is not None:
                locked_instruction = Instruction.objects.select_for_update().get(
                    pk=resolved_instruction.pk,
                )
                if locked_instruction.version != source_version:
                    raise AIServiceError(
                        "Инструкция была изменена во время генерации. "
                        "Повторите запрос, чтобы использовать актуальную версию."
                    )

                proposed_version = locked_instruction.version + 1
                InstructionVersion.objects.get_or_create(
                    instruction=locked_instruction,
                    version_number=locked_instruction.version,
                    defaults={
                        "content": locked_instruction.content,
                        "changelog": (
                            "Архив опубликованной версии перед "
                            f"AI-обновлением до v{proposed_version}."
                        ),
                    },
                )

            ai_request = AIRequest.objects.create(
                user=user,
                part=resolved_part,
                prompt=goal.strip(),
                response=markdown,
                tokens_used=decision.tokens_used + provider.tokens_used,
                request_type="repair_instruction_moderation_pending",
            )
            generated = AIGeneratedInstruction.objects.create(
                ai_request=ai_request,
                instruction=locked_instruction,
                generated_content=markdown,
                version_number=proposed_version,
                is_cached=False,
                moderation_status=(
                    AIGeneratedInstruction.ModerationStatus.PENDING
                ),
            )

        payload["cache"] = {
            "hit": False,
            "ttl_days": self._instruction_ttl_days(),
        }
        payload["revision"] = {
            "published_instruction_id": (
                resolved_instruction.pk
                if resolved_instruction is not None
                else None
            ),
            "source_version": source_version,
            "proposed_version": proposed_version,
            "moderation_status": (
                AIGeneratedInstruction.ModerationStatus.PENDING
            ),
        }

        return InstructionServiceResult(
            ai_request=ai_request,
            generated_instruction=generated,
            payload=payload,
            moderation=decision,
            cached=False,
            requires_moderation=True,
        )

    def approve_generated_instruction(
        self,
        *,
        moderator: Any,
        generated_instruction: AIGeneratedInstruction | int,
        moderation_note: str = "",
    ) -> AIGeneratedInstruction:
        """
        Публикует проверенную AI-версию и увеличивает ``Instruction.version``.

        Метод разрешён только модератору, администратору или суперпользователю.
        Обновление выполняется под блокировкой строк, чтобы два модератора не
        смогли одновременно опубликовать разные версии с одним номером.
        """

        self._assert_can_moderate(moderator)
        generated_id = (
            generated_instruction.pk
            if isinstance(generated_instruction, AIGeneratedInstruction)
            else generated_instruction
        )

        with transaction.atomic():
            generated = (
                AIGeneratedInstruction.objects.select_for_update()
                .select_related("instruction")
                .get(pk=generated_id)
            )
            if generated.is_cached:
                raise AIServiceError(
                    "Кэшированная выдача уже содержит опубликованную версию."
                )
            if (
                generated.moderation_status
                != AIGeneratedInstruction.ModerationStatus.PENDING
            ):
                raise AIServiceError(
                    "Решение по этой AI-инструкции уже принято."
                )
            if generated.instruction_id is None:
                raise AIServiceError(
                    "Для публикации новой инструкции сначала свяжите "
                    "AI-черновик с объектом Instruction."
                )

            instruction = Instruction.objects.select_for_update().get(
                pk=generated.instruction_id,
            )
            expected_version = instruction.version + 1
            if generated.version_number != expected_version:
                raise AIServiceError(
                    "Опубликованная инструкция уже изменилась. "
                    "AI-версию необходимо пересоздать на актуальной основе."
                )

            InstructionVersion.objects.get_or_create(
                instruction=instruction,
                version_number=instruction.version,
                defaults={
                    "content": instruction.content,
                    "changelog": (
                        "Архив опубликованной версии перед "
                        f"публикацией AI-редакции v{generated.version_number}."
                    ),
                },
            )
            instruction.content = generated.generated_content
            instruction.version = generated.version_number
            instruction.save(
                update_fields=(
                    "content",
                    "version",
                    "updated_at",
                )
            )

            generated.moderation_status = (
                AIGeneratedInstruction.ModerationStatus.APPROVED
            )
            generated.moderation_note = moderation_note.strip()
            generated.reviewed_by = moderator
            generated.reviewed_at = timezone.now()
            generated.save(
                update_fields=(
                    "moderation_status",
                    "moderation_note",
                    "reviewed_by",
                    "reviewed_at",
                )
            )

        return generated

    def reject_generated_instruction(
        self,
        *,
        moderator: Any,
        generated_instruction: AIGeneratedInstruction | int,
        moderation_note: str,
    ) -> AIGeneratedInstruction:
        """Отклоняет AI-версию, не меняя опубликованную инструкцию."""

        self._assert_can_moderate(moderator)
        note = moderation_note.strip()
        if not note:
            raise ValueError("Укажите причину отклонения AI-инструкции.")

        generated_id = (
            generated_instruction.pk
            if isinstance(generated_instruction, AIGeneratedInstruction)
            else generated_instruction
        )
        with transaction.atomic():
            generated = AIGeneratedInstruction.objects.select_for_update().get(
                pk=generated_id,
            )
            if (
                generated.moderation_status
                != AIGeneratedInstruction.ModerationStatus.PENDING
            ):
                raise AIServiceError(
                    "Решение по этой AI-инструкции уже принято."
                )

            generated.moderation_status = (
                AIGeneratedInstruction.ModerationStatus.REJECTED
            )
            generated.moderation_note = note
            generated.reviewed_by = moderator
            generated.reviewed_at = timezone.now()
            generated.save(
                update_fields=(
                    "moderation_status",
                    "moderation_note",
                    "reviewed_by",
                    "reviewed_at",
                )
            )

        return generated

    def _resolve_saved_instruction(
        self,
        *,
        part: Part,
        instruction: Instruction | None,
        goal: str,
    ) -> Instruction | None:
        """
        Находит опубликованную инструкцию для повторного запроса.

        Явно переданная инструкция имеет приоритет. Без неё используется
        инструкция из ранее одобренного идентичного запроса. Если такой
        связи нет, единственная инструкция детали выбирается автоматически;
        при нескольких вариантах вызывающая сторона должна передать нужную.
        """

        if instruction is not None:
            resolved = Instruction.objects.get(pk=instruction.pk)
            if resolved.part_id != part.pk:
                raise ValueError(
                    "Связанная инструкция относится к другой запчасти."
                )
            return resolved

        previous = (
            AIGeneratedInstruction.objects.select_related("instruction")
            .filter(
                ai_request__part=part,
                ai_request__prompt__iexact=goal.strip(),
                instruction__isnull=False,
                moderation_status=(
                    AIGeneratedInstruction.ModerationStatus.APPROVED
                ),
            )
            .order_by("-created_at")
            .first()
        )
        if previous is not None:
            return previous.instruction

        candidates = list(
            Instruction.objects.filter(part=part)
            .order_by("-updated_at")[:2]
        )
        return candidates[0] if len(candidates) == 1 else None

    def _instruction_is_fresh(self, instruction: Instruction) -> bool:
        return timezone.now() < self._instruction_refresh_due_at(instruction)

    def _instruction_refresh_due_at(
        self,
        instruction: Instruction,
    ) -> Any:
        last_refresh = instruction.updated_at
        latest_generated = (
            AIGeneratedInstruction.objects.filter(
                instruction=instruction,
                is_cached=False,
                moderation_status__in=(
                    AIGeneratedInstruction.ModerationStatus.PENDING,
                    AIGeneratedInstruction.ModerationStatus.APPROVED,
                ),
            )
            .order_by("-created_at")
            .only("created_at")
            .first()
        )
        if (
            latest_generated is not None
            and latest_generated.created_at > last_refresh
        ):
            last_refresh = latest_generated.created_at

        return last_refresh + timedelta(days=self._instruction_ttl_days())

    @staticmethod
    def _instruction_ttl_days() -> int:
        return max(
            0,
            int(getattr(settings, "AI_INSTRUCTION_CACHE_TTL_DAYS", 365)),
        )

    def _return_cached_instruction(
        self,
        *,
        user: Any,
        part: Part,
        goal: str,
        instruction: Instruction,
        decision: ModerationDecision,
    ) -> InstructionServiceResult:
        """Сохраняет оплачиваемую выдачу опубликованной инструкции из БД."""

        loaded_instruction = self.context_builder._load_instruction(
            instruction.pk
        )
        serialized = self.context_builder._serialize_instruction(
            loaded_instruction
        )
        refresh_due_at = self._instruction_refresh_due_at(
            loaded_instruction
        )
        payload = {
            "source": "database",
            "cached": True,
            "instruction": serialized,
            "refresh_due_at": refresh_due_at.isoformat(),
            "ttl_days": self._instruction_ttl_days(),
            "moderation_status": (
                AIGeneratedInstruction.ModerationStatus.APPROVED
            ),
        }

        with transaction.atomic():
            ai_request = AIRequest.objects.create(
                user=user,
                part=part,
                prompt=goal.strip(),
                response=loaded_instruction.content,
                tokens_used=decision.tokens_used,
                request_type="repair_instruction_cached",
            )
            generated = AIGeneratedInstruction.objects.create(
                ai_request=ai_request,
                instruction=loaded_instruction,
                generated_content=loaded_instruction.content,
                version_number=loaded_instruction.version,
                is_cached=True,
                moderation_status=(
                    AIGeneratedInstruction.ModerationStatus.APPROVED
                ),
            )

        return InstructionServiceResult(
            ai_request=ai_request,
            generated_instruction=generated,
            payload=payload,
            moderation=decision,
            cached=True,
            requires_moderation=False,
        )

    @staticmethod
    def _assert_can_moderate(user: Any) -> None:
        if not getattr(user, "is_authenticated", False):
            raise AIAccessDenied("Для модерации необходимо войти в аккаунт.")
        if not (
            bool(getattr(user, "can_moderate", False))
            or bool(getattr(user, "can_administrate", False))
            or bool(getattr(user, "is_superuser", False))
        ):
            raise AIAccessDenied(
                "Публиковать AI-версии может только модератор."
            )

    @staticmethod
    def _normalise_image_analysis(
        output: PartImageAnalysisOutput,
        *,
        catalog: ImageCatalogContext,
    ) -> PartImageAnalysisOutput:
        confidence = float(output.confidence_score)
        if not math.isfinite(confidence):
            confidence = 0.0
        output.confidence_score = min(max(confidence, 0.0), 100.0)

        output.part_name = ProjectContextBuilder._trim(
            output.part_name,
            255,
        )
        output.part_category = ProjectContextBuilder._trim(
            output.part_category,
            255,
        )
        output.manufacturer = ProjectContextBuilder._trim(
            output.manufacturer,
            255,
        )
        output.description = ProjectContextBuilder._trim(
            output.description,
            3_000,
        )
        output.match_basis = ProjectContextBuilder._trim(
            output.match_basis,
            1_500,
        )

        list_fields = (
            "visible_oem_numbers",
            "visible_markings",
            "observed_damage",
            "safety_notes",
            "limitations",
        )
        for field_name in list_fields:
            values = getattr(output, field_name)
            cleaned = [
                ProjectContextBuilder._trim(str(value), 500)
                for value in values[:30]
                if str(value).strip()
            ]
            setattr(output, field_name, cleaned)

        if (
            not output.is_automotive_part
            or output.matched_part_id not in catalog.parts_by_id
        ):
            output.matched_part_id = 0

        valid_alternatives: list[int] = []
        for part_id in output.alternative_part_ids:
            if (
                part_id in catalog.parts_by_id
                and part_id != output.matched_part_id
                and part_id not in valid_alternatives
            ):
                valid_alternatives.append(part_id)
        output.alternative_part_ids = valid_alternatives[:5]
        return output

    @staticmethod
    def _render_image_analysis(
        output: PartImageAnalysisOutput,
        *,
        detected_part: Part | None,
    ) -> str:
        if not output.is_automotive_part:
            return (
                "На изображении не удалось подтвердить наличие "
                "автомобильной запчасти."
            )

        detected_text = (
            f"{detected_part.name} ({detected_part.original_number})"
            if detected_part is not None
            else "точного совпадения в каталоге не подтверждено"
        )
        lines = [
            f"Предполагаемая деталь: {output.part_name or 'не определена'}.",
            f"Совпадение SmartAutoParts: {detected_text}.",
            f"Уверенность анализа: {output.confidence_score:.2f}%.",
            f"Состояние: {output.condition}.",
        ]
        if output.description:
            lines.append(output.description)
        if output.visible_oem_numbers:
            lines.append(
                "Видимые OEM-номера: "
                + ", ".join(output.visible_oem_numbers)
                + "."
            )
        if output.limitations:
            lines.append(
                "Ограничения: " + "; ".join(output.limitations)
            )
        lines.append(
            "Совместимость необходимо подтвердить по OEM-номеру и VIN."
        )
        return "\n".join(lines)

    @staticmethod
    def _normalise_instruction(
        output: RepairInstructionOutput,
        *,
        decision: ModerationDecision,
    ) -> RepairInstructionOutput:
        output.title = output.title.strip()
        output.summary = output.summary.strip()
        output.estimated_time_minutes = max(
            0,
            output.estimated_time_minutes,
        )

        if not output.title or not output.summary:
            raise AIProviderError(
                "Сгенерированная инструкция не содержит заголовок или описание."
            )
        if len(output.steps) < 3:
            raise AIProviderError(
                "Сгенерированная инструкция содержит менее трёх шагов."
            )

        for number, step in enumerate(output.steps, start=1):
            step.number = number
            step.title = step.title.strip() or f"Шаг {number}"
            step.description = step.description.strip()
            step.warning = step.warning.strip()
            step.estimated_minutes = max(0, step.estimated_minutes)
            if not step.description:
                raise AIProviderError(
                    f"Шаг {number} не содержит описания."
                )

        if decision.requires_professional:
            output.professional_service_required = True
            if not output.professional_service_reason.strip():
                output.professional_service_reason = (
                    "Работа относится к системе повышенного риска."
                )

        return output

    @staticmethod
    def _render_instruction(output: RepairInstructionOutput) -> str:
        lines = [
            f"# {output.title}",
            "",
            output.summary,
            "",
            f"**Сложность:** {output.difficulty}",
            (
                "**Ориентировочное время:** "
                f"{output.estimated_time_minutes} мин."
            ),
            "",
            "## Предупреждения по безопасности",
            "",
        ]
        lines.extend(
            f"- {item}" for item in output.safety_warnings
        )

        lines.extend(["", "## Перед началом", ""])
        lines.extend(f"- {item}" for item in output.preconditions)

        lines.extend(["", "## Инструменты", ""])
        for tool in output.tools:
            size = f", {tool.size}" if tool.size else ""
            status = "обязательно" if tool.required else "желательно"
            usage = f" — {tool.usage}" if tool.usage else ""
            lines.append(
                f"- **{tool.name}{size}** ({status}){usage}"
            )

        lines.extend(["", "## Пошаговая инструкция", ""])
        for step in output.steps:
            lines.extend(
                [
                    f"### {step.number}. {step.title}",
                    "",
                    step.description,
                ]
            )
            if step.warning:
                lines.extend(["", f"> Внимание: {step.warning}"])
            if step.estimated_minutes:
                lines.extend(
                    [
                        "",
                        f"Ориентировочное время: {step.estimated_minutes} мин.",
                    ]
                )
            lines.append("")

        lines.extend(["## Финальная проверка", ""])
        lines.extend(f"- {item}" for item in output.final_checks)

        if output.assumptions:
            lines.extend(["", "## Что требуется уточнить", ""])
            lines.extend(f"- {item}" for item in output.assumptions)

        if output.professional_service_required:
            lines.extend(
                [
                    "",
                    "## Когда нужен профессиональный сервис",
                    "",
                    (
                        output.professional_service_reason
                        or "Работа требует квалифицированного специалиста."
                    ),
                ]
            )

        return "\n".join(lines).strip()

    @staticmethod
    def _safety_identifier(user: Any) -> str | None:
        user_id = getattr(user, "pk", None)
        if user_id is None:
            return None
        secret = str(getattr(settings, "SECRET_KEY", ""))
        return hashlib.sha256(
            f"{secret}:smartautoparts:{user_id}".encode("utf-8")
        ).hexdigest()

    @staticmethod
    def _part_instance(part: Part | int | None) -> Part | None:
        if part is None or isinstance(part, Part):
            return part
        return Part.objects.get(pk=part, is_active=True)

    @staticmethod
    def _chat_history(
        *,
        user: Any,
        room: ChatRoom | int | None,
        limit: int,
    ) -> list[dict[str, str]]:
        if room is None:
            return []
        resolved_room = (
            room
            if isinstance(room, ChatRoom)
            else ChatRoom.objects.get(pk=room)
        )

        if (
            resolved_room.is_private
            and resolved_room.created_by_id != getattr(user, "pk", None)
            and not bool(getattr(user, "can_administrate", False))
            and not ChatParticipant.objects.filter(
                room=resolved_room,
                user=user,
            ).exists()
        ):
            raise AIAccessDenied("Нет доступа к истории приватного чата.")

        safe_limit = min(max(int(limit), 0), 50)
        messages = list(
            ChatMessage.objects.select_related("user")
            .filter(room=resolved_room)
            .order_by("-created_at")[:safe_limit]
        )
        messages.reverse()
        return [
            {
                "author": item.user.email,
                "content": ProjectContextBuilder._trim(
                    item.message,
                    2_000,
                ),
            }
            for item in messages
        ]

    @staticmethod
    def _save_blocked_request(
        *,
        user: Any,
        part: Part | int | None,
        prompt: str,
        request_type: str,
        decision: ModerationDecision,
    ) -> AIRequest:
        resolved_part = (
            part
            if part is None or isinstance(part, Part)
            else Part.objects.filter(pk=part).first()
        )
        return AIRequest.objects.create(
            user=user,
            part=resolved_part,
            prompt=prompt.strip(),
            response=(
                "Запрос отклонён модерацией: "
                f"{decision.reason}"
            ),
            tokens_used=decision.tokens_used,
            request_type=request_type,
        )
