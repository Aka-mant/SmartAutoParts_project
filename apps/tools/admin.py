from django.contrib import admin

from .models import PartTool, Tool, ToolCategory, ToolImage


class ToolImageInline(admin.TabularInline):
    """Позволяет редактировать галерею в карточке инструмента."""

    model = ToolImage
    extra = 0
    fields = ("image", "alt_text", "is_main", "uploaded_at")
    readonly_fields = ("uploaded_at",)


@admin.register(ToolCategory)
class ToolCategoryAdmin(admin.ModelAdmin):
    list_display = ("id", "name", "slug")
    search_fields = ("name",)
    prepopulated_fields = {"slug": ("name",)}


@admin.register(Tool)
class ToolAdmin(admin.ModelAdmin):
    list_display = ("id", "name", "category", "size", "created_at")
    list_filter = ("category",)
    search_fields = ("name", "description", "size")
    autocomplete_fields = ("category",)
    readonly_fields = ("created_at",)
    inlines = (ToolImageInline,)


@admin.register(ToolImage)
class ToolImageAdmin(admin.ModelAdmin):
    """Управляет дополнительными изображениями инструментов."""

    list_display = ("id", "tool", "is_main", "uploaded_at")
    list_filter = ("is_main", "uploaded_at")
    search_fields = ("tool__name", "alt_text")
    autocomplete_fields = ("tool",)
    readonly_fields = ("uploaded_at",)


@admin.register(PartTool)
class PartToolAdmin(admin.ModelAdmin):
    list_display = ("id", "part", "tool", "required")
    list_filter = ("required",)
    search_fields = (
        "part__name",
        "part__original_number",
        "tool__name",
    )
    autocomplete_fields = ("part", "tool")
