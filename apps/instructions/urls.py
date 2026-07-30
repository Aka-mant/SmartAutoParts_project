from django.urls import path

from .views import (
    # Instruction
    InstructionListAPIView,
    InstructionCreateAPIView,
    InstructionRetrieveAPIView,
    InstructionUpdateAPIView,
    InstructionDeleteAPIView,

    # InstructionVersion
    InstructionVersionListAPIView,
    InstructionVersionCreateAPIView,
    InstructionVersionRetrieveAPIView,
    InstructionVersionUpdateAPIView,
    InstructionVersionDeleteAPIView,

    # InstructionStep
    InstructionStepListAPIView,
    InstructionStepCreateAPIView,
    InstructionStepRetrieveAPIView,
    InstructionStepUpdateAPIView,
    InstructionStepDeleteAPIView,

    # InstructionImage
    InstructionImageListAPIView,
    InstructionImageCreateAPIView,
    InstructionImageRetrieveAPIView,
    InstructionImageUpdateAPIView,
    InstructionImageDeleteAPIView,

    # InstructionTool
    InstructionToolListAPIView,
    InstructionToolCreateAPIView,
    InstructionToolRetrieveAPIView,
    InstructionToolUpdateAPIView,
    InstructionToolDeleteAPIView,

    # HTML
    InstructionDetailPageView,
    InstructionListPageView,
    InstructionRepairNavigateView,
    InstructionRepairSessionView,
    InstructionRepairStartView,
)

app_name = "instructions_api"

api_urlpatterns = [
    # ==========================
    # Instructions
    # ==========================
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

    # ==========================
    # Instruction versions
    # ==========================
    path(
        "versions/",
        InstructionVersionListAPIView.as_view(),
        name="instruction_version_list",
    ),
    path(
        "versions/create/",
        InstructionVersionCreateAPIView.as_view(),
        name="instruction_version_create",
    ),
    path(
        "versions/<int:pk>/",
        InstructionVersionRetrieveAPIView.as_view(),
        name="instruction_version_detail",
    ),
    path(
        "versions/<int:pk>/update/",
        InstructionVersionUpdateAPIView.as_view(),
        name="instruction_version_update",
    ),
    path(
        "versions/<int:pk>/delete/",
        InstructionVersionDeleteAPIView.as_view(),
        name="instruction_version_delete",
    ),

    # ==========================
    # Instruction steps
    # ==========================
    path(
        "steps/",
        InstructionStepListAPIView.as_view(),
        name="instruction_step_list",
    ),
    path(
        "steps/create/",
        InstructionStepCreateAPIView.as_view(),
        name="instruction_step_create",
    ),
    path(
        "steps/<int:pk>/",
        InstructionStepRetrieveAPIView.as_view(),
        name="instruction_step_detail",
    ),
    path(
        "steps/<int:pk>/update/",
        InstructionStepUpdateAPIView.as_view(),
        name="instruction_step_update",
    ),
    path(
        "steps/<int:pk>/delete/",
        InstructionStepDeleteAPIView.as_view(),
        name="instruction_step_delete",
    ),

    # ==========================
    # Instruction images
    # ==========================
    path(
        "images/",
        InstructionImageListAPIView.as_view(),
        name="instruction_image_list",
    ),
    path(
        "images/create/",
        InstructionImageCreateAPIView.as_view(),
        name="instruction_image_create",
    ),
    path(
        "images/<int:pk>/",
        InstructionImageRetrieveAPIView.as_view(),
        name="instruction_image_detail",
    ),
    path(
        "images/<int:pk>/update/",
        InstructionImageUpdateAPIView.as_view(),
        name="instruction_image_update",
    ),
    path(
        "images/<int:pk>/delete/",
        InstructionImageDeleteAPIView.as_view(),
        name="instruction_image_delete",
    ),

    # ==========================
    # Instruction tools
    # ==========================
    path(
        "tools/",
        InstructionToolListAPIView.as_view(),
        name="instruction_tool_list",
    ),
    path(
        "tools/create/",
        InstructionToolCreateAPIView.as_view(),
        name="instruction_tool_create",
    ),
    path(
        "tools/<int:pk>/",
        InstructionToolRetrieveAPIView.as_view(),
        name="instruction_tool_detail",
    ),
    path(
        "tools/<int:pk>/update/",
        InstructionToolUpdateAPIView.as_view(),
        name="instruction_tool_update",
    ),
    path(
        "tools/<int:pk>/delete/",
        InstructionToolDeleteAPIView.as_view(),
        name="instruction_tool_delete",
    ),
]

web_urlpatterns = [
    path("", InstructionListPageView.as_view(), name="list"),
    path(
        "repair/<int:pk>/",
        InstructionRepairSessionView.as_view(),
        name="repair",
    ),
    path(
        "repair/<int:pk>/navigate/",
        InstructionRepairNavigateView.as_view(),
        name="repair_navigate",
    ),
    path(
        "<str:slug>/start-repair/",
        InstructionRepairStartView.as_view(),
        name="start_repair",
    ),
    path(
        "<str:slug>/",
        InstructionDetailPageView.as_view(),
        name="detail",
    ),
]

# Совместимость с прямым include("apps.instructions.urls").
urlpatterns = api_urlpatterns
