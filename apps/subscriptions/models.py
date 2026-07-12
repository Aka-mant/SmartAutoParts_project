from django.conf import settings
from django.db import models
from django.utils.translation import gettext_lazy as _


class SubscriptionPlan(models.Model):
    """
    Модель тарифного плана подписки.

    Хранит информацию о доступных тарифах приложения,
    включая стоимость, срок действия и доступные
    возможности для пользователей.
    """

    name = models.CharField(
        max_length=255,
        verbose_name=_("Name"),
    )

    description = models.TextField(
        blank=True,
        verbose_name=_("Description"),
    )

    price = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        verbose_name=_("Price"),
    )

    duration_days = models.PositiveIntegerField(
        verbose_name=_("Duration (days)"),
        help_text=_("Subscription duration in days."),
    )

    max_ai_requests = models.PositiveIntegerField(
        default=0,
        verbose_name=_("Maximum AI requests"),
        help_text=_("Maximum number of AI requests available within the subscription."),
    )

    has_chat_access = models.BooleanField(
        default=False,
        verbose_name=_("Chat access"),
        help_text=_("Allows access to the AI chat."),
    )

    has_image_analysis = models.BooleanField(
        default=False,
        verbose_name=_("Image analysis"),
        help_text=_("Allows using AI image analysis."),
    )

    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name=_("Created at"),
    )

    class Meta:
        db_table = "subscriptions_subscriptionplan"
        ordering = ("price",)
        verbose_name = _("Subscription plan")
        verbose_name_plural = _("Subscription plans")

    def __str__(self):
        return f"{self.name} (${self.price})"


class UserSubscription(models.Model):
    """
    Модель пользовательской подписки.

    Хранит информацию об активных и завершенных подписках
    пользователей. Определяет выбранный тарифный план,
    период действия подписки, ее текущий статус и настройки
    автоматического продления.
    """

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="subscriptions",
        verbose_name=_("User"),
    )

    plan = models.ForeignKey(
        SubscriptionPlan,
        on_delete=models.RESTRICT,
        related_name="subscriptions",
        verbose_name=_("Subscription plan"),
    )

    start_date = models.DateTimeField(
        verbose_name=_("Start date"),
    )

    end_date = models.DateTimeField(
        verbose_name=_("End date"),
    )

    is_active = models.BooleanField(
        default=True,
        verbose_name=_("Active"),
    )

    auto_renew = models.BooleanField(
        default=False,
        verbose_name=_("Auto renew"),
        help_text=_("Automatically renew the subscription after expiration."),
    )

    class Meta:
        db_table = "subscriptions_usersubscription"
        ordering = ("-end_date",)
        verbose_name = _("User subscription")
        verbose_name_plural = _("User subscriptions")

    def __str__(self):
        return f"{self.user.email} — {self.plan.name}"


class SubscriptionPayment(models.Model):
    """
    Модель платежа за подписку.

    Хранит информацию обо всех платежах пользователей,
    связанных с оформлением или продлением подписки.
    Содержит сведения о платежном провайдере, сумме,
    валюте, статусе платежа и идентификаторе операции
    во внешней платежной системе.
    """

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="subscription_payments",
        verbose_name=_("User"),
    )

    subscription = models.ForeignKey(
        UserSubscription,
        on_delete=models.SET_NULL,
        related_name="payments",
        null=True,
        blank=True,
        verbose_name=_("Subscription"),
    )

    provider = models.CharField(
        max_length=100,
        verbose_name=_("Payment provider"),
    )

    external_payment_id = models.CharField(
        max_length=255,
        blank=True,
        verbose_name=_("External payment ID"),
        help_text=_("Payment identifier returned by the payment provider."),
    )

    amount = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        verbose_name=_("Amount"),
    )

    currency = models.CharField(
        max_length=10,
        default="USD",
        verbose_name=_("Currency"),
    )

    status = models.CharField(
        max_length=50,
        blank=True,
        verbose_name=_("Payment status"),
    )

    paid_at = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name=_("Paid at"),
    )

    class Meta:
        db_table = "subscriptions_subscriptionpayment"
        ordering = ("-paid_at", "-id")
        verbose_name = _("Subscription payment")
        verbose_name_plural = _("Subscription payments")

    def __str__(self):
        return (
            f"{self.user.email} — "
            f"{self.amount} {self.currency}"
        )
