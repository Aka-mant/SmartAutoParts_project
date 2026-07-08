from django.contrib import admin
from .models import User, Profile
from django.utils.translation import gettext_lazy as _

@admin.register(User)
class UserAdmin(admin.ModelAdmin):
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

