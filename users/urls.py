from django.urls import path
from rest_framework_simplejwt.views import TokenRefreshView

from .apps import UsersConfig
from .views import (
    ProfileRetrieveAPIView,
    ProfileUpdateAPIView,
    RepairHistoryCreateAPIView,
    RepairHistoryDeleteAPIView,
    RepairHistoryListAPIView,
    RepairHistoryRetrieveAPIView,
    RepairHistoryUpdateAPIView,
    SearchHistoryListAPIView,
    UserCreateAPIView,
    UserDeleteAPIView,
    UserListAPIView,
    UserRetrieveAPIView,
    UserTokenObtainPairView,
    UserUpdateAPIView,
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
        "<int:pk>/",
        UserRetrieveAPIView.as_view(),
        name="user_detail",
    ),
    path(
        "<int:pk>/update/",
        UserUpdateAPIView.as_view(),
        name="user_update",
    ),
    path(
        "<int:pk>/delete/",
        UserDeleteAPIView.as_view(),
        name="user_delete",
    ),

    # Профили
    path(
        "profiles/<int:pk>/",
        ProfileRetrieveAPIView.as_view(),
        name="profile_detail",
    ),
    path(
        "profiles/<int:pk>/update/",
        ProfileUpdateAPIView.as_view(),
        name="profile_update",
    ),

    # История поиска
    path(
        "search-history/",
        SearchHistoryListAPIView.as_view(),
        name="search_history",
    ),

    # История ремонтов
    path(
        "repair-history/",
        RepairHistoryListAPIView.as_view(),
        name="repair_history_list",
    ),
    path(
        "repair-history/create/",
        RepairHistoryCreateAPIView.as_view(),
        name="repair_history_create",
    ),
    path(
        "repair-history/<int:pk>/",
        RepairHistoryRetrieveAPIView.as_view(),
        name="repair_history_detail",
    ),
    path(
        "repair-history/<int:pk>/update/",
        RepairHistoryUpdateAPIView.as_view(),
        name="repair_history_update",
    ),
    path(
        "repair-history/<int:pk>/delete/",
        RepairHistoryDeleteAPIView.as_view(),
        name="repair_history_delete",
    ),
]