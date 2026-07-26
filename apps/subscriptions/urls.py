from django.urls import path

from .views import (
    # SubscriptionPlan
    SubscriptionPlanListAPIView,
    SubscriptionPlanCreateAPIView,
    SubscriptionPlanRetrieveAPIView,
    SubscriptionPlanUpdateAPIView,
    SubscriptionPlanDeleteAPIView,

    # UserSubscription
    UserSubscriptionListAPIView,
    UserSubscriptionCreateAPIView,
    UserSubscriptionRetrieveAPIView,
    UserSubscriptionUpdateAPIView,
    UserSubscriptionDeleteAPIView,

    # SubscriptionPayment
    SubscriptionPaymentListAPIView,
    SubscriptionPaymentCreateAPIView,
    SubscriptionPaymentRetrieveAPIView,
    SubscriptionPaymentUpdateAPIView,
    SubscriptionPaymentDeleteAPIView,

    # HTML
    SubscriptionCheckoutPageView,
    SubscriptionPlansPageView,
)

app_name = "subscriptions_api"

api_urlpatterns = [
    # ==========================
    # Тарифные планы
    # ==========================
    path(
        "plans/",
        SubscriptionPlanListAPIView.as_view(),
        name="subscription_plan_list",
    ),
    path(
        "plans/create/",
        SubscriptionPlanCreateAPIView.as_view(),
        name="subscription_plan_create",
    ),
    path(
        "plans/<int:pk>/",
        SubscriptionPlanRetrieveAPIView.as_view(),
        name="subscription_plan_detail",
    ),
    path(
        "plans/<int:pk>/update/",
        SubscriptionPlanUpdateAPIView.as_view(),
        name="subscription_plan_update",
    ),
    path(
        "plans/<int:pk>/delete/",
        SubscriptionPlanDeleteAPIView.as_view(),
        name="subscription_plan_delete",
    ),

    # ==========================
    # Подписки пользователей
    # ==========================
    path(
        "",
        UserSubscriptionListAPIView.as_view(),
        name="user_subscription_list",
    ),
    path(
        "create/",
        UserSubscriptionCreateAPIView.as_view(),
        name="user_subscription_create",
    ),
    path(
        "<int:pk>/",
        UserSubscriptionRetrieveAPIView.as_view(),
        name="user_subscription_detail",
    ),
    path(
        "<int:pk>/update/",
        UserSubscriptionUpdateAPIView.as_view(),
        name="user_subscription_update",
    ),
    path(
        "<int:pk>/delete/",
        UserSubscriptionDeleteAPIView.as_view(),
        name="user_subscription_delete",
    ),

    # ==========================
    # Платежи
    # ==========================
    path(
        "payments/",
        SubscriptionPaymentListAPIView.as_view(),
        name="subscription_payment_list",
    ),
    path(
        "payments/create/",
        SubscriptionPaymentCreateAPIView.as_view(),
        name="subscription_payment_create",
    ),
    path(
        "payments/<int:pk>/",
        SubscriptionPaymentRetrieveAPIView.as_view(),
        name="subscription_payment_detail",
    ),
    path(
        "payments/<int:pk>/update/",
        SubscriptionPaymentUpdateAPIView.as_view(),
        name="subscription_payment_update",
    ),
    path(
        "payments/<int:pk>/delete/",
        SubscriptionPaymentDeleteAPIView.as_view(),
        name="subscription_payment_delete",
    ),
]

web_urlpatterns = [
    path("", SubscriptionPlansPageView.as_view(), name="plans"),
    path(
        "payment/<int:plan_id>/",
        SubscriptionCheckoutPageView.as_view(),
        name="payment",
    ),
]

# Совместимость с прямым include("apps.subscriptions.urls").
urlpatterns = api_urlpatterns
