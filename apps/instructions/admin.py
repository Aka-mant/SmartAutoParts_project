from django.contrib import admin

from .models import (
    Instruction,
    InstructionImage,
    InstructionStep,
    InstructionTool,
    InstructionVersion,
)


class InstructionStepInline(admin.TabularInline):
    model = InstructionStep
    extra = 0
    ordering = ("step_number",)


class InstructionToolInline(admin.TabularInline):
    model = InstructionTool
    extra = 0


@admin.register(Instruction)
class InstructionAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "title",
        "part",
        "difficulty",
        "version",
        "is_published",
        "updated_at",
    )
    list_filter = ("is_published", "premium_only", "difficulty")
    search_fields = ("title", "part__name", "part__original_number")
    prepopulated_fields = {"slug": ("title",)}
    autocomplete_fields = ("part", "created_by", "updated_by")
    readonly_fields = ("created_at", "updated_at", "published_at")
    inlines = (InstructionStepInline, InstructionToolInline)


@admin.register(InstructionVersion)
class InstructionVersionAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "instruction",
        "version_number",
        "created_by",
        "created_at",
    )
    search_fields = ("instruction__title", "changelog")
    autocomplete_fields = ("instruction", "created_by")
    readonly_fields = ("created_at",)


@admin.register(InstructionStep)
class InstructionStepAdmin(admin.ModelAdmin):
    list_display = ("id", "instruction", "step_number", "title")
    ordering = ("instruction", "step_number")
    search_fields = ("instruction__title", "title", "description")
    autocomplete_fields = ("instruction",)


@admin.register(InstructionImage)
class InstructionImageAdmin(admin.ModelAdmin):
    list_display = ("id", "instruction", "description")
    autocomplete_fields = ("instruction",)


@admin.register(InstructionTool)
class InstructionToolAdmin(admin.ModelAdmin):
    list_display = ("id", "instruction", "tool", "usage_description")
    autocomplete_fields = ("instruction", "tool")
