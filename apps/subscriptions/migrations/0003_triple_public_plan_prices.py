from decimal import Decimal

from django.db import migrations


NEW_PRICES = {
    "Старт": Decimal("1170.00"),
    "Стандарт": Decimal("2970.00"),
    "Профессиональный": Decimal("7470.00"),
}

OLD_PRICES = {
    "Старт": Decimal("390.00"),
    "Стандарт": Decimal("990.00"),
    "Профессиональный": Decimal("2490.00"),
}


def set_prices(apps, prices):
    SubscriptionPlan = apps.get_model(
        "subscriptions",
        "SubscriptionPlan",
    )
    for name, price in prices.items():
        SubscriptionPlan.objects.filter(name=name).update(price=price)


def triple_prices(apps, schema_editor):
    set_prices(apps, NEW_PRICES)


def restore_prices(apps, schema_editor):
    set_prices(apps, OLD_PRICES)


class Migration(migrations.Migration):

    dependencies = [
        ("subscriptions", "0002_subscription_plan_ai_limits"),
    ]

    operations = [
        migrations.RunPython(triple_prices, restore_prices),
    ]
