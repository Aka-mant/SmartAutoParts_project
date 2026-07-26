from django.test import TestCase

from .models import Tool
from .serializers import (
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
