from urllib.parse import urlencode

from django.contrib.auth.models import AbstractUser
from django.conf import settings
from django.core.validators import MinValueValidator
from django.db import models
from django.utils import timezone
from django.urls import reverse
from django.utils.translation import gettext_lazy as _

from apps.instructions.models import Instruction


class UserRole(models.TextChoices):
    """
    Роли пользователей в системе.
    """

    USER = "user", _("Пользователь")
    PREMIUM = "premium", _("Премиум")
    MODERATOR = "moderator", _("Модератор")
    ADMIN = "admin", _("Администратор")



class User(AbstractUser):
    """
    Модель пользователя системы.

    Расширяет стандартную модель AbstractUser и хранит
    основную информацию о пользователе, включая контактные
    данные, аватар, роль и служебные поля.
    """

    email = models.EmailField(
        unique=True,
        verbose_name=_("Email"),
    )

    username = models.CharField(
        max_length=150,
        unique=True,
        verbose_name=_("Username"),
    )

    first_name = models.CharField(
        max_length=150,
        blank=True,
        verbose_name=_("First name"),
    )

    last_name = models.CharField(
        max_length=150,
        blank=True,
        verbose_name=_("Last name"),
    )

    phone = models.CharField(
        max_length=30,
        blank=True,
        verbose_name=_("Phone"),
    )

    avatar = models.ImageField(
        upload_to="avatars/",
        blank=True,
        null=True,
        verbose_name=_("Avatar"),
    )

    role = models.CharField(
        max_length=20,
        choices=UserRole.choices,
        default=UserRole.USER,
        verbose_name=_("Role"),
        help_text=_("Роль пользователя в системе."),
    )

    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name=_("Created at"),
    )

    updated_at = models.DateTimeField(
        auto_now=True,
        verbose_name=_("Updated at"),
    )

    is_active = models.BooleanField(
        default=True,
        verbose_name=_('Is Active')
    )

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = ["username"]

    class Meta:
        db_table = "users_user"
        ordering = ("id",)
        verbose_name = _("User")
        verbose_name_plural = _("Users")

    def __str__(self):
        return self.email

    def save(self, *args, **kwargs):
        """Синхронизирует служебные роли с доступом в Django Admin."""

        if self.role in (UserRole.MODERATOR, UserRole.ADMIN):
            self.is_staff = True
        return super().save(*args, **kwargs)


    @property
    def has_paid_access(self) -> bool:
        """
        Имеет доступ к платным функциям.
        """

        if self.can_administrate:
            return True

        now = timezone.now()
        return self.subscriptions.filter(
            is_active=True,
            start_date__lte=now,
            end_date__gt=now,
        ).exists()

    @property
    def can_moderate(self) -> bool:
        """
        Может модерировать контент.
        """

        return (
                self.role == UserRole.MODERATOR
                or self.role == UserRole.ADMIN
                or self.is_superuser
        )

    @property
    def can_administrate(self):
        """
        Определяет, может ли пользователь
        выполнять административные действия.

        Доступ предоставляется пользователям
        с ролью администратора, а также
        системным суперпользователям Django.
        """
        return (
                self.role == UserRole.ADMIN
                or self.is_superuser
        )

    def has_accepted_user_agreement(self, version=None) -> bool:
        """Возвращает факт принятия указанной редакции соглашения."""

        if self.is_superuser or self.can_administrate:
            return True

        current_version = version or settings.USER_AGREEMENT_VERSION
        return self.agreement_acceptances.filter(
            agreement_version=current_version,
        ).exists()



class Profile(models.Model):
    """
    Модель профиля пользователя.

    Хранит дополнительную информацию о пользователе,
    такую как место проживания, предпочитаемый язык,
    сведения об автомобиле и краткую биографию.
    """

    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="profile",
        verbose_name=_("User"),
    )

    country = models.CharField(
        max_length=255,
        blank=True,
        verbose_name=_("Country"),
    )

    city = models.CharField(
        max_length=255,
        blank=True,
        verbose_name=_("City"),
    )

    preferred_language = models.CharField(
        max_length=255,
        blank=True,
        verbose_name=_("Preferred language"),
    )

    car_brand = models.CharField(
        max_length=255,
        blank=True,
        verbose_name=_("Car brand"),
    )

    car_model = models.CharField(
        max_length=255,
        blank=True,
        verbose_name=_("Car model"),
    )

    car_year = models.PositiveIntegerField(
        null=True,
        blank=True,
        verbose_name=_("Car year"),
    )

    bio = models.TextField(
        blank=True,
        verbose_name=_("Biography"),
    )

    class Meta:
        db_table = "users_profile"
        ordering = ("id",)
        verbose_name = _("Profile")
        verbose_name_plural = _("Profiles")

    def __str__(self):
        return f"{self.user.email} - {self.car_brand or _('No car')}"


class UserAgreementAcceptance(models.Model):
    """Фиксирует принятие пользователем действующей редакции соглашения."""

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="agreement_acceptances",
        verbose_name=_("User"),
    )
    agreement_version = models.CharField(
        max_length=32,
        verbose_name=_("Agreement version"),
    )
    accepted_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name=_("Accepted at"),
    )
    ip_address = models.GenericIPAddressField(
        null=True,
        blank=True,
        verbose_name=_("IP address"),
    )
    user_agent = models.CharField(
        max_length=500,
        blank=True,
        verbose_name=_("User agent"),
    )

    class Meta:
        db_table = "users_useragreementacceptance"
        ordering = ("-accepted_at",)
        verbose_name = _("User agreement acceptance")
        verbose_name_plural = _("User agreement acceptances")
        constraints = (
            models.UniqueConstraint(
                fields=("user", "agreement_version"),
                name="unique_user_agreement_version_acceptance",
            ),
        )

    def __str__(self):
        return (
            f"{self.user.email} — {self.agreement_version} "
            f"({self.accepted_at:%d.%m.%Y %H:%M})"
        )


class SearchHistory(models.Model):
    """
    Модель истории поисковых запросов пользователя.

    Хранит информацию о выполненных поисках, включая
    исходный номер детали, поисковый запрос, результат
    поиска и дату выполнения.
    """

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        related_name="search_history",
        null=True,
        blank=True,
        verbose_name=_("User"),
    )

    original_number = models.CharField(
        max_length=255,
        blank=True,
        verbose_name=_("Original number"),
    )

    search_query = models.CharField(
        max_length=500,
        blank=True,
        verbose_name=_("Search query"),
    )

    result_found = models.BooleanField(
        default=False,
        verbose_name=_("Result found"),
    )

    searched_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name=_("Searched at"),
    )

    class Meta:
        db_table = "users_searchhistory"
        ordering = ("-searched_at",)
        verbose_name = _("Search history")
        verbose_name_plural = _("Search history")

    def __str__(self):
        return f"{self.search_query} ({self.searched_at: %d.%m.%Y  %H:%M})"

    def get_search_results_url(self) -> str:
        """
        Возвращает страницу результатов для запроса из истории.

        В первую очередь используется OEM-номер, который отображается
        заголовком карточки. Для старых записей без OEM-номера применяется
        сохранённая поисковая строка.
        """

        query = (self.original_number or self.search_query).strip()
        search_url = reverse("users:part_search")

        if not query:
            return search_url

        return f"{search_url}?{urlencode({'q': query})}"


class RepairHistory(models.Model):
    """
    Модель истории выполненных ремонтов.

    Хранит информацию о прохождении пользователем инструкций
    по ремонту или обслуживанию автомобиля. Позволяет отслеживать
    статус выполнения, сохранять заметки пользователя и дату
    выполнения работ.
    """

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="repair_history",
        verbose_name=_("User"),
    )

    instruction = models.ForeignKey(
        Instruction,
        on_delete=models.CASCADE,
        related_name="repair_history",
        verbose_name=_("Instruction"),
    )

    completed = models.BooleanField(
        default=False,
        verbose_name=_("Completed"),
    )

    current_step = models.PositiveIntegerField(
        default=1,
        validators=(MinValueValidator(1),),
        verbose_name=_("Current step"),
        help_text=_("Current step of the unfinished repair."),
    )

    notes = models.TextField(
        blank=True,
        verbose_name=_("Notes"),
        help_text=_("User notes about the completed repair."),
    )

    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name=_("Created at"),
    )

    progress_updated_at = models.DateTimeField(
        auto_now=True,
        verbose_name=_("Progress updated at"),
    )

    class Meta:
        db_table = "users_repairhistory"
        ordering = ("-created_at",)
        verbose_name = _("Repair history")
        verbose_name_plural = _("Repair history")
        constraints = [
            models.CheckConstraint(
                condition=models.Q(current_step__gte=1),
                name="repair_history_current_step_gte_1",
            ),
        ]

    def __str__(self):
        status = _("Completed") if self.completed else _("In progress")
        return f"{self.user.email} — {self.instruction.title} ({status})"

