from django.urls import path

from .apps import InstructionsConfig
from .views import (
    InstructionListAPIView,
    InstructionCreateAPIView,
    InstructionRetrieveAPIView,
    InstructionUpdateAPIView,
    InstructionDeleteAPIView,
)

app_name = InstructionsConfig.name


urlpatterns = [
    # Инструкции
    path(
        "",
        InstructionListAPIView.as_view(),
        name="instruction_list",
    ),
    path(
        "create/",
        InstructionCreateAPIView.as_view(),
        name="instruction_create",
    ),
    path(
        "<int:pk>/",
        InstructionRetrieveAPIView.as_view(),
        name="instruction_detail",
    ),
    path(
        "<int:pk>/update/",
        InstructionUpdateAPIView.as_view(),
        name="instruction_update",
    ),
    path(
        "<int:pk>/delete/",
        InstructionDeleteAPIView.as_view(),
        name="instruction_delete",
    ),
]

