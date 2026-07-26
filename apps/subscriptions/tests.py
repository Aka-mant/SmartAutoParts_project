from datetime import timedelta

from django.conf import settings
from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone
from rest_framework.test import APIClient

from apps.AI.models import AIRequest
from apps.AI.services import (
    AIAccessDenied,
    AIQuotaExceeded,
    AIQuotaService,
)
from users.models import UserAgreementAcceptance

from .models import (
    SubscriptionPayment,
    SubscriptionPlan,
    UserSubscription,
)
from .serializers import SubscriptionPlanCreateSerializer


class SubscriptionPlanPageTests(TestCase):
    def setUp(self):
        self.hidden_plan = SubscriptionPlan.objects.create(
            name="Архивный",
            description="Не должен показываться.",
            price="1.00",
            duration_days=1,
            max_ai_requests=1,
            has_chat_access=False,
            has_instruction_generation=False,
            has_image_analysis=False,
            is_public=False,
        )

    def test_seed_contains_exactly_three_public_plans(self):
        self.assertQuerySetEqual(
            SubscriptionPlan.objects.filter(is_public=True).values_list(
                "name",
                flat=True,
            ),
            ["Старт", "Стандарт", "Профессиональный"],
            ordered=True,
        )

    def test_pricing_page_displays_public_plans_only(self):
        response = self.client.get(
            reverse("subscriptions_web:plans")
        )

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Старт")
        self.assertContains(response, "Стандарт")
        self.assertContains(response, "Профессиональный")
        self.assertNotContains(response, self.hidden_plan.name)
        self.assertEqual(len(response.context["plans"]), 3)
        self.assertContains(response, "1170")
        self.assertContains(response, "2970")
        self.assertContains(response, "7470")
        self.assertNotContains(
            response,
            "Получение сохранённой AI-инструкции",
        )

    def test_pricing_page_marks_current_plan(self):
        user = get_user_model().objects.create_user(
            username="subscriber",
            email="subscriber@example.com",
            password="test-password",
        )
        plan = SubscriptionPlan.objects.get(name="Стандарт")
        UserSubscription.objects.create(
            user=user,
            plan=plan,
            start_date=timezone.now() - timedelta(days=1),
            end_date=timezone.now() + timedelta(days=29),
            is_active=True,
        )
        self.client.force_login(user)
        UserAgreementAcceptance.objects.create(
            user=user,
            agreement_version=settings.USER_AGREEMENT_VERSION,
        )

        response = self.client.get(
            reverse("subscriptions_web:plans")
        )

        self.assertContains(response, "Ваш текущий тариф")
        self.assertContains(response, "Текущий тариф")

    def test_plan_serializer_rejects_feature_limit_above_total(self):
        serializer = SubscriptionPlanCreateSerializer(
            data={
                "name": "Некорректный",
                "description": "",
                "price": "100.00",
                "duration_days": 30,
                "max_ai_requests": 10,
                "max_chat_requests": 11,
                "max_instruction_requests": 0,
                "max_image_analyses": 0,
                "has_chat_access": True,
                "has_instruction_generation": False,
                "has_image_analysis": False,
                "is_public": False,
                "sort_order": 99,
            }
        )

        self.assertFalse(serializer.is_valid())
        self.assertIn("max_chat_requests", serializer.errors)

    def test_plan_api_hides_non_public_plans(self):
        user = get_user_model().objects.create_user(
            username="api-subscriber",
            email="api-subscriber@example.com",
            password="test-password",
        )
        client = APIClient()
        client.force_authenticate(user)

        response = client.get(
            reverse("subscriptions_api:subscription_plan_list")
        )

        self.assertEqual(response.status_code, 200)
        payload = response.json()
        results = payload.get("results", payload)
        self.assertNotIn(
            self.hidden_plan.name,
            {item["name"] for item in results},
        )

    def create_checkout_user(self):
        user = get_user_model().objects.create_user(
            username="checkout-user",
            email="checkout@example.com",
            password="test-password",
        )
        UserAgreementAcceptance.objects.create(
            user=user,
            agreement_version=settings.USER_AGREEMENT_VERSION,
        )
        return user

    def test_payment_page_requires_login(self):
        plan = SubscriptionPlan.objects.get(name="Старт")

        response = self.client.get(
            reverse(
                "subscriptions_web:payment",
                kwargs={"plan_id": plan.pk},
            )
        )

        self.assertEqual(response.status_code, 302)
        self.assertIn(reverse("users:login"), response.url)

    def test_payment_page_displays_supported_payment_methods(self):
        user = self.create_checkout_user()
        plan = SubscriptionPlan.objects.get(name="Старт")
        self.client.force_login(user)

        response = self.client.get(
            reverse(
                "subscriptions_web:payment",
                kwargs={"plan_id": plan.pk},
            )
        )

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Система быстрых платежей")
        self.assertContains(response, "Банковская карта")
        self.assertContains(response, "Банковский перевод")
        self.assertContains(response, 'name="payment_method"', count=11)
        self.assertContains(response, "деньги не списываются")

    def test_demo_payment_activates_selected_plan_and_records_payment(self):
        user = self.create_checkout_user()
        old_plan = SubscriptionPlan.objects.get(name="Старт")
        selected_plan = SubscriptionPlan.objects.get(name="Стандарт")
        old_subscription = UserSubscription.objects.create(
            user=user,
            plan=old_plan,
            start_date=timezone.now() - timedelta(days=2),
            end_date=timezone.now() + timedelta(days=10),
            is_active=True,
        )
        self.client.force_login(user)

        response = self.client.post(
            reverse(
                "subscriptions_web:payment",
                kwargs={"plan_id": selected_plan.pk},
            ),
            {"payment_method": "sbp"},
        )

        self.assertRedirects(
            response,
            reverse("users:dashboard"),
            fetch_redirect_response=False,
        )
        old_subscription.refresh_from_db()
        self.assertFalse(old_subscription.is_active)
        subscription = UserSubscription.objects.get(
            user=user,
            is_active=True,
        )
        self.assertEqual(subscription.plan, selected_plan)
        payment = SubscriptionPayment.objects.get(
            subscription=subscription
        )
        self.assertEqual(payment.amount, selected_plan.price)
        self.assertEqual(payment.currency, "RUB")
        self.assertEqual(payment.status, "succeeded")
        self.assertIn("Система быстрых платежей", payment.provider)

    def test_payment_rejects_unknown_method_and_private_plan(self):
        user = self.create_checkout_user()
        public_plan = SubscriptionPlan.objects.get(name="Старт")
        self.client.force_login(user)

        invalid_method = self.client.post(
            reverse(
                "subscriptions_web:payment",
                kwargs={"plan_id": public_plan.pk},
            ),
            {"payment_method": "unknown"},
        )
        private_plan = self.client.get(
            reverse(
                "subscriptions_web:payment",
                kwargs={"plan_id": self.hidden_plan.pk},
            )
        )

        self.assertEqual(invalid_method.status_code, 400)
        self.assertFalse(
            UserSubscription.objects.filter(user=user).exists()
        )
        self.assertFalse(
            SubscriptionPayment.objects.filter(user=user).exists()
        )
        self.assertEqual(private_plan.status_code, 404)


class AIQuotaFeatureTests(TestCase):
    def setUp(self):
        self.user = get_user_model().objects.create_user(
            username="quota-user",
            email="quota@example.com",
            password="test-password",
        )
        UserAgreementAcceptance.objects.create(
            user=self.user,
            agreement_version=settings.USER_AGREEMENT_VERSION,
        )
        self.plan = SubscriptionPlan.objects.create(
            name="Лимитный",
            description="Тест отдельных лимитов.",
            price="100.00",
            duration_days=30,
            max_ai_requests=5,
            max_chat_requests=1,
            max_instruction_requests=2,
            max_image_analyses=2,
            has_chat_access=True,
            has_instruction_generation=True,
            has_image_analysis=True,
            is_public=False,
        )
        self.subscription = UserSubscription.objects.create(
            user=self.user,
            plan=self.plan,
            start_date=timezone.now() - timedelta(days=1),
            end_date=timezone.now() + timedelta(days=29),
            is_active=True,
        )

    def test_chat_limit_does_not_block_available_image_quota(self):
        AIRequest.objects.create(
            user=self.user,
            prompt="Чат",
            response="Ответ",
            request_type="chat",
        )
        quota = AIQuotaService()

        with self.assertRaises(AIQuotaExceeded):
            quota.check(self.user, feature="chat")

        self.assertEqual(
            quota.check(self.user, feature="image_analysis"),
            self.subscription,
        )

    def test_cached_instruction_spends_instruction_quota(self):
        for index in range(2):
            AIRequest.objects.create(
                user=self.user,
                prompt=f"Инструкция {index}",
                response="Сохранённое содержимое",
                request_type="repair_instruction_cached",
            )

        with self.assertRaises(AIQuotaExceeded):
            AIQuotaService().check(
                self.user,
                feature="instruction",
            )

    def test_tool_recommendation_spends_chat_quota(self):
        AIRequest.objects.create(
            user=self.user,
            prompt="Подбор инструмента",
            response="Набор ключей",
            request_type="tool_recommendation_moderation_pending",
        )

        with self.assertRaises(AIQuotaExceeded):
            AIQuotaService().check(
                self.user,
                feature="chat",
            )

    def test_superuser_has_unlimited_ai_access_without_subscription(self):
        superuser = get_user_model().objects.create_superuser(
            username="quota-root",
            email="quota-root@example.com",
            password="test-password",
        )
        UserAgreementAcceptance.objects.create(
            user=superuser,
            agreement_version=settings.USER_AGREEMENT_VERSION,
        )

        self.assertIsNone(
            AIQuotaService().check(superuser, feature="chat")
        )
        self.assertIsNone(
            AIQuotaService().check(superuser, feature="instruction")
        )

    def test_moderator_cannot_send_ai_requests(self):
        moderator = get_user_model().objects.create_user(
            username="quota-moderator",
            email="quota-moderator@example.com",
            password="test-password",
            role="moderator",
            is_staff=True,
        )
        UserAgreementAcceptance.objects.create(
            user=moderator,
            agreement_version=settings.USER_AGREEMENT_VERSION,
        )

        with self.assertRaises(AIAccessDenied):
            AIQuotaService().check(moderator, feature="chat")
