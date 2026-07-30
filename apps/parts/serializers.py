from rest_framework import serializers

from .models import PartCategory, Part, OEMNumber, Compatibility, PartImage


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

    def validate_slug(self, value):
        """
        Проверяет уникальность slug категории.
        """
        if PartCategory.objects.filter(slug=value).exists():
            raise serializers.ValidationError(
                "Категория с таким slug уже существует."
            )
        return value


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

    def validate_slug(self, value):
        """
        Проверяет уникальность slug категории.
        """
        if (
            PartCategory.objects.filter(slug=value)
            .exclude(pk=self.instance.pk)
            .exists()
        ):
            raise serializers.ValidationError(
                "Категория с таким slug уже существует."
            )
        return value


class OEMNumberSerializer(serializers.ModelSerializer):
    """
    Сериализатор OEM-номера запчасти.

    Используется для отображения информации
    об оригинальном номере производителя.
    """

    class Meta:
        model = OEMNumber
        fields = (
            "id",
            "part",
            "number",
            "manufacturer",
        )
        read_only_fields = (
            "id",
        )


class OEMNumberCreateSerializer(serializers.ModelSerializer):
    """
    Сериализатор создания OEM-номера
    запчасти.
    """

    class Meta:
        model = OEMNumber
        fields = (
            "part",
            "number",
            "manufacturer",
        )

    def validate(self, attrs):
        """
        Проверяет отсутствие дублирующего
        OEM-номера для выбранной запчасти.
        """
        part = attrs.get("part")
        number = attrs.get("number")

        if OEMNumber.objects.filter(
            part=part,
            number=number,
        ).exists():
            raise serializers.ValidationError(
                {
                    "number": (
                        "Такой OEM-номер уже существует "
                        "для данной запчасти."
                    )
                }
            )

        return attrs


class OEMNumberUpdateSerializer(serializers.ModelSerializer):
    """
    Сериализатор обновления OEM-номера
    запчасти.
    """

    class Meta:
        model = OEMNumber
        fields = (
            "number",
            "manufacturer",
        )

    def validate_number(self, value):
        """
        Проверяет уникальность OEM-номера.
        """
        if (
            OEMNumber.objects.filter(number=value)
            .exclude(pk=self.instance.pk)
            .exists()
        ):
            raise serializers.ValidationError(
                "OEM-номер уже существует."
            )

        return value

    def validate(self, attrs):
        """
        Проверяет отсутствие дублирующего
        OEM-номера для выбранной запчасти.
        """
        number = attrs.get("number", self.instance.number)

        if (
            OEMNumber.objects.filter(
                part=self.instance.part,
                number=number,
            )
            .exclude(pk=self.instance.pk)
            .exists()
        ):
            raise serializers.ValidationError(
                {
                    "number": (
                        "Такой OEM-номер уже существует "
                        "для данной запчасти."
                    )
                }
            )

        return attrs


class CompatibilitySerializer(serializers.ModelSerializer):
    """
    Сериализатор совместимости запчасти.

    Используется для отображения информации
    о совместимости запчасти с автомобилями.
    """

    class Meta:
        model = Compatibility
        fields = (
            "id",
            "part",
            "brand",
            "model",
            "generation",
            "engine",
            "year_from",
            "year_to",
        )
        read_only_fields = (
            "id",
        )


class CompatibilityCreateSerializer(serializers.ModelSerializer):
    """
    Сериализатор создания записи
    совместимости запчасти.
    """

    class Meta:
        model = Compatibility
        fields = (
            "part",
            "brand",
            "model",
            "generation",
            "engine",
            "year_from",
            "year_to",
        )

    def validate(self, attrs):
        """
        Проверяет корректность диапазона
        годов выпуска автомобиля.
        """
        year_from = attrs.get("year_from")
        year_to = attrs.get("year_to")

        if (
            year_from is not None
            and year_to is not None
            and year_from > year_to
        ):
            raise serializers.ValidationError(
                {
                    "year_to": (
                        "Год окончания не может быть "
                        "меньше года начала."
                    )
                }
            )

        return attrs


class CompatibilityUpdateSerializer(serializers.ModelSerializer):
    """
    Сериализатор обновления записи
    совместимости запчасти.
    """

    class Meta:
        model = Compatibility
        fields = (
            "brand",
            "model",
            "generation",
            "engine",
            "year_from",
            "year_to",
        )

    def validate(self, attrs):
        """
        Проверяет корректность диапазона
        годов выпуска автомобиля.
        """
        year_from = attrs.get(
            "year_from",
            self.instance.year_from,
        )

        year_to = attrs.get(
            "year_to",
            self.instance.year_to,
        )

        if (
            year_from is not None
            and year_to is not None
            and year_from > year_to
        ):
            raise serializers.ValidationError(
                {
                    "year_to": (
                        "Год окончания не может быть "
                        "меньше года начала."
                    )
                }
            )

        return attrs


class PartImageSerializer(serializers.ModelSerializer):
    """
    Сериализатор изображения запчасти.

    Используется для отображения информации
    об изображении автомобильной запчасти.
    """

    class Meta:
        model = PartImage
        fields = (
            "id",
            "part",
            "image",
            "alt_text",
            "is_main",
            "uploaded_at",
        )
        read_only_fields = (
            "id",
            "uploaded_at",
        )


class PartImageCreateSerializer(serializers.ModelSerializer):
    """
    Сериализатор создания изображения
    автомобильной запчасти.
    """

    class Meta:
        model = PartImage
        fields = (
            "part",
            "image",
            "alt_text",
            "is_main",
        )

    def validate(self, attrs):
        """
        Проверяет, что у запчасти существует
        только одно основное изображение.
        """
        part = attrs.get("part")
        is_main = attrs.get("is_main", False)

        if (
            part is not None
            and is_main
            and PartImage.objects.filter(
                part=part,
                is_main=True,
            ).exists()
        ):
            raise serializers.ValidationError(
                {
                    "is_main": (
                        "Для данной запчасти уже существует "
                        "основное изображение."
                    )
                }
            )

        return attrs


class PartImageUpdateSerializer(serializers.ModelSerializer):
    """
    Сериализатор обновления изображения
    автомобильной запчасти.
    """

    class Meta:
        model = PartImage
        fields = (
            "image",
            "alt_text",
            "is_main",
        )

    def validate(self, attrs):
        """
        Проверяет, что у запчасти существует
        только одно основное изображение.
        """
        is_main = attrs.get(
            "is_main",
            self.instance.is_main,
        )

        if (
            is_main
            and PartImage.objects.filter(
                part=self.instance.part,
                is_main=True,
            )
            .exclude(pk=self.instance.pk)
            .exists()
        ):
            raise serializers.ValidationError(
                {
                    "is_main": (
                        "Для данной запчасти уже существует "
                        "основное изображение."
                    )
                }
            )

        return attrs


class PartSerializer(serializers.ModelSerializer):
    """
    Сериализатор автомобильной запчасти.
    """

    category_name = serializers.CharField(
        source="category.name",
        read_only=True,
    )

    oem_numbers = OEMNumberSerializer(
        many=True,
        read_only=True,
    )

    compatibilities = CompatibilitySerializer(
        many=True,
        read_only=True,
    )

    images = PartImageSerializer(
        many=True,
        read_only=True,
    )

    class Meta:
        model = Part
        fields = (
            "id",
            "category",
            "category_name",
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
            "oem_numbers",
            "compatibilities",
            "images",
        )
        read_only_fields = (
            "id",
            "created_at",
            "updated_at",
        )


class PartCreateSerializer(serializers.ModelSerializer):
    """
    Сериализатор создания автомобильной
    запчасти.
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

    def validate_original_number(self, value):
        """
        Проверяет уникальность оригинального
        номера запчасти.
        """
        if Part.objects.filter(
            original_number=value,
        ).exists():
            raise serializers.ValidationError(
                "Запчасть с таким оригинальным номером уже существует."
            )

        return value

    def validate_slug(self, value):
        if Part.objects.filter(slug=value).exists():
            raise serializers.ValidationError(
                "Запчасть с таким slug уже существует."
            )
        return value


class PartUpdateSerializer(serializers.ModelSerializer):
    """
    Сериализатор обновления автомобильной
    запчасти.
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

    def validate_original_number(self, value):
        """
        Проверяет уникальность оригинального
        номера запчасти.
        """
        if (
            Part.objects.filter(
                original_number=value,
            )
            .exclude(pk=self.instance.pk)
            .exists()
        ):
            raise serializers.ValidationError(
                "Запчасть с таким оригинальным номером уже существует."
            )

        return value

    def validate_slug(self, value):
        """
        Проверяет уникальность slug.
        """
        if (
            Part.objects.filter(
                slug=value,
            )
            .exclude(pk=self.instance.pk)
            .exists()
        ):
            raise serializers.ValidationError(
                "Запчасть с таким slug уже существует."
            )

        return value
