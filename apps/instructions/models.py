from django.conf import settings
from django.db import models
from django.utils.translation import gettext_lazy as _


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

