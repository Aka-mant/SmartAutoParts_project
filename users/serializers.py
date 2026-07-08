from rest_framework import serializers
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer

from .models import User, Profile

from .validators import PasswordValidator


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ('id', 'email', 'phone_number', 'is_active',)


class UserCreateSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, required=True, min_length=0, max_length=16)

    class Meta:
        model = User
        fields = ('email', 'password',)
        validators = [PasswordValidator(field='password')]

    def create(self, validated_data):
        user = User.objects.create(**validated_data)
        user.set_password(user.password)
        user.save()
        return user


class UserTokenObtainSerializer(TokenObtainPairSerializer):
    @classmethod
    def get_token(cls, user):
        token = super().get_token(user)
        token['email'] = user.email
        return token


class UserUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ('email', 'phone_number', 'is_active',)


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
