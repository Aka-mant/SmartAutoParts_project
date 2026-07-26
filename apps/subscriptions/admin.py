from django.contrib import admin

from .models import (
    SubscriptionPayment,
    SubscriptionPlan,
    UserSubscription,
)


@admin.register(SubscriptionPlan)
class SubscriptionPlanAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "name",
        "price",
        "duration_days",
        "max_ai_requests",
        "is_public",
        "sort_order",
    )
    list_editable = ("price", "is_public", "sort_order")
    search_fields = ("name",)
    ordering = ("sort_order", "price")


@admin.register(UserSubscription)
class UserSubscriptionAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "user",
        "plan",
        "start_date",
        "end_date",
        "is_active",
        "auto_renew",
    )
    list_filter = ("is_active", "auto_renew", "plan")
    search_fields = ("user__email", "user__username")
    autocomplete_fields = ("user", "plan")


@admin.register(SubscriptionPayment)
class SubscriptionPaymentAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "user",
        "subscription",
        "amount",
        "currency",
        "status",
        "paid_at",
    )
    list_filter = ("status", "currency")
    search_fields = ("user__email", "external_payment_id")
    autocomplete_fields = ("user", "subscription")
