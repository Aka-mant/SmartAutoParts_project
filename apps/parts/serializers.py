from rest_framework import serializers

from .models import Part, PartCategory


class PartSerializer(serializers.ModelSerializer):
    """
    Сериализатор автомобильной запчасти.

    Используется для получения информации
    о запчасти через API.
    """

    class Meta:
        model = Part
        fields = (
            "id",
            "category",
            "name",
            "slug",
            "original_number",
            "manufacturer",
            "description",
            "seo_title",
            "seo_description",
            "seo_keywords",
            "weight",
            "dimensions",
            "is_active",
            "created_at",
            "updated_at",
        )
        read_only_fields = (
            "id",
            "created_at",
            "updated_at",
        )


class PartCreateSerializer(serializers.ModelSerializer):
    """
    Сериализатор создания
    автомобильной запчасти.
    """

    class Meta:
        model = Part
        fields = (
            "category",
            "name",
            "slug",
            "original_number",
            "manufacturer",
            "description",
            "seo_title",
            "seo_description",
            "seo_keywords",
            "weight",
            "dimensions",
            "is_active",
        )


class PartUpdateSerializer(serializers.ModelSerializer):
    """
    Сериализатор обновления
    автомобильной запчасти.
    """

    class Meta:
        model = Part
        fields = (
            "category",
            "name",
            "slug",
            "original_number",
            "manufacturer",
            "description",
            "seo_title",
            "seo_description",
            "seo_keywords",
            "weight",
            "dimensions",
            "is_active",
        )

class PartCategorySerializer(serializers.ModelSerializer):
    """
    Сериализатор категории запчастей.

    Используется для отображения информации
    о категории автомобильных запчастей.
    """

    class Meta:
        model = PartCategory
        fields = (
            "id",
            "name",
            "slug",
            "description",
        )
        read_only_fields = (
            "id",
        )


class PartCategoryCreateSerializer(serializers.ModelSerializer):
    """
    Сериализатор создания категории
    автомобильных запчастей.
    """

    class Meta:
        model = PartCategory
        fields = (
            "name",
            "slug",
            "description",
        )


class PartCategoryUpdateSerializer(serializers.ModelSerializer):
    """
    Сериализатор обновления категории
    автомобильных запчастей.
    """

    class Meta:
        model = PartCategory
        fields = (
            "name",
            "slug",
            "description",
        )