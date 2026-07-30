from django.db import transaction

from rest_framework import serializers

from apps.subscriptions.access import (
    has_instruction_access,
    has_purchased_instruction,
)

from .models import (
    Instruction,
    InstructionVersion,
    InstructionStep,
    InstructionImage,
    InstructionTool,
)


class InstructionVersionSerializer(serializers.ModelSerializer):
    """
    Сериализатор версии инструкции.
    """

    class Meta:
        model = InstructionVersion
        fields = (
            "id",
            "instruction",
            "version_number",
            "content",
            "changelog",
            "created_by",
            "created_at",
        )
        read_only_fields = (
            "id",
            "created_by",
            "created_at",
        )


class InstructionVersionCreateSerializer(serializers.ModelSerializer):
    """
    Сериализатор создания версии инструкции.
    """

    class Meta:
        model = InstructionVersion
        fields = (
            "instruction",
            "version_number",
            "content",
            "changelog",
        )


class InstructionVersionUpdateSerializer(serializers.ModelSerializer):
    """
    Сериализатор обновления версии инструкции.
    """

    class Meta:
        model = InstructionVersion
        fields = (
            "version_number",
            "content",
            "changelog",
        )


class InstructionStepSerializer(serializers.ModelSerializer):
    """
    Сериализатор шага инструкции.
    """

    class Meta:
        model = InstructionStep
        fields = (
            "id",
            "instruction",
            "step_number",
            "title",
            "description",
            "warning",
            "estimated_minutes",
        )
        read_only_fields = (
            "id",
        )


class InstructionStepCreateSerializer(serializers.ModelSerializer):
    """
    Сериализатор создания шага инструкции.
    """

    class Meta:
        model = InstructionStep
        fields = (
            "instruction",
            "step_number",
            "title",
            "description",
            "warning",
            "estimated_minutes",
        )


class InstructionStepUpdateSerializer(serializers.ModelSerializer):
    """
    Сериализатор обновления шага инструкции.
    """

    class Meta:
        model = InstructionStep
        fields = (
            "step_number",
            "title",
            "description",
            "warning",
            "estimated_minutes",
        )


class InstructionImageSerializer(serializers.ModelSerializer):
    """
    Сериализатор изображения инструкции.
    """

    class Meta:
        model = InstructionImage
        fields = (
            "id",
            "instruction",
            "image",
            "description",
        )
        read_only_fields = (
            "id",
        )


class InstructionImageCreateSerializer(serializers.ModelSerializer):
    """
    Сериализатор создания изображения инструкции.
    """

    class Meta:
        model = InstructionImage
        fields = (
            "instruction",
            "image",
            "description",
        )


class InstructionImageUpdateSerializer(serializers.ModelSerializer):
    """
    Сериализатор обновления изображения инструкции.
    """

    class Meta:
        model = InstructionImage
        fields = (
            "image",
            "description",
        )


class InstructionToolSerializer(serializers.ModelSerializer):
    """
    Сериализатор инструмента инструкции.
    """

    tool_name = serializers.CharField(
        source="tool.name",
        read_only=True,
    )

    class Meta:
        model = InstructionTool
        fields = (
            "id",
            "instruction",
            "tool",
            "tool_name",
            "usage_description",
        )
        read_only_fields = (
            "id",
        )


class InstructionToolCreateSerializer(serializers.ModelSerializer):
    """
    Сериализатор создания связи инструкции
    с инструментом.
    """

    class Meta:
        model = InstructionTool
        fields = (
            "instruction",
            "tool",
            "usage_description",
        )


class InstructionToolUpdateSerializer(serializers.ModelSerializer):
    """
    Сериализатор обновления связи инструкции
    с инструментом.
    """

    class Meta:
        model = InstructionTool
        fields = (
            "tool",
            "usage_description",
        )


class InstructionSerializer(serializers.ModelSerializer):
    """
    Сериализатор инструкции.
    """

    versions = InstructionVersionSerializer(
        many=True,
        read_only=True,
    )

    steps = InstructionStepSerializer(
        many=True,
        read_only=True,
    )

    images = InstructionImageSerializer(
        many=True,
        read_only=True,
    )

    instruction_tools = InstructionToolSerializer(
        many=True,
        read_only=True,
    )

    access_restricted = serializers.SerializerMethodField()

    class Meta:
        model = Instruction
        fields = (
            "id",
            "part",
            "title",
            "slug",
            "short_description",
            "content",
            "difficulty",
            "estimated_time",
            "premium_only",
            "version",
            "created_by",
            "updated_by",
            "is_published",
            "published_at",
            "created_at",
            "updated_at",
            "access_restricted",
            "versions",
            "steps",
            "images",
            "instruction_tools",
        )
        read_only_fields = (
            "id",
            "version",
            "created_by",
            "updated_by",
            "published_at",
            "created_at",
            "updated_at",
            "access_restricted",
        )

    def get_access_restricted(self, instance):
        request = self.context.get("request")
        user = getattr(request, "user", None)
        return not (
            has_instruction_access(user)
            and has_purchased_instruction(user, instance)
        )

    def to_representation(self, instance):
        """
        Не отдаёт содержимое через API без активного тарифа.

        Метаданные детали и инструкции остаются видимыми, чтобы клиент
        мог показать корректное предложение выбрать тариф.
        """

        data = super().to_representation(instance)
        if data["access_restricted"]:
            data["content"] = ""
            data["versions"] = []
            data["steps"] = []
            data["images"] = []
            data["instruction_tools"] = []
        return data


class InstructionCreateSerializer(serializers.ModelSerializer):
    """
    Сериализатор создания инструкции.
    """

    class Meta:
        model = Instruction
        fields = (
            "part",
            "title",
            "slug",
            "short_description",
            "content",
            "difficulty",
            "estimated_time",
            "premium_only",
            "is_published",
        )


class InstructionUpdateSerializer(serializers.ModelSerializer):
    """
    Сериализатор обновления инструкции.
    """

    class Meta:
        model = Instruction
        fields = (
            "title",
            "slug",
            "short_description",
            "content",
            "difficulty",
            "estimated_time",
            "premium_only",
            "is_published",
        )

    def update(self, instance, validated_data):
        """
        Обновляет инструкцию и увеличивает
        номер версии.
        """
        with transaction.atomic():
            InstructionVersion.objects.get_or_create(
                instruction=instance,
                version_number=instance.version,
                defaults={
                    "content": instance.content,
                    "changelog": (
                        "Архив версии перед ручным обновлением."
                    ),
                    "created_by": (
                        instance.updated_by
                        or instance.created_by
                    ),
                },
            )

            for attr, value in validated_data.items():
                setattr(instance, attr, value)

            instance.version += 1
            instance.save()

        return instance
