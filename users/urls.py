from django.urls import path
from rest_framework_simplejwt.views import TokenRefreshView

from .apps import UsersConfig
from .views import (
    UserListAPIView,
    UserCreateAPIView,
    UserRetrieveAPIView,
    UserUpdateAPIView,
    UserDeleteAPIView,
    UserTokenObtainPairView,
    ProfileRetrieveAPIView,
    ProfileUpdateAPIView,
    SearchHistoryListAPIView,
)

app_name = UsersConfig.name

urlpatterns = [
    # Аутентификация
    path(
        "token/",
        UserTokenObtainPairView.as_view(),
        name="token_obtain_pair",
    ),
    path(
        "token/refresh/",
        TokenRefreshView.as_view(),
        name="token_refresh",
    ),

    # Пользователи
    path(
        "register/",
        UserCreateAPIView.as_view(),
        name="user_register",
    ),
    path(
        "",
        UserListAPIView.as_view(),
        name="user_list",
    ),
    path(
        "me/",
        UserUpdateAPIView.as_view(),
        name="user_update",
    ),
    path(
        "<int:pk>/",
        UserRetrieveAPIView.as_view(),
        name="user_detail",
    ),
    path(
        "<int:pk>/delete/",
        UserDeleteAPIView.as_view(),
        name="user_delete",
    ),

    # Профиль
    path(
        "profile/",
        ProfileRetrieveAPIView.as_view(),
        name="profile_detail",
    ),
    path(
        "profile/update/",
        ProfileUpdateAPIView.as_view(),
        name="profile_update",
    ),

    # История поиска
    path(
        "search-history/",
        SearchHistoryListAPIView.as_view(),
        name="search_history",
    ),
]