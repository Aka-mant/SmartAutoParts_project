from rest_framework import serializers

from .models import UserActivity, SearchLog, PopularPart


class UserActivitySerializer(serializers.ModelSerializer):
    """
    Сериализатор активности пользователя.

    Используется для отображения журнала
    действий пользователя.
    """

    user_email = serializers.EmailField(
        source="user.email",
        read_only=True,
    )

    username = serializers.CharField(
        source="user.username",
        read_only=True,
    )

    class Meta:
        model = UserActivity
        fields = (
            "id",
            "user",
            "user_email",
            "username",
            "action",
            "metadata",
            "created_at",
        )
        read_only_fields = (
            "id",
            "user",
            "created_at",
        )


class UserActivityCreateSerializer(serializers.ModelSerializer):
    """
    Сериализатор создания записи
    активности пользователя.

    Пользователь назначается автоматически
    в API-представлении.
    """

    class Meta:
        model = UserActivity
        fields = (
            "action",
            "metadata",
        )

    def validate_action(self, value):
        """
        Проверяет корректность названия
        выполняемого действия.
        """
        value = value.strip()

        if not value:
            raise serializers.ValidationError(
                "Название действия не может быть пустым."
            )

        return value


class UserActivityUpdateSerializer(serializers.ModelSerializer):
    """
    Сериализатор обновления записи
    активности пользователя.
    """

    class Meta:
        model = UserActivity
        fields = (
            "action",
            "metadata",
        )

    def validate_action(self, value):
        """
        Проверяет корректность названия
        выполняемого действия.
        """
        value = value.strip()

        if not value:
            raise serializers.ValidationError(
                "Название действия не может быть пустым."
            )

        return value


class SearchLogSerializer(serializers.ModelSerializer):
    """
    Сериализатор журнала поисковых запросов.

    Используется для отображения информации
    о выполненных поисковых запросах.
    """

    user_email = serializers.EmailField(
        source="user.email",
        read_only=True,
        default=None,
    )

    username = serializers.CharField(
        source="user.username",
        read_only=True,
        default=None,
    )

    class Meta:
        model = SearchLog
        fields = (
            "id",
            "user",
            "user_email",
            "username",
            "query",
            "results_count",
            "ip_address",
            "created_at",
        )
        read_only_fields = (
            "id",
            "user",
            "results_count",
            "ip_address",
            "created_at",
        )


class SearchLogCreateSerializer(serializers.ModelSerializer):
    """
    Сериализатор создания записи
    журнала поискового запроса.

    Пользователь и IP-адрес
    назначаются автоматически
    в API-представлении.
    """

    class Meta:
        model = SearchLog
        fields = (
            "query",
        )

    def validate_query(self, value):
        """
        Проверяет корректность
        поискового запроса.
        """
        value = value.strip()

        if not value:
            raise serializers.ValidationError(
                "Поисковый запрос не может быть пустым."
            )

        return value


class SearchLogUpdateSerializer(serializers.ModelSerializer):
    """
    Сериализатор обновления записи
    журнала поисковых запросов.
    """

    class Meta:
        model = SearchLog
        fields = (
            "query",
            "results_count",
            "ip_address",
        )

    def validate_query(self, value):
        """
        Проверяет корректность
        поискового запроса.
        """
        value = value.strip()

        if not value:
            raise serializers.ValidationError(
                "Поисковый запрос не может быть пустым."
            )

        return value

    def validate_results_count(self, value):
        """
        Проверяет корректность количества
        найденных результатов.
        """
        if value < 0:
            raise serializers.ValidationError(
                "Количество результатов не может быть отрицательным."
            )

        return value


class PopularPartSerializer(serializers.ModelSerializer):
    """
    Сериализатор популярной запчасти.

    Используется для отображения
    статистики популярности
    автомобильных запчастей.
    """

    part_name = serializers.CharField(
        source="part.name",
        read_only=True,
    )

    original_number = serializers.CharField(
        source="part.original_number",
        read_only=True,
    )

    manufacturer = serializers.CharField(
        source="part.manufacturer",
        read_only=True,
    )

    class Meta:
        model = PopularPart
        fields = (
            "id",
            "part",
            "part_name",
            "original_number",
            "manufacturer",
            "searches_count",
            "views_count",
            "updated_at",
        )
        read_only_fields = (
            "id",
            "updated_at",
        )


class PopularPartCreateSerializer(serializers.ModelSerializer):
    """
    Сериализатор создания записи
    популярной запчасти.
    """

    class Meta:
        model = PopularPart
        fields = (
            "part",
            "searches_count",
            "views_count",
        )

    def validate_searches_count(self, value):
        """
        Проверяет корректность количества
        поисковых запросов.
        """
        if value < 0:
            raise serializers.ValidationError(
                "Количество поисков не может быть отрицательным."
            )

        return value

    def validate_views_count(self, value):
        """
        Проверяет корректность количества
        просмотров.
        """
        if value < 0:
            raise serializers.ValidationError(
                "Количество просмотров не может быть отрицательным."
            )

        return value

    def validate(self, attrs):
        """
        Проверяет отсутствие дублирующей
        записи статистики для запчасти.
        """
        part = attrs.get("part")

        if PopularPart.objects.filter(
            part=part,
        ).exists():
            raise serializers.ValidationError(
                {
                    "part": (
                        "Статистика для данной "
                        "запчасти уже существует."
                    )
                }
            )

        return attrs


class PopularPartUpdateSerializer(serializers.ModelSerializer):
    """
    Сериализатор обновления статистики
    популярной запчасти.
    """

    class Meta:
        model = PopularPart
        fields = (
            "searches_count",
            "views_count",
        )

    def validate_searches_count(self, value):
        """
        Проверяет корректность количества
        поисковых запросов.
        """
        if value < 0:
            raise serializers.ValidationError(
                "Количество поисков не может быть отрицательным."
            )

        return value

    def validate_views_count(self, value):
        """
        Проверяет корректность количества
        просмотров.
        """
        if value < 0:
            raise serializers.ValidationError(
                "Количество просмотров не может быть отрицательным."
            )

        return value