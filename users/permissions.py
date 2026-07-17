from django.contrib.auth import get_user_model
from django.utils.translation import gettext_lazy as _

from rest_framework.permissions import BasePermission


User = get_user_model()


def is_authenticated_and_active(user) -> bool:
    """
    Проверяет, что пользователь
    авторизован и активен.
    """

    return bool(
        user
        and user.is_authenticated
        and user.is_active
    )


class IsModerator(BasePermission):
    """
    Разрешает доступ пользователям,
    имеющим право модерировать контент.

    Доступ предоставляется:

    - модераторам;
    - администраторам;
    - системным суперпользователям Django.
    """

    message = _(
        "Для выполнения этого действия "
        "необходимы права модератора."
    )

    def has_permission(self, request, view):
        """
        Проверяет наличие прав
        на модерацию контента.
        """

        user = request.user

        return (
            is_authenticated_and_active(user)
            and user.can_moderate
        )


class IsAdmin(BasePermission):
    """
    Разрешает доступ пользователям,
    имеющим административные права.

    Доступ предоставляется:

    - пользователям с ролью администратора;
    - системным суперпользователям Django.
    """

    message = _(
        "Для выполнения этого действия "
        "необходимы права администратора."
    )

    def has_permission(self, request, view):
        """
        Проверяет наличие административных прав.
        """

        user = request.user

        return (
            is_authenticated_and_active(user)
            and user.can_administrate
        )


class IsSuperuser(BasePermission):
    """
    Разрешает доступ только системным
    суперпользователям Django.

    Пользователь с ролью администратора,
    но без флага is_superuser, эту
    проверку не проходит.
    """

    message = _(
        "Для выполнения этого действия "
        "вы должны быть суперпользователем."
    )

    def has_permission(self, request, view):
        """
        Проверяет флаг is_superuser.
        """

        user = request.user

        return (
            is_authenticated_and_active(user)
            and user.is_superuser
        )


class HasPaidAccess(BasePermission):
    """
    Разрешает доступ пользователям,
    имеющим доступ к платным функциям.

    Доступ предоставляется:

    - премиум-пользователям;
    - модераторам;
    - администраторам;
    - системным суперпользователям Django.
    """

    message = _(
        "Для выполнения этого действия "
        "требуется платный доступ."
    )

    def has_permission(self, request, view):
        """
        Проверяет наличие доступа
        к платным функциям.
        """

        user = request.user

        return (
            is_authenticated_and_active(user)
            and user.has_paid_access
        )


class CanModerate(BasePermission):
    """
    Разрешает доступ пользователям,
    имеющим право модерировать контент.

    Использует свойство can_moderate
    модели пользователя.
    """

    message = _(
        "У вас недостаточно прав "
        "для модерации контента."
    )

    def has_permission(self, request, view):
        """
        Проверяет право пользователя
        модерировать контент.
        """

        user = request.user

        return (
            is_authenticated_and_active(user)
            and user.can_moderate
        )


class CanAdministrate(BasePermission):
    """
    Разрешает доступ пользователям,
    имеющим право выполнять
    административные действия.

    Использует свойство can_administrate
    модели пользователя.
    """

    message = _(
        "У вас недостаточно прав "
        "для выполнения административных действий."
    )

    def has_permission(self, request, view):
        """
        Проверяет право пользователя
        выполнять административные действия.
        """

        user = request.user

        return (
            is_authenticated_and_active(user)
            and user.can_administrate
        )


class IsOwner(BasePermission):
    """
    Разрешает доступ владельцу объекта.

    Полный доступ к объектам всех
    пользователей получают:

    - пользователи с ролью администратора;
    - системные суперпользователи Django.

    Поддерживаются:

    - экземпляры модели пользователя;
    - модели с прямым полем user;
    - модели со связью ai_request.user.
    """

    message = _(
        "Вы можете выполнять это действие "
        "только для собственных данных."
    )

    def has_permission(self, request, view):
        """
        Разрешает переход к объектной проверке
        только активным авторизованным
        пользователям.
        """

        return is_authenticated_and_active(
            request.user
        )

    def has_object_permission(
        self,
        request,
        view,
        obj,
    ):
        """
        Проверяет, является ли текущий
        пользователь владельцем объекта.

        Администраторы и суперпользователи
        получают доступ ко всем объектам.
        """

        user = request.user

        if not is_authenticated_and_active(user):
            return False

        # Роль ADMIN и системный суперпользователь
        # проходят проверку через одно свойство.
        if user.can_administrate:
            return True

        # Проверка экземпляра пользователя.
        if isinstance(obj, User):
            return obj.pk == user.pk

        # Проверка модели с прямым полем user.
        object_user = getattr(
            obj,
            "user",
            None,
        )

        if object_user is not None:
            return object_user.pk == user.pk

        # Проверка объекта, связанного
        # с моделью AIRequest.
        ai_request = getattr(
            obj,
            "ai_request",
            None,
        )

        if ai_request is not None:
            ai_request_user = getattr(
                ai_request,
                "user",
                None,
            )

            if ai_request_user is not None:
                return ai_request_user.pk == user.pk

        return False
