from django.contrib.auth.models import AbstractUser
from django.conf import settings
from django.db import models
from django.utils.translation import gettext_lazy as _

from apps.instructions.models import Instruction


class UserRole(models.TextChoices):
    """
    Роли пользователей в системе.
    """

    GUEST = "guest", _("Гость")
    USER = "user", _("Пользователь")
    PREMIUM = "premium", _("Премиум")
    MODERATOR = "moderator", _("Модератор")



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


    @property
    def has_paid_access(self) -> bool:
        """
        Имеет доступ к платным функциям.
        """

        return (
                self.role in (
            UserRole.PREMIUM,
            UserRole.MODERATOR,
        )
                or self.is_superuser
        )

    @property
    def can_moderate(self) -> bool:
        """
        Может модерировать контент.
        """

        return (
                self.role == UserRole.MODERATOR
                or self.is_superuser
        )



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

    notes = models.TextField(
        blank=True,
        verbose_name=_("Notes"),
        help_text=_("User notes about the completed repair."),
    )

    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name=_("Created at"),
    )

    class Meta:
        db_table = "users_repairhistory"
        ordering = ("-created_at",)
        verbose_name = _("Repair history")
        verbose_name_plural = _("Repair history")

    def __str__(self):
        status = _("Completed") if self.completed else _("In progress")
        return f"{self.user.email} — {self.instruction.title} ({status})"

