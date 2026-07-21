from django.contrib import admin
from django.utils.html import format_html
from django.utils.translation import gettext_lazy as _

from .models import (
    Compatibility,
    OEMNumber,
    Part,
    PartCategory,
    PartImage,
)


class OEMNumberInline(admin.TabularInline):
    """
    Встроенная административная форма OEM-номеров.

    Позволяет добавлять и редактировать дополнительные
    OEM-номера непосредственно на странице запчасти.
    """

    model = OEMNumber
    extra = 0
    fields = (
        "number",
        "manufacturer",
    )

    show_change_link = True


class CompatibilityInline(admin.TabularInline):
    """
    Встроенная административная форма совместимости.

    Позволяет управлять совместимостью запчасти
    с автомобилями непосредственно на странице запчасти.
    """

    model = Compatibility
    extra = 0
    fields = (
        "brand",
        "model",
        "generation",
        "engine",
        "year_from",
        "year_to",
    )

    show_change_link = True


class PartImageInline(admin.TabularInline):
    """
    Встроенная административная форма изображений.

    Позволяет добавлять изображения непосредственно
    на странице редактирования автомобильной запчасти.
    """

    model = PartImage
    extra = 0
    fields = (
        "image",
        "alt_text",
        "is_main",
        "image_preview",
        "uploaded_at",
    )

    readonly_fields = (
        "image_preview",
        "uploaded_at",
    )

    show_change_link = True

    @admin.display(description=_("Preview"))
    def image_preview(self, obj):
        """
        Возвращает уменьшенное изображение запчасти.
        """

        if obj.pk and obj.image:
            return format_html(
                '<img src="{}" '
                'alt="{}" '
                'style="width: 80px; '
                'height: 80px; '
                'object-fit: cover; '
                'border-radius: 8px;">',
                obj.image.url,
                obj.alt_text or obj.part.name,
            )

        return "—"


@admin.register(PartCategory)
class PartCategoryAdmin(admin.ModelAdmin):
    """
    Административная панель категорий запчастей.
    """

    list_display = (
        "id",
        "name",
        "slug",
        "parts_count",
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

    list_per_page = 25

    fieldsets = (
        (
            _("Main information"),
            {
                "fields": (
                    "name",
                    "slug",
                    "description",
                ),
            },
        ),
    )

    @admin.display(
        description=_("Parts count"),
        ordering="parts_count",
    )
    def parts_count(self, obj):
        """
        Возвращает количество запчастей категории.
        """

        return obj.parts.count()


@admin.register(Part)
class PartAdmin(admin.ModelAdmin):
    """
    Административная панель автомобильных запчастей.
    """

    list_display = (
        "id",
        "name",
        "original_number",
        "normalized_original_number",
        "manufacturer",
        "category",
        "weight",
        "images_count",
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
        "normalized_original_number",
        "slug",
        "manufacturer",
        "description",
        "category__name",
        "oem_numbers__number",
        "compatibilities__brand",
        "compatibilities__model",
    )

    readonly_fields = (
        "normalized_original_number",
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

    list_select_related = (
        "category",
    )

    list_per_page = 25

    inlines = (
        OEMNumberInline,
        CompatibilityInline,
        PartImageInline,
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
                    "normalized_original_number",
                    "manufacturer",
                    "description",
                ),
            },
        ),
        (
            _("SEO information"),
            {
                "fields": (
                    "seo_title",
                    "seo_description",
                    "seo_keywords",
                ),
                "classes": (
                    "collapse",
                ),
            },
        ),
        (
            _("Physical parameters"),
            {
                "fields": (
                    "weight",
                    "dimensions",
                ),
            },
        ),
        (
            _("Status"),
            {
                "fields": (
                    "is_active",
                ),
            },
        ),
        (
            _("System information"),
            {
                "fields": (
                    "created_at",
                    "updated_at",
                ),
                "classes": (
                    "collapse",
                ),
            },
        ),
    )

    @admin.display(
        description=_("Images"),
        ordering="images_count",
    )
    def images_count(self, obj):
        """
        Возвращает количество изображений запчасти.
        """

        return obj.images.count()

    def get_queryset(self, request):
        """
        Оптимизирует запрос списка запчастей.
        """

        queryset = super().get_queryset(request)

        return queryset.select_related(
            "category",
        ).prefetch_related(
            "images",
            "oem_numbers",
            "compatibilities",
        )


@admin.register(OEMNumber)
class OEMNumberAdmin(admin.ModelAdmin):
    """
    Административная панель OEM-номеров запчастей.
    """

    list_display = (
        "id",
        "number",
        "manufacturer",
        "part",
        "part_original_number",
    )

    list_display_links = (
        "id",
        "number",
    )

    list_filter = (
        "manufacturer",
    )

    search_fields = (
        "number",
        "manufacturer",
        "part__name",
        "part__original_number",
        "part__normalized_original_number",
    )

    autocomplete_fields = (
        "part",
    )

    list_select_related = (
        "part",
    )

    ordering = (
        "number",
    )

    list_per_page = 25

    fieldsets = (
        (
            _("OEM information"),
            {
                "fields": (
                    "part",
                    "number",
                    "manufacturer",
                ),
            },
        ),
    )

    @admin.display(
        description=_("Original number"),
        ordering="part__original_number",
    )
    def part_original_number(self, obj):
        """
        Возвращает основной OEM-номер запчасти.
        """

        return obj.part.original_number


@admin.register(Compatibility)
class CompatibilityAdmin(admin.ModelAdmin):
    """
    Административная панель совместимости запчастей.
    """

    list_display = (
        "id",
        "part",
        "brand",
        "model",
        "generation",
        "engine",
        "year_from",
        "year_to",
    )

    list_display_links = (
        "id",
        "part",
    )

    list_filter = (
        "brand",
        "model",
        "generation",
        "engine",
        "year_from",
        "year_to",
    )

    search_fields = (
        "part__name",
        "part__original_number",
        "brand",
        "model",
        "generation",
        "engine",
    )

    autocomplete_fields = (
        "part",
    )

    list_select_related = (
        "part",
    )

    ordering = (
        "brand",
        "model",
        "generation",
        "year_from",
    )

    list_per_page = 25

    fieldsets = (
        (
            _("Part"),
            {
                "fields": (
                    "part",
                ),
            },
        ),
        (
            _("Vehicle"),
            {
                "fields": (
                    "brand",
                    "model",
                    "generation",
                    "engine",
                ),
            },
        ),
        (
            _("Production years"),
            {
                "fields": (
                    "year_from",
                    "year_to",
                ),
            },
        ),
    )


@admin.register(PartImage)
class PartImageAdmin(admin.ModelAdmin):
    """
    Административная панель изображений запчастей.
    """

    list_display = (
        "id",
        "part",
        "image_preview",
        "image",
        "alt_text",
        "is_main",
        "uploaded_at",
    )

    list_display_links = (
        "id",
        "part",
    )

    list_filter = (
        "is_main",
        "uploaded_at",
    )

    search_fields = (
        "part__name",
        "part__original_number",
        "alt_text",
        "image",
    )

    readonly_fields = (
        "image_preview",
        "uploaded_at",
    )

    autocomplete_fields = (
        "part",
    )

    list_select_related = (
        "part",
    )

    ordering = (
        "-is_main",
        "id",
    )

    list_editable = (
        "is_main",
    )

    list_per_page = 25

    date_hierarchy = "uploaded_at"

    fieldsets = (
        (
            _("Part"),
            {
                "fields": (
                    "part",
                ),
            },
        ),
        (
            _("Image information"),
            {
                "fields": (
                    "image",
                    "image_preview",
                    "alt_text",
                    "is_main",
                ),
            },
        ),
        (
            _("System information"),
            {
                "fields": (
                    "uploaded_at",
                ),
                "classes": (
                    "collapse",
                ),
            },
        ),
    )

    @admin.display(description=_("Preview"))
    def image_preview(self, obj):
        """
        Возвращает предварительный просмотр изображения.
        """

        if obj.pk and obj.image:
            return format_html(
                '<a href="{}" target="_blank">'
                '<img src="{}" '
                'alt="{}" '
                'style="width: 90px; '
                'height: 90px; '
                'object-fit: cover; '
                'border-radius: 8px; '
                'border: 1px solid #ddd;">'
                "</a>",
                obj.image.url,
                obj.image.url,
                obj.alt_text or obj.part.name,
            )

        return "—"
