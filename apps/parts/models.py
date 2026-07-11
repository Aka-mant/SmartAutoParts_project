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


class OEMNumber(models.Model):
    """
    Модель OEM-номера запчасти.

    Хранит оригинальные номера производителей (OEM),
    соответствующие конкретной запчасти. Одна запчасть
    может иметь несколько OEM-номеров.
    """

    part = models.ForeignKey(
        Part,
        on_delete=models.CASCADE,
        related_name="oem_numbers",
        verbose_name=_("Part"),
    )

    number = models.CharField(
        max_length=255,
        unique=True,
        verbose_name=_("OEM number"),
    )

    manufacturer = models.CharField(
        max_length=255,
        blank=True,
        verbose_name=_("Manufacturer"),
    )

    class Meta:
        db_table = "parts_oemnumber"
        ordering = ("number",)
        verbose_name = _("OEM number")
        verbose_name_plural = _("OEM numbers")
        constraints = [
            models.UniqueConstraint(
                fields=["part", "number"],
                name="parts_oemnumber_index_0",
            ),
        ]

    def __str__(self):
        return self.number

class Compatibility(models.Model):
    """
    Модель совместимости запчасти.

    Хранит информацию о совместимости запчасти с различными
    автомобилями. Позволяет определить, для каких марок,
    моделей, поколений, двигателей и годов выпуска подходит
    конкретная запчасть.
    """

    part = models.ForeignKey(
        Part,
        on_delete=models.CASCADE,
        related_name="compatibilities",
        verbose_name=_("Part"),
    )

    brand = models.CharField(
        max_length=255,
        blank=True,
        verbose_name=_("Brand"),
    )

    model = models.CharField(
        max_length=255,
        blank=True,
        verbose_name=_("Model"),
    )

    generation = models.CharField(
        max_length=255,
        blank=True,
        verbose_name=_("Generation"),
    )

    engine = models.CharField(
        max_length=255,
        blank=True,
        verbose_name=_("Engine"),
    )

    year_from = models.PositiveIntegerField(
        null=True,
        blank=True,
        verbose_name=_("Year from"),
    )

    year_to = models.PositiveIntegerField(
        null=True,
        blank=True,
        verbose_name=_("Year to"),
    )

    class Meta:
        db_table = "parts_compatibility"
        ordering = (
            "brand",
            "model",
            "generation",
            "year_from",
        )
        verbose_name = _("Compatibility")
        verbose_name_plural = _("Compatibilities")

    def __str__(self):
        years = ""

        if self.year_from and self.year_to:
            years = f" ({self.year_from}-{self.year_to})"
        elif self.year_from:
            years = f" (с {self.year_from})"
        elif self.year_to:
            years = f" (до {self.year_to})"

        return (
            f"{self.brand} "
            f"{self.model} "
            f"{self.generation}"
            f"{years}"
        ).strip()


class PartImage(models.Model):
    """
    Модель изображения запчасти.

    Хранит изображения, относящиеся к конкретной запчасти.
    Позволяет хранить несколько изображений для одной
    запчасти, при этом одно из них может быть отмечено
    как основное.
    """

    part = models.ForeignKey(
        Part,
        on_delete=models.CASCADE,
        related_name="images",
        verbose_name=_("Part"),
    )

    image = models.ImageField(
        upload_to="parts/images/",
        verbose_name=_("Image"),
    )

    alt_text = models.CharField(
        max_length=255,
        blank=True,
        verbose_name=_("Alternative text"),
        help_text=_("Alternative text for SEO and accessibility."),
    )

    is_main = models.BooleanField(
        default=False,
        verbose_name=_("Main image"),
        help_text=_("Indicates whether this image is the primary image for the part."),
    )

    uploaded_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name=_("Uploaded at"),
    )

    class Meta:
        db_table = "parts_partimage"
        ordering = ("-is_main", "id")
        verbose_name = _("Part image")
        verbose_name_plural = _("Part images")

    def __str__(self):
        return (
            f"{self.part.name} "
            f"{_('(main)') if self.is_main else ''}"
        ).strip()