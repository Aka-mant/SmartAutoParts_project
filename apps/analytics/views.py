from rest_framework.generics import (
    CreateAPIView,
    DestroyAPIView,
    ListAPIView,
    RetrieveAPIView,
    UpdateAPIView,
)
from rest_framework.permissions import IsAuthenticated

from users.permissions import IsOwner, IsSuperuser, IsModerator

from .models import UserActivity, SearchLog, PopularPart
from .serializers import (
    UserActivityCreateSerializer,
    UserActivitySerializer,
    UserActivityUpdateSerializer, SearchLogSerializer, SearchLogCreateSerializer, SearchLogUpdateSerializer,
    PopularPartSerializer, PopularPartCreateSerializer, PopularPartUpdateSerializer,
)


class UserActivityListAPIView(ListAPIView):
    """
    API-представление для получения
    списка действий пользователя.

    Обычный пользователь видит только
    собственную историю активности.

    Суперпользователь Django имеет
    доступ ко всем записям.
    """

    serializer_class = UserActivitySerializer
    permission_classes = [
        IsAuthenticated,
    ]

    def get_queryset(self):
        """
        Возвращает записи активности
        текущего пользователя.

        Суперпользователь получает
        полный список записей.
        """
        queryset = UserActivity.objects.select_related(
            "user",
        )

        if self.request.user.is_superuser:
            return queryset.all()

        return queryset.filter(
            user=self.request.user,
        )


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
        IsAuthenticated,
    ]

    def perform_create(self, serializer):
        """
        Создает запись активности
        текущего пользователя.
        """
        serializer.save(
            user=self.request.user,
        )


class UserActivityRetrieveAPIView(RetrieveAPIView):
    """
    API-представление для получения
    отдельной записи активности.

    Пользователь может просматривать
    только собственные записи.

    Суперпользователь Django имеет
    доступ ко всем записям.
    """

    serializer_class = UserActivitySerializer
    permission_classes = [
        IsAuthenticated,
        IsOwner | IsSuperuser,
    ]

    def get_queryset(self):
        """
        Возвращает доступные текущему
        пользователю записи активности.
        """
        queryset = UserActivity.objects.select_related(
            "user",
        )

        if self.request.user.is_superuser:
            return queryset.all()

        return queryset.filter(
            user=self.request.user,
        )


class UserActivityUpdateAPIView(UpdateAPIView):
    """
    API-представление для обновления
    записи активности пользователя.

    Пользователь может изменять только
    собственные записи.

    Суперпользователь Django имеет
    доступ ко всем записям.
    """

    serializer_class = UserActivityUpdateSerializer
    permission_classes = [
        IsAuthenticated,
        IsOwner | IsSuperuser,
    ]

    def get_queryset(self):
        """
        Возвращает доступные текущему
        пользователю записи активности.
        """
        if self.request.user.is_superuser:
            return UserActivity.objects.all()

        return UserActivity.objects.filter(
            user=self.request.user,
        )


class UserActivityDeleteAPIView(DestroyAPIView):
    """
    API-представление для удаления
    записи активности пользователя.

    Пользователь может удалять только
    собственные записи.

    Суперпользователь Django имеет
    доступ ко всем записям.
    """

    permission_classes = [
        IsAuthenticated,
        IsOwner | IsSuperuser,
    ]

    def get_queryset(self):
        """
        Возвращает доступные текущему
        пользователю записи активности.
        """
        if self.request.user.is_superuser:
            return UserActivity.objects.all()

        return UserActivity.objects.filter(
            user=self.request.user,
        )


def get_client_ip(request):
    """
    Возвращает IP-адрес клиента.

    Сначала проверяет заголовок
    X-Forwarded-For, затем REMOTE_ADDR.
    """
    forwarded_for = request.META.get(
        "HTTP_X_FORWARDED_FOR"
    )

    if forwarded_for:
        return forwarded_for.split(",")[0].strip()

    return request.META.get("REMOTE_ADDR")


class SearchLogListAPIView(ListAPIView):
    """
    API-представление для получения
    списка поисковых запросов.

    Обычный пользователь видит только
    собственные поисковые запросы.

    Суперпользователь Django имеет
    доступ ко всем записям.
    """

    serializer_class = SearchLogSerializer
    permission_classes = [
        IsAuthenticated,
    ]

    def get_queryset(self):
        """
        Возвращает поисковые запросы
        текущего пользователя.

        Суперпользователь получает
        полный список записей.
        """
        queryset = SearchLog.objects.select_related(
            "user",
        )

        if self.request.user.is_superuser:
            return queryset.all()

        return queryset.filter(
            user=self.request.user,
        )


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
        IsAuthenticated,
    ]

    def perform_create(self, serializer):
        """
        Создает запись поискового запроса
        текущего пользователя и сохраняет
        IP-адрес клиента.
        """
        serializer.save(
            user=self.request.user,
            ip_address=get_client_ip(
                self.request,
            ),
        )


class SearchLogRetrieveAPIView(RetrieveAPIView):
    """
    API-представление для получения
    отдельной записи поискового запроса.

    Пользователь может просматривать
    только собственные записи.

    Суперпользователь Django имеет
    доступ ко всем записям.
    """

    serializer_class = SearchLogSerializer
    permission_classes = [
        IsAuthenticated,
        IsOwner | IsSuperuser,
    ]

    def get_queryset(self):
        """
        Возвращает доступные текущему
        пользователю поисковые запросы.
        """
        queryset = SearchLog.objects.select_related(
            "user",
        )

        if self.request.user.is_superuser:
            return queryset.all()

        return queryset.filter(
            user=self.request.user,
        )


class SearchLogUpdateAPIView(UpdateAPIView):
    """
    API-представление для обновления
    записи поискового запроса.

    Пользователь может изменять только
    собственные записи.

    Суперпользователь Django имеет
    доступ ко всем записям.
    """

    serializer_class = SearchLogUpdateSerializer
    permission_classes = [
        IsAuthenticated,
        IsOwner | IsSuperuser,
    ]

    def get_queryset(self):
        """
        Возвращает доступные текущему
        пользователю поисковые запросы.
        """
        if self.request.user.is_superuser:
            return SearchLog.objects.all()

        return SearchLog.objects.filter(
            user=self.request.user,
        )


class SearchLogDeleteAPIView(DestroyAPIView):
    """
    API-представление для удаления
    записи поискового запроса.

    Пользователь может удалять только
    собственные записи.

    Суперпользователь Django имеет
    доступ ко всем записям.
    """

    permission_classes = [
        IsAuthenticated,
        IsOwner | IsSuperuser,
    ]

    def get_queryset(self):
        """
        Возвращает доступные текущему
        пользователю поисковые запросы.
        """
        if self.request.user.is_superuser:
            return SearchLog.objects.all()

        return SearchLog.objects.filter(
            user=self.request.user,
        )


class PopularPartListAPIView(ListAPIView):
    """
    API-представление для получения
    списка популярных запчастей.

    Доступно авторизованным
    пользователям.
    """

    serializer_class = PopularPartSerializer
    permission_classes = [
        IsAuthenticated,
    ]

    def get_queryset(self):
        """
        Возвращает статистику популярных
        запчастей с данными о запчастях.
        """
        return PopularPart.objects.select_related(
            "part",
        ).all()


class PopularPartCreateAPIView(CreateAPIView):
    """
    API-представление для создания
    записи статистики популярности
    запчасти.

    Доступно модераторам и
    суперпользователям Django.
    """

    queryset = PopularPart.objects.all()
    serializer_class = PopularPartCreateSerializer
    permission_classes = [
        IsAuthenticated,
        IsModerator | IsSuperuser,
    ]


class PopularPartRetrieveAPIView(RetrieveAPIView):
    """
    API-представление для получения
    отдельной записи статистики
    популярной запчасти.

    Доступно авторизованным
    пользователям.
    """

    serializer_class = PopularPartSerializer
    permission_classes = [
        IsAuthenticated,
    ]

    def get_queryset(self):
        """
        Возвращает статистику популярных
        запчастей с данными о запчастях.
        """
        return PopularPart.objects.select_related(
            "part",
        ).all()


class PopularPartUpdateAPIView(UpdateAPIView):
    """
    API-представление для обновления
    статистики популярной запчасти.

    Доступно модераторам и
    суперпользователям Django.
    """

    queryset = PopularPart.objects.all()
    serializer_class = PopularPartUpdateSerializer
    permission_classes = [
        IsAuthenticated,
        IsModerator | IsSuperuser,
    ]


class PopularPartDeleteAPIView(DestroyAPIView):
    """
    API-представление для удаления
    статистики популярной запчасти.

    Доступно только системным
    суперпользователям Django.
    """

    queryset = PopularPart.objects.all()
    permission_classes = [
        IsAuthenticated,
        IsSuperuser,
    ]
