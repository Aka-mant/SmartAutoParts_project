from django.db.models import QuerySet

from rest_framework.generics import (
    CreateAPIView,
    DestroyAPIView,
    ListAPIView,
    RetrieveAPIView,
    UpdateAPIView,
)
from rest_framework.permissions import IsAuthenticated

from users.permissions import (
    IsAdmin,
    IsModerator,
    IsOwner,
)

from .models import (
    SubscriptionPayment,
    SubscriptionPlan,
    UserSubscription,
)
from .serializers import (
    SubscriptionPaymentCreateSerializer,
    SubscriptionPaymentSerializer,
    SubscriptionPaymentUpdateSerializer,
    SubscriptionPlanCreateSerializer,
    SubscriptionPlanSerializer,
    SubscriptionPlanUpdateSerializer,
    UserSubscriptionCreateSerializer,
    UserSubscriptionSerializer,
    UserSubscriptionUpdateSerializer,
)


class UserOwnedQuerySetMixin:
    """
    Ограничивает queryset объектами,
    принадлежащими текущему пользователю.

    Администраторы и системные
    суперпользователи Django получают
    доступ ко всем объектам.
    """

    owner_lookup = "user"

    def get_queryset(self) -> QuerySet:
        """
        Возвращает queryset с учётом
        прав текущего пользователя.
        """

        queryset = super().get_queryset()
        user = self.request.user

        if not user.is_authenticated:
            return queryset.none()

        if user.can_administrate:
            return queryset

        return queryset.filter(
            **{
                self.owner_lookup: user,
            }
        )


class SubscriptionPlanListAPIView(ListAPIView):
    """
    API-представление для получения
    списка тарифных планов подписки.

    Доступно всем авторизованным
    пользователям.
    """

    queryset = SubscriptionPlan.objects.all()
    serializer_class = SubscriptionPlanSerializer
    permission_classes = [
        IsAuthenticated,
    ]


class SubscriptionPlanCreateAPIView(CreateAPIView):
    """
    API-представление для создания
    тарифного плана подписки.

    Доступ предоставляется:

    - модераторам;
    - администраторам;
    - системным суперпользователям Django.
    """

    queryset = SubscriptionPlan.objects.all()
    serializer_class = SubscriptionPlanCreateSerializer
    permission_classes = [
        IsAuthenticated,
        IsModerator,
    ]


class SubscriptionPlanRetrieveAPIView(RetrieveAPIView):
    """
    API-представление для получения
    информации о тарифном плане подписки.

    Доступно всем авторизованным
    пользователям.
    """

    queryset = SubscriptionPlan.objects.all()
    serializer_class = SubscriptionPlanSerializer
    permission_classes = [
        IsAuthenticated,
    ]


class SubscriptionPlanUpdateAPIView(UpdateAPIView):
    """
    API-представление для обновления
    тарифного плана подписки.

    Доступ предоставляется:

    - модераторам;
    - администраторам;
    - системным суперпользователям Django.
    """

    queryset = SubscriptionPlan.objects.all()
    serializer_class = SubscriptionPlanUpdateSerializer
    permission_classes = [
        IsAuthenticated,
        IsModerator,
    ]


class SubscriptionPlanDeleteAPIView(DestroyAPIView):
    """
    API-представление для удаления
    тарифного плана подписки.

    Доступ предоставляется:

    - администраторам;
    - системным суперпользователям Django.
    """

    queryset = SubscriptionPlan.objects.all()
    permission_classes = [
        IsAuthenticated,
        IsAdmin,
    ]


class UserSubscriptionListAPIView(
    UserOwnedQuerySetMixin,
    ListAPIView,
):
    """
    API-представление для получения
    списка пользовательских подписок.

    Обычный пользователь получает только
    собственные подписки.

    Администраторы и системные
    суперпользователи получают все подписки.
    """

    queryset = UserSubscription.objects.select_related(
        "user",
        "plan",
    )
    serializer_class = UserSubscriptionSerializer
    permission_classes = [
        IsAuthenticated,
    ]


class UserSubscriptionCreateAPIView(CreateAPIView):
    """
    API-представление для создания
    пользовательской подписки.

    Текущий пользователь автоматически
    назначается владельцем подписки.
    """

    queryset = UserSubscription.objects.all()
    serializer_class = UserSubscriptionCreateSerializer
    permission_classes = [
        IsAuthenticated,
    ]

    def perform_create(self, serializer):
        """
        Создаёт подписку для текущего
        авторизованного пользователя.

        Значение поля user, переданное
        клиентом, не используется.
        """

        serializer.save(
            user=self.request.user,
        )


class UserSubscriptionRetrieveAPIView(
    UserOwnedQuerySetMixin,
    RetrieveAPIView,
):
    """
    API-представление для получения
    информации о пользовательской подписке.

    Пользователь может просматривать
    только собственные подписки.

    Администраторы и системные
    суперпользователи могут просматривать
    любые подписки.
    """

    queryset = UserSubscription.objects.select_related(
        "user",
        "plan",
    )
    serializer_class = UserSubscriptionSerializer
    permission_classes = [
        IsAuthenticated,
        IsOwner,
    ]


class UserSubscriptionUpdateAPIView(
    UserOwnedQuerySetMixin,
    UpdateAPIView,
):
    """
    API-представление для обновления
    пользовательской подписки.

    Пользователь может изменять
    только собственные подписки.

    Администраторы и системные
    суперпользователи могут изменять
    любые подписки.
    """

    queryset = UserSubscription.objects.select_related(
        "user",
        "plan",
    )
    serializer_class = UserSubscriptionUpdateSerializer
    permission_classes = [
        IsAuthenticated,
        IsOwner,
    ]

    def perform_update(self, serializer):
        """
        Обновляет пользовательскую подписку,
        сохраняя её текущего владельца.
        """

        instance = self.get_object()

        serializer.save(
            user=instance.user,
        )


class UserSubscriptionDeleteAPIView(
    UserOwnedQuerySetMixin,
    DestroyAPIView,
):
    """
    API-представление для удаления
    пользовательской подписки.

    Пользователь может удалить
    только собственную подписку.

    Администраторы и системные
    суперпользователи могут удалять
    любые подписки.
    """

    queryset = UserSubscription.objects.select_related(
        "user",
        "plan",
    )
    permission_classes = [
        IsAuthenticated,
        IsOwner,
    ]


class SubscriptionPaymentListAPIView(
    UserOwnedQuerySetMixin,
    ListAPIView,
):
    """
    API-представление для получения
    списка платежей пользователя.

    Обычный пользователь получает только
    собственные платежи.

    Администраторы и системные
    суперпользователи получают все платежи.
    """

    queryset = SubscriptionPayment.objects.select_related(
        "user",
        "subscription",
    )
    serializer_class = SubscriptionPaymentSerializer
    permission_classes = [
        IsAuthenticated,
    ]


class SubscriptionPaymentCreateAPIView(CreateAPIView):
    """
    API-представление для создания
    платежа за подписку.

    Текущий пользователь автоматически
    назначается владельцем платежа.
    """

    queryset = SubscriptionPayment.objects.all()
    serializer_class = SubscriptionPaymentCreateSerializer
    permission_classes = [
        IsAuthenticated,
    ]

    def perform_create(self, serializer):
        """
        Создаёт платёж для текущего
        авторизованного пользователя.

        Значение поля user, переданное
        клиентом, не используется.
        """

        serializer.save(
            user=self.request.user,
        )


class SubscriptionPaymentRetrieveAPIView(
    UserOwnedQuerySetMixin,
    RetrieveAPIView,
):
    """
    API-представление для получения
    информации о платеже.

    Пользователь может просматривать
    только собственные платежи.

    Администраторы и системные
    суперпользователи могут просматривать
    любые платежи.
    """

    queryset = SubscriptionPayment.objects.select_related(
        "user",
        "subscription",
    )
    serializer_class = SubscriptionPaymentSerializer
    permission_classes = [
        IsAuthenticated,
        IsOwner,
    ]


class SubscriptionPaymentUpdateAPIView(
    UserOwnedQuerySetMixin,
    UpdateAPIView,
):
    """
    API-представление для обновления
    информации о платеже.

    Пользователь может изменять
    только собственные платежи.

    Администраторы и системные
    суперпользователи могут изменять
    любые платежи.
    """

    queryset = SubscriptionPayment.objects.select_related(
        "user",
        "subscription",
    )
    serializer_class = SubscriptionPaymentUpdateSerializer
    permission_classes = [
        IsAuthenticated,
        IsOwner,
    ]

    def perform_update(self, serializer):
        """
        Обновляет платёж, сохраняя
        его текущего владельца.
        """

        instance = self.get_object()

        serializer.save(
            user=instance.user,
        )


class SubscriptionPaymentDeleteAPIView(
    UserOwnedQuerySetMixin,
    DestroyAPIView,
):
    """
    API-представление для удаления
    платежа.

    Пользователь может удалить
    только собственный платёж.

    Администраторы и системные
    суперпользователи могут удалять
    любые платежи.
    """

    queryset = SubscriptionPayment.objects.select_related(
        "user",
        "subscription",
    )
    permission_classes = [
        IsAuthenticated,
        IsOwner,
    ]

