# Generated manually for the SmartAutoParts tool gallery.

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):
    """Добавляет галерею изображений инструментов."""

    dependencies = [
        ("tools", "0002_remove_tool_amazon_url_tool_ozon_url"),
    ]

    operations = [
        migrations.CreateModel(
            name="ToolImage",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                (
                    "image",
                    models.ImageField(
                        upload_to="tools/images/",
                        verbose_name="Image",
                    ),
                ),
                (
                    "alt_text",
                    models.CharField(
                        blank=True,
                        max_length=255,
                        verbose_name="Alternative text",
                    ),
                ),
                (
                    "is_main",
                    models.BooleanField(
                        default=False,
                        verbose_name="Main image",
                    ),
                ),
                (
                    "uploaded_at",
                    models.DateTimeField(
                        auto_now_add=True,
                        verbose_name="Uploaded at",
                    ),
                ),
                (
                    "tool",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="images",
                        to="tools.tool",
                        verbose_name="Tool",
                    ),
                ),
            ],
            options={
                "verbose_name": "Tool image",
                "verbose_name_plural": "Tool images",
                "db_table": "tools_toolimage",
                "ordering": ("-is_main", "id"),
            },
        ),
    ]
