from django.urls import path

from .apps import ToolsConfig
from .views import (
    # ToolCategory
    ToolCategoryListAPIView,
    ToolCategoryCreateAPIView,
    ToolCategoryRetrieveAPIView,
    ToolCategoryUpdateAPIView,
    ToolCategoryDeleteAPIView,

    # Tool
    ToolListAPIView,
    ToolCreateAPIView,
    ToolRetrieveAPIView,
    ToolUpdateAPIView,
    ToolDeleteAPIView,

    # PartTool
    PartToolListAPIView,
    PartToolCreateAPIView,
    PartToolRetrieveAPIView,
    PartToolUpdateAPIView,
    PartToolDeleteAPIView,
)

app_name = ToolsConfig.name

urlpatterns = [
    # ==========================
    # Категории инструментов
    # ==========================
    path(
        "categories/",
        ToolCategoryListAPIView.as_view(),
        name="tool_category_list",
    ),
    path(
        "categories/create/",
        ToolCategoryCreateAPIView.as_view(),
        name="tool_category_create",
    ),
    path(
        "categories/<int:pk>/",
        ToolCategoryRetrieveAPIView.as_view(),
        name="tool_category_detail",
    ),
    path(
        "categories/<int:pk>/update/",
        ToolCategoryUpdateAPIView.as_view(),
        name="tool_category_update",
    ),
    path(
        "categories/<int:pk>/delete/",
        ToolCategoryDeleteAPIView.as_view(),
        name="tool_category_delete",
    ),

    # ==========================
    # Инструменты
    # ==========================
    path(
        "",
        ToolListAPIView.as_view(),
        name="tool_list",
    ),
    path(
        "create/",
        ToolCreateAPIView.as_view(),
        name="tool_create",
    ),
    path(
        "<int:pk>/",
        ToolRetrieveAPIView.as_view(),
        name="tool_detail",
    ),
    path(
        "<int:pk>/update/",
        ToolUpdateAPIView.as_view(),
        name="tool_update",
    ),
    path(
        "<int:pk>/delete/",
        ToolDeleteAPIView.as_view(),
        name="tool_delete",
    ),

    # ==========================
    # Связи запчастей и инструментов
    # ==========================
    path(
        "part-tools/",
        PartToolListAPIView.as_view(),
        name="part_tool_list",
    ),
    path(
        "part-tools/create/",
        PartToolCreateAPIView.as_view(),
        name="part_tool_create",
    ),
    path(
        "part-tools/<int:pk>/",
        PartToolRetrieveAPIView.as_view(),
        name="part_tool_detail",
    ),
    path(
        "part-tools/<int:pk>/update/",
        PartToolUpdateAPIView.as_view(),
        name="part_tool_update",
    ),
    path(
        "part-tools/<int:pk>/delete/",
        PartToolDeleteAPIView.as_view(),
        name="part_tool_delete",
    ),
]