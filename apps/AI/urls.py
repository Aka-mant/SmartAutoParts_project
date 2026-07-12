from django.urls import path

from .apps import AIConfig
from .views import (
    # AIRequest
    AIRequestListAPIView,
    AIRequestCreateAPIView,
    AIRequestRetrieveAPIView,
    AIRequestUpdateAPIView,
    AIRequestDeleteAPIView,

    # AIGeneratedInstruction
    AIGeneratedInstructionListAPIView,
    AIGeneratedInstructionCreateAPIView,
    AIGeneratedInstructionRetrieveAPIView,
    AIGeneratedInstructionUpdateAPIView,
    AIGeneratedInstructionDeleteAPIView,

    # AIImageAnalysis
    AIImageAnalysisListAPIView,
    AIImageAnalysisCreateAPIView,
    AIImageAnalysisRetrieveAPIView,
    AIImageAnalysisUpdateAPIView,
    AIImageAnalysisDeleteAPIView,
)

app_name = AIConfig.name

urlpatterns = [
    # ==========================
    # AI-запросы
    # ==========================
    path(
        "requests/",
        AIRequestListAPIView.as_view(),
        name="ai_request_list",
    ),
    path(
        "requests/create/",
        AIRequestCreateAPIView.as_view(),
        name="ai_request_create",
    ),
    path(
        "requests/<int:pk>/",
        AIRequestRetrieveAPIView.as_view(),
        name="ai_request_detail",
    ),
    path(
        "requests/<int:pk>/update/",
        AIRequestUpdateAPIView.as_view(),
        name="ai_request_update",
    ),
    path(
        "requests/<int:pk>/delete/",
        AIRequestDeleteAPIView.as_view(),
        name="ai_request_delete",
    ),

    # ==========================
    # AI-сгенерированные инструкции
    # ==========================
    path(
        "generated-instructions/",
        AIGeneratedInstructionListAPIView.as_view(),
        name="generated_instruction_list",
    ),
    path(
        "generated-instructions/create/",
        AIGeneratedInstructionCreateAPIView.as_view(),
        name="generated_instruction_create",
    ),
    path(
        "generated-instructions/<int:pk>/",
        AIGeneratedInstructionRetrieveAPIView.as_view(),
        name="generated_instruction_detail",
    ),
    path(
        "generated-instructions/<int:pk>/update/",
        AIGeneratedInstructionUpdateAPIView.as_view(),
        name="generated_instruction_update",
    ),
    path(
        "generated-instructions/<int:pk>/delete/",
        AIGeneratedInstructionDeleteAPIView.as_view(),
        name="generated_instruction_delete",
    ),

    # ==========================
    # AI-анализ изображений
    # ==========================
    path(
        "image-analyses/",
        AIImageAnalysisListAPIView.as_view(),
        name="image_analysis_list",
    ),
    path(
        "image-analyses/create/",
        AIImageAnalysisCreateAPIView.as_view(),
        name="image_analysis_create",
    ),
    path(
        "image-analyses/<int:pk>/",
        AIImageAnalysisRetrieveAPIView.as_view(),
        name="image_analysis_detail",
    ),
    path(
        "image-analyses/<int:pk>/update/",
        AIImageAnalysisUpdateAPIView.as_view(),
        name="image_analysis_update",
    ),
    path(
        "image-analyses/<int:pk>/delete/",
        AIImageAnalysisDeleteAPIView.as_view(),
        name="image_analysis_delete",
    ),
]
