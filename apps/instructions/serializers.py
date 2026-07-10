from rest_framework import serializers

from .models import Instruction


class InstructionSerializer(serializers.ModelSerializer):
    """
    Сериализатор инструкции.

    Используется для отображения
    информации об инструкции по ремонту.
    """

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
    Сериализатор создания
    инструкции по ремонту.
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
    Сериализатор обновления
    инструкции по ремонту.
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
        Обновляет инструкцию и
        увеличивает номер версии.
        """
        for attr, value in validated_data.items():
            setattr(instance, attr, value)

        instance.version += 1
        instance.save()

        return instance

