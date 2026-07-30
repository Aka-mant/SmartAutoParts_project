import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models
from django.utils import timezone


def set_existing_publication_dates(apps, schema_editor):
    Instruction = apps.get_model("instructions", "Instruction")
    for instruction in Instruction.objects.filter(
        published_at__isnull=True,
    ).iterator():
        Instruction.objects.filter(pk=instruction.pk).update(
            published_at=instruction.created_at or timezone.now(),
        )


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(
            settings.AUTH_USER_MODEL),
        ("instructions",
         "0003_instructionstep_instructions_step_instruction_number_uniq"),
    ]

    operations = [
        migrations.AddField(
            model_name="instruction",
            name="is_published",
            field=models.BooleanField(
                db_index=True,
                default=True,
                verbose_name="Published",
            ),
        ),
        migrations.AddField(
            model_name="instruction",
            name="published_at",
            field=models.DateTimeField(
                blank=True,
                null=True,
                verbose_name="Published at",
            ),
        ),
        migrations.AddField(
            model_name="instruction",
            name="updated_by",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name="updated_instructions",
                to=settings.AUTH_USER_MODEL,
                verbose_name="Updated by",
            ),
        ),
        migrations.AddField(
            model_name="instructionversion",
            name="created_by",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name="instruction_versions",
                to=settings.AUTH_USER_MODEL,
                verbose_name="Created by",
            ),
        ),
        migrations.AlterField(
            model_name="instruction",
            name="difficulty",
            field=models.CharField(
                blank=True,
                choices=[
                    ("easy", "Легко"),
                    ("medium", "Средняя"),
                    ("hard", "Сложно"),
                    ("expert", "Экспертная"),
                ],
                max_length=50,
                verbose_name="Difficulty",
            ),
        ),
        migrations.AddIndex(
            model_name="instruction",
            index=models.Index(
                fields=["is_published", "difficulty"],
                name="instruction_public_diff_idx",
            ),
        ),
        migrations.AddIndex(
            model_name="instruction",
            index=models.Index(
                fields=["part", "premium_only"],
                name="instruction_part_premium_idx",
            ),
        ),
        migrations.RunPython(
            set_existing_publication_dates,
            migrations.RunPython.noop,
        ),
    ]
