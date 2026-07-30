from rest_framework import serializers

from .models import (
    ChatMessage,
    ChatParticipant,
    ChatRoom,
)


class ChatParticipantSerializer(serializers.ModelSerializer):
    """
    Сериализатор участника комнаты чата.

    Используется для отображения информации
    о пользователе, состоящем в комнате чата.
    """

    user_email = serializers.EmailField(
        source="user.email",
        read_only=True,
    )

    username = serializers.CharField(
        source="user.username",
        read_only=True,
    )

    room_name = serializers.CharField(
        source="room.name",
        read_only=True,
    )

    class Meta:
        model = ChatParticipant
        fields = (
            "id",
            "room",
            "room_name",
            "user",
            "user_email",
            "username",
            "joined_at",
        )
        read_only_fields = (
            "id",
            "joined_at",
        )


class ChatParticipantCreateSerializer(serializers.ModelSerializer):
    """
    Сериализатор добавления участника
    в комнату чата.
    """

    class Meta:
        model = ChatParticipant
        fields = (
            "room",
            "user",
        )

    def validate(self, attrs):
        """
        Проверяет отсутствие пользователя
        среди участников выбранной комнаты.
        """
        room = attrs.get("room")
        user = attrs.get("user")

        if ChatParticipant.objects.filter(
            room=room,
            user=user,
        ).exists():
            raise serializers.ValidationError(
                {
                    "user": (
                        "Этот пользователь уже является "
                        "участником выбранной комнаты."
                    )
                }
            )

        return attrs


class ChatParticipantUpdateSerializer(serializers.ModelSerializer):
    """
    Сериализатор обновления участника
    комнаты чата.

    Позволяет перенести участника в другую
    комнату или изменить пользователя.
    """

    class Meta:
        model = ChatParticipant
        fields = (
            "room",
            "user",
        )

    def validate(self, attrs):
        """
        Проверяет отсутствие дублирующей
        связи комнаты и пользователя.
        """
        room = attrs.get(
            "room",
            self.instance.room,
        )
        user = attrs.get(
            "user",
            self.instance.user,
        )

        if (
            ChatParticipant.objects.filter(
                room=room,
                user=user,
            )
            .exclude(pk=self.instance.pk)
            .exists()
        ):
            raise serializers.ValidationError(
                {
                    "user": (
                        "Этот пользователь уже является "
                        "участником выбранной комнаты."
                    )
                }
            )

        return attrs


class ChatMessageSerializer(serializers.ModelSerializer):
    """
    Сериализатор сообщения чата.

    Используется для отображения сообщения,
    его автора, комнаты и даты отправки.
    """

    user_email = serializers.EmailField(
        source="user.email",
        read_only=True,
    )

    username = serializers.CharField(
        source="user.username",
        read_only=True,
    )

    room_name = serializers.CharField(
        source="room.name",
        read_only=True,
    )

    class Meta:
        model = ChatMessage
        fields = (
            "id",
            "room",
            "room_name",
            "user",
            "user_email",
            "username",
            "message",
            "is_edited",
            "created_at",
        )
        read_only_fields = (
            "id",
            "user",
            "is_edited",
            "created_at",
        )


class ChatMessageCreateSerializer(serializers.ModelSerializer):
    """
    Сериализатор создания сообщения
    в комнате чата.

    Автор сообщения назначается
    автоматически в API-представлении.
    """

    class Meta:
        model = ChatMessage
        fields = (
            "room",
            "message",
        )

    def validate_message(self, value):
        """
        Проверяет, что сообщение
        не является пустым.
        """
        value = value.strip()

        if not value:
            raise serializers.ValidationError(
                "Сообщение не может быть пустым."
            )
        if len(value) > 500:
            raise serializers.ValidationError(
                "Сообщение не должно превышать 500 символов."
            )

        return value

    def validate_room(self, value):
        """
        Проверяет доступ пользователя
        к выбранной комнате чата.
        """
        request = self.context.get("request")

        if (
            request is None
            or not request.user.is_authenticated
            or request.user.is_superuser
        ):
            return value

        if value.is_private:
            is_participant = ChatParticipant.objects.filter(
                room=value,
                user=request.user,
            ).exists()

            is_creator = value.created_by == request.user

            if not is_participant and not is_creator:
                raise serializers.ValidationError(
                    "Вы не являетесь участником этой приватной комнаты."
                )

        return value


class ChatMessageUpdateSerializer(serializers.ModelSerializer):
    """
    Сериализатор обновления сообщения
    чата.

    После изменения сообщение автоматически
    отмечается как отредактированное.
    """

    class Meta:
        model = ChatMessage
        fields = (
            "message",
        )

    def validate_message(self, value):
        """
        Проверяет, что сообщение
        не является пустым.
        """
        value = value.strip()

        if not value:
            raise serializers.ValidationError(
                "Сообщение не может быть пустым."
            )
        if len(value) > 500:
            raise serializers.ValidationError(
                "Сообщение не должно превышать 500 символов."
            )

        return value

    def update(self, instance, validated_data):
        """
        Обновляет текст сообщения
        и устанавливает отметку редактирования.
        """
        instance.message = validated_data.get(
            "message",
            instance.message,
        )
        instance.is_edited = True

        instance.save(
            update_fields=(
                "message",
                "is_edited",
            )
        )

        return instance


class ChatRoomSerializer(serializers.ModelSerializer):
    """
    Сериализатор комнаты чата.

    Возвращает основную информацию
    о комнате и список ее участников.
    """

    created_by_email = serializers.EmailField(
        source="created_by.email",
        read_only=True,
        default=None,
    )

    participants_count = serializers.SerializerMethodField()

    participants = ChatParticipantSerializer(
        many=True,
        read_only=True,
    )

    class Meta:
        model = ChatRoom
        fields = (
            "id",
            "name",
            "is_private",
            "created_by",
            "created_by_email",
            "created_at",
            "participants_count",
            "participants",
        )
        read_only_fields = (
            "id",
            "created_by",
            "created_at",
        )

    def get_participants_count(self, obj):
        """
        Возвращает количество участников
        комнаты чата.
        """
        return obj.participants.count()


class ChatRoomCreateSerializer(serializers.ModelSerializer):
    """
    Сериализатор создания комнаты чата.

    Создатель комнаты назначается
    автоматически в API-представлении.
    """

    class Meta:
        model = ChatRoom
        fields = (
            "name",
            "is_private",
        )

    def validate_name(self, value):
        """
        Проверяет, что название комнаты
        не является пустым.
        """
        value = value.strip()

        if not value:
            raise serializers.ValidationError(
                "Название комнаты не может быть пустым."
            )

        return value


class ChatRoomUpdateSerializer(serializers.ModelSerializer):
    """
    Сериализатор обновления комнаты чата.
    """

    class Meta:
        model = ChatRoom
        fields = (
            "name",
            "is_private",
        )

    def validate_name(self, value):
        """
        Проверяет, что название комнаты
        не является пустым.
        """
        value = value.strip()

        if not value:
            raise serializers.ValidationError(
                "Название комнаты не может быть пустым."
            )

        return value
