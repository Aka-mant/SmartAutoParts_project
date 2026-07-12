from rest_framework.generics import (
    CreateAPIView,
    DestroyAPIView,
    ListAPIView,
    RetrieveAPIView,
    UpdateAPIView,
)
from rest_framework.permissions import IsAuthenticated

from users.permissions import (
    IsModerator,
    IsSuperuser,
    IsOwner
)

from .models import (
    SubscriptionPlan,
    UserSubscription,
    SubscriptionPayment
)
from .serializers import (
    SubscriptionPlanSerializer,
    SubscriptionPlanCreateSerializer,
    SubscriptionPlanUpdateSerializer,
    UserSubscriptionSerializer,
    UserSubscriptionCreateSerializer,
    UserSubscriptionUpdateSerializer,
    SubscriptionPaymentSerializer,
    SubscriptionPaymentCreateSerializer,
    SubscriptionPaymentUpdateSerializer,
)


class SubscriptionPlanListAPIView(ListAPIView):
    """
    API-представление для получения
    списка тарифных планов подписки.

    Доступно авторизованным
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

    Доступно модераторам и
    суперпользователям Django.
    """

    queryset = SubscriptionPlan.objects.all()
    serializer_class = SubscriptionPlanCreateSerializer
    permission_classes = [
        IsAuthenticated,
        IsModerator | IsSuperuser,
    ]


class SubscriptionPlanRetrieveAPIView(RetrieveAPIView):
    """
    API-представление для получения
    информации о тарифном плане
    подписки.

    Доступно авторизованным
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

    Доступно модераторам и
    суперпользователям Django.
    """

    queryset = SubscriptionPlan.objects.all()
    serializer_class = SubscriptionPlanUpdateSerializer
    permission_classes = [
        IsAuthenticated,
        IsModerator | IsSuperuser,
    ]


class SubscriptionPlanDeleteAPIView(DestroyAPIView):
    """
    API-представление для удаления
    тарифного плана подписки.

    Доступно только системным
    суперпользователям Django.
    """

    queryset = SubscriptionPlan.objects.all()
    permission_classes = [
        IsAuthenticated,
        IsSuperuser,
    ]


class UserSubscriptionListAPIView(ListAPIView):
    """
    API-представление для получения
    списка подписок текущего пользователя.

    Суперпользователь Django имеет
    доступ ко всем подпискам.
    """

    serializer_class = UserSubscriptionSerializer
    permission_classes = [
        IsAuthenticated,
    ]

    def get_queryset(self):
        """
        Возвращает подписки текущего
        пользователя.

        Суперпользователь получает
        полный список подписок.
        """
        if self.request.user.is_superuser:
            return UserSubscription.objects.all()

        return UserSubscription.objects.filter(
            user=self.request.user,
        )


class UserSubscriptionCreateAPIView(CreateAPIView):
    """
    API-представление для создания
    пользовательской подписки.

    Пользователь автоматически
    назначается владельцем подписки.
    """

    queryset = UserSubscription.objects.all()
    serializer_class = UserSubscriptionCreateSerializer
    permission_classes = [
        IsAuthenticated,
    ]

    def perform_create(self, serializer):
        """
        Создает подписку для текущего
        авторизованного пользователя.
        """
        serializer.save(
            user=self.request.user,
        )


class UserSubscriptionRetrieveAPIView(RetrieveAPIView):
    """
    API-представление для получения
    информации о пользовательской
    подписке.

    Пользователь может просматривать
    только собственные подписки.
    """

    serializer_class = UserSubscriptionSerializer
    permission_classes = [
        IsAuthenticated,
        IsOwner | IsSuperuser,
    ]

    def get_queryset(self):
        """
        Возвращает подписки текущего
        пользователя.

        Суперпользователь получает
        доступ ко всем подпискам.
        """
        if self.request.user.is_superuser:
            return UserSubscription.objects.all()

        return UserSubscription.objects.filter(
            user=self.request.user,
        )


class UserSubscriptionUpdateAPIView(UpdateAPIView):
    """
    API-представление для обновления
    пользовательской подписки.

    Пользователь может изменять
    только собственную подписку.
    """

    serializer_class = UserSubscriptionUpdateSerializer
    permission_classes = [
        IsAuthenticated,
        IsOwner | IsSuperuser,
    ]

    def get_queryset(self):
        """
        Возвращает подписки текущего
        пользователя.

        Суперпользователь получает
        доступ ко всем подпискам.
        """
        if self.request.user.is_superuser:
            return UserSubscription.objects.all()

        return UserSubscription.objects.filter(
            user=self.request.user,
        )


class UserSubscriptionDeleteAPIView(DestroyAPIView):
    """
    API-представление для удаления
    пользовательской подписки.

    Пользователь может удалить
    только собственную подписку.
    """

    permission_classes = [
        IsAuthenticated,
        IsOwner | IsSuperuser,
    ]

    def get_queryset(self):
        """
        Возвращает подписки текущего
        пользователя.

        Суперпользователь получает
        доступ ко всем подпискам.
        """
        if self.request.user.is_superuser:
            return UserSubscription.objects.all()

        return UserSubscription.objects.filter(
            user=self.request.user,
        )


class SubscriptionPaymentListAPIView(ListAPIView):
    """
    API-представление для получения
    списка платежей текущего пользователя.

    Суперпользователь Django имеет
    доступ ко всем платежам.
    """

    serializer_class = SubscriptionPaymentSerializer
    permission_classes = [
        IsAuthenticated,
    ]

    def get_queryset(self):
        """
        Возвращает платежи текущего
        пользователя.

        Суперпользователь получает
        полный список платежей.
        """
        if self.request.user.is_superuser:
            return SubscriptionPayment.objects.all()

        return SubscriptionPayment.objects.filter(
            user=self.request.user,
        )


class SubscriptionPaymentCreateAPIView(CreateAPIView):
    """
    API-представление для создания
    платежа за подписку.

    Пользователь автоматически
    назначается владельцем платежа.
    """

    queryset = SubscriptionPayment.objects.all()
    serializer_class = SubscriptionPaymentCreateSerializer
    permission_classes = [
        IsAuthenticated,
    ]

    def perform_create(self, serializer):
        """
        Создает платеж для текущего
        авторизованного пользователя.
        """
        serializer.save(
            user=self.request.user,
        )


class SubscriptionPaymentRetrieveAPIView(RetrieveAPIView):
    """
    API-представление для получения
    информации о платеже.

    Пользователь может просматривать
    только собственные платежи.
    """

    serializer_class = SubscriptionPaymentSerializer
    permission_classes = [
        IsAuthenticated,
        IsOwner | IsSuperuser,
    ]

    def get_queryset(self):
        """
        Возвращает платежи текущего
        пользователя.

        Суперпользователь получает
        доступ ко всем платежам.
        """
        if self.request.user.is_superuser:
            return SubscriptionPayment.objects.all()

        return SubscriptionPayment.objects.filter(
            user=self.request.user,
        )


class SubscriptionPaymentUpdateAPIView(UpdateAPIView):
    """
    API-представление для обновления
    информации о платеже.

    Пользователь может изменять
    только собственные платежи.
    """

    serializer_class = SubscriptionPaymentUpdateSerializer
    permission_classes = [
        IsAuthenticated,
        IsOwner | IsSuperuser,
    ]

    def get_queryset(self):
        """
        Возвращает платежи текущего
        пользователя.

        Суперпользователь получает
        доступ ко всем платежам.
        """
        if self.request.user.is_superuser:
            return SubscriptionPayment.objects.all()

        return SubscriptionPayment.objects.filter(
            user=self.request.user,
        )


class SubscriptionPaymentDeleteAPIView(DestroyAPIView):
    """
    API-представление для удаления
    платежа.

    Пользователь может удалить
    только собственный платеж.

    Суперпользователь Django имеет
    доступ ко всем платежам.
    """

    permission_classes = [
        IsAuthenticated,
        IsOwner | IsSuperuser,
    ]

    def get_queryset(self):
        """
        Возвращает платежи текущего
        пользователя.

        Суперпользователь получает
        доступ ко всем платежам.
        """
        if self.request.user.is_superuser:
            return SubscriptionPayment.objects.all()

        return SubscriptionPayment.objects.filter(
            user=self.request.user,
        )
