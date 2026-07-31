from django.urls import path

from .views import (
    # PartCategory
    PartCategoryListAPIView,
    PartCategoryCreateAPIView,
    PartCategoryRetrieveAPIView,
    PartCategoryUpdateAPIView,
    PartCategoryDeleteAPIView,

    # Part
    PartListAPIView,
    PartCreateAPIView,
    PartRetrieveAPIView,
    PartUpdateAPIView,
    PartDeleteAPIView,

    # OEMNumber
    OEMNumberListAPIView,
    OEMNumberCreateAPIView,
    OEMNumberRetrieveAPIView,
    OEMNumberUpdateAPIView,
    OEMNumberDeleteAPIView,

    # Compatibility
    CompatibilityListAPIView,
    CompatibilityCreateAPIView,
    CompatibilityRetrieveAPIView,
    CompatibilityUpdateAPIView,
    CompatibilityDeleteAPIView,

    # PartImage
    PartImageListAPIView,
    PartImageCreateAPIView,
    PartImageRetrieveAPIView,
    PartImageUpdateAPIView,
    PartImageDeleteAPIView,

    # HTML
    PartDetailPageView,
    PartImageAnalysisResultView,
    PartImageAnalysisUploadView,
    PartInstructionRequestView,
    PartToolRecommendationRequestView,
    ToolRecommendationDetailView,
)

app_name = "parts_api"

api_urlpatterns = [
    # ==========================
    # Категории запчастей
    # ==========================
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

    # ==========================
    # Запчасти
    # ==========================
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

    # ==========================
    # OEM-номера
    # ==========================
    path(
        "oem-numbers/",
        OEMNumberListAPIView.as_view(),
        name="oem_number_list",
    ),
    path(
        "oem-numbers/create/",
        OEMNumberCreateAPIView.as_view(),
        name="oem_number_create",
    ),
    path(
        "oem-numbers/<int:pk>/",
        OEMNumberRetrieveAPIView.as_view(),
        name="oem_number_detail",
    ),
    path(
        "oem-numbers/<int:pk>/update/",
        OEMNumberUpdateAPIView.as_view(),
        name="oem_number_update",
    ),
    path(
        "oem-numbers/<int:pk>/delete/",
        OEMNumberDeleteAPIView.as_view(),
        name="oem_number_delete",
    ),

    # ==========================
    # Совместимость
    # ==========================
    path(
        "compatibilities/",
        CompatibilityListAPIView.as_view(),
        name="compatibility_list",
    ),
    path(
        "compatibilities/create/",
        CompatibilityCreateAPIView.as_view(),
        name="compatibility_create",
    ),
    path(
        "compatibilities/<int:pk>/",
        CompatibilityRetrieveAPIView.as_view(),
        name="compatibility_detail",
    ),
    path(
        "compatibilities/<int:pk>/update/",
        CompatibilityUpdateAPIView.as_view(),
        name="compatibility_update",
    ),
    path(
        "compatibilities/<int:pk>/delete/",
        CompatibilityDeleteAPIView.as_view(),
        name="compatibility_delete",
    ),

    # ==========================
    # Изображения запчастей
    # ==========================
    path(
        "images/",
        PartImageListAPIView.as_view(),
        name="part_image_list",
    ),
    path(
        "images/create/",
        PartImageCreateAPIView.as_view(),
        name="part_image_create",
    ),
    path(
        "images/<int:pk>/",
        PartImageRetrieveAPIView.as_view(),
        name="part_image_detail",
    ),
    path(
        "images/<int:pk>/update/",
        PartImageUpdateAPIView.as_view(),
        name="part_image_update",
    ),
    path(
        "images/<int:pk>/delete/",
        PartImageDeleteAPIView.as_view(),
        name="part_image_delete",
    ),
]

web_urlpatterns = [
    path(
        "image-analysis/",
        PartImageAnalysisUploadView.as_view(),
        name="image_analysis",
    ),
    path(
        "image-analysis/<int:pk>/",
        PartImageAnalysisResultView.as_view(),
        name="image_analysis_result",
    ),
    path(
        "<str:slug>/request-instruction/",
        PartInstructionRequestView.as_view(),
        name="request_instruction",
    ),
    path(
        "<str:slug>/request-tools/",
        PartToolRecommendationRequestView.as_view(),
        name="request_tools",
    ),
    path(
        "tool-recommendations/<int:pk>/",
        ToolRecommendationDetailView.as_view(),
        name="tool_recommendation_detail",
    ),
    path("<str:slug>/", PartDetailPageView.as_view(), name="detail"),
]

# Совместимость с прямым include("apps.parts.urls").
urlpatterns = api_urlpatterns
