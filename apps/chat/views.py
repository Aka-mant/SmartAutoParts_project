from django.db.models import Q, QuerySet

from rest_framework.exceptions import PermissionDenied
from rest_framework.generics import (
    CreateAPIView,
    DestroyAPIView,
    ListAPIView,
    RetrieveAPIView,
    UpdateAPIView,
)
from rest_framework.permissions import IsAuthenticated

from .models import (
    ChatMessage,
    ChatParticipant,
    ChatRoom,
)
from .serializers import (
    ChatMessageCreateSerializer,
    ChatMessageSerializer,
    ChatMessageUpdateSerializer,
    ChatParticipantCreateSerializer,
    ChatParticipantSerializer,
    ChatParticipantUpdateSerializer,
    ChatRoomCreateSerializer,
    ChatRoomSerializer,
    ChatRoomUpdateSerializer,
)


def user_can_administrate(user) -> bool:
    """
    Проверяет, обладает ли пользователь
    административными правами.
    """

    return bool(
        user
        and user.is_authenticated
        and user.is_active
        and user.can_administrate
    )


def available_rooms_queryset(user) -> QuerySet:
    """
    Возвращает комнаты, доступные
    указанному пользователю.

    Администраторы и суперпользователи
    получают доступ ко всем комнатам.

    Обычному пользователю доступны:

    - публичные комнаты;
    - созданные им комнаты;
    - приватные комнаты, в которых
      он является участником.
    """

    queryset = (
        ChatRoom.objects
        .select_related(
            "created_by",
        )
        .prefetch_related(
            "participants",
            "participants__user",
        )
    )

    if user_can_administrate(user):
        return queryset

    return queryset.filter(
        Q(is_private=False)
        | Q(created_by=user)
        | Q(participants__user=user)
    ).distinct()


def manageable_rooms_queryset(user) -> QuerySet:
    """
    Возвращает комнаты, которыми
    пользователь может управлять.

    Администраторы и суперпользователи
    могут управлять всеми комнатами.

    Обычный пользователь может управлять
    только созданными им комнатами.
    """

    queryset = ChatRoom.objects.select_related(
        "created_by",
    )

    if user_can_administrate(user):
        return queryset

    return queryset.filter(
        created_by=user,
    )


def available_participants_queryset(user) -> QuerySet:
    """
    Возвращает записи участников
    доступных пользователю комнат.
    """

    queryset = (
        ChatParticipant.objects
        .select_related(
            "room",
            "room__created_by",
            "user",
        )
    )

    if user_can_administrate(user):
        return queryset

    return queryset.filter(
        Q(room__is_private=False)
        | Q(room__created_by=user)
        | Q(room__participants__user=user)
    ).distinct()


def manageable_participants_queryset(user) -> QuerySet:
    """
    Возвращает участников комнат,
    которыми пользователь может управлять.
    """

    queryset = (
        ChatParticipant.objects
        .select_related(
            "room",
            "room__created_by",
            "user",
        )
    )

    if user_can_administrate(user):
        return queryset

    return queryset.filter(
        room__created_by=user,
    )


def available_messages_queryset(user) -> QuerySet:
    """
    Возвращает сообщения из комнат,
    доступных пользователю.
    """

    queryset = (
        ChatMessage.objects
        .select_related(
            "room",
            "room__created_by",
            "user",
        )
    )

    if user_can_administrate(user):
        return queryset

    return queryset.filter(
        Q(room__is_private=False)
        | Q(room__created_by=user)
        | Q(room__participants__user=user)
    ).distinct()


class ChatRoomListAPIView(ListAPIView):
    """
    API-представление для получения
    списка доступных комнат чата.

    Пользователь видит:

    - все публичные комнаты;
    - созданные им комнаты;
    - приватные комнаты, участником
      которых он является.

    Администраторы и системные
    суперпользователи видят все комнаты.
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

        return available_rooms_queryset(
            self.request.user,
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
        Создаёт комнату и назначает
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

    Приватная комната доступна:

    - её создателю;
    - участникам комнаты;
    - администраторам;
    - системным суперпользователям Django.
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

        return available_rooms_queryset(
            self.request.user,
        )


class ChatRoomUpdateAPIView(UpdateAPIView):
    """
    API-представление для обновления
    комнаты чата.

    Изменять комнату могут:

    - её создатель;
    - администратор;
    - системный суперпользователь Django.
    """

    serializer_class = ChatRoomUpdateSerializer
    permission_classes = [
        IsAuthenticated,
    ]

    def get_queryset(self):
        """
        Возвращает комнаты, которыми
        текущий пользователь может управлять.
        """

        return manageable_rooms_queryset(
            self.request.user,
        )

    def perform_update(self, serializer):
        """
        Обновляет комнату, сохраняя
        текущего создателя.

        Поле created_by не может быть
        изменено через API.
        """

        instance = self.get_object()

        serializer.save(
            created_by=instance.created_by,
        )


class ChatRoomDeleteAPIView(DestroyAPIView):
    """
    API-представление для удаления
    комнаты чата.

    Удалять комнату могут:

    - её создатель;
    - администратор;
    - системный суперпользователь Django.
    """

    serializer_class = ChatRoomSerializer
    permission_classes = [
        IsAuthenticated,
    ]

    def get_queryset(self):
        """
        Возвращает комнаты, которые
        текущий пользователь может удалить.
        """

        return manageable_rooms_queryset(
            self.request.user,
        )


class ChatParticipantListAPIView(ListAPIView):
    """
    API-представление для получения
    списка участников комнат чата.

    Пользователь видит участников:

    - публичных комнат;
    - созданных им комнат;
    - доступных ему приватных комнат.

    Администраторы и системные
    суперпользователи видят все записи.
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

        return available_participants_queryset(
            self.request.user,
        )


class ChatParticipantCreateAPIView(CreateAPIView):
    """
    API-представление для добавления
    участника в комнату чата.

    Добавлять участников могут:

    - создатель комнаты;
    - администратор;
    - системный суперпользователь Django.
    """

    queryset = ChatParticipant.objects.select_related(
        "room",
        "room__created_by",
        "user",
    )
    serializer_class = ChatParticipantCreateSerializer
    permission_classes = [
        IsAuthenticated,
    ]

    def perform_create(self, serializer):
        """
        Проверяет право пользователя
        добавлять участника в выбранную комнату.
        """

        user = self.request.user
        room = serializer.validated_data["room"]

        if (
            not user_can_administrate(user)
            and room.created_by_id != user.pk
        ):
            raise PermissionDenied(
                "Добавлять участников может только "
                "создатель комнаты или администратор."
            )

        serializer.save()


class ChatParticipantRetrieveAPIView(RetrieveAPIView):
    """
    API-представление для получения
    информации об участнике комнаты.

    Запись доступна пользователям,
    имеющим доступ к соответствующей комнате.
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

        return available_participants_queryset(
            self.request.user,
        )


class ChatParticipantUpdateAPIView(UpdateAPIView):
    """
    API-представление для обновления
    участника комнаты чата.

    Изменять участников могут:

    - создатель соответствующей комнаты;
    - администратор;
    - системный суперпользователь Django.
    """

    serializer_class = ChatParticipantUpdateSerializer
    permission_classes = [
        IsAuthenticated,
    ]

    def get_queryset(self):
        """
        Возвращает записи участников,
        которыми пользователь может управлять.
        """

        return manageable_participants_queryset(
            self.request.user,
        )

    def perform_update(self, serializer):
        """
        Проверяет право пользователя
        перенести участника в другую комнату.
        """

        user = self.request.user
        instance = self.get_object()

        room = serializer.validated_data.get(
            "room",
            instance.room,
        )

        if (
            not user_can_administrate(user)
            and room.created_by_id != user.pk
        ):
            raise PermissionDenied(
                "Перемещать участников может только "
                "создатель комнаты или администратор."
            )

        serializer.save()


class ChatParticipantDeleteAPIView(DestroyAPIView):
    """
    API-представление для удаления
    участника из комнаты чата.

    Удалять участника могут:

    - создатель комнаты;
    - администратор;
    - системный суперпользователь Django.

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

        user = self.request.user

        queryset = (
            ChatParticipant.objects
            .select_related(
                "room",
                "room__created_by",
                "user",
            )
        )

        if user_can_administrate(user):
            return queryset

        return queryset.filter(
            Q(room__created_by=user)
            | Q(user=user)
        ).distinct()


class ChatMessageListAPIView(ListAPIView):
    """
    API-представление для получения
    списка сообщений чата.

    Пользователь видит сообщения:

    - публичных комнат;
    - созданных им комнат;
    - приватных комнат, участником
      которых он является.

    Администраторы и системные
    суперпользователи видят все сообщения.
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

        return available_messages_queryset(
            self.request.user,
        )


class ChatMessageCreateAPIView(CreateAPIView):
    """
    API-представление для создания
    сообщения в комнате чата.

    Автором сообщения автоматически
    назначается текущий пользователь.

    Отправить сообщение можно только
    в доступную пользователю комнату.
    """

    queryset = ChatMessage.objects.all()
    serializer_class = ChatMessageCreateSerializer
    permission_classes = [
        IsAuthenticated,
    ]

    def perform_create(self, serializer):
        """
        Проверяет доступ пользователя
        к выбранной комнате и создаёт
        сообщение от его имени.
        """

        user = self.request.user
        room = serializer.validated_data["room"]

        has_room_access = (
            available_rooms_queryset(user)
            .filter(pk=room.pk)
            .exists()
        )

        if not has_room_access:
            raise PermissionDenied(
                "У вас нет доступа к этой комнате."
            )

        serializer.save(
            user=user,
        )


class ChatMessageRetrieveAPIView(RetrieveAPIView):
    """
    API-представление для получения
    информации о сообщении чата.

    Сообщение доступно пользователям,
    имеющим доступ к соответствующей комнате.
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

        return available_messages_queryset(
            self.request.user,
        )


class ChatMessageUpdateAPIView(UpdateAPIView):
    """
    API-представление для обновления
    сообщения чата.

    Обычный пользователь может изменять
    только собственные сообщения.

    Администраторы и системные
    суперпользователи могут изменять
    любые сообщения.
    """

    serializer_class = ChatMessageUpdateSerializer
    permission_classes = [
        IsAuthenticated,
    ]

    def get_queryset(self):
        """
        Возвращает сообщения, которые
        пользователь может изменять.
        """

        user = self.request.user

        queryset = ChatMessage.objects.select_related(
            "room",
            "room__created_by",
            "user",
        )

        if user_can_administrate(user):
            return queryset

        return queryset.filter(
            user=user,
        )

    def perform_update(self, serializer):
        """
        Обновляет сообщение, сохраняя
        его автора.

        При изменении комнаты проверяет,
        что пользователь имеет к ней доступ.
        """

        user = self.request.user
        instance = self.get_object()

        room = serializer.validated_data.get(
            "room",
            instance.room,
        )

        has_room_access = (
            available_rooms_queryset(user)
            .filter(pk=room.pk)
            .exists()
        )

        if not has_room_access:
            raise PermissionDenied(
                "У вас нет доступа к выбранной комнате."
            )

        serializer.save(
            user=instance.user,
        )


class ChatMessageDeleteAPIView(DestroyAPIView):
    """
    API-представление для удаления
    сообщения чата.

    Удалять сообщение могут:

    - автор сообщения;
    - создатель комнаты;
    - администратор;
    - системный суперпользователь Django.
    """

    serializer_class = ChatMessageSerializer
    permission_classes = [
        IsAuthenticated,
    ]

    def get_queryset(self):
        """
        Возвращает сообщения, которые
        текущий пользователь может удалить.
        """

        user = self.request.user

        queryset = ChatMessage.objects.select_related(
            "room",
            "room__created_by",
            "user",
        )

        if user_can_administrate(user):
            return queryset

        return queryset.filter(
            Q(user=user)
            | Q(room__created_by=user)
        ).distinct()
