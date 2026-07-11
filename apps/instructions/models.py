from django.conf import settings
from django.db import models
from django.utils.translation import gettext_lazy as _

from apps.parts.models import Part


class Instruction(models.Model):
    """
    Модель инструкции по ремонту.

    Хранит подробное руководство по ремонту, обслуживанию
    или замене автомобильной запчасти. Инструкция содержит
    SEO-информацию, уровень сложности, примерное время
    выполнения и сведения об авторе.
    """

    part = models.ForeignKey(
        Part,
        on_delete=models.CASCADE,
        related_name="instructions",
        verbose_name=_("Part"),
    )

    title = models.CharField(
        max_length=255,
        verbose_name=_("Title"),
    )

    slug = models.SlugField(
        max_length=255,
        unique=True,
        verbose_name=_("Slug"),
        help_text=_("SEO-friendly URL."),
    )

    short_description = models.TextField(
        blank=True,
        verbose_name=_("Short description"),
    )

    content = models.TextField(
        verbose_name=_("Content"),
    )

    difficulty = models.CharField(
        max_length=50,
        blank=True,
        verbose_name=_("Difficulty"),
    )

    estimated_time = models.PositiveIntegerField(
        null=True,
        blank=True,
        verbose_name=_("Estimated time"),
        help_text=_("Estimated completion time in minutes."),
    )

    premium_only = models.BooleanField(
        default=False,
        verbose_name=_("Premium only"),
    )

    version = models.PositiveIntegerField(
        default=1,
        verbose_name=_("Version"),
    )

    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        related_name="created_instructions",
        null=True,
        blank=True,
        verbose_name=_("Created by"),
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
        db_table = "instructions_instruction"
        ordering = ("title",)
        verbose_name = _("Instruction")
        verbose_name_plural = _("Instructions")

    def __str__(self):
        return self.title

class InstructionVersion(models.Model):
    """
    Модель версии инструкции.

    Хранит историю изменений инструкции. Каждая запись
    представляет отдельную версию содержимого с описанием
    внесенных изменений и датой создания версии.
    """

    instruction = models.ForeignKey(
        Instruction,
        on_delete=models.CASCADE,
        related_name="versions",
        verbose_name=_("Instruction"),
    )

    version_number = models.PositiveIntegerField(
        verbose_name=_("Version number"),
    )

    content = models.TextField(
        verbose_name=_("Content"),
    )

    changelog = models.TextField(
        blank=True,
        verbose_name=_("Changelog"),
        help_text=_("Description of changes made in this version."),
    )

    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name=_("Created at"),
    )

    class Meta:
        db_table = "instructions_instructionversion"
        ordering = ("-version_number",)
        verbose_name = _("Instruction version")
        verbose_name_plural = _("Instruction versions")

    def __str__(self):
        return (
            f"{self.instruction.title} "
            f"v{self.version_number}"
        )


class InstructionStep(models.Model):
    """
    Модель шага инструкции.

    Хранит последовательные шаги выполнения инструкции по
    ремонту или обслуживанию. Каждый шаг содержит описание,
    при необходимости предупреждение и ориентировочное время
    выполнения.
    """

    instruction = models.ForeignKey(
        Instruction,
        on_delete=models.CASCADE,
        related_name="steps",
        verbose_name=_("Instruction"),
    )

    step_number = models.PositiveIntegerField(
        verbose_name=_("Step number"),
        help_text=_("Sequential number of the instruction step."),
    )

    title = models.CharField(
        max_length=255,
        blank=True,
        verbose_name=_("Title"),
    )

    description = models.TextField(
        verbose_name=_("Description"),
    )

    warning = models.TextField(
        blank=True,
        verbose_name=_("Warning"),
        help_text=_("Important safety information or recommendations."),
    )

    estimated_minutes = models.PositiveIntegerField(
        null=True,
        blank=True,
        verbose_name=_("Estimated minutes"),
        help_text=_("Estimated time to complete this step."),
    )

    class Meta:
        db_table = "instructions_instructionstep"
        ordering = ("instruction", "step_number")
        verbose_name = _("Instruction step")
        verbose_name_plural = _("Instruction steps")

    def __str__(self):
        return (
            f"{self.instruction.title} — "
            f"{_('Step')} {self.step_number}"
        )


class InstructionImage(models.Model):
    """
    Модель изображения инструкции.

    Хранит изображения, используемые в инструкции по ремонту
    или обслуживанию. Изображения помогают визуализировать
    отдельные этапы выполнения работ и могут сопровождаться
    пояснительным описанием.
    """

    instruction = models.ForeignKey(
        Instruction,
        on_delete=models.CASCADE,
        related_name="images",
        verbose_name=_("Instruction"),
    )

    image = models.ImageField(
        upload_to="instructions/images/",
        verbose_name=_("Image"),
    )

    description = models.TextField(
        blank=True,
        verbose_name=_("Description"),
        help_text=_("Description of the image or the illustrated step."),
    )

    class Meta:
        db_table = "instructions_instructionimage"
        ordering = ("instruction", "id")
        verbose_name = _("Instruction image")
        verbose_name_plural = _("Instruction images")

    def __str__(self):
        return (
            f"{self.instruction.title} — "
            f"{_('Image')} #{self.pk}"
        )

class InstructionTool(models.Model):
    """
    Модель связи инструкции с инструментом.

    Определяет, какие инструменты используются при выполнении
    конкретной инструкции. Позволяет хранить дополнительное
    описание применения каждого инструмента на отдельных этапах
    ремонта или обслуживания.
    """

    instruction = models.ForeignKey(
        Instruction,
        on_delete=models.CASCADE,
        related_name="instruction_tools",
        verbose_name=_("Instruction"),
    )

    tool = models.ForeignKey(
        Tool,
        on_delete=models.CASCADE,
        related_name="instruction_tools",
        verbose_name=_("Tool"),
    )

    usage_description = models.TextField(
        blank=True,
        verbose_name=_("Usage description"),
        help_text=_("Description of how this tool is used in the instruction."),
    )

    class Meta:
        db_table = "instructions_instructiontool"
        ordering = ("instruction", "tool")
        verbose_name = _("Instruction tool")
        verbose_name_plural = _("Instruction tools")

    def __str__(self):
        return f"{self.instruction.title} → {self.tool.name}"

