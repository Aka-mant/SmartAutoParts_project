# flake8: noqa: E501

from django.db import migrations, models


PLANS = (
    {
        "name": "Старт",
        "description": (
            "Для самостоятельного обслуживания: базовый AI-чат "
            "и готовые пошаговые инструкции."
        ),
        "price": "390.00",
        "duration_days": 30,
        "max_ai_requests": 30,
        "max_chat_requests": 20,
        "max_instruction_requests": 10,
        "max_image_analyses": 0,
        "has_chat_access": True,
        "has_instruction_generation": True,
        "has_image_analysis": False,
        "is_public": True,
        "sort_order": 10,
    },
    {
        "name": "Стандарт",
        "description": (
            "Для регулярного ремонта: расширенные лимиты, "
            "генерация инструкций и анализ фотографий."
        ),
        "price": "990.00",
        "duration_days": 30,
        "max_ai_requests": 120,
        "max_chat_requests": 80,
        "max_instruction_requests": 30,
        "max_image_analyses": 10,
        "has_chat_access": True,
        "has_instruction_generation": True,
        "has_image_analysis": True,
        "is_public": True,
        "sort_order": 20,
    },
    {
        "name": "Профессиональный",
        "description": (
            "Для мастерских и интенсивной работы: максимальные "
            "лимиты всех AI-возможностей."
        ),
        "price": "2490.00",
        "duration_days": 30,
        "max_ai_requests": 500,
        "max_chat_requests": 320,
        "max_instruction_requests": 120,
        "max_image_analyses": 60,
        "has_chat_access": True,
        "has_instruction_generation": True,
        "has_image_analysis": True,
        "is_public": True,
        "sort_order": 30,
    },
)


def seed_plans(apps, schema_editor):
    SubscriptionPlan = apps.get_model(
        "subscriptions",
        "SubscriptionPlan",
    )
    names = [item["name"] for item in PLANS]
    SubscriptionPlan.objects.exclude(name__in=names).update(is_public=False)

    for item in PLANS:
        SubscriptionPlan.objects.update_or_create(
            name=item["name"],
            defaults=item,
        )


def unpublish_seeded_plans(apps, schema_editor):
    SubscriptionPlan = apps.get_model(
        "subscriptions",
        "SubscriptionPlan",
    )
    SubscriptionPlan.objects.filter(
        name__in=[item["name"] for item in PLANS]
    ).update(is_public=False)


class Migration(migrations.Migration):

    dependencies = [
        ("subscriptions", "0001_initial"),
    ]

    operations = [
        migrations.AddField(
            model_name="subscriptionplan",
            name="has_instruction_generation",
            field=models.BooleanField(
                default=True,
                help_text="Allows generating and retrieving AI repair instructions.",
                verbose_name="Instruction generation",
            ),
        ),
        migrations.AddField(
            model_name="subscriptionplan",
            name="is_public",
            field=models.BooleanField(
                db_index=True,
                default=True,
                help_text="Display the plan on the public pricing page.",
                verbose_name="Public",
            ),
        ),
        migrations.AddField(
            model_name="subscriptionplan",
            name="max_chat_requests",
            field=models.PositiveIntegerField(
                blank=True,
                help_text="Chat request limit. Empty value inherits the total AI limit.",
                null=True,
                verbose_name="Maximum chat requests",
            ),
        ),
        migrations.AddField(
            model_name="subscriptionplan",
            name="max_image_analyses",
            field=models.PositiveIntegerField(
                blank=True,
                help_text="Image analysis limit. Empty value inherits the total AI limit.",
                null=True,
                verbose_name="Maximum image analyses",
            ),
        ),
        migrations.AddField(
            model_name="subscriptionplan",
            name="max_instruction_requests",
            field=models.PositiveIntegerField(
                blank=True,
                help_text="Instruction request limit. Empty value inherits the total AI limit.",
                null=True,
                verbose_name="Maximum instruction requests",
            ),
        ),
        migrations.AddField(
            model_name="subscriptionplan",
            name="sort_order",
            field=models.PositiveSmallIntegerField(
                default=0,
                verbose_name="Sort order",
            ),
        ),
        migrations.AlterModelOptions(
            name="subscriptionplan",
            options={
                "ordering": ("sort_order", "price", "id"),
                "verbose_name": "Subscription plan",
                "verbose_name_plural": "Subscription plans",
            },
        ),
        migrations.RunPython(seed_plans, unpublish_seeded_plans),
    ]
