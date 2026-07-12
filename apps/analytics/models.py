from django.conf import settings
from django.db import models
from django.utils.translation import gettext_lazy as _

from apps.parts.models import Part


class UserActivity(models.Model):
    """
    Модель активности пользователя.

    Хранит журнал действий пользователей в системе.
    Используется для аналитики, аудита и отслеживания
    поведения пользователей. Дополнительные сведения
    о действии сохраняются в формате JSON.
    """

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="activities",
        verbose_name=_("User"),
    )

    action = models.CharField(
        max_length=255,
        blank=True,
        verbose_name=_("Action"),
        help_text=_("Name or type of the performed action."),
    )

    metadata = models.JSONField(
        null=True,
        blank=True,
        verbose_name=_("Metadata"),
        help_text=_("Additional information about the performed action in JSON format."),
    )

    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name=_("Created at"),
    )

    class Meta:
        db_table = "analytics_useractivity"
        ordering = ("-created_at",)
        verbose_name = _("User activity")
        verbose_name_plural = _("User activities")

    def __str__(self):
        return (
            f"{self.user.email} — "
            f"{self.action or _('Unknown action')}"
        )


class SearchLog(models.Model):
    """
    Модель журнала поисковых запросов.

    Предназначена для сбора аналитики поисковых запросов.
    Хранит информацию о пользователе, поисковом запросе,
    количестве найденных результатов, IP-адресе клиента
    и времени выполнения поиска.
    """

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        related_name="search_logs",
        null=True,
        blank=True,
        verbose_name=_("User"),
    )

    query = models.CharField(
        max_length=255,
        blank=True,
        verbose_name=_("Search query"),
        help_text=_("Search query entered by the user."),
    )

    results_count = models.PositiveIntegerField(
        default=0,
        verbose_name=_("Results count"),
        help_text=_("Number of search results returned."),
    )

    ip_address = models.GenericIPAddressField(
        protocol="both",
        unpack_ipv4=True,
        null=True,
        blank=True,
        verbose_name=_("IP address"),
    )

    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name=_("Created at"),
    )

    class Meta:
        db_table = "analytics_searchlog"
        ordering = ("-created_at",)
        verbose_name = _("Search log")
        verbose_name_plural = _("Search logs")

    def __str__(self):
        return (
            f"{self.query or _('Empty query')} "
            f"({self.results_count})"
        )


class PopularPart(models.Model):
    """
    Модель популярной запчасти.

    Используется для хранения статистики популярности
    автомобильных запчастей. Содержит количество поисковых
    запросов, просмотров и дату последнего обновления
    аналитических данных.
    """

    part = models.ForeignKey(
        Part,
        on_delete=models.CASCADE,
        related_name="popularity_statistics",
        verbose_name=_("Part"),
    )

    searches_count = models.PositiveIntegerField(
        default=0,
        verbose_name=_("Searches count"),
        help_text=_("Total number of searches for the part."),
    )

    views_count = models.PositiveIntegerField(
        default=0,
        verbose_name=_("Views count"),
        help_text=_("Total number of views for the part."),
    )

    updated_at = models.DateTimeField(
        auto_now=True,
        verbose_name=_("Updated at"),
    )

    class Meta:
        db_table = "analytics_popularpart"
        ordering = ("-searches_count", "-views_count")
        verbose_name = _("Popular part")
        verbose_name_plural = _("Popular parts")

    def __str__(self):
        return (
            f"{self.part.name} "
            f"({self.searches_count} {_('searches')})"
        )