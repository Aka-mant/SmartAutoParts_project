from rest_framework.generics import (
    CreateAPIView,
    DestroyAPIView,
    ListAPIView,
    RetrieveAPIView,
    UpdateAPIView,
)
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework_simplejwt.views import TokenObtainPairView

from .mixins.mixins import UserOwnedQuerySetMixin
from .models import (
    Profile,
    RepairHistory,
    SearchHistory,
    User,
)
from .permissions import (
    IsModerator,
    IsOwner,
    IsSuperuser,
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

    Доступно модераторам и
    суперпользователям Django.
    """

    queryset = User.objects.all()
    serializer_class = UserSerializer
    permission_classes = [
        IsAuthenticated,
        IsModerator | IsSuperuser,
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

    Пользователь может просматривать
    только собственную учетную запись.

    Суперпользователь может
    просматривать любую учетную запись.
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

    Пользователь может изменять
    только собственную учетную запись.

    Суперпользователь может изменять
    любую учетную запись.
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

    Доступно только системному
    суперпользователю Django.
    """

    queryset = User.objects.all()
    permission_classes = [
        IsSuperuser,
    ]


class UserTokenObtainPairView(TokenObtainPairView):
    """
    API-представление для получения
    JWT access и refresh токенов.
    """

    serializer_class = UserTokenObtainSerializer
    permission_classes = [
        AllowAny,
    ]

    def post(self, request, *args, **kwargs):
        """
        Выполняет аутентификацию
        пользователя и выдает
        JWT-токены.
        """
        return super().post(
            request,
            *args,
            **kwargs,
        )

class ProfileRetrieveAPIView(
    UserOwnedQuerySetMixin,
    RetrieveAPIView,
):
    """
    API-представление для получения
    профиля пользователя.

    Пользователь может просматривать
    только собственный профиль.

    Суперпользователь может
    просматривать любой профиль.
    """

    queryset = Profile.objects.all()
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

    Пользователь может изменять
    только собственный профиль.

    Суперпользователь может
    изменять любой профиль.
    """

    queryset = Profile.objects.all()
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

    Пользователь может просматривать
    только собственную историю.

    Суперпользователь может
    просматривать всю историю.
    """

    queryset = SearchHistory.objects.all()
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

    Пользователь может просматривать
    только собственную историю.

    Суперпользователь может
    просматривать всю историю.
    """

    queryset = RepairHistory.objects.all()
    serializer_class = RepairHistorySerializer
    permission_classes = [
        IsAuthenticated,
    ]


class RepairHistoryCreateAPIView(CreateAPIView):
    """
    API-представление для создания
    записи истории ремонта.

    Доступно только авторизованным
    пользователям.
    """

    serializer_class = RepairHistoryCreateSerializer
    permission_classes = [
        IsAuthenticated,
    ]

    def perform_create(self, serializer):
        """
        Создает запись истории
        ремонта для текущего
        пользователя.
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
    записи истории ремонта.

    Пользователь может просматривать
    только собственные записи.

    Суперпользователь может
    просматривать любые записи.
    """

    queryset = RepairHistory.objects.all()
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

    Пользователь может изменять
    только собственные записи.

    Суперпользователь может
    изменять любые записи.
    """

    queryset = RepairHistory.objects.all()
    serializer_class = RepairHistoryUpdateSerializer
    permission_classes = [
        IsAuthenticated,
        IsOwner,
    ]


class RepairHistoryDeleteAPIView(
    UserOwnedQuerySetMixin,
    DestroyAPIView,
):
    """
    API-представление для удаления
    записи истории ремонта.

    Пользователь может удалять
    только собственные записи.

    Суперпользователь может
    удалять любые записи.
    """

    queryset = RepairHistory.objects.all()
    permission_classes = [
        IsAuthenticated,
        IsOwner,
    ]