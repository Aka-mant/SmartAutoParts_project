from rest_framework.generics import (
    CreateAPIView,
    DestroyAPIView,
    ListAPIView,
    RetrieveAPIView,
    UpdateAPIView,
)
from rest_framework.permissions import (
    AllowAny,
    IsAuthenticated,
)
from rest_framework_simplejwt.views import TokenObtainPairView

from .mixins.mixins import UserOwnedQuerySetMixin
from .models import (
    Profile,
    RepairHistory,
    SearchHistory,
    User,
)
from .permissions import (
    IsAdmin,
    IsModerator,
    IsOwner,
)
from .serializers import (
    ProfileSerializer,
    ProfileUpdateSerializer,
    RepairHistoryCreateSerializer,
    RepairHistorySerializer,
    RepairHistoryUpdateSerializer,
    SearchHistorySerializer,
    UserCreateSerializer,
    UserSerializer,
    UserTokenObtainSerializer,
    UserUpdateSerializer,
)


class UserListAPIView(ListAPIView):
    """
    API-представление для получения
    списка пользователей.

    Доступ предоставляется:

    - модераторам;
    - администраторам;
    - системным суперпользователям Django.
    """

    queryset = User.objects.all()
    serializer_class = UserSerializer
    permission_classes = [
        IsAuthenticated,
        IsModerator,
    ]


class UserCreateAPIView(CreateAPIView):
    """
    API-представление для регистрации
    нового пользователя.

    Доступно без авторизации.
    """

    queryset = User.objects.all()
    serializer_class = UserCreateSerializer
    permission_classes = [
        AllowAny,
    ]


class UserRetrieveAPIView(RetrieveAPIView):
    """
    API-представление для получения
    информации о пользователе.

    Обычный пользователь может просматривать
    только собственную учётную запись.

    Администраторы и системные суперпользователи
    могут просматривать любую учётную запись.
    """

    queryset = User.objects.all()
    serializer_class = UserSerializer
    permission_classes = [
        IsAuthenticated,
        IsOwner,
    ]


class UserUpdateAPIView(UpdateAPIView):
    """
    API-представление для обновления
    данных пользователя.

    Обычный пользователь может изменять
    только собственную учётную запись.

    Администраторы и системные суперпользователи
    могут изменять любую учётную запись.
    """

    queryset = User.objects.all()
    serializer_class = UserUpdateSerializer
    permission_classes = [
        IsAuthenticated,
        IsOwner,
    ]


class UserDeleteAPIView(DestroyAPIView):
    """
    API-представление для удаления
    пользователя.

    Доступ предоставляется:

    - пользователям с ролью администратора;
    - системным суперпользователям Django.
    """

    queryset = User.objects.all()
    permission_classes = [
        IsAuthenticated,
        IsAdmin,
    ]

    def perform_destroy(self, instance):
        """
        Удаляет выбранного пользователя.

        Запрещает администратору или
        суперпользователю удалить самого себя
        через этот endpoint.
        """

        if instance.pk == self.request.user.pk:
            from rest_framework.exceptions import PermissionDenied

            raise PermissionDenied(
                "Нельзя удалить собственную "
                "учётную запись через этот endpoint."
            )

        instance.delete()


class UserTokenObtainPairView(TokenObtainPairView):
    """
    API-представление для получения
    JWT access и refresh токенов.
    """

    serializer_class = UserTokenObtainSerializer
    permission_classes = [
        AllowAny,
    ]


class ProfileRetrieveAPIView(
    UserOwnedQuerySetMixin,
    RetrieveAPIView,
):
    """
    API-представление для получения
    профиля пользователя.

    Обычный пользователь может просматривать
    только собственный профиль.

    Администраторы и системные суперпользователи
    могут просматривать любой профиль.
    """

    queryset = Profile.objects.select_related(
        "user",
    )
    serializer_class = ProfileSerializer
    permission_classes = [
        IsAuthenticated,
        IsOwner,
    ]


class ProfileUpdateAPIView(
    UserOwnedQuerySetMixin,
    UpdateAPIView,
):
    """
    API-представление для изменения
    профиля пользователя.

    Обычный пользователь может изменять
    только собственный профиль.

    Администраторы и системные суперпользователи
    могут изменять любой профиль.
    """

    queryset = Profile.objects.select_related(
        "user",
    )
    serializer_class = ProfileUpdateSerializer
    permission_classes = [
        IsAuthenticated,
        IsOwner,
    ]


class SearchHistoryListAPIView(
    UserOwnedQuerySetMixin,
    ListAPIView,
):
    """
    API-представление для получения
    истории поисковых запросов.

    Обычный пользователь получает только
    собственную историю поиска.

    Администраторы и системные суперпользователи
    получают историю всех пользователей.
    """

    queryset = SearchHistory.objects.select_related(
        "user",
    )
    serializer_class = SearchHistorySerializer
    permission_classes = [
        IsAuthenticated,
    ]


class RepairHistoryListAPIView(
    UserOwnedQuerySetMixin,
    ListAPIView,
):
    """
    API-представление для получения
    истории ремонтов.

    Обычный пользователь получает только
    собственную историю ремонтов.

    Администраторы и системные суперпользователи
    получают историю всех пользователей.
    """

    queryset = RepairHistory.objects.select_related(
        "user",
        "instruction",
    )
    serializer_class = RepairHistorySerializer
    permission_classes = [
        IsAuthenticated,
    ]


class RepairHistoryCreateAPIView(CreateAPIView):
    """
    API-представление для создания
    записи истории ремонта.

    Доступно активным авторизованным
    пользователям.
    """

    queryset = RepairHistory.objects.all()
    serializer_class = RepairHistoryCreateSerializer
    permission_classes = [
        IsAuthenticated,
    ]

    def perform_create(self, serializer):
        """
        Создаёт запись истории ремонта
        для текущего пользователя.

        Значение поля user, переданное клиентом,
        игнорируется.
        """

        serializer.save(
            user=self.request.user,
        )


class RepairHistoryRetrieveAPIView(
    UserOwnedQuerySetMixin,
    RetrieveAPIView,
):
    """
    API-представление для получения
    отдельной записи истории ремонта.

    Обычный пользователь может просматривать
    только собственные записи.

    Администраторы и системные суперпользователи
    могут просматривать любые записи.
    """

    queryset = RepairHistory.objects.select_related(
        "user",
        "instruction",
    )
    serializer_class = RepairHistorySerializer
    permission_classes = [
        IsAuthenticated,
        IsOwner,
    ]


class RepairHistoryUpdateAPIView(
    UserOwnedQuerySetMixin,
    UpdateAPIView,
):
    """
    API-представление для изменения
    записи истории ремонта.

    Обычный пользователь может изменять
    только собственные записи.

    Администраторы и системные суперпользователи
    могут изменять любые записи.
    """

    queryset = RepairHistory.objects.select_related(
        "user",
        "instruction",
    )
    serializer_class = RepairHistoryUpdateSerializer
    permission_classes = [
        IsAuthenticated,
        IsOwner,
    ]

    def perform_update(self, serializer):
        """
        Обновляет запись, не позволяя
        изменить её владельца через API.
        """

        serializer.save(
            user=self.get_object().user,
        )


class RepairHistoryDeleteAPIView(
    UserOwnedQuerySetMixin,
    DestroyAPIView,
):
    """
    API-представление для удаления
    записи истории ремонта.

    Обычный пользователь может удалять
    только собственные записи.

    Администраторы и системные суперпользователи
    могут удалять любые записи.
    """

    queryset = RepairHistory.objects.select_related(
        "user",
        "instruction",
    )
    permission_classes = [
        IsAuthenticated,
        IsOwner,
    ]
    