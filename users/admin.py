from django.contrib import admin

from django.utils.translation import gettext_lazy as _

from apps.instructions.models import Instruction
from .models import User, Profile, SearchHistory, RepairHistory


@admin.register(User)
class UserAdmin(admin.ModelAdmin):
    """
    Настройки отображения модели User в административной панели.
    """
    list_display = (
        'id',
        'email',
        'username',
        'first_name',
        'last_name',
        'role',
        'is_staff',
        'is_superuser',
        'is_active',
        'phone',
    )
    list_filter = (
        'role',
        'is_staff',
        'is_superuser',
        'created_at',
    )
    search_fields = ('email', 'username', 'first_name', 'last_name', 'phone')
    ordering = ('-created_at',)
    readonly_fields = ('created_at', 'updated_at')

    fieldsets = (
        (_('Личные данные'), {
            'fields': ('email', 'username', 'first_name', 'last_name', 'phone', 'avatar'),
        }),
        (_('Роли и права'), {
            'fields': ('role', 'is_staff', 'is_superuser'),
        }),
        (_('Даты'), {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',),
        }),
    )

@admin.register(Profile)
class ProfileAdmin(admin.ModelAdmin):
    """
    Настройки отображения модели Profile в административной панели.
    """

    list_display = (
        "id",
        "user",
        "country",
        "city",
        "preferred_language",
        "car_brand",
        "car_model",
        "car_year",
    )

    list_display_links = (
        "id",
        "user",
    )

    search_fields = (
        "user__email",
        "user__username",
        "country",
        "city",
        "car_brand",
        "car_model",
    )

    list_filter = (
        "country",
        "city",
        "preferred_language",
        "car_brand",
    )

    ordering = (
        "id",
    )

    autocomplete_fields = (
        "user",
    )

    list_per_page = 25

    fieldsets = (
        (
            _("User"),
            {
                "fields": (
                    "user",
                )
            },
        ),
        (
            _("Location"),
            {
                "fields": (
                    "country",
                    "city",
                )
            },
        ),
        (
            _("Preferences"),
            {
                "fields": (
                    "preferred_language",
                )
            },
        ),
        (
            _("Car information"),
            {
                "fields": (
                    "car_brand",
                    "car_model",
                    "car_year",
                )
            },
        ),
        (
            _("Biography"),
            {
                "fields": (
                    "bio",
                )
            },
        ),
    )

@admin.register(SearchHistory)
class SearchHistoryAdmin(admin.ModelAdmin):
    """
    Настройки отображения модели SearchHistory
    в административной панели.
    """

    list_display = (
        "id",
        "user",
        "original_number",
        "search_query",
        "result_found",
        "searched_at",
    )

    list_display_links = (
        "id",
        "search_query",
    )

    search_fields = (
        "user__email",
        "user__username",
        "original_number",
        "search_query",
    )

    list_filter = (
        "result_found",
        "searched_at",
    )

    ordering = (
        "-searched_at",
    )

    readonly_fields = (
        "searched_at",
    )

    autocomplete_fields = (
        "user",
    )

    list_per_page = 25

    date_hierarchy = "searched_at"

    fieldsets = (
        (
            _("User"),
            {
                "fields": (
                    "user",
                ),
            },
        ),
        (
            _("Search information"),
            {
                "fields": (
                    "original_number",
                    "search_query",
                    "result_found",
                ),
            },
        ),
        (
            _("Service information"),
            {
                "fields": (
                    "searched_at",
                ),
            },
        ),
    )


@admin.register(RepairHistory)
class RepairHistoryAdmin(admin.ModelAdmin):
    """
    Административная панель модели истории ремонтов.
    """

    list_display = (
        "id",
        "user",
        "instruction",
        "completed",
        "created_at",
    )

    list_display_links = (
        "id",
        "instruction",
    )

    list_filter = (
        "completed",
        "created_at",
    )

    search_fields = (
        "user__email",
        "user__username",
        "instruction__title",
        "notes",
    )

    readonly_fields = (
        "created_at",
    )

    autocomplete_fields = (
        "user",
        "instruction",
    )

    ordering = (
        "-created_at",
    )

    fieldsets = (
        (
            None,
            {
                "fields": (
                    "user",
                    "instruction",
                    "completed",
                )
            },
        ),
        (
            _("Additional information"),
            {
                "fields": (
                    "notes",
                )
            },
        ),
        (
            _("System information"),
            {
                "fields": (
                    "created_at",
                )
            },
        ),
    )


@admin.register(Instruction)
class InstructionAdmin(admin.ModelAdmin):
    """
    Административная панель инструкций по ремонту.
    """

    list_display = (
        "id",
        "title",
        "part",
        "difficulty",
        "estimated_time",
        "premium_only",
        "version",
        "created_by",
        "created_at",
        "updated_at",
    )

    list_display_links = (
        "id",
        "title",
    )

    list_filter = (
        "premium_only",
        "difficulty",
        "created_at",
        "updated_at",
        "version",
    )

    search_fields = (
        "title",
        "slug",
        "short_description",
        "content",
        "part__name",
        "created_by__email",
        "created_by__username",
    )

    readonly_fields = (
        "version",
        "created_at",
        "updated_at",
    )

    autocomplete_fields = (
        "part",
        "created_by",
    )

    prepopulated_fields = {
        "slug": (
            "title",
        ),
    }

    ordering = (
        "title",
    )

    fieldsets = (
        (
            _("Main information"),
            {
                "fields": (
                    "part",
                    "title",
                    "slug",
                    "short_description",
                    "content",
                )
            },
        ),
        (
            _("Repair parameters"),
            {
                "fields": (
                    "difficulty",
                    "estimated_time",
                    "premium_only",
                    "version",
                )
            },
        ),
        (
            _("Author and dates"),
            {
                "fields": (
                    "created_by",
                    "created_at",
                    "updated_at",
                )
            },
        ),
    )

    def save_model(self, request, obj, form, change):
        """
        Автоматически назначает автора
        при создании инструкции.
        """
        if not obj.created_by:
            obj.created_by = request.user

        super().save_model(
            request,
            obj,
            form,
            change,
        )

