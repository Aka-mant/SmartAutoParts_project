from django.utils.translation import gettext_lazy as _

from rest_framework.permissions import BasePermission


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

    Используется для проверки объектных
    разрешений моделей, имеющих поле
    ``user``.
    """

    message = _("Вы можете выполнять это действие только для собственных данных.")

    def has_object_permission(self, request, view, obj):
        return (
            request.user.is_authenticated
            and hasattr(obj, "user")
            and obj.user == request.user
        )