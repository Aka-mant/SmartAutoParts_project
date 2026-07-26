from django.urls import path
from rest_framework_simplejwt.views import TokenRefreshView

from .apps import UsersConfig
from .views import (
    ProfileDetailView,
    ProfileRetrieveAPIView,
    ProfileUpdateAPIView,
    ProfileUpdatePageView,
    RepairHistoryCreateAPIView,
    RepairHistoryDeleteAPIView,
    RepairHistoryListAPIView,
    RepairHistoryPageView,
    RepairStepNavigationView,
    RepairHistoryRetrieveAPIView,
    RepairHistoryUpdateAPIView,
    SearchHistoryListAPIView,
    SearchHistoryPageView,
    UserCreateAPIView,
    UserDashboardView,
    UserDeleteAPIView,
    UserListAPIView,
    UserLoginView,
    UserLogoutView,
    UserRegistrationPageView,
    UserAgreementView,
    UserRetrieveAPIView,
    UserTokenObtainPairView,
    UserUpdateAPIView,
    PartSearchPageView,
)


app_name = UsersConfig.name


urlpatterns = [
    path(
        "user-agreement/",
        UserAgreementView.as_view(),
        name="user_agreement",
    ),

    # HTML-аутентификация
    path(
        "login/",
        UserLoginView.as_view(),
        name="login",
    ),
    path(
        "logout/",
        UserLogoutView.as_view(),
        name="logout",
    ),

    # Регистрация
    path(
        "register/",
        UserRegistrationPageView.as_view(),
        name="register",
    ),

    # Dashboard
    path(
        "dashboard/",
        UserDashboardView.as_view(),
        name="dashboard",
    ),
# Поиск запчастей
    path(
        "search/",
        PartSearchPageView.as_view(),
        name="part_search",
    ),

    # HTML-страницы личного кабинета
    path(
        "profile/",
        ProfileDetailView.as_view(),
        name="profile_detail",
    ),
    path(
        "profile/edit/",
        ProfileUpdatePageView.as_view(),
        name="profile_update",
    ),
    path(
        "search-history/",
        SearchHistoryPageView.as_view(),
        name="search_history",
    ),
    path(
        "repair-history/",
        RepairHistoryPageView.as_view(),
        name="repair_history_list",
    ),
    path(
        "repair-history/<int:pk>/step/",
        RepairStepNavigationView.as_view(),
        name="repair_step_navigation",
    ),

    # JWT-аутентификация
    path(
        "api/token/",
        UserTokenObtainPairView.as_view(),
        name="token_obtain_pair",
    ),
    path(
        "api/token/refresh/",
        TokenRefreshView.as_view(),
        name="token_refresh",
    ),

    # API пользователей
    path(
        "api/register/",
        UserCreateAPIView.as_view(),
        name="user_register",
    ),
    path(
        "api/",
        UserListAPIView.as_view(),
        name="user_list",
    ),
    path(
        "api/me/",
        UserUpdateAPIView.as_view(),
        name="user_update",
    ),
    path(
        "api/<int:pk>/",
        UserRetrieveAPIView.as_view(),
        name="user_detail",
    ),
    path(
        "api/<int:pk>/delete/",
        UserDeleteAPIView.as_view(),
        name="user_delete",
    ),

    # API профиля
    path(
        "api/profile/",
        ProfileRetrieveAPIView.as_view(),
        name="api_profile_detail",
    ),
    path(
        "api/profile/update/",
        ProfileUpdateAPIView.as_view(),
        name="api_profile_update",
    ),

    # API истории поиска
    path(
        "api/search-history/",
        SearchHistoryListAPIView.as_view(),
        name="api_search_history",
    ),

    # API истории ремонта
    path(
        "api/repair-history/",
        RepairHistoryListAPIView.as_view(),
        name="api_repair_history_list",
    ),
    path(
        "api/repair-history/create/",
        RepairHistoryCreateAPIView.as_view(),
        name="repair_history_create",
    ),
    path(
        "api/repair-history/<int:pk>/",
        RepairHistoryRetrieveAPIView.as_view(),
        name="repair_history_detail",
    ),
    path(
        "api/repair-history/<int:pk>/update/",
        RepairHistoryUpdateAPIView.as_view(),
        name="repair_history_update",
    ),
    path(
        "api/repair-history/<int:pk>/delete/",
        RepairHistoryDeleteAPIView.as_view(),
        name="repair_history_delete",
    ),
]
