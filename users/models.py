from django.contrib.auth.models import AbstractUser
from django.conf import settings
from django.db import models
from django.utils.translation import gettext_lazy as _


class UserRole(models.TextChoices):
    """
    Роли пользователей в системе.
    """

    GUEST = "guest", _("Гость")
    USER = "user", _("Пользователь")
    PREMIUM = "premium", _("Премиум")
    MODERATOR = "moderator", _("Модератор")
    SUPERUSER = "superuser", _("Суперпользователь")


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
    def is_guest(self) -> bool:
        """Является гостем."""
        return self.role == UserRole.GUEST

    @property
    def is_user(self) -> bool:
        """Является обычным пользователем."""
        return self.role == UserRole.USER

    @property
    def is_premium(self) -> bool:
        """Является премиум-пользователем."""
        return self.role == UserRole.PREMIUM

    @property
    def is_moderator(self) -> bool:
        """Является модератором."""
        return self.role == UserRole.MODERATOR

    @property
    def is_role_superuser(self) -> bool:
        """Является суперпользователем согласно ролевой модели."""
        return self.role == UserRole.SUPERUSER

    @property
    def is_staff_role(self) -> bool:
        """Имеет служебную роль."""
        return self.role in (
            UserRole.MODERATOR,
            UserRole.SUPERUSER,
        )

    @property
    def has_paid_access(self) -> bool:
        """Имеет доступ к платным функциям."""
        return self.role in (
            UserRole.PREMIUM,
            UserRole.MODERATOR,
            UserRole.SUPERUSER,
        )

    @property
    def can_moderate(self) -> bool:
        """Может модерировать контент."""
        return self.role in (
            UserRole.MODERATOR,
            UserRole.SUPERUSER,
        )

    @property
    def can_manage_users(self) -> bool:
        """Может управлять пользователями."""
        return self.role == UserRole.SUPERUSER

    @property
    def is_regular(self) -> bool:
        """Является обычным зарегистрированным пользователем."""
        return self.role in (
            UserRole.USER,
            UserRole.PREMIUM,
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
        return f"{self.search_query} ({self.searched_at:%d.%m.%Y %H:%M})"

