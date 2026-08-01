from tempfile import TemporaryDirectory
from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase, override_settings
from django.urls import reverse
from rest_framework.exceptions import ValidationError

from apps.parts.models import Part

from .models import PartTool, Tool, ToolCategory, ToolImage
from .serializers import (
    PartToolCreateSerializer,
    ToolCategoryCreateSerializer,
    ToolCategoryUpdateSerializer,
    ToolCreateSerializer,
    ToolSerializer,
    ToolUpdateSerializer,
)


class ToolSerializerTests(TestCase):
    """Проверяет согласованность API инструмента с моделью Tool."""

    def test_serializers_use_ozon_url_model_field(self):
        tool = Tool.objects.create(
            name="Динамометрический ключ",
            ozon_url="https://www.ozon.ru/example/",
        )

        self.assertEqual(
            ToolSerializer(tool).data["ozon_url"],
            tool.ozon_url,
        )
        self.assertIn("ozon_url", ToolCreateSerializer().fields)
        self.assertIn("ozon_url", ToolUpdateSerializer().fields)


class ToolSerializerValidationTests(TestCase):
    """Проверяет успешные и конфликтующие связи каталога инструментов."""

    def setUp(self):
        self.category = ToolCategory.objects.create(
            name="Диагностическое оборудование",
            slug="diagnostic-equipment",
        )
        self.part = Part.objects.create(
            name="Датчик тестовой системы",
            slug="test-system-sensor",
            original_number="TEST-SENSOR-001",
        )
        self.tool = Tool.objects.create(
            category=self.category,
            name="Тестовый мультиметр",
        )

    def test_category_serializers_accept_available_slug(self):
        """Разрешает новый slug при создании и обновлении категории."""

        create_serializer = ToolCategoryCreateSerializer()
        self.assertEqual(
            create_serializer.validate_slug("new-diagnostic-tools"),
            "new-diagnostic-tools",
        )

        update_serializer = ToolCategoryUpdateSerializer(
            instance=self.category,
        )
        self.assertEqual(
            update_serializer.validate_slug("updated-diagnostic-tools"),
            "updated-diagnostic-tools",
        )

    def test_part_tool_serializer_accepts_new_relation(self):
        """Разрешает первичную связь детали с инструментом."""

        attrs = {
            "part": self.part,
            "tool": self.tool,
            "required": True,
        }
        serializer = PartToolCreateSerializer()

        self.assertEqual(serializer.validate(attrs), attrs)

        PartTool.objects.create(part=self.part, tool=self.tool)
        with self.assertRaises(ValidationError):
            serializer.validate(attrs)


class ToolPageAndImageTests(TestCase):
    """Проверяет доступ, галерею и файловые ветви инструментов."""

    def setUp(self):
        self.media_directory = TemporaryDirectory()
        self.media_override = override_settings(
            MEDIA_ROOT=self.media_directory.name,
        )
        self.media_override.enable()
        self.addCleanup(self.media_override.disable)
        self.addCleanup(self.media_directory.cleanup)
        self.category = ToolCategory.objects.create(
            name="Ключи",
            slug="test-keys",
        )
        self.tool = Tool.objects.create(
            category=self.category,
            name="Тестовый ключ",
            image=SimpleUploadedFile("main.jpg", b"main-image"),
        )
        self.extra_image = ToolImage.objects.create(
            tool=self.tool,
            image=SimpleUploadedFile("extra.jpg", b"extra-image"),
            alt_text="Дополнительный ракурс",
        )

    def test_superuser_sees_complete_tool_gallery(self):
        user = get_user_model().objects.create_superuser(
            username="tool-admin",
            email="tool-admin@example.com",
            password="safe-test-password",
        )
        self.client.force_login(user)

        response = self.client.get(self.tool.get_absolute_url())

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Тестовый ключ")
        self.assertContains(response, "Дополнительный ракурс")
        self.assertEqual(len(response.context["tool_gallery_images"]), 2)
        self.assertEqual(str(self.tool), self.tool.name)
        self.assertIn(self.tool.name, str(self.extra_image))

    def test_user_without_tariff_is_redirected_from_tool_card(self):
        user = get_user_model().objects.create_user(
            username="tool-free-user",
            email="tool-free-user@example.com",
            password="safe-test-password",
        )
        self.client.force_login(user)

        response = self.client.get(
            reverse("tools_web:detail", kwargs={"pk": self.tool.pk})
        )

        self.assertRedirects(
            response,
            reverse("subscriptions_web:plans"),
            fetch_redirect_response=False,
        )

    def test_image_exists_handles_empty_and_storage_errors(self):
        empty_tool = Tool.objects.create(name="Без изображения")
        empty_image = ToolImage(tool=empty_tool)
        self.assertFalse(empty_tool.image_exists)
        self.assertFalse(empty_image.image_exists)

        with patch.object(
            self.tool.image.storage,
            "exists",
            side_effect=OSError,
        ):
            self.assertFalse(self.tool.image_exists)
            self.assertFalse(self.extra_image.image_exists)
