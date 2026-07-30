"""Единые проверки активной подписки и доступа к функциям тарифа."""

from __future__ import annotations

from typing import Any

from django.utils import timezone

from .models import UserSubscription


def is_privileged_user(user: Any) -> bool:
    """Проверяет административный доступ к данным проекта."""

    return bool(
        getattr(user, "is_authenticated", False)
        and (
            getattr(user, "is_superuser", False)
            or getattr(user, "can_administrate", False)
            or getattr(user, "role", "") == "admin"
        )
    )


def has_unlimited_ai_access(user: Any) -> bool:
    """Безлимитные AI-запросы доступны только суперпользователю."""

    return bool(
        getattr(user, "is_authenticated", False)
        and getattr(user, "is_active", False)
        and getattr(user, "is_superuser", False)
    )


def is_moderator_only(user: Any) -> bool:
    """Проверяет роль модератора без административных полномочий."""

    return bool(
        getattr(user, "is_authenticated", False)
        and getattr(user, "is_active", False)
        and getattr(user, "role", "") == "moderator"
        and not is_privileged_user(user)
    )


def get_active_subscription(user: Any) -> UserSubscription | None:
    """Возвращает действующую подписку пользователя."""

    if not getattr(user, "is_authenticated", False):
        return None

    now = timezone.now()
    return (
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


def has_instruction_access(user: Any) -> bool:
    """Проверяет базовый доступ к ранее приобретённым инструкциям."""

    if is_privileged_user(user):
        return True

    return get_active_subscription(user) is not None


def has_part_card_access(user: Any) -> bool:
    """
    Проверяет доступ к карточкам деталей.
    """

    return bool(
        is_privileged_user(user)
        or get_active_subscription(user) is not None
    )


def purchased_instruction_ids(user: Any):
    """
    Возвращает ID приобретённых инструкций.

    ``None`` означает отсутствие фильтрации для администратора или
    суперпользователя.
    """

    if is_privileged_user(user):
        return None

    from apps.AI.models import AIContentPurchase

    return AIContentPurchase.objects.filter(
        user=user,
        content_type=AIContentPurchase.ContentType.INSTRUCTION,
        instruction_id__isnull=False,
    ).values_list("instruction_id", flat=True)


def has_purchased_instruction(user: Any, instruction: Any) -> bool:
    """Проверяет постоянное право пользователя на инструкцию."""

    if is_privileged_user(user):
        return True
    if not getattr(user, "is_authenticated", False):
        return False

    from apps.AI.models import AIContentPurchase

    instruction_id = getattr(instruction, "pk", instruction)
    return AIContentPurchase.objects.filter(
        user=user,
        content_type=AIContentPurchase.ContentType.INSTRUCTION,
        instruction_id=instruction_id,
    ).exists()


def has_purchased_tools(user: Any, part: Any) -> bool:
    """Проверяет постоянное право на блок инструментов детали."""

    if is_privileged_user(user):
        return True
    if not getattr(user, "is_authenticated", False):
        return False

    from apps.AI.models import AIContentPurchase

    part_id = getattr(part, "pk", part)
    return AIContentPurchase.objects.filter(
        user=user,
        content_type=AIContentPurchase.ContentType.TOOLS,
        part_id=part_id,
    ).exists()
