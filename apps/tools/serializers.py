from rest_framework import serializers

from .models import ToolCategory, Tool, PartTool


class ToolCategorySerializer(serializers.ModelSerializer):
    """
    Сериализатор категории инструментов.
    """

    class Meta:
        model = ToolCategory
        fields = (
            "id",
            "name",
            "slug",
        )
        read_only_fields = (
            "id",
        )


class ToolCategoryCreateSerializer(serializers.ModelSerializer):
    """
    Сериализатор создания категории
    инструментов.
    """

    class Meta:
        model = ToolCategory
        fields = (
            "name",
            "slug",
        )

    def validate_slug(self, value):
        """
        Проверяет уникальность slug
        категории инструментов.
        """
        if ToolCategory.objects.filter(
            slug=value,
        ).exists():
            raise serializers.ValidationError(
                "Категория с таким slug уже существует."
            )

        return value


class ToolCategoryUpdateSerializer(serializers.ModelSerializer):
    """
    Сериализатор обновления категории
    инструментов.
    """

    class Meta:
        model = ToolCategory
        fields = (
            "name",
            "slug",
        )

    def validate_slug(self, value):
        """
        Проверяет уникальность slug
        категории инструментов.
        """
        if (
            ToolCategory.objects.filter(
                slug=value,
            )
            .exclude(pk=self.instance.pk)
            .exists()
        ):
            raise serializers.ValidationError(
                "Категория с таким slug уже существует."
            )

        return value


class ToolSerializer(serializers.ModelSerializer):
    """
    Сериализатор инструмента.

    Используется для отображения информации
    об инструменте через API.
    """

    category_name = serializers.CharField(
        source="category.name",
        read_only=True,
    )

    class Meta:
        model = Tool
        fields = (
            "id",
            "category",
            "category_name",
            "name",
            "description",
            "size",
            "image",
            "ozon_url",
            "created_at",
        )
        read_only_fields = (
            "id",
            "created_at",
        )


class ToolCreateSerializer(serializers.ModelSerializer):
    """
    Сериализатор создания инструмента.
    """

    class Meta:
        model = Tool
        fields = (
            "category",
            "name",
            "description",
            "size",
            "image",
            "ozon_url",
        )


class ToolUpdateSerializer(serializers.ModelSerializer):
    """
    Сериализатор обновления инструмента.
    """

    class Meta:
        model = Tool
        fields = (
            "category",
            "name",
            "description",
            "size",
            "image",
            "ozon_url",
        )


class PartToolSerializer(serializers.ModelSerializer):
    """
    Сериализатор связи запчасти
    с инструментом.

    Используется для отображения информации
    о необходимых инструментах для
    конкретной запчасти.
    """

    part_name = serializers.CharField(
        source="part.name",
        read_only=True,
    )

    tool_name = serializers.CharField(
        source="tool.name",
        read_only=True,
    )

    class Meta:
        model = PartTool
        fields = (
            "id",
            "part",
            "part_name",
            "tool",
            "tool_name",
            "required",
        )
        read_only_fields = (
            "id",
        )


class PartToolCreateSerializer(serializers.ModelSerializer):
    """
    Сериализатор создания связи
    между запчастью и инструментом.
    """

    class Meta:
        model = PartTool
        fields = (
            "part",
            "tool",
            "required",
        )

    def validate(self, attrs):
        """
        Проверяет отсутствие дублирующей
        связи между запчастью
        и инструментом.
        """
        part = attrs.get("part")
        tool = attrs.get("tool")

        if PartTool.objects.filter(
            part=part,
            tool=tool,
        ).exists():
            raise serializers.ValidationError(
                {
                    "tool": (
                        "Этот инструмент уже привязан "
                        "к выбранной запчасти."
                    )
                }
            )

        return attrs


class PartToolUpdateSerializer(serializers.ModelSerializer):
    """
    Сериализатор обновления связи
    между запчастью и инструментом.
    """

    class Meta:
        model = PartTool
        fields = (
            "required",
        )
