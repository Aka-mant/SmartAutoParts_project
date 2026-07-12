from django.db.models import Q

from rest_framework.generics import (
    CreateAPIView,
    DestroyAPIView,
    ListAPIView,
    RetrieveAPIView,
    UpdateAPIView,
)
from rest_framework.permissions import IsAuthenticated

from .models import (
    ChatRoom,
    ChatParticipant,
    ChatMessage
)
from .serializers import (
    ChatRoomCreateSerializer,
    ChatRoomSerializer,
    ChatRoomUpdateSerializer,
    ChatParticipantCreateSerializer,
    ChatParticipantSerializer,
    ChatParticipantUpdateSerializer,
    ChatMessageSerializer,
    ChatMessageCreateSerializer,
    ChatMessageUpdateSerializer,
)


class ChatRoomListAPIView(ListAPIView):
    """
    API-представление для получения
    списка доступных комнат чата.

    Пользователь видит все публичные комнаты,
    созданные им приватные комнаты и приватные
    комнаты, участником которых он является.

    Суперпользователь Django имеет доступ
    ко всем комнатам.
    """

    serializer_class = ChatRoomSerializer
    permission_classes = [
        IsAuthenticated,
    ]

    def get_queryset(self):
        """
        Возвращает комнаты, доступные
        текущему пользователю.
        """
        if self.request.user.is_superuser:
            return ChatRoom.objects.all()

        return (
            ChatRoom.objects.filter(
                Q(is_private=False)
                | Q(created_by=self.request.user)
                | Q(participants__user=self.request.user)
            )
            .select_related(
                "created_by",
            )
            .prefetch_related(
                "participants",
                "participants__user",
            )
            .distinct()
        )


class ChatRoomCreateAPIView(CreateAPIView):
    """
    API-представление для создания
    комнаты чата.

    Создателем комнаты автоматически
    назначается текущий пользователь.
    """

    queryset = ChatRoom.objects.all()
    serializer_class = ChatRoomCreateSerializer
    permission_classes = [
        IsAuthenticated,
    ]

    def perform_create(self, serializer):
        """
        Создает комнату и назначает
        текущего пользователя создателем.
        """
        serializer.save(
            created_by=self.request.user,
        )


class ChatRoomRetrieveAPIView(RetrieveAPIView):
    """
    API-представление для получения
    информации о комнате чата.

    Публичная комната доступна любому
    авторизованному пользователю.

    Приватная комната доступна ее создателю,
    участникам и суперпользователю Django.
    """

    serializer_class = ChatRoomSerializer
    permission_classes = [
        IsAuthenticated,
    ]

    def get_queryset(self):
        """
        Возвращает комнаты, доступные
        текущему пользователю.
        """
        if self.request.user.is_superuser:
            return ChatRoom.objects.all()

        return (
            ChatRoom.objects.filter(
                Q(is_private=False)
                | Q(created_by=self.request.user)
                | Q(participants__user=self.request.user)
            )
            .select_related(
                "created_by",
            )
            .prefetch_related(
                "participants",
                "participants__user",
            )
            .distinct()
        )


class ChatRoomUpdateAPIView(UpdateAPIView):
    """
    API-представление для обновления
    комнаты чата.

    Изменять комнату может только ее
    создатель или суперпользователь Django.
    """

    serializer_class = ChatRoomUpdateSerializer
    permission_classes = [
        IsAuthenticated,
    ]

    def get_queryset(self):
        """
        Возвращает комнаты, которые текущий
        пользователь имеет право изменять.
        """
        if self.request.user.is_superuser:
            return ChatRoom.objects.all()

        return ChatRoom.objects.filter(
            created_by=self.request.user,
        )


class ChatRoomDeleteAPIView(DestroyAPIView):
    """
    API-представление для удаления
    комнаты чата.

    Удалять комнату может только ее
    создатель или суперпользователь Django.
    """

    serializer_class = ChatRoomSerializer
    permission_classes = [
        IsAuthenticated,
    ]

    def get_queryset(self):
        """
        Возвращает комнаты, которые текущий
        пользователь имеет право удалять.
        """
        if self.request.user.is_superuser:
            return ChatRoom.objects.all()

        return ChatRoom.objects.filter(
            created_by=self.request.user,
        )


class ChatParticipantListAPIView(ListAPIView):
    """
    API-представление для получения
    списка участников комнат чата.

    Пользователь видит участников публичных
    комнат, а также доступных ему приватных
    комнат.

    Суперпользователь Django имеет доступ
    ко всем участникам.
    """

    serializer_class = ChatParticipantSerializer
    permission_classes = [
        IsAuthenticated,
    ]

    def get_queryset(self):
        """
        Возвращает участников комнат,
        доступных текущему пользователю.
        """
        if self.request.user.is_superuser:
            return ChatParticipant.objects.all()

        return (
            ChatParticipant.objects.filter(
                Q(room__is_private=False)
                | Q(room__created_by=self.request.user)
                | Q(room__participants__user=self.request.user)
            )
            .select_related(
                "room",
                "user",
            )
            .distinct()
        )


class ChatParticipantCreateAPIView(CreateAPIView):
    """
    API-представление для добавления
    участника в комнату чата.

    Добавлять участников может создатель
    комнаты или суперпользователь Django.
    """

    serializer_class = ChatParticipantCreateSerializer
    permission_classes = [
        IsAuthenticated,
    ]

    def get_queryset(self):
        """
        Возвращает участников комнат,
        которыми управляет текущий
        пользователь.
        """
        if self.request.user.is_superuser:
            return ChatParticipant.objects.all()

        return ChatParticipant.objects.filter(
            room__created_by=self.request.user,
        )

    def perform_create(self, serializer):
        """
        Проверяет право текущего пользователя
        добавлять участников в выбранную комнату.
        """
        room = serializer.validated_data["room"]

        if (
            not self.request.user.is_superuser
            and room.created_by != self.request.user
        ):
            from rest_framework.exceptions import PermissionDenied

            raise PermissionDenied(
                "Добавлять участников может только создатель комнаты."
            )

        serializer.save()


class ChatParticipantRetrieveAPIView(RetrieveAPIView):
    """
    API-представление для получения
    информации об участнике чата.

    Запись доступна участникам публичных
    комнат, участникам доступных приватных
    комнат и суперпользователю Django.
    """

    serializer_class = ChatParticipantSerializer
    permission_classes = [
        IsAuthenticated,
    ]

    def get_queryset(self):
        """
        Возвращает участников комнат,
        доступных текущему пользователю.
        """
        if self.request.user.is_superuser:
            return ChatParticipant.objects.all()

        return (
            ChatParticipant.objects.filter(
                Q(room__is_private=False)
                | Q(room__created_by=self.request.user)
                | Q(room__participants__user=self.request.user)
            )
            .select_related(
                "room",
                "user",
            )
            .distinct()
        )


class ChatParticipantUpdateAPIView(UpdateAPIView):
    """
    API-представление для обновления
    участника комнаты чата.

    Изменять участников может только
    создатель соответствующей комнаты
    или суперпользователь Django.
    """

    serializer_class = ChatParticipantUpdateSerializer
    permission_classes = [
        IsAuthenticated,
    ]

    def get_queryset(self):
        """
        Возвращает записи участников,
        которыми может управлять текущий
        пользователь.
        """
        if self.request.user.is_superuser:
            return ChatParticipant.objects.all()

        return ChatParticipant.objects.filter(
            room__created_by=self.request.user,
        )

    def perform_update(self, serializer):
        """
        Проверяет право пользователя
        перемещать участника в другую комнату.
        """
        room = serializer.validated_data.get(
            "room",
            serializer.instance.room,
        )

        if (
            not self.request.user.is_superuser
            and room.created_by != self.request.user
        ):
            from rest_framework.exceptions import PermissionDenied

            raise PermissionDenied(
                "Изменять участников может только создатель комнаты."
            )

        serializer.save()


class ChatParticipantDeleteAPIView(DestroyAPIView):
    """
    API-представление для удаления
    участника из комнаты чата.

    Удалять участников может создатель
    комнаты или суперпользователь Django.

    Пользователь также может самостоятельно
    покинуть комнату.
    """

    serializer_class = ChatParticipantSerializer
    permission_classes = [
        IsAuthenticated,
    ]

    def get_queryset(self):
        """
        Возвращает записи участников,
        которые текущий пользователь
        имеет право удалить.
        """
        if self.request.user.is_superuser:
            return ChatParticipant.objects.all()

        return ChatParticipant.objects.filter(
            Q(room__created_by=self.request.user)
            | Q(user=self.request.user)
        ).distinct()

class ChatMessageListAPIView(ListAPIView):
    """
    API-представление для получения
    списка сообщений чата.

    Пользователь видит сообщения публичных
    комнат, созданных им приватных комнат
    и приватных комнат, участником которых
    он является.

    Суперпользователь Django имеет доступ
    ко всем сообщениям.
    """

    serializer_class = ChatMessageSerializer
    permission_classes = [
        IsAuthenticated,
    ]

    def get_queryset(self):
        """
        Возвращает сообщения комнат,
        доступных текущему пользователю.
        """
        if self.request.user.is_superuser:
            return ChatMessage.objects.all()

        return (
            ChatMessage.objects.filter(
                Q(room__is_private=False)
                | Q(room__created_by=self.request.user)
                | Q(room__participants__user=self.request.user)
            )
            .select_related(
                "room",
                "user",
            )
            .distinct()
        )


class ChatMessageCreateAPIView(CreateAPIView):
    """
    API-представление для создания
    сообщения в комнате чата.

    Автором сообщения автоматически
    назначается текущий пользователь.
    """

    queryset = ChatMessage.objects.all()
    serializer_class = ChatMessageCreateSerializer
    permission_classes = [
        IsAuthenticated,
    ]

    def perform_create(self, serializer):
        """
        Создает сообщение и назначает
        текущего пользователя автором.
        """
        serializer.save(
            user=self.request.user,
        )


class ChatMessageRetrieveAPIView(RetrieveAPIView):
    """
    API-представление для получения
    информации о сообщении чата.

    Сообщение доступно пользователям,
    имеющим доступ к соответствующей комнате.

    Суперпользователь Django имеет
    доступ ко всем сообщениям.
    """

    serializer_class = ChatMessageSerializer
    permission_classes = [
        IsAuthenticated,
    ]

    def get_queryset(self):
        """
        Возвращает сообщения комнат,
        доступных текущему пользователю.
        """
        if self.request.user.is_superuser:
            return ChatMessage.objects.all()

        return (
            ChatMessage.objects.filter(
                Q(room__is_private=False)
                | Q(room__created_by=self.request.user)
                | Q(room__participants__user=self.request.user)
            )
            .select_related(
                "room",
                "user",
            )
            .distinct()
        )


class ChatMessageUpdateAPIView(UpdateAPIView):
    """
    API-представление для обновления
    сообщения чата.

    Пользователь может изменять только
    собственные сообщения.

    Суперпользователь Django имеет
    доступ ко всем сообщениям.
    """

    serializer_class = ChatMessageUpdateSerializer
    permission_classes = [
        IsAuthenticated,
    ]

    def get_queryset(self):
        """
        Возвращает сообщения, которые
        текущий пользователь имеет право
        изменять.
        """
        if self.request.user.is_superuser:
            return ChatMessage.objects.all()

        return ChatMessage.objects.filter(
            user=self.request.user,
        )


class ChatMessageDeleteAPIView(DestroyAPIView):
    """
    API-представление для удаления
    сообщения чата.

    Пользователь может удалять собственные
    сообщения.

    Создатель комнаты может удалять любые
    сообщения своей комнаты.

    Суперпользователь Django имеет
    доступ ко всем сообщениям.
    """

    serializer_class = ChatMessageSerializer
    permission_classes = [
        IsAuthenticated,
    ]

    def get_queryset(self):
        """
        Возвращает сообщения, которые
        текущий пользователь имеет право
        удалить.
        """
        if self.request.user.is_superuser:
            return ChatMessage.objects.all()

        return ChatMessage.objects.filter(
            Q(user=self.request.user)
            | Q(room__created_by=self.request.user)
        ).distinct()