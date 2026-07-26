"""Единые проверки активной подписки и доступа к функциям тарифа."""

from __future__ import annotations

from typing import Any

from django.utils import timezone

from .models import UserSubscription


def is_privileged_user(user: Any) -> bool:
    """Администраторы не ограничиваются пользовательскими тарифами."""

    return bool(
        getattr(user, "is_authenticated", False)
        and (
            getattr(user, "is_superuser", False)
            or getattr(user, "can_administrate", False)
            or getattr(user, "role", "") == "admin"
        )
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
    """Проверяет доступ ко всему содержимому ремонтных инструкций."""

    if is_privileged_user(user):
        return True

    subscription = get_active_subscription(user)
    return bool(
        subscription
        and subscription.plan.has_instruction_generation
        and subscription.plan.get_feature_limit("instruction") > 0
    )


def has_part_card_access(user: Any) -> bool:
    """Проверяет доступ к карточкам деталей."""

    return bool(
        is_privileged_user(user)
        or get_active_subscription(user) is not None
    )
