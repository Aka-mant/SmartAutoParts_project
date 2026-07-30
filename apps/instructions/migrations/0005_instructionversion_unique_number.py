from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        (
            "instructions",
            "0004_instruction_publication_and_authors",
        ),
    ]

    operations = [
        migrations.AddConstraint(
            model_name="instructionversion",
            constraint=models.UniqueConstraint(
                fields=("instruction", "version_number"),
                name="instruction_version_number_uniq",
            ),
        ),
    ]
