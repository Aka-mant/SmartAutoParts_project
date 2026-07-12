from django.contrib.auth import get_user_model
from django.utils.translation import gettext_lazy as _

from rest_framework.permissions import BasePermission

User = get_user_model()


class IsModerator(BasePermission):
    """
    Разрешает доступ только пользователям
    с ролью «Модератор».

    Системные суперпользователи Django
    также имеют доступ.
    """

    message = _("Для выполнения этого действия вы должны быть модератором.")

    def has_permission(self, request, view):
        return (
            request.user.is_authenticated
            and request.user.can_moderate
        )


class IsSuperuser(BasePermission):
    """
    Разрешает доступ только системным
    суперпользователям Django.
    """

    message = _("Для выполнения этого действия вы должны быть суперпользователем.")

    def has_permission(self, request, view):
        return (
            request.user.is_authenticated
            and request.user.is_superuser
        )


class HasPaidAccess(BasePermission):
    """
    Разрешает доступ пользователям,
    имеющим доступ к платным функциям.

    Доступ предоставляется премиум-
    пользователям, модераторам и
    суперпользователям Django.
    """

    message = _("Для выполнения этого действия требуется платный доступ.")

    def has_permission(self, request, view):
        return (
            request.user.is_authenticated
            and request.user.has_paid_access
        )


class CanModerate(BasePermission):
    """
    Разрешает доступ пользователям,
    имеющим право модерировать контент.

    Право имеют модераторы и
    суперпользователи Django.
    """

    message = _("У вас недостаточно прав для модерации.")

    def has_permission(self, request, view):
        return (
            request.user.is_authenticated
            and request.user.can_moderate
        )


class IsOwner(BasePermission):
    """
    Разрешает доступ только владельцу объекта.

    Поддерживает:
    - объекты пользователя;
    - модели с полем user;
    - модели, владелец которых определяется
      через связанный AI-запрос;
    - системных суперпользователей Django.
    """

    message = _(
        "Вы можете выполнять это действие "
        "только для собственных данных."
    )

    def has_permission(self, request, view):
        """
        Разрешает проверку объектных прав
        только авторизованным пользователям.
        """
        return request.user.is_authenticated

    def has_object_permission(self, request, view, obj):
        """
        Проверяет, является ли текущий
        пользователь владельцем объекта.
        """
        if not request.user.is_authenticated:
            return False

        if request.user.is_superuser:
            return True

        if isinstance(obj, User):
            return obj == request.user

        if hasattr(obj, "user"):
            return obj.user == request.user

        if (
            hasattr(obj, "ai_request")
            and obj.ai_request
            and hasattr(obj.ai_request, "user")
        ):
            return obj.ai_request.user == request.user

        return False