from datetime import timedelta
from uuid import uuid4

from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.db import transaction
from django.db.models import QuerySet
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from django.views import View
from django.views.generic import ListView

from rest_framework.generics import (
    CreateAPIView,
    DestroyAPIView,
    ListAPIView,
    RetrieveAPIView,
    UpdateAPIView,
)
from rest_framework.permissions import IsAuthenticated

from users.permissions import (
    IsAdmin,
    IsModerator,
    IsOwner,
)

from .models import (
    SubscriptionPayment,
    SubscriptionPlan,
    UserSubscription,
)
from .access import (
    get_active_subscription,
    has_unlimited_ai_access,
)
from .serializers import (
    SubscriptionPaymentCreateSerializer,
    SubscriptionPaymentSerializer,
    SubscriptionPaymentUpdateSerializer,
    SubscriptionPlanCreateSerializer,
    SubscriptionPlanSerializer,
    SubscriptionPlanUpdateSerializer,
    UserSubscriptionCreateSerializer,
    UserSubscriptionSerializer,
    UserSubscriptionUpdateSerializer,
)


PAYMENT_METHODS = (
    {
        "code": "bank_card",
        "name": "Банковская карта",
        "description": "МИР и карты российских банков",
        "icon": "bi-credit-card-2-front",
    },
    {
        "code": "sbp",
        "name": "Система быстрых платежей",
        "description": "Оплата по QR-коду через приложение банка",
        "icon": "bi-qr-code",
    },
    {
        "code": "sberpay",
        "name": "SberPay",
        "description": "Подтверждение в приложении СберБанк Онлайн",
        "icon": "bi-phone",
    },
    {
        "code": "tpay",
        "name": "T-Pay",
        "description": "Оплата через приложение Т-Банка",
        "icon": "bi-phone-vibrate",
    },
    {
        "code": "yandex_pay",
        "name": "Яндекс Пэй",
        "description": "Оплата сохранённым способом Яндекса",
        "icon": "bi-wallet2",
    },
    {
        "code": "mir_pay",
        "name": "Mir Pay",
        "description": "Бесконтактная оплата картой МИР",
        "icon": "bi-phone-flip",
    },
    {
        "code": "yoomoney",
        "name": "ЮMoney",
        "description": "Оплата из электронного кошелька",
        "icon": "bi-wallet",
    },
    {
        "code": "mobile_balance",
        "name": "Баланс телефона",
        "description": "Списание со счёта мобильного оператора",
        "icon": "bi-sim",
    },
    {
        "code": "bank_transfer",
        "name": "Банковский перевод",
        "description": "Перевод по реквизитам или квитанции",
        "icon": "bi-bank",
    },
    {
        "code": "cash_terminal",
        "name": "Наличные",
        "description": "Оплата по коду через платёжный терминал",
        "icon": "bi-cash-coin",
    },
    {
        "code": "installments",
        "name": "Рассрочка",
        "description": "Оплата частями через банк-партнёр",
        "icon": "bi-calendar2-check",
    },
)


class UserOwnedQuerySetMixin:
    """
    Ограничивает queryset объектами,
    принадлежащими текущему пользователю.

    Администраторы и системные
    суперпользователи Django получают
    доступ ко всем объектам.
    """

    owner_lookup = "user"

    def get_queryset(self) -> QuerySet:
        """
        Возвращает queryset с учётом
        прав текущего пользователя.
        """

        queryset = super().get_queryset()
        user = self.request.user

        if not user.is_authenticated:
            return queryset.none()

        if user.can_administrate:
            return queryset

        return queryset.filter(
            **{
                self.owner_lookup: user,
            }
        )


class SubscriptionPlanListAPIView(ListAPIView):
    """
    API-представление для получения
    списка тарифных планов подписки.

    Доступно всем авторизованным
    пользователям.
    """

    queryset = SubscriptionPlan.objects.filter(is_public=True)
    serializer_class = SubscriptionPlanSerializer
    permission_classes = [
        IsAuthenticated,
    ]


class SubscriptionPlansPageView(ListView):
    """Публичная страница сравнения тарифных планов."""

    model = SubscriptionPlan
    template_name = "subscriptions/plan_list.html"
    context_object_name = "plans"

    def get_queryset(self):
        return SubscriptionPlan.objects.filter(is_public=True).order_by(
            "sort_order",
            "price",
            "id",
        )

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["active_subscription"] = get_active_subscription(
            self.request.user
        )
        context["is_service_privileged"] = has_unlimited_ai_access(
            self.request.user
        )
        return context


class SubscriptionCheckoutPageView(LoginRequiredMixin, View):
    """Имитирует оплату и активирует выбранный тариф."""

    login_url = "users:login"
    template_name = "subscriptions/payment.html"

    def get_plan(self, plan_id):
        return get_object_or_404(
            SubscriptionPlan,
            pk=plan_id,
            is_public=True,
        )

    def dispatch(self, request, *args, **kwargs):
        if request.user.is_authenticated and has_unlimited_ai_access(
            request.user
        ):
            messages.info(
                request,
                "Для вашей роли функции сервиса уже доступны без ограничений.",
            )
            return redirect("users:dashboard")
        return super().dispatch(request, *args, **kwargs)

    def get(self, request, plan_id):
        return render(
            request,
            self.template_name,
            {
                "plan": self.get_plan(plan_id),
                "payment_methods": PAYMENT_METHODS,
            },
        )

    def post(self, request, plan_id):
        plan = self.get_plan(plan_id)
        method_code = request.POST.get("payment_method", "").strip()
        methods_by_code = {
            method["code"]: method
            for method in PAYMENT_METHODS
        }
        payment_method = methods_by_code.get(method_code)
        if payment_method is None:
            messages.error(
                request,
                "Выберите доступный способ оплаты.",
            )
            return render(
                request,
                self.template_name,
                {
                    "plan": plan,
                    "payment_methods": PAYMENT_METHODS,
                },
                status=400,
            )

        now = timezone.now()
        with transaction.atomic():
            UserSubscription.objects.filter(
                user=request.user,
                is_active=True,
            ).update(is_active=False)
            subscription = UserSubscription.objects.create(
                user=request.user,
                plan=plan,
                start_date=now,
                end_date=now + timedelta(days=plan.duration_days),
                is_active=True,
                auto_renew=False,
            )
            SubscriptionPayment.objects.create(
                user=request.user,
                subscription=subscription,
                provider=f"Демо: {payment_method['name']}",
                external_payment_id=f"demo-{uuid4()}",
                amount=plan.price,
                currency="RUB",
                status="succeeded",
                paid_at=now,
            )

        messages.success(
            request,
            f"Оплата имитирована. Тариф «{plan.name}» активирован.",
        )
        return redirect("users:dashboard")


class SubscriptionPlanCreateAPIView(CreateAPIView):
    """
    API-представление для создания
    тарифного плана подписки.

    Доступ предоставляется:

    - модераторам;
    - администраторам;
    - системным суперпользователям Django.
    """

    queryset = SubscriptionPlan.objects.all()
    serializer_class = SubscriptionPlanCreateSerializer
    permission_classes = [
        IsAuthenticated,
        IsModerator,
    ]


class SubscriptionPlanRetrieveAPIView(RetrieveAPIView):
    """
    API-представление для получения
    информации о тарифном плане подписки.

    Доступно всем авторизованным
    пользователям.
    """

    queryset = SubscriptionPlan.objects.all()
    serializer_class = SubscriptionPlanSerializer
    permission_classes = [
        IsAuthenticated,
    ]


class SubscriptionPlanUpdateAPIView(UpdateAPIView):
    """
    API-представление для обновления
    тарифного плана подписки.

    Доступ предоставляется:

    - модераторам;
    - администраторам;
    - системным суперпользователям Django.
    """

    queryset = SubscriptionPlan.objects.all()
    serializer_class = SubscriptionPlanUpdateSerializer
    permission_classes = [
        IsAuthenticated,
        IsModerator,
    ]


class SubscriptionPlanDeleteAPIView(DestroyAPIView):
    """
    API-представление для удаления
    тарифного плана подписки.

    Доступ предоставляется:

    - администраторам;
    - системным суперпользователям Django.
    """

    queryset = SubscriptionPlan.objects.all()
    permission_classes = [
        IsAuthenticated,
        IsAdmin,
    ]


class UserSubscriptionListAPIView(
    UserOwnedQuerySetMixin,
    ListAPIView,
):
    """
    API-представление для получения
    списка пользовательских подписок.

    Обычный пользователь получает только
    собственные подписки.

    Администраторы и системные
    суперпользователи получают все подписки.
    """

    queryset = UserSubscription.objects.select_related(
        "user",
        "plan",
    )
    serializer_class = UserSubscriptionSerializer
    permission_classes = [
        IsAuthenticated,
    ]


class UserSubscriptionCreateAPIView(CreateAPIView):
    """
    API-представление для создания
    пользовательской подписки.

    Текущий пользователь автоматически
    назначается владельцем подписки.
    """

    queryset = UserSubscription.objects.all()
    serializer_class = UserSubscriptionCreateSerializer
    permission_classes = [
        IsAuthenticated,
    ]

    def perform_create(self, serializer):
        """
        Создаёт подписку для текущего
        авторизованного пользователя.

        Значение поля user, переданное
        клиентом, не используется.
        """

        serializer.save(
            user=self.request.user,
        )


class UserSubscriptionRetrieveAPIView(
    UserOwnedQuerySetMixin,
    RetrieveAPIView,
):
    """
    API-представление для получения
    информации о пользовательской подписке.

    Пользователь может просматривать
    только собственные подписки.

    Администраторы и системные
    суперпользователи могут просматривать
    любые подписки.
    """

    queryset = UserSubscription.objects.select_related(
        "user",
        "plan",
    )
    serializer_class = UserSubscriptionSerializer
    permission_classes = [
        IsAuthenticated,
        IsOwner,
    ]


class UserSubscriptionUpdateAPIView(
    UserOwnedQuerySetMixin,
    UpdateAPIView,
):
    """
    API-представление для обновления
    пользовательской подписки.

    Пользователь может изменять
    только собственные подписки.

    Администраторы и системные
    суперпользователи могут изменять
    любые подписки.
    """

    queryset = UserSubscription.objects.select_related(
        "user",
        "plan",
    )
    serializer_class = UserSubscriptionUpdateSerializer
    permission_classes = [
        IsAuthenticated,
        IsOwner,
    ]

    def perform_update(self, serializer):
        """
        Обновляет пользовательскую подписку,
        сохраняя её текущего владельца.
        """

        instance = self.get_object()

        serializer.save(
            user=instance.user,
        )


class UserSubscriptionDeleteAPIView(
    UserOwnedQuerySetMixin,
    DestroyAPIView,
):
    """
    API-представление для удаления
    пользовательской подписки.

    Пользователь может удалить
    только собственную подписку.

    Администраторы и системные
    суперпользователи могут удалять
    любые подписки.
    """

    queryset = UserSubscription.objects.select_related(
        "user",
        "plan",
    )
    permission_classes = [
        IsAuthenticated,
        IsOwner,
    ]


class SubscriptionPaymentListAPIView(
    UserOwnedQuerySetMixin,
    ListAPIView,
):
    """
    API-представление для получения
    списка платежей пользователя.

    Обычный пользователь получает только
    собственные платежи.

    Администраторы и системные
    суперпользователи получают все платежи.
    """

    queryset = SubscriptionPayment.objects.select_related(
        "user",
        "subscription",
    )
    serializer_class = SubscriptionPaymentSerializer
    permission_classes = [
        IsAuthenticated,
    ]


class SubscriptionPaymentCreateAPIView(CreateAPIView):
    """
    API-представление для создания
    платежа за подписку.

    Текущий пользователь автоматически
    назначается владельцем платежа.
    """

    queryset = SubscriptionPayment.objects.all()
    serializer_class = SubscriptionPaymentCreateSerializer
    permission_classes = [
        IsAuthenticated,
    ]

    def perform_create(self, serializer):
        """
        Создаёт платёж для текущего
        авторизованного пользователя.

        Значение поля user, переданное
        клиентом, не используется.
        """

        serializer.save(
            user=self.request.user,
        )


class SubscriptionPaymentRetrieveAPIView(
    UserOwnedQuerySetMixin,
    RetrieveAPIView,
):
    """
    API-представление для получения
    информации о платеже.

    Пользователь может просматривать
    только собственные платежи.

    Администраторы и системные
    суперпользователи могут просматривать
    любые платежи.
    """

    queryset = SubscriptionPayment.objects.select_related(
        "user",
        "subscription",
    )
    serializer_class = SubscriptionPaymentSerializer
    permission_classes = [
        IsAuthenticated,
        IsOwner,
    ]


class SubscriptionPaymentUpdateAPIView(
    UserOwnedQuerySetMixin,
    UpdateAPIView,
):
    """
    API-представление для обновления
    информации о платеже.

    Пользователь может изменять
    только собственные платежи.

    Администраторы и системные
    суперпользователи могут изменять
    любые платежи.
    """

    queryset = SubscriptionPayment.objects.select_related(
        "user",
        "subscription",
    )
    serializer_class = SubscriptionPaymentUpdateSerializer
    permission_classes = [
        IsAuthenticated,
        IsOwner,
    ]

    def perform_update(self, serializer):
        """
        Обновляет платёж, сохраняя
        его текущего владельца.
        """

        instance = self.get_object()

        serializer.save(
            user=instance.user,
        )


class SubscriptionPaymentDeleteAPIView(
    UserOwnedQuerySetMixin,
    DestroyAPIView,
):
    """
    API-представление для удаления
    платежа.

    Пользователь может удалить
    только собственный платёж.

    Администраторы и системные
    суперпользователи могут удалять
    любые платежи.
    """

    queryset = SubscriptionPayment.objects.select_related(
        "user",
        "subscription",
    )
    permission_classes = [
        IsAuthenticated,
        IsOwner,
    ]
