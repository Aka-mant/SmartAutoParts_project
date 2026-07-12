from rest_framework import serializers

from .models import (
    SubscriptionPayment,
    SubscriptionPlan,
    UserSubscription,
)


class SubscriptionPlanSerializer(serializers.ModelSerializer):
    """
    Сериализатор тарифного плана подписки.

    Используется для получения информации
    о доступном тарифном плане.
    """

    class Meta:
        model = SubscriptionPlan
        fields = (
            "id",
            "name",
            "description",
            "price",
            "duration_days",
            "max_ai_requests",
            "has_chat_access",
            "has_image_analysis",
            "created_at",
        )
        read_only_fields = (
            "id",
            "created_at",
        )


class SubscriptionPlanCreateSerializer(serializers.ModelSerializer):
    """
    Сериализатор создания тарифного
    плана подписки.
    """

    class Meta:
        model = SubscriptionPlan
        fields = (
            "name",
            "description",
            "price",
            "duration_days",
            "max_ai_requests",
            "has_chat_access",
            "has_image_analysis",
        )

    def validate_price(self, value):
        """
        Проверяет корректность стоимости
        тарифного плана.
        """
        if value <= 0:
            raise serializers.ValidationError(
                "Стоимость тарифного плана должна быть больше нуля."
            )

        return value

    def validate_duration_days(self, value):
        """
        Проверяет срок действия
        тарифного плана.
        """
        if value <= 0:
            raise serializers.ValidationError(
                "Срок действия подписки должен быть больше нуля."
            )

        return value


class SubscriptionPlanUpdateSerializer(serializers.ModelSerializer):
    """
    Сериализатор обновления тарифного
    плана подписки.
    """

    class Meta:
        model = SubscriptionPlan
        fields = (
            "name",
            "description",
            "price",
            "duration_days",
            "max_ai_requests",
            "has_chat_access",
            "has_image_analysis",
        )

    def validate_price(self, value):
        """
        Проверяет корректность стоимости
        тарифного плана.
        """
        if value <= 0:
            raise serializers.ValidationError(
                "Стоимость тарифного плана должна быть больше нуля."
            )

        return value

    def validate_duration_days(self, value):
        """
        Проверяет срок действия
        тарифного плана.
        """
        if value <= 0:
            raise serializers.ValidationError(
                "Срок действия подписки должен быть больше нуля."
            )

        return value


class UserSubscriptionSerializer(serializers.ModelSerializer):
    """
    Сериализатор пользовательской подписки.

    Используется для получения информации
    о подписке пользователя.
    """

    user_email = serializers.EmailField(
        source="user.email",
        read_only=True,
    )

    plan_name = serializers.CharField(
        source="plan.name",
        read_only=True,
    )

    class Meta:
        model = UserSubscription
        fields = (
            "id",
            "user",
            "user_email",
            "plan",
            "plan_name",
            "start_date",
            "end_date",
            "is_active",
            "auto_renew",
        )
        read_only_fields = (
            "id",
            "user",
        )


class UserSubscriptionCreateSerializer(serializers.ModelSerializer):
    """
    Сериализатор создания пользовательской
    подписки.

    Пользователь назначается автоматически
    в API-представлении.
    """

    class Meta:
        model = UserSubscription
        fields = (
            "plan",
            "start_date",
            "end_date",
            "is_active",
            "auto_renew",
        )

    def validate(self, attrs):
        """
        Проверяет корректность периода
        действия подписки.
        """
        start_date = attrs.get("start_date")
        end_date = attrs.get("end_date")

        if (
            start_date is not None
            and end_date is not None
            and end_date <= start_date
        ):
            raise serializers.ValidationError(
                {
                    "end_date": (
                        "Дата окончания подписки должна быть "
                        "позже даты начала."
                    )
                }
            )

        return attrs


class UserSubscriptionUpdateSerializer(serializers.ModelSerializer):
    """
    Сериализатор обновления пользовательской
    подписки.
    """

    class Meta:
        model = UserSubscription
        fields = (
            "plan",
            "start_date",
            "end_date",
            "is_active",
            "auto_renew",
        )

    def validate(self, attrs):
        """
        Проверяет корректность периода
        действия подписки.
        """
        start_date = attrs.get(
            "start_date",
            self.instance.start_date,
        )
        end_date = attrs.get(
            "end_date",
            self.instance.end_date,
        )

        if end_date <= start_date:
            raise serializers.ValidationError(
                {
                    "end_date": (
                        "Дата окончания подписки должна быть "
                        "позже даты начала."
                    )
                }
            )

        return attrs


class SubscriptionPaymentSerializer(serializers.ModelSerializer):
    """
    Сериализатор платежа за подписку.

    Используется для получения информации
    о платеже пользователя.
    """

    user_email = serializers.EmailField(
        source="user.email",
        read_only=True,
    )

    plan_name = serializers.CharField(
        source="subscription.plan.name",
        read_only=True,
        default=None,
    )

    class Meta:
        model = SubscriptionPayment
        fields = (
            "id",
            "user",
            "user_email",
            "subscription",
            "plan_name",
            "provider",
            "external_payment_id",
            "amount",
            "currency",
            "status",
            "paid_at",
        )
        read_only_fields = (
            "id",
            "user",
        )


class SubscriptionPaymentCreateSerializer(serializers.ModelSerializer):
    """
    Сериализатор создания платежа
    за подписку.

    Пользователь назначается автоматически
    в API-представлении.
    """

    class Meta:
        model = SubscriptionPayment
        fields = (
            "subscription",
            "provider",
            "external_payment_id",
            "amount",
            "currency",
            "status",
            "paid_at",
        )

    def validate_amount(self, value):
        """
        Проверяет корректность суммы платежа.
        """
        if value <= 0:
            raise serializers.ValidationError(
                "Сумма платежа должна быть больше нуля."
            )

        return value

    def validate_currency(self, value):
        """
        Нормализует код валюты.
        """
        value = value.strip().upper()

        if len(value) != 3:
            raise serializers.ValidationError(
                "Код валюты должен состоять из трех символов."
            )

        return value

    def validate_subscription(self, value):
        """
        Проверяет, что выбранная подписка
        принадлежит текущему пользователю.
        """
        request = self.context.get("request")

        if (
            value is not None
            and request is not None
            and request.user.is_authenticated
            and value.user != request.user
            and not request.user.is_superuser
        ):
            raise serializers.ValidationError(
                "Нельзя создать платеж для чужой подписки."
            )

        return value


class SubscriptionPaymentUpdateSerializer(serializers.ModelSerializer):
    """
    Сериализатор обновления платежа
    за подписку.
    """

    class Meta:
        model = SubscriptionPayment
        fields = (
            "subscription",
            "provider",
            "external_payment_id",
            "amount",
            "currency",
            "status",
            "paid_at",
        )

    def validate_amount(self, value):
        """
        Проверяет корректность суммы платежа.
        """
        if value <= 0:
            raise serializers.ValidationError(
                "Сумма платежа должна быть больше нуля."
            )

        return value

    def validate_currency(self, value):
        """
        Нормализует код валюты.
        """
        value = value.strip().upper()

        if len(value) != 3:
            raise serializers.ValidationError(
                "Код валюты должен состоять из трех символов."
            )

        return value

    def validate_subscription(self, value):
        """
        Проверяет, что выбранная подписка
        принадлежит текущему пользователю.
        """
        request = self.context.get("request")

        if (
            value is not None
            and request is not None
            and request.user.is_authenticated
            and value.user != request.user
            and not request.user.is_superuser
        ):
            raise serializers.ValidationError(
                "Нельзя привязать платеж к чужой подписке."
            )

        return value
