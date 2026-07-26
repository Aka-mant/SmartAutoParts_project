from urllib.parse import urlencode

from django.conf import settings
from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from apps.instructions.models import Instruction, InstructionStep
from apps.parts.models import Part
from users.models import (
    RepairHistory,
    SearchHistory,
    UserAgreementAcceptance,
)


class UserAgreementTests(TestCase):
    """Проверяет обязательное и версионируемое принятие соглашения."""

    def setUp(self):
        self.user = get_user_model().objects.create_user(
            username="agreement-user",
            email="agreement@example.com",
            password="safe-test-password",
        )
        self.client.force_login(self.user)

    def test_first_service_page_redirects_to_agreement(self):
        response = self.client.get(reverse("users:dashboard"))

        self.assertEqual(response.status_code, 302)
        self.assertTrue(
            response.url.startswith(reverse("users:user_agreement"))
        )
        self.assertIn("next=", response.url)

    def test_acceptance_is_recorded_and_allows_service_page(self):
        response = self.client.post(
            reverse("users:user_agreement"),
            {
                "agreement_accepted": "on",
                "next": reverse("users:dashboard"),
            },
        )

        self.assertRedirects(
            response,
            reverse("users:dashboard"),
            fetch_redirect_response=False,
        )
        self.assertTrue(
            UserAgreementAcceptance.objects.filter(
                user=self.user,
                agreement_version=settings.USER_AGREEMENT_VERSION,
            ).exists()
        )

        dashboard = self.client.get(reverse("users:dashboard"))
        self.assertEqual(dashboard.status_code, 200)

    def test_acceptance_requires_checkbox(self):
        response = self.client.post(
            reverse("users:user_agreement"),
            {"next": reverse("users:dashboard")},
        )

        self.assertEqual(response.status_code, 200)
        self.assertFalse(
            UserAgreementAcceptance.objects.filter(
                user=self.user,
            ).exists()
        )


class DashboardAccessPresentationTests(TestCase):
    """Проверяет счётчики и служебные состояния личного кабинета."""

    def accept(self, user):
        UserAgreementAcceptance.objects.create(
            user=user,
            agreement_version=settings.USER_AGREEMENT_VERSION,
        )

    def test_free_card_has_no_ai_counter(self):
        user = get_user_model().objects.create_user(
            username="free-dashboard",
            email="free-dashboard@example.com",
            password="safe-test-password",
        )
        self.accept(user)
        self.client.force_login(user)

        response = self.client.get(reverse("users:dashboard"))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Без подписки")
        self.assertNotContains(response, "AI-запросы</span>")
        self.assertContains(response, "Выбрать тариф")

    def test_superuser_counters_are_unlimited_without_purchase_banner(self):
        user = get_user_model().objects.create_superuser(
            username="unlimited-dashboard",
            email="unlimited-dashboard@example.com",
            password="safe-test-password",
        )
        self.accept(user)
        self.client.force_login(user)

        response = self.client.get(reverse("users:dashboard"))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Безлимит", count=5)
        self.assertNotContains(
            response,
            "card-body p-4 p-lg-5 position-relative",
        )
        self.assertNotContains(response, "Выбрать тариф")


class SearchHistoryLinkTests(TestCase):
    """Проверяет повторный поиск из истории пользователя."""

    def setUp(self):
        self.user = get_user_model().objects.create_user(
            username="history-user",
            email="history@example.com",
            password="safe-test-password",
        )
        UserAgreementAcceptance.objects.create(
            user=self.user,
            agreement_version=settings.USER_AGREEMENT_VERSION,
        )
        self.part = Part.objects.create(
            name="Тестовый масляный фильтр",
            slug="test-oil-filter",
            original_number="OEM-TEST-001",
            manufacturer="SmartAutoParts",
            description="Деталь для проверки истории поиска.",
        )
        self.history = SearchHistory.objects.create(
            user=self.user,
            original_number=self.part.original_number,
            search_query="масляный фильтр",
            result_found=True,
        )
        self.client.force_login(self.user)

    def test_history_item_builds_url_for_displayed_oem_number(self):
        expected_url = (
            f"{reverse('users:part_search')}?"
            f"{urlencode({'q': self.part.original_number})}"
        )

        self.assertEqual(
            self.history.get_search_results_url(),
            expected_url,
        )

    def test_history_page_contains_link_to_saved_search_results(self):
        response = self.client.get(reverse("users:search_history"))

        self.assertEqual(response.status_code, 200)
        self.assertContains(
            response,
            f'href="{self.history.get_search_results_url()}"',
            html=False,
        )

    def test_history_link_opens_results_for_displayed_part(self):
        response = self.client.get(
            self.history.get_search_results_url(),
        )

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, self.part.name)
        self.assertEqual(
            response.context["search_query"],
            self.part.original_number,
        )


class RepairStepNavigationTests(TestCase):
    """Проверяет сохранение и безопасную навигацию по шагам ремонта."""

    def setUp(self):
        user_model = get_user_model()
        self.user = user_model.objects.create_user(
            username="repair-user",
            email="repair@example.com",
            password="safe-test-password",
        )
        self.other_user = user_model.objects.create_user(
            username="other-repair-user",
            email="other-repair@example.com",
            password="safe-test-password",
        )
        self.superuser = user_model.objects.create_superuser(
            username="repair-root",
            email="repair-root@example.com",
            password="safe-test-password",
        )
        for accepted_user in (
            self.user,
            self.other_user,
            self.superuser,
        ):
            UserAgreementAcceptance.objects.create(
                user=accepted_user,
                agreement_version=settings.USER_AGREEMENT_VERSION,
            )
        self.part = Part.objects.create(
            name="Тестовый амортизатор",
            slug="repair-test-shock",
            original_number="SHOCK-TEST-001",
        )
        self.instruction = Instruction.objects.create(
            part=self.part,
            title="Замена тестового амортизатора",
            slug="replace-repair-test-shock",
            content="Проверенная инструкция.",
            is_published=True,
        )
        for number in range(1, 4):
            InstructionStep.objects.create(
                instruction=self.instruction,
                step_number=number,
                title=f"Шаг {number}",
                description=f"Описание шага {number}.",
            )
        self.repair = RepairHistory.objects.create(
            user=self.user,
            instruction=self.instruction,
        )
        self.url = reverse(
            "users:repair_step_navigation",
            kwargs={"pk": self.repair.pk},
        )

    def test_new_repair_starts_at_first_step(self):
        self.assertEqual(self.repair.current_step, 1)

    def test_owner_can_move_to_next_and_previous_step(self):
        self.client.force_login(self.user)

        self.client.post(self.url, {"action": "next"})
        self.repair.refresh_from_db()
        self.assertEqual(self.repair.current_step, 2)

        self.client.post(self.url, {"action": "previous"})
        self.repair.refresh_from_db()
        self.assertEqual(self.repair.current_step, 1)

    def test_navigation_does_not_cross_first_or_last_step(self):
        self.client.force_login(self.user)

        self.client.post(self.url, {"action": "previous"})
        self.repair.refresh_from_db()
        self.assertEqual(self.repair.current_step, 1)

        self.repair.current_step = 3
        self.repair.save()
        self.client.post(self.url, {"action": "next"})
        self.repair.refresh_from_db()
        self.assertEqual(self.repair.current_step, 3)

    def test_user_cannot_change_another_users_repair(self):
        self.client.force_login(self.other_user)

        response = self.client.post(self.url, {"action": "next"})

        self.assertEqual(response.status_code, 404)
        self.repair.refresh_from_db()
        self.assertEqual(self.repair.current_step, 1)

    def test_superuser_can_change_any_repair(self):
        self.client.force_login(self.superuser)

        response = self.client.post(self.url, {"action": "next"})

        self.assertEqual(response.status_code, 302)
        self.repair.refresh_from_db()
        self.assertEqual(self.repair.current_step, 2)

    def test_completed_repair_cannot_be_navigated(self):
        self.repair.completed = True
        self.repair.save()
        self.client.force_login(self.user)

        response = self.client.post(self.url, {"action": "next"})

        self.assertEqual(response.status_code, 404)

    def test_dashboard_shows_previous_and_next_buttons(self):
        self.client.force_login(self.user)

        response = self.client.get(reverse("users:dashboard"))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Предыдущий шаг")
        self.assertContains(response, "Следующий шаг")
        self.assertContains(response, "Шаг 1")

    def test_repair_history_shows_navigation_for_unfinished_repair(self):
        self.client.force_login(self.user)

        response = self.client.get(
            reverse("users:repair_history_list")
        )

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Предыдущий шаг")
        self.assertContains(response, "Следующий шаг")
        self.assertContains(response, "из 3")
