from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse
from rest_framework.test import APIClient


class AnalyticsSuperuserAccessTests(TestCase):
    def setUp(self):
        self.user = get_user_model().objects.create_user(
            username="analytics-user",
            email="analytics-user@example.com",
            password="test-password",
        )
        self.superuser = get_user_model().objects.create_superuser(
            username="analytics-root",
            email="analytics-root@example.com",
            password="test-password",
        )

    def test_regular_user_cannot_read_or_create_analytics(self):
        client = APIClient()
        client.force_authenticate(self.user)

        list_response = client.get(
            reverse("apps.analytics:user_activity_list")
        )
        create_response = client.post(
            reverse("apps.analytics:user_activity_create"),
            {"action": "private-event"},
            format="json",
        )

        self.assertEqual(list_response.status_code, 403)
        self.assertEqual(create_response.status_code, 403)

    def test_superuser_can_open_analytics(self):
        client = APIClient()
        client.force_authenticate(self.superuser)

        response = client.get(
            reverse("apps.analytics:user_activity_list")
        )

        self.assertEqual(response.status_code, 200)
