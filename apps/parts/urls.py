from django.urls import path

from .apps import PartsConfig
from .views import (
    PartListAPIView,
    PartCreateAPIView,
    PartRetrieveAPIView,
    PartUpdateAPIView,
    PartDeleteAPIView,
    PartCategoryListAPIView,
    PartCategoryCreateAPIView,
    PartCategoryRetrieveAPIView,
    PartCategoryUpdateAPIView,
    PartCategoryDeleteAPIView,
)


app_name = PartsConfig.name


urlpatterns = [
    # Запчасти
    path(
        "",
        PartListAPIView.as_view(),
        name="part_list",
    ),
    path(
        "create/",
        PartCreateAPIView.as_view(),
        name="part_create",
    ),
    path(
        "<int:pk>/",
        PartRetrieveAPIView.as_view(),
        name="part_detail",
    ),
    path(
        "<int:pk>/update/",
        PartUpdateAPIView.as_view(),
        name="part_update",
    ),
    path(
        "<int:pk>/delete/",
        PartDeleteAPIView.as_view(),
        name="part_delete",
    ),
    # Категории запчастей
    path(
        "categories/",
        PartCategoryListAPIView.as_view(),
        name="part_category_list",
    ),
    path(
        "categories/create/",
        PartCategoryCreateAPIView.as_view(),
        name="part_category_create",
    ),
    path(
        "categories/<int:pk>/",
        PartCategoryRetrieveAPIView.as_view(),
        name="part_category_detail",
    ),
    path(
        "categories/<int:pk>/update/",
        PartCategoryUpdateAPIView.as_view(),
        name="part_category_update",
    ),
    path(
        "categories/<int:pk>/delete/",
        PartCategoryDeleteAPIView.as_view(),
        name="part_category_delete",
    ),
]