from django.urls import path

from .apps import PartsConfig
from .views import (
    PartListAPIView,
    PartCreateAPIView,
    PartRetrieveAPIView,
    PartUpdateAPIView,
    PartDeleteAPIView,
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
]