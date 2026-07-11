from rest_framework import serializers

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
            "created_at",
        )
        read_only_fields = (
            "id",
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
            "created_at",
            "updated_at",
            "versions",
            "steps",
            "images",
            "instruction_tools",
        )
        read_only_fields = (
            "id",
            "version",
            "created_by",
            "created_at",
            "updated_at",
        )


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
        )

    def update(self, instance, validated_data):
        """
        Обновляет инструкцию и увеличивает
        номер версии.
        """
        for attr, value in validated_data.items():
            setattr(instance, attr, value)

        instance.version += 1
        instance.save()

        return instance