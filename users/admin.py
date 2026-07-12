from django.contrib import admin

from django.utils.translation import gettext_lazy as _

from apps.instructions.models import Instruction, InstructionVersion, InstructionStep, InstructionImage, InstructionTool
from apps.parts.models import Part, PartCategory
from apps.tools.models import PartTool, Tool, ToolCategory
from apps.subscriptions.models import SubscriptionPayment, UserSubscription, SubscriptionPlan
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

@admin.register(InstructionVersion)
class InstructionVersionAdmin(admin.ModelAdmin):
    """
    Административная панель версий инструкций.
    """

    list_display = (
        "id",
        "instruction",
        "version_number",
        "created_at",
    )

    list_display_links = (
        "id",
        "instruction",
    )

    list_filter = (
        "created_at",
    )

    search_fields = (
        "instruction__title",
        "content",
        "changelog",
    )

    ordering = (
        "-version_number",
    )

    readonly_fields = (
        "created_at",
    )

    autocomplete_fields = (
        "instruction",
    )

    fieldsets = (
        (
            _("Version information"),
            {
                "fields": (
                    "instruction",
                    "version_number",
                    "content",
                    "changelog",
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


@admin.register(InstructionStep)
class InstructionStepAdmin(admin.ModelAdmin):
    """
    Административная панель шагов инструкции.
    """

    list_display = (
        "id",
        "instruction",
        "step_number",
        "title",
        "estimated_minutes",
    )

    list_display_links = (
        "id",
        "title",
    )

    list_filter = (
        "instruction",
    )

    search_fields = (
        "instruction__title",
        "title",
        "description",
        "warning",
    )

    ordering = (
        "instruction",
        "step_number",
    )

    autocomplete_fields = (
        "instruction",
    )

    fieldsets = (
        (
            _("Step information"),
            {
                "fields": (
                    "instruction",
                    "step_number",
                    "title",
                    "description",
                    "warning",
                    "estimated_minutes",
                )
            },
        ),
    )


@admin.register(InstructionImage)
class InstructionImageAdmin(admin.ModelAdmin):
    """
    Административная панель изображений инструкции.
    """

    list_display = (
        "id",
        "instruction",
        "image",
    )

    list_display_links = (
        "id",
        "instruction",
    )

    search_fields = (
        "instruction__title",
        "description",
    )

    autocomplete_fields = (
        "instruction",
    )

    fieldsets = (
        (
            _("Image information"),
            {
                "fields": (
                    "instruction",
                    "image",
                    "description",
                )
            },
        ),
    )


@admin.register(InstructionTool)
class InstructionToolAdmin(admin.ModelAdmin):
    """
    Административная панель инструментов инструкции.
    """

    list_display = (
        "id",
        "instruction",
        "tool",
    )

    list_display_links = (
        "id",
        "instruction",
    )

    list_filter = (
        "tool",
    )

    search_fields = (
        "instruction__title",
        "tool__name",
        "usage_description",
    )

    autocomplete_fields = (
        "instruction",
        "tool",
    )

    fieldsets = (
        (
            _("Tool information"),
            {
                "fields": (
                    "instruction",
                    "tool",
                    "usage_description",
                )
            },
        ),
    )

@admin.register(Part)
class PartAdmin(admin.ModelAdmin):
    """
    Административная панель автомобильных запчастей.
    """

    list_display = (
        "id",
        "name",
        "original_number",
        "manufacturer",
        "category",
        "weight",
        "is_active",
        "created_at",
        "updated_at",
    )

    list_display_links = (
        "id",
        "name",
    )

    list_filter = (
        "is_active",
        "manufacturer",
        "category",
        "created_at",
        "updated_at",
    )

    search_fields = (
        "name",
        "original_number",
        "slug",
        "manufacturer",
        "description",
        "category__name",
    )

    readonly_fields = (
        "created_at",
        "updated_at",
    )

    autocomplete_fields = (
        "category",
    )

    prepopulated_fields = {
        "slug": (
            "name",
        ),
    }

    ordering = (
        "name",
    )

    list_editable = (
        "is_active",
    )

    fieldsets = (
        (
            _("Main information"),
            {
                "fields": (
                    "category",
                    "name",
                    "slug",
                    "original_number",
                    "manufacturer",
                    "description",
                )
            },
        ),
        (
            _("SEO information"),
            {
                "fields": (
                    "seo_title",
                    "seo_description",
                    "seo_keywords",
                )
            },
        ),
        (
            _("Physical parameters"),
            {
                "fields": (
                    "weight",
                    "dimensions",
                )
            },
        ),
        (
            _("Status"),
            {
                "fields": (
                    "is_active",
                )
            },
        ),
        (
            _("System information"),
            {
                "fields": (
                    "created_at",
                    "updated_at",
                )
            },
        ),
    )

@admin.register(PartCategory)
class PartCategoryAdmin(admin.ModelAdmin):
    """
    Административная панель категорий запчастей.
    """

    list_display = (
        "id",
        "name",
        "slug",
    )

    list_display_links = (
        "id",
        "name",
    )

    search_fields = (
        "name",
        "slug",
        "description",
    )

    ordering = (
        "name",
    )

    prepopulated_fields = {
        "slug": (
            "name",
        ),
    }

    fieldsets = (
        (
            _("Main information"),
            {
                "fields": (
                    "name",
                    "slug",
                    "description",
                )
            },
        ),
    )

@admin.register(ToolCategory)
class ToolCategoryAdmin(admin.ModelAdmin):
    """
    Административная панель категорий
    инструментов.
    """

    list_display = (
        "id",
        "name",
        "slug",
    )

    list_display_links = (
        "id",
        "name",
    )

    search_fields = (
        "name",
        "slug",
    )

    ordering = (
        "name",
    )

    prepopulated_fields = {
        "slug": (
            "name",
        ),
    }

    fieldsets = (
        (
            _("Main information"),
            {
                "fields": (
                    "name",
                    "slug",
                ),
            },
        ),
    )


@admin.register(Tool)
class ToolAdmin(admin.ModelAdmin):
    """
    Административная панель
    автомобильных инструментов.
    """

    list_display = (
        "id",
        "name",
        "category",
        "size",
        "has_image",
        "has_amazon_url",
        "created_at",
    )

    list_display_links = (
        "id",
        "name",
    )

    list_filter = (
        "category",
        "created_at",
    )

    search_fields = (
        "name",
        "description",
        "size",
        "category__name",
    )

    readonly_fields = (
        "created_at",
    )

    autocomplete_fields = (
        "category",
    )

    ordering = (
        "name",
    )

    fieldsets = (
        (
            _("Main information"),
            {
                "fields": (
                    "category",
                    "name",
                    "description",
                    "size",
                ),
            },
        ),
        (
            _("Image and external link"),
            {
                "fields": (
                    "image",
                    "amazon_url",
                ),
            },
        ),
        (
            _("System information"),
            {
                "fields": (
                    "created_at",
                ),
            },
        ),
    )

    @admin.display(
        boolean=True,
        description=_("Image"),
    )
    def has_image(self, obj):
        """
        Показывает наличие изображения
        инструмента.
        """
        return bool(obj.image)

    @admin.display(
        boolean=True,
        description=_("Amazon URL"),
    )
    def has_amazon_url(self, obj):
        """
        Показывает наличие ссылки
        на Amazon.
        """
        return bool(obj.amazon_url)


@admin.register(PartTool)
class PartToolAdmin(admin.ModelAdmin):
    """
    Административная панель связей
    между запчастями и инструментами.
    """

    list_display = (
        "id",
        "part",
        "tool",
        "required",
    )

    list_display_links = (
        "id",
        "part",
    )

    list_filter = (
        "required",
        "tool",
        "part",
    )

    search_fields = (
        "part__name",
        "part__original_number",
        "tool__name",
    )

    autocomplete_fields = (
        "part",
        "tool",
    )

    list_editable = (
        "required",
    )

    ordering = (
        "part",
        "tool",
    )

    fieldsets = (
        (
            _("Part and tool"),
            {
                "fields": (
                    "part",
                    "tool",
                    "required",
                ),
            },
        ),
    )

@admin.register(SubscriptionPlan)
class SubscriptionPlanAdmin(admin.ModelAdmin):
    """
    Административная панель
    тарифных планов подписки.
    """

    list_display = (
        "id",
        "name",
        "price",
        "duration_days",
        "max_ai_requests",
        "has_chat_access",
        "has_image_analysis",
        "created_at",
    )

    list_display_links = (
        "id",
        "name",
    )

    list_filter = (
        "has_chat_access",
        "has_image_analysis",
        "created_at",
    )

    search_fields = (
        "name",
        "description",
    )

    readonly_fields = (
        "created_at",
    )

    ordering = (
        "price",
    )

    fieldsets = (
        (
            _("General information"),
            {
                "fields": (
                    "name",
                    "description",
                ),
            },
        ),
        (
            _("Subscription settings"),
            {
                "fields": (
                    "price",
                    "duration_days",
                    "max_ai_requests",
                ),
            },
        ),
        (
            _("Features"),
            {
                "fields": (
                    "has_chat_access",
                    "has_image_analysis",
                ),
            },
        ),
        (
            _("System information"),
            {
                "fields": (
                    "created_at",
                ),
            },
        ),
    )


@admin.register(UserSubscription)
class UserSubscriptionAdmin(admin.ModelAdmin):
    """
    Административная панель
    пользовательских подписок.
    """

    list_display = (
        "id",
        "user",
        "plan",
        "start_date",
        "end_date",
        "is_active",
        "auto_renew",
    )

    list_display_links = (
        "id",
        "user",
    )

    list_filter = (
        "is_active",
        "auto_renew",
        "plan",
        "start_date",
        "end_date",
    )

    search_fields = (
        "user__email",
        "user__username",
        "plan__name",
    )

    autocomplete_fields = (
        "user",
        "plan",
    )

    ordering = (
        "-end_date",
    )

    fieldsets = (
        (
            _("Subscription"),
            {
                "fields": (
                    "user",
                    "plan",
                ),
            },
        ),
        (
            _("Period"),
            {
                "fields": (
                    "start_date",
                    "end_date",
                ),
            },
        ),
        (
            _("Status"),
            {
                "fields": (
                    "is_active",
                    "auto_renew",
                ),
            },
        ),
    )


@admin.register(SubscriptionPayment)
class SubscriptionPaymentAdmin(admin.ModelAdmin):
    """
    Административная панель
    платежей за подписки.
    """

    list_display = (
        "id",
        "user",
        "subscription",
        "provider",
        "amount",
        "currency",
        "status",
        "paid_at",
    )

    list_display_links = (
        "id",
        "user",
    )

    list_filter = (
        "provider",
        "status",
        "currency",
        "paid_at",
    )

    search_fields = (
        "user__email",
        "user__username",
        "provider",
        "external_payment_id",
    )

    autocomplete_fields = (
        "user",
        "subscription",
    )

    ordering = (
        "-paid_at",
        "-id",
    )

    fieldsets = (
        (
            _("Payment information"),
            {
                "fields": (
                    "user",
                    "subscription",
                    "provider",
                    "external_payment_id",
                ),
            },
        ),
        (
            _("Amount"),
            {
                "fields": (
                    "amount",
                    "currency",
                ),
            },
        ),
        (
            _("Status"),
            {
                "fields": (
                    "status",
                    "paid_at",
                ),
            },
        ),
    )
