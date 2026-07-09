from rest_framework.generics import (
    CreateAPIView,
    DestroyAPIView,
    ListAPIView,
    RetrieveAPIView,
    UpdateAPIView,
)
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework_simplejwt.views import TokenObtainPairView

from .models import User, Profile, SearchHistory
from .permissions import IsModerator, IsSuperuser
from .serializers import (
    UserCreateSerializer,
    UserSerializer,
    UserTokenObtainSerializer,
    UserUpdateSerializer,
    ProfileSerializer,
    ProfileUpdateSerializer,
    SearchHistorySerializer,
)


class UserListAPIView(ListAPIView):
    """
    API-представление для получения списка пользователей.

    Доступно модераторам и
    суперпользователям Django.
    """

    queryset = User.objects.all()
    serializer_class = UserSerializer
    permission_classes = [IsAuthenticated, IsModerator | IsSuperuser]


class UserCreateAPIView(CreateAPIView):
    """
    API-представление для регистрации
    нового пользователя.

    Доступно без авторизации.
    """

    queryset = User.objects.all()
    serializer_class = UserCreateSerializer
    permission_classes = [AllowAny]


class UserRetrieveAPIView(RetrieveAPIView):
    """
    API-представление для получения
    информации о пользователе.

    Доступно авторизованным
    пользователям.
    """

    queryset = User.objects.all()
    serializer_class = UserSerializer
    permission_classes = [IsAuthenticated]


class UserUpdateAPIView(UpdateAPIView):
    """
    API-представление для обновления
    данных текущего пользователя.

    Пользователь может изменять
    только собственную учетную запись.
    """

    serializer_class = UserUpdateSerializer
    permission_classes = [IsAuthenticated]

    def get_object(self):
        """
        Возвращает текущего
        авторизованного пользователя.
        """
        return self.request.user


class UserDeleteAPIView(DestroyAPIView):
    """
    API-представление для удаления
    пользователя.

    Доступно только системному
    суперпользователю Django.
    """

    queryset = User.objects.all()
    permission_classes = [IsSuperuser]


class UserTokenObtainPairView(TokenObtainPairView):
    """
    API-представление для получения
    JWT access и refresh токенов.
    """

    serializer_class = UserTokenObtainSerializer
    permission_classes = [AllowAny]

    def post(self, request, *args, **kwargs):
        """
        Выполняет аутентификацию
        пользователя и выдает JWT-токены.
        """
        return super().post(request, *args, **kwargs)


class ProfileRetrieveAPIView(RetrieveAPIView):
    """
    API-представление для получения
    профиля текущего пользователя.

    Доступно только авторизованным
    пользователям.
    """

    serializer_class = ProfileSerializer
    permission_classes = [IsAuthenticated]

    def get_object(self):
        """
        Возвращает профиль текущего
        авторизованного пользователя.
        """
        return self.request.user.profile


class ProfileUpdateAPIView(UpdateAPIView):
    """
    API-представление для изменения
    профиля текущего пользователя.

    Пользователь может изменять
    только собственный профиль.
    """

    serializer_class = ProfileUpdateSerializer
    permission_classes = [IsAuthenticated]

    def get_object(self):
        """
        Возвращает профиль текущего
        авторизованного пользователя.
        """
        return self.request.user.profile


class SearchHistoryListAPIView(ListAPIView):
    """
    API-представление для получения
    истории поисковых запросов
    текущего пользователя.

    Доступно только авторизованным
    пользователям.
    """

    serializer_class = SearchHistorySerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        """
        Возвращает историю поиска
        текущего пользователя.
        """
        return SearchHistory.objects.filter(
            user=self.request.user
        )