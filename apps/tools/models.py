from django.db import models
from django.urls import reverse
from django.utils.translation import gettext_lazy as _

from apps.parts.models import Part


class ToolCategory(models.Model):
    """
    Модель категории инструментов.

    Используется для группировки инструментов по категориям.
    Например: ключи, отвертки, съемники, диагностическое
    оборудование и другие виды инструментов.
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

    class Meta:
        db_table = "tools_toolcategory"
        ordering = ("name",)
        verbose_name = _("Tool category")
        verbose_name_plural = _("Tool categories")

    def __str__(self):
        return self.name


class Tool(models.Model):
    """
    Модель инструмента.

    Хранит информацию об инструментах, необходимых для
    выполнения ремонта или обслуживания автомобиля.
    Инструмент может использоваться в нескольких инструкциях
    и быть связан с различными запчастями.
    """

    category = models.ForeignKey(
        ToolCategory,
        on_delete=models.SET_NULL,
        related_name="tools",
        null=True,
        blank=True,
        verbose_name=_("Category"),
    )

    name = models.CharField(
        max_length=255,
        verbose_name=_("Name"),
    )

    description = models.TextField(
        blank=True,
        verbose_name=_("Description"),
    )

    size = models.CharField(
        max_length=255,
        blank=True,
        verbose_name=_("Size"),
    )

    image = models.ImageField(
        upload_to="tools/images/",
        blank=True,
        null=True,
        verbose_name=_("Image"),
    )

    ozon_url = models.URLField(
        max_length=1000,
        blank=True,
        verbose_name=_("Ozon URL"),
    )

    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name=_("Created at"),
    )

    class Meta:
        db_table = "tools_tool"
        ordering = ("name",)
        verbose_name = _("Tool")
        verbose_name_plural = _("Tools")

    def __str__(self):
        return self.name

    def get_absolute_url(self):
        """Возвращает адрес полной карточки инструмента."""

        return reverse(
            "tools_web:detail",
            kwargs={"pk": self.pk},
        )

    @property
    def image_exists(self) -> bool:
        """Проверяет наличие основного файла изображения."""

        if not self.image or not self.image.name:
            return False
        try:
            return self.image.storage.exists(self.image.name)
        except (OSError, ValueError):
            return False


class ToolImage(models.Model):
    """Хранит дополнительные изображения инструмента."""

    tool = models.ForeignKey(
        Tool,
        on_delete=models.CASCADE,
        related_name="images",
        verbose_name=_("Tool"),
    )

    image = models.ImageField(
        upload_to="tools/images/",
        verbose_name=_("Image"),
    )

    alt_text = models.CharField(
        max_length=255,
        blank=True,
        verbose_name=_("Alternative text"),
    )

    is_main = models.BooleanField(
        default=False,
        verbose_name=_("Main image"),
    )

    uploaded_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name=_("Uploaded at"),
    )

    class Meta:
        db_table = "tools_toolimage"
        ordering = ("-is_main", "id")
        verbose_name = _("Tool image")
        verbose_name_plural = _("Tool images")

    def __str__(self):
        return f"{self.tool.name}: {self.image.name}"

    @property
    def image_exists(self) -> bool:
        """Проверяет наличие файла изображения в хранилище."""

        if not self.image or not self.image.name:
            return False
        try:
            return self.image.storage.exists(self.image.name)
        except (OSError, ValueError):
            return False


class PartTool(models.Model):
    """
    Промежуточная модель связи запчастей и инструментов.

    Определяет, какие инструменты необходимы для работы
    с конкретной запчастью. Один инструмент может использоваться
    для нескольких запчастей, а одна запчасть может требовать
    несколько различных инструментов.
    """

    part = models.ForeignKey(
        Part,
        on_delete=models.CASCADE,
        related_name="part_tools",
        verbose_name=_("Part"),
    )

    tool = models.ForeignKey(
        Tool,
        on_delete=models.CASCADE,
        related_name="tool_parts",
        verbose_name=_("Tool"),
    )

    required = models.BooleanField(
        default=True,
        verbose_name=_("Required"),
        help_text=_("Indicates whether this tool is required."),
    )

    class Meta:
        db_table = "parts_parttool"
        ordering = ("part", "tool")
        verbose_name = _("Part tool")
        verbose_name_plural = _("Part tools")
        constraints = [
            models.UniqueConstraint(
                fields=("part", "tool"),
                name="uq_part_tool",
            ),
        ]

    def __str__(self):
        return f"{self.part.name} → {self.tool.name}"
