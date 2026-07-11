from django.db import models
from django.utils.translation import gettext_lazy as _


class PartCategory(models.Model):
    """
    Модель категории запчастей.

    Используется для группировки запчастей по категориям.
    Каждая категория имеет уникальное название, SEO-совместимый
    slug и описание.
    """

    name = models.CharField(
        max_length=255,
        verbose_name=_("Name"),
    )

    slug = models.SlugField(
        max_length=255,
        unique=True,
        verbose_name=_("Slug"),
        help_text=_("SEO-friendly URL."),
    )

    description = models.TextField(
        blank=True,
        verbose_name=_("Description"),
    )

    class Meta:
        db_table = "parts_partcategory"
        ordering = ("name",)
        verbose_name = _("Part category")
        verbose_name_plural = _("Part categories")

    def __str__(self):
        return self.name


class Part(models.Model):
    """
    Модель автомобильной запчасти.

    Хранит основную информацию о запчасти, включая категорию,
    оригинальный номер, производителя, SEO-данные, физические
    характеристики и служебные поля.
    """

    category = models.ForeignKey(
        PartCategory,
        on_delete=models.SET_NULL,
        related_name="parts",
        null=True,
        blank=True,
        verbose_name=_("Category"),
    )

    name = models.CharField(
        max_length=255,
        verbose_name=_("Name"),
    )

    slug = models.SlugField(
        max_length=255,
        unique=True,
        verbose_name=_("Slug"),
        help_text=_("SEO-friendly URL."),
    )

    original_number = models.CharField(
        max_length=255,
        db_index=True,
        verbose_name=_("Original number"),
    )

    manufacturer = models.CharField(
        max_length=255,
        blank=True,
        verbose_name=_("Manufacturer"),
    )

    description = models.TextField(
        blank=True,
        verbose_name=_("Description"),
    )

    seo_title = models.CharField(
        max_length=255,
        blank=True,
        verbose_name=_("SEO title"),
    )

    seo_description = models.TextField(
        blank=True,
        verbose_name=_("SEO description"),
    )

    seo_keywords = models.TextField(
        blank=True,
        verbose_name=_("SEO keywords"),
    )

    weight = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        null=True,
        blank=True,
        verbose_name=_("Weight"),
    )

    dimensions = models.JSONField(
        null=True,
        blank=True,
        verbose_name=_("Dimensions"),
        help_text=_("Part dimensions in JSON format."),
    )

    is_active = models.BooleanField(
        default=True,
        verbose_name=_("Is active"),
    )

    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name=_("Created at"),
    )

    updated_at = models.DateTimeField(
        auto_now=True,
        verbose_name=_("Updated at"),
    )

    class Meta:
        db_table = "parts_part"
        ordering = ("name",)
        verbose_name = _("Part")
        verbose_name_plural = _("Parts")
        indexes = [
            models.Index(
                fields=["original_number"],
                name='part_original_oem_idx',
            ),
        ]

    def __str__(self):
        return f"{self.name} ({self.original_number})"


