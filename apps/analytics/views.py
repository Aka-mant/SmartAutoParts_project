from django.db.models import QuerySet

from rest_framework.generics import (
    CreateAPIView,
    DestroyAPIView,
    ListAPIView,
    RetrieveAPIView,
    UpdateAPIView,
)
from users.permissions import (
    IsAdmin,
    IsModerator,
    IsOwner,
    IsSuperuser,
)

from .models import (
    PopularPart,
    SearchLog,
    UserActivity,
)
from .serializers import (
    PopularPartCreateSerializer,
    PopularPartSerializer,
    PopularPartUpdateSerializer,
    SearchLogCreateSerializer,
    SearchLogSerializer,
    SearchLogUpdateSerializer,
    UserActivityCreateSerializer,
    UserActivitySerializer,
    UserActivityUpdateSerializer,
)


class UserOwnedQuerySetMixin:
    """
    Ограничивает queryset объектами
    текущего пользователя.

    Пользователи с административными
    правами получают полный queryset.
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


def get_client_ip(request) -> str | None:
    """
    Возвращает IP-адрес клиента.

    Сначала проверяет заголовок
    X-Forwarded-For, затем REMOTE_ADDR.

    При наличии нескольких адресов в
    X-Forwarded-For возвращает первый.
    """

    forwarded_for = request.META.get(
        "HTTP_X_FORWARDED_FOR"
    )

    if forwarded_for:
        return forwarded_for.split(",")[0].strip()

    return request.META.get(
        "REMOTE_ADDR"
    )


class UserActivityListAPIView(
    UserOwnedQuerySetMixin,
    ListAPIView,
):
    """
    API-представление для получения
    списка действий пользователя.

    Обычный пользователь получает только
    собственную историю активности.

    Администраторы и системные
    суперпользователи получают все записи.
    """

    queryset = UserActivity.objects.select_related(
        "user",
    )
    serializer_class = UserActivitySerializer
    permission_classes = [
        IsSuperuser,
    ]


class UserActivityCreateAPIView(CreateAPIView):
    """
    API-представление для создания
    записи активности пользователя.

    Текущий пользователь автоматически
    назначается владельцем записи.
    """

    queryset = UserActivity.objects.all()
    serializer_class = UserActivityCreateSerializer
    permission_classes = [
        IsSuperuser,
    ]

    def perform_create(self, serializer):
        """
        Создаёт запись активности
        текущего пользователя.

        Значение поля user, переданное
        клиентом, не используется.
        """

        serializer.save(
            user=self.request.user,
        )


class UserActivityRetrieveAPIView(
    UserOwnedQuerySetMixin,
    RetrieveAPIView,
):
    """
    API-представление для получения
    отдельной записи активности.

    Пользователь может просматривать
    только собственные записи.

    Администраторы и системные
    суперпользователи могут просматривать
    любые записи.
    """

    queryset = UserActivity.objects.select_related(
        "user",
    )
    serializer_class = UserActivitySerializer
    permission_classes = [
        IsSuperuser,
        IsOwner,
    ]


class UserActivityUpdateAPIView(
    UserOwnedQuerySetMixin,
    UpdateAPIView,
):
    """
    API-представление для обновления
    записи активности пользователя.

    Пользователь может изменять
    только собственные записи.

    Администраторы и системные
    суперпользователи могут изменять
    любые записи.
    """

    queryset = UserActivity.objects.select_related(
        "user",
    )
    serializer_class = UserActivityUpdateSerializer
    permission_classes = [
        IsSuperuser,
        IsOwner,
    ]

    def perform_update(self, serializer):
        """
        Обновляет запись, сохраняя
        текущего владельца.
        """

        instance = self.get_object()

        serializer.save(
            user=instance.user,
        )


class UserActivityDeleteAPIView(
    UserOwnedQuerySetMixin,
    DestroyAPIView,
):
    """
    API-представление для удаления
    записи активности пользователя.

    Пользователь может удалять
    только собственные записи.

    Администраторы и системные
    суперпользователи могут удалять
    любые записи.
    """

    queryset = UserActivity.objects.select_related(
        "user",
    )
    permission_classes = [
        IsSuperuser,
        IsOwner,
    ]


class SearchLogListAPIView(
    UserOwnedQuerySetMixin,
    ListAPIView,
):
    """
    API-представление для получения
    списка поисковых запросов.

    Обычный пользователь получает только
    собственные поисковые запросы.

    Администраторы и системные
    суперпользователи получают все записи.
    """

    queryset = SearchLog.objects.select_related(
        "user",
    )
    serializer_class = SearchLogSerializer
    permission_classes = [
        IsSuperuser,
    ]


class SearchLogCreateAPIView(CreateAPIView):
    """
    API-представление для создания
    записи поискового запроса.

    Пользователь и IP-адрес клиента
    назначаются автоматически.
    """

    queryset = SearchLog.objects.all()
    serializer_class = SearchLogCreateSerializer
    permission_classes = [
        IsSuperuser,
    ]

    def perform_create(self, serializer):
        """
        Создаёт запись поискового запроса
        текущего пользователя и сохраняет
        его IP-адрес.
        """

        serializer.save(
            user=self.request.user,
            ip_address=get_client_ip(
                self.request,
            ),
        )


class SearchLogRetrieveAPIView(
    UserOwnedQuerySetMixin,
    RetrieveAPIView,
):
    """
    API-представление для получения
    отдельной записи поискового запроса.

    Пользователь может просматривать
    только собственные записи.

    Администраторы и системные
    суперпользователи могут просматривать
    любые записи.
    """

    queryset = SearchLog.objects.select_related(
        "user",
    )
    serializer_class = SearchLogSerializer
    permission_classes = [
        IsSuperuser,
        IsOwner,
    ]


class SearchLogUpdateAPIView(
    UserOwnedQuerySetMixin,
    UpdateAPIView,
):
    """
    API-представление для обновления
    записи поискового запроса.

    Пользователь может изменять
    только собственные записи.

    Администраторы и системные
    суперпользователи могут изменять
    любые записи.
    """

    queryset = SearchLog.objects.select_related(
        "user",
    )
    serializer_class = SearchLogUpdateSerializer
    permission_classes = [
        IsSuperuser,
        IsOwner,
    ]

    def perform_update(self, serializer):
        """
        Обновляет поисковый запрос,
        сохраняя владельца и IP-адрес.

        Клиент не может изменить эти поля.
        """

        instance = self.get_object()

        serializer.save(
            user=instance.user,
            ip_address=instance.ip_address,
        )


class SearchLogDeleteAPIView(
    UserOwnedQuerySetMixin,
    DestroyAPIView,
):
    """
    API-представление для удаления
    записи поискового запроса.

    Пользователь может удалять
    только собственные записи.

    Администраторы и системные
    суперпользователи могут удалять
    любые записи.
    """

    queryset = SearchLog.objects.select_related(
        "user",
    )
    permission_classes = [
        IsSuperuser,
        IsOwner,
    ]


class PopularPartListAPIView(ListAPIView):
    """
    API-представление для получения
    списка популярных запчастей.

    Доступно всем авторизованным
    пользователям.
    """

    queryset = PopularPart.objects.select_related(
        "part",
    )
    serializer_class = PopularPartSerializer
    permission_classes = [
        IsSuperuser,
    ]


class PopularPartCreateAPIView(CreateAPIView):
    """
    API-представление для создания
    статистики популярности запчасти.

    Доступ предоставляется:

    - модераторам;
    - администраторам;
    - системным суперпользователям Django.
    """

    queryset = PopularPart.objects.select_related(
        "part",
    )
    serializer_class = PopularPartCreateSerializer
    permission_classes = [
        IsSuperuser,
        IsModerator,
    ]


class PopularPartRetrieveAPIView(RetrieveAPIView):
    """
    API-представление для получения
    отдельной записи статистики
    популярной запчасти.

    Доступно всем авторизованным
    пользователям.
    """

    queryset = PopularPart.objects.select_related(
        "part",
    )
    serializer_class = PopularPartSerializer
    permission_classes = [
        IsSuperuser,
    ]


class PopularPartUpdateAPIView(UpdateAPIView):
    """
    API-представление для обновления
    статистики популярной запчасти.

    Доступ предоставляется:

    - модераторам;
    - администраторам;
    - системным суперпользователям Django.
    """

    queryset = PopularPart.objects.select_related(
        "part",
    )
    serializer_class = PopularPartUpdateSerializer
    permission_classes = [
        IsSuperuser,
        IsModerator,
    ]


class PopularPartDeleteAPIView(DestroyAPIView):
    """
    API-представление для удаления
    статистики популярной запчасти.

    Доступ предоставляется:

    - администраторам;
    - системным суперпользователям Django.
    """

    queryset = PopularPart.objects.select_related(
        "part",
    )
    permission_classes = [
        IsSuperuser,
        IsAdmin,
    ]
