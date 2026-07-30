from rest_framework import serializers
from django.contrib.auth.password_validation import validate_password
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer

from .models import User, Profile, SearchHistory, RepairHistory


class UserSerializer(serializers.ModelSerializer):
    """
    Сериализатор пользователя.
    """

    class Meta:
        model = User
        fields = (
            "id",
            "email",
            "username",
            "first_name",
            "last_name",
            "phone",
            "avatar",
            "role",
            "is_active",
            "created_at",
            "updated_at",
        )
        read_only_fields = (
            "id",
            "role",
            "created_at",
            "updated_at",
        )


class UserCreateSerializer(serializers.ModelSerializer):
    """
    Сериализатор регистрации пользователя.
    """
    password = serializers.CharField(
        write_only=True,
        validators=[validate_password],
        style={"input_type": "password"},
    )

    class Meta:
        model = User
        fields = (
            "email",
            "username",
            "password",
            "first_name",
            "last_name",
            "phone",
        )

    def create(self, validated_data):
        password = validated_data.pop("password")

        user = User(**validated_data)
        user.set_password(password)
        user.save()

        return user


class UserTokenObtainSerializer(TokenObtainPairSerializer):
    """
    Сериализатор получения JWT-токенов.
    """

    @classmethod
    def get_token(cls, user):
        token = super().get_token(user)

        token["id"] = user.id
        token["email"] = user.email
        token["username"] = user.username
        token["role"] = user.role

        return token

    def validate(self, attrs):
        data = super().validate(attrs)

        data["user"] = {
            "id": self.user.id,
            "email": self.user.email,
            "username": self.user.username,
            "first_name": self.user.first_name,
            "last_name": self.user.last_name,
            "role": self.user.role,
        }

        return data


class UserUpdateSerializer(serializers.ModelSerializer):
    """
    Сериализатор обновления данных пользователя.
    """

    class Meta:
        model = User
        fields = (
            "first_name",
            "last_name",
            "phone",
            "avatar",
        )


class ProfileSerializer(serializers.ModelSerializer):
    """
    Сериализатор профиля пользователя.
    """

    user_email = serializers.EmailField(
        source="user.email",
        read_only=True,
    )

    class Meta:
        model = Profile
        fields = (
            "id",
            "user",
            "user_email",
            "country",
            "city",
            "preferred_language",
            "car_brand",
            "car_model",
            "car_year",
            "bio",
        )
        read_only_fields = (
            "id",
            "user",
            "user_email",
        )


class ProfileUpdateSerializer(serializers.ModelSerializer):
    """
    Сериализатор обновления профиля пользователя.
    """

    class Meta:
        model = Profile
        fields = (
            "country",
            "city",
            "preferred_language",
            "car_brand",
            "car_model",
            "car_year",
            "bio",
        )


class SearchHistorySerializer(serializers.ModelSerializer):
    """
    Сериализатор истории поисковых запросов.
    """

    class Meta:
        model = SearchHistory
        fields = (
            "id",
            "user",
            "original_number",
            "search_query",
            "result_found",
            "searched_at",
        )
        read_only_fields = (
            "id",
            "user",
            "searched_at",
        )


class RepairHistorySerializer(serializers.ModelSerializer):
    """
    Сериализатор истории ремонтов.
    """

    class Meta:
        model = RepairHistory
        fields = (
            "id",
            "user",
            "instruction",
            "completed",
            "current_step",
            "notes",
            "created_at",
            "progress_updated_at",
        )
        read_only_fields = (
            "id",
            "current_step",
            "created_at",
            "progress_updated_at",
        )


class RepairHistoryCreateSerializer(serializers.ModelSerializer):
    """
    Сериализатор создания записи
    истории ремонта.
    """

    class Meta:
        model = RepairHistory
        fields = (
            "user",
            "instruction",
            "completed",
            "notes",
        )


class RepairHistoryUpdateSerializer(serializers.ModelSerializer):
    """
    Сериализатор обновления записи
    истории ремонта.
    """

    class Meta:
        model = RepairHistory
        fields = (
            "completed",
            "notes",
        )
