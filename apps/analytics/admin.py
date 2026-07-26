from django.contrib import admin

from .models import PopularPart, SearchLog, UserActivity


class SuperuserAnalyticsAdmin(admin.ModelAdmin):
    """Полностью скрывает аналитические данные от несуперпользователей."""

    def has_module_permission(self, request):
        return bool(request.user.is_active and request.user.is_superuser)

    def has_view_permission(self, request, obj=None):
        return bool(request.user.is_active and request.user.is_superuser)

    def has_add_permission(self, request):
        return bool(request.user.is_active and request.user.is_superuser)

    def has_change_permission(self, request, obj=None):
        return bool(request.user.is_active and request.user.is_superuser)

    def has_delete_permission(self, request, obj=None):
        return bool(request.user.is_active and request.user.is_superuser)


@admin.register(UserActivity)
class UserActivityAdmin(SuperuserAnalyticsAdmin):
    list_display = ("id", "user", "action", "created_at")
    list_filter = ("action", "created_at")
    search_fields = ("user__email", "action")
    autocomplete_fields = ("user",)
    readonly_fields = ("created_at",)


@admin.register(SearchLog)
class SearchLogAdmin(SuperuserAnalyticsAdmin):
    list_display = (
        "id",
        "user",
        "query",
        "results_count",
        "ip_address",
        "created_at",
    )
    list_filter = ("created_at",)
    search_fields = ("user__email", "query", "ip_address")
    autocomplete_fields = ("user",)
    readonly_fields = ("created_at",)


@admin.register(PopularPart)
class PopularPartAdmin(SuperuserAnalyticsAdmin):
    list_display = ("id", "part", "views_count", "searches_count")
    search_fields = ("part__name", "part__original_number")
    autocomplete_fields = ("part",)
