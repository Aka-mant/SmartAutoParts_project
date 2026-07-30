import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


def backfill_content_purchases(apps, schema_editor):
    AIRequest = apps.get_model("AI", "AIRequest")
    AIGeneratedInstruction = apps.get_model(
        "AI",
        "AIGeneratedInstruction",
    )
    AIContentPurchase = apps.get_model("AI", "AIContentPurchase")

    for request in AIRequest.objects.filter(request_type="chat").iterator():
        AIContentPurchase.objects.get_or_create(
            user_id=request.user_id,
            content_type="chat",
            content_key=f"chat:{request.pk}",
            defaults={
                "part_id": request.part_id,
                "source_request_id": request.pk,
                "source": "ai",
            },
        )

    for generated in (
        AIGeneratedInstruction.objects.select_related("ai_request")
        .exclude(ai_request__request_type__endswith="_blocked")
        .iterator()
    ):
        request = generated.ai_request
        content_key = (
            f"instruction:{generated.instruction_id}"
            if generated.instruction_id
            else f"instruction-request:{request.pk}"
        )
        AIContentPurchase.objects.get_or_create(
            user_id=request.user_id,
            content_type="instruction",
            content_key=content_key,
            defaults={
                "part_id": request.part_id,
                "instruction_id": generated.instruction_id,
                "source_request_id": request.pk,
                "source": "database" if generated.is_cached else "ai",
            },
        )

    tool_requests = (
        AIRequest.objects.filter(
            request_type__startswith="tool_recommendation",
            part_id__isnull=False,
        )
        .exclude(request_type__endswith="_blocked")
        .order_by("created_at", "pk")
    )
    for request in tool_requests.iterator():
        AIContentPurchase.objects.get_or_create(
            user_id=request.user_id,
            content_type="tools",
            content_key=f"tools:{request.part_id}",
            defaults={
                "part_id": request.part_id,
                "source_request_id": request.pk,
                "source": "ai",
            },
        )


class Migration(migrations.Migration):

    dependencies = [
        ("AI", "0003_aiimageanalysis_moderation_categories_and_more"),
        ("instructions", "0005_instructionversion_unique_number"),
        ("parts", "0004_alter_part_dimensions"),
        ("subscriptions", "0003_triple_public_plan_prices"),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name="AIContentPurchase",
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
                    "content_type",
                    models.CharField(
                        choices=[
                            ("chat", "AI chat response"),
                            ("instruction", "Repair instruction"),
                            ("tools", "Tool selection"),
                        ],
                        db_index=True,
                        max_length=20,
                        verbose_name="Content type",
                    ),
                ),
                (
                    "content_key",
                    models.CharField(
                        help_text=(
                            "Stable identifier used to prevent "
                            "a repeated purchase."
                        ),
                        max_length=160,
                        verbose_name="Content key",
                    ),
                ),
                (
                    "source",
                    models.CharField(
                        choices=[
                            ("database", "Project database"),
                            ("ai", "AI generation"),
                        ],
                        default="ai",
                        max_length=20,
                        verbose_name="Content source",
                    ),
                ),
                (
                    "purchased_at",
                    models.DateTimeField(
                        auto_now_add=True,
                        verbose_name="Purchased at",
                    ),
                ),
                (
                    "last_accessed_at",
                    models.DateTimeField(
                        auto_now=True,
                        verbose_name="Last accessed at",
                    ),
                ),
                (
                    "instruction",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        related_name="ai_content_purchases",
                        to="instructions.instruction",
                        verbose_name="Instruction",
                    ),
                ),
                (
                    "part",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        related_name="ai_content_purchases",
                        to="parts.part",
                        verbose_name="Part",
                    ),
                ),
                (
                    "source_request",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        related_name="content_purchases",
                        to="AI.airequest",
                        verbose_name="Source AI request",
                    ),
                ),
                (
                    "subscription",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        related_name="content_purchases",
                        to="subscriptions.usersubscription",
                        verbose_name="Subscription",
                    ),
                ),
                (
                    "user",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="ai_content_purchases",
                        to=settings.AUTH_USER_MODEL,
                        verbose_name="User",
                    ),
                ),
            ],
            options={
                "verbose_name": "AI content purchase",
                "verbose_name_plural": "AI content purchases",
                "db_table": "ai_aicontentpurchase",
                "ordering": ("-purchased_at",),
                "indexes": [
                    models.Index(
                        fields=["user", "content_type", "part"],
                        name="ai_purchase_user_part_idx",
                    ),
                    models.Index(
                        fields=["user", "content_type", "instruction"],
                        name="ai_purchase_user_instr_idx",
                    ),
                ],
                "constraints": [
                    models.UniqueConstraint(
                        fields=("user", "content_type", "content_key"),
                        name="ai_purchase_user_type_key_uniq",
                    ),
                ],
            },
        ),
        migrations.RunPython(
            backfill_content_purchases,
            migrations.RunPython.noop,
        ),
    ]
