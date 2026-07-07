from django.contrib.auth.models import AbstractUser
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

    def save(self, *args, **kwargs):
        """
        Синхронизирует роль с правами Django.
        """

        self.is_staff = self.role in (
            UserRole.MODERATOR,
            UserRole.SUPERUSER,
        )

        self.is_superuser = self.role == UserRole.SUPERUSER

        super().save(*args, **kwargs)