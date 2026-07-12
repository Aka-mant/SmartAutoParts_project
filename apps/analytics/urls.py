from django.urls import path

from .apps import AnalyticsConfig
from .views import (
    # UserActivity
    UserActivityListAPIView,
    UserActivityCreateAPIView,
    UserActivityRetrieveAPIView,
    UserActivityUpdateAPIView,
    UserActivityDeleteAPIView,

    # SearchLog
    SearchLogListAPIView,
    SearchLogCreateAPIView,
    SearchLogRetrieveAPIView,
    SearchLogUpdateAPIView,
    SearchLogDeleteAPIView,

    # PopularPart
    PopularPartListAPIView,
    PopularPartCreateAPIView,
    PopularPartRetrieveAPIView,
    PopularPartUpdateAPIView,
    PopularPartDeleteAPIView,
)

app_name = AnalyticsConfig.name

urlpatterns = [
    # ==========================
    # Активность пользователей
    # ==========================
    path(
        "activities/",
        UserActivityListAPIView.as_view(),
        name="user_activity_list",
    ),
    path(
        "activities/create/",
        UserActivityCreateAPIView.as_view(),
        name="user_activity_create",
    ),
    path(
        "activities/<int:pk>/",
        UserActivityRetrieveAPIView.as_view(),
        name="user_activity_detail",
    ),
    path(
        "activities/<int:pk>/update/",
        UserActivityUpdateAPIView.as_view(),
        name="user_activity_update",
    ),
    path(
        "activities/<int:pk>/delete/",
        UserActivityDeleteAPIView.as_view(),
        name="user_activity_delete",
    ),

    # ==========================
    # Журнал поисковых запросов
    # ==========================
    path(
        "search-logs/",
        SearchLogListAPIView.as_view(),
        name="search_log_list",
    ),
    path(
        "search-logs/create/",
        SearchLogCreateAPIView.as_view(),
        name="search_log_create",
    ),
    path(
        "search-logs/<int:pk>/",
        SearchLogRetrieveAPIView.as_view(),
        name="search_log_detail",
    ),
    path(
        "search-logs/<int:pk>/update/",
        SearchLogUpdateAPIView.as_view(),
        name="search_log_update",
    ),
    path(
        "search-logs/<int:pk>/delete/",
        SearchLogDeleteAPIView.as_view(),
        name="search_log_delete",
    ),

    # ==========================
    # Популярные запчасти
    # ==========================
    path(
        "popular-parts/",
        PopularPartListAPIView.as_view(),
        name="popular_part_list",
    ),
    path(
        "popular-parts/create/",
        PopularPartCreateAPIView.as_view(),
        name="popular_part_create",
    ),
    path(
        "popular-parts/<int:pk>/",
        PopularPartRetrieveAPIView.as_view(),
        name="popular_part_detail",
    ),
    path(
        "popular-parts/<int:pk>/update/",
        PopularPartUpdateAPIView.as_view(),
        name="popular_part_update",
    ),
    path(
        "popular-parts/<int:pk>/delete/",
        PopularPartDeleteAPIView.as_view(),
        name="popular_part_delete",
    ),
]
