from django.contrib import admin

from .models import PartTool, Tool, ToolCategory


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
