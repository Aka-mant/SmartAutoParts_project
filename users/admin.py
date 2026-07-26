from django.contrib import admin

from .models import (
    Profile,
    RepairHistory,
    SearchHistory,
    User,
    UserAgreementAcceptance,
)


@admin.register(User)
class UserAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "email",
        "username",
        "role",
        "is_staff",
        "is_superuser",
        "is_active",
    )
    list_filter = ("role", "is_staff", "is_superuser", "is_active")
    search_fields = ("email", "username", "first_name", "last_name")
    readonly_fields = ("created_at", "updated_at")
    ordering = ("-created_at",)


@admin.register(Profile)
class ProfileAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "user",
        "country",
        "city",
        "car_brand",
        "car_model",
        "car_year",
    )
    search_fields = (
        "user__email",
        "user__username",
        "car_brand",
        "car_model",
    )
    autocomplete_fields = ("user",)


@admin.register(SearchHistory)
class SearchHistoryAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "user",
        "original_number",
        "search_query",
        "result_found",
        "searched_at",
    )
    search_fields = ("user__email", "original_number", "search_query")
    list_filter = ("result_found", "searched_at")
    readonly_fields = ("searched_at",)
    autocomplete_fields = ("user",)


@admin.register(RepairHistory)
class RepairHistoryAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "user",
        "instruction",
        "current_step",
        "completed",
        "created_at",
    )
    list_filter = ("completed", "created_at")
    search_fields = ("user__email", "instruction__title", "notes")
    autocomplete_fields = ("user", "instruction")
    readonly_fields = ("created_at",)


@admin.register(UserAgreementAcceptance)
class UserAgreementAcceptanceAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "user",
        "agreement_version",
        "accepted_at",
        "ip_address",
    )
    list_filter = ("agreement_version", "accepted_at")
    search_fields = ("user__email", "user__username", "ip_address")
    readonly_fields = (
        "user",
        "agreement_version",
        "accepted_at",
        "ip_address",
        "user_agent",
    )
    ordering = ("-accepted_at",)
