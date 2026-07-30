from decimal import Decimal

from rest_framework import serializers

from .models import (
    AIGeneratedInstruction,
    AIImageAnalysis,
    AIRequest,
)


class AIRequestSerializer(serializers.ModelSerializer):
    """
    Сериализатор запроса к AI-сервису.

    Используется для отображения истории
    запросов пользователя и результатов
    их обработки.
    """

    user_email = serializers.EmailField(
        source="user.email",
        read_only=True,
    )

    part_name = serializers.CharField(
        source="part.name",
        read_only=True,
        default=None,
    )

    part_original_number = serializers.CharField(
        source="part.original_number",
        read_only=True,
        default=None,
    )

    response = serializers.SerializerMethodField()

    def get_response(self, obj):
        """
        Не раскрывает непроверенную рекомендацию инструментов пользователю.

        После одобрения исходный ответ становится доступен через историю
        AI-запросов. Модераторы видят материал на любом этапе.
        """

        request = self.context.get("request")
        user = getattr(request, "user", None)
        can_moderate = bool(
            user
            and (
                getattr(user, "can_moderate", False)
                or getattr(user, "can_administrate", False)
                or getattr(user, "is_superuser", False)
            )
        )
        if not obj.request_type.startswith("tool_recommendation"):
            return obj.response

        try:
            recommendation = obj.tool_recommendation
        except AttributeError:
            return obj.response

        if (
            can_moderate
            or recommendation.moderation_status == "approved"
        ):
            return obj.response
        if recommendation.moderation_status == "rejected":
            return (
                "Рекомендация отклонена модератором: "
                f"{recommendation.moderation_note}"
            )
        return "Рекомендация ожидает технической модерации."

    class Meta:
        model = AIRequest
        fields = (
            "id",
            "user",
            "user_email",
            "part",
            "part_name",
            "part_original_number",
            "prompt",
            "response",
            "tokens_used",
            "request_type",
            "created_at",
        )
        read_only_fields = (
            "id",
            "user",
            "response",
            "tokens_used",
            "created_at",
        )


class AIRequestCreateSerializer(serializers.ModelSerializer):
    """
    Сериализатор создания запроса
    к AI-сервису.

    Пользователь автоматически назначается
    в API-представлении.
    """

    class Meta:
        model = AIRequest
        fields = (
            "part",
            "prompt",
            "request_type",
        )

    def validate_prompt(self, value):
        """
        Проверяет, что текст запроса
        не является пустым.
        """
        value = value.strip()

        if not value:
            raise serializers.ValidationError(
                "Текст запроса не может быть пустым."
            )
        if len(value) > 500:
            raise serializers.ValidationError(
                "Текст запроса не должен превышать 500 символов."
            )

        return value


class AIRequestUpdateSerializer(serializers.ModelSerializer):
    """
    Сериализатор обновления результата
    AI-запроса.

    Предназначен для сохранения ответа,
    количества использованных токенов
    и типа обработанного запроса.
    """

    class Meta:
        model = AIRequest
        fields = (
            "part",
            "prompt",
            "response",
            "tokens_used",
            "request_type",
        )
        read_only_fields = (
            "response",
            "tokens_used",
            "request_type",
        )

    def validate_prompt(self, value):
        """
        Проверяет, что текст запроса
        не является пустым.
        """
        value = value.strip()

        if not value:
            raise serializers.ValidationError(
                "Текст запроса не может быть пустым."
            )
        if len(value) > 500:
            raise serializers.ValidationError(
                "Текст запроса не должен превышать 500 символов."
            )

        return value


class AIGeneratedInstructionSerializer(serializers.ModelSerializer):
    """
    Сериализатор инструкции,
    сгенерированной AI-сервисом.
    """

    user_email = serializers.EmailField(
        source="ai_request.user.email",
        read_only=True,
    )

    request_prompt = serializers.CharField(
        source="ai_request.prompt",
        read_only=True,
    )

    instruction_title = serializers.CharField(
        source="instruction.title",
        read_only=True,
        default=None,
    )

    class Meta:
        model = AIGeneratedInstruction
        fields = (
            "id",
            "ai_request",
            "user_email",
            "request_prompt",
            "instruction",
            "instruction_title",
            "generated_content",
            "version_number",
            "is_cached",
            "moderation_status",
            "moderation_note",
            "reviewed_by",
            "reviewed_at",
            "created_at",
        )
        read_only_fields = (
            "id",
            "version_number",
            "is_cached",
            "moderation_status",
            "moderation_note",
            "reviewed_by",
            "reviewed_at",
            "created_at",
        )


class AIGeneratedInstructionCreateSerializer(
    serializers.ModelSerializer
):
    """
    Сериализатор создания инструкции,
    сгенерированной AI-сервисом.
    """

    class Meta:
        model = AIGeneratedInstruction
        fields = (
            "ai_request",
            "instruction",
            "generated_content",
        )

    def validate_ai_request(self, value):
        """
        Проверяет принадлежность AI-запроса
        текущему пользователю и отсутствие
        созданной ранее инструкции.
        """
        request = self.context.get("request")

        if (
            request is not None
            and request.user.is_authenticated
            and value.user != request.user
            and not request.user.is_superuser
        ):
            raise serializers.ValidationError(
                "Нельзя использовать AI-запрос другого пользователя."
            )

        if AIGeneratedInstruction.objects.filter(
            ai_request=value,
        ).exists():
            raise serializers.ValidationError(
                "Для этого AI-запроса уже создана инструкция."
            )

        return value

    def validate_generated_content(self, value):
        """
        Проверяет, что сгенерированное
        содержимое не является пустым.
        """
        value = value.strip()

        if not value:
            raise serializers.ValidationError(
                "Содержимое инструкции не может быть пустым."
            )

        return value


class AIGeneratedInstructionUpdateSerializer(
    serializers.ModelSerializer
):
    """
    Сериализатор обновления инструкции,
    сгенерированной AI-сервисом.
    """

    class Meta:
        model = AIGeneratedInstruction
        fields = (
            "instruction",
            "generated_content",
        )

    def validate_generated_content(self, value):
        """
        Проверяет, что сгенерированное
        содержимое не является пустым.
        """
        value = value.strip()

        if not value:
            raise serializers.ValidationError(
                "Содержимое инструкции не может быть пустым."
            )

        return value


class AIImageAnalysisSerializer(serializers.ModelSerializer):
    """
    Сериализатор анализа изображения
    с помощью AI-сервиса.
    """

    user_email = serializers.EmailField(
        source="user.email",
        read_only=True,
    )

    detected_part_name = serializers.CharField(
        source="detected_part.name",
        read_only=True,
        default=None,
    )

    detected_part_original_number = serializers.CharField(
        source="detected_part.original_number",
        read_only=True,
        default=None,
    )

    class Meta:
        model = AIImageAnalysis
        fields = (
            "id",
            "user",
            "user_email",
            "image",
            "detected_part",
            "detected_part_name",
            "detected_part_original_number",
            "confidence_score",
            "analysis_result",
            "moderation_status",
            "moderation_categories",
            "moderation_model",
            "moderation_checked_at",
            "created_at",
        )
        read_only_fields = (
            "id",
            "user",
            "detected_part",
            "confidence_score",
            "analysis_result",
            "moderation_status",
            "moderation_categories",
            "moderation_model",
            "moderation_checked_at",
            "created_at",
        )


class AIImageAnalysisCreateSerializer(serializers.ModelSerializer):
    """
    Сериализатор создания запроса
    на анализ изображения.

    Пользователь автоматически назначается
    в API-представлении.
    """

    confirm_automotive_content = serializers.BooleanField(
        write_only=True,
        required=True,
    )

    class Meta:
        model = AIImageAnalysis
        fields = (
            "image",
            "confirm_automotive_content",
        )

    def validate_confirm_automotive_content(self, value):
        if value is not True:
            raise serializers.ValidationError(
                "Подтвердите, что на фото изображена запчасть или инструмент."
            )
        return value


class AIImageAnalysisUpdateSerializer(serializers.ModelSerializer):
    """
    Сериализатор обновления результата
    анализа изображения.

    Используется для сохранения найденной
    запчасти, уровня уверенности и полного
    результата AI-анализа.
    """

    class Meta:
        model = AIImageAnalysis
        fields = (
            "detected_part",
            "confidence_score",
            "analysis_result",
        )

    def validate_confidence_score(self, value):
        """
        Проверяет, что уровень уверенности
        находится в диапазоне от 0 до 100.
        """
        if value is None:
            return value

        if value < Decimal("0") or value > Decimal("100"):
            raise serializers.ValidationError(
                "Уровень уверенности должен быть от 0 до 100."
            )

        return value
