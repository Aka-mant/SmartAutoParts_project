# Generated manually for the AI instruction revision workflow.

import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("AI", "0001_initial"),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.AddField(
            model_name="aigeneratedinstruction",
            name="is_cached",
            field=models.BooleanField(
                default=False,
                help_text=(
                    "The saved published instruction was returned "
                    "without regeneration."
                ),
                verbose_name="Returned from cache",
            ),
        ),
        migrations.AddField(
            model_name="aigeneratedinstruction",
            name="moderation_note",
            field=models.TextField(
                blank=True,
                verbose_name="Moderation note",
            ),
        ),
        migrations.AddField(
            model_name="aigeneratedinstruction",
            name="moderation_status",
            field=models.CharField(
                choices=[
                    ("pending", "Pending moderation"),
                    ("approved", "Approved"),
                    ("rejected", "Rejected"),
                ],
                db_index=True,
                default="pending",
                max_length=20,
                verbose_name="Moderation status",
            ),
        ),
        migrations.AddField(
            model_name="aigeneratedinstruction",
            name="reviewed_at",
            field=models.DateTimeField(
                blank=True,
                null=True,
                verbose_name="Reviewed at",
            ),
        ),
        migrations.AddField(
            model_name="aigeneratedinstruction",
            name="reviewed_by",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name="reviewed_ai_instructions",
                to=settings.AUTH_USER_MODEL,
                verbose_name="Reviewed by",
            ),
        ),
        migrations.AddField(
            model_name="aigeneratedinstruction",
            name="version_number",
            field=models.PositiveIntegerField(
                default=1,
                help_text=(
                    "Published or proposed instruction version "
                    "returned to the user."
                ),
                verbose_name="Version number",
            ),
        ),
    ]
