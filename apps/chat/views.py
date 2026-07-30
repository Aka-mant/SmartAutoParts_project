import hashlib

from django.conf import settings
from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.core.cache import cache
from django.db.models import Q, QuerySet
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.utils import timezone
from django.views import View

from rest_framework.exceptions import (
    PermissionDenied,
    ValidationError,
)
from rest_framework.generics import (
    CreateAPIView,
    DestroyAPIView,
    ListAPIView,
    RetrieveAPIView,
    UpdateAPIView,
)
from rest_framework.permissions import IsAuthenticated
from rest_framework.throttling import UserRateThrottle

from apps.AI.services import (
    AIAccessDenied,
    AIRequestRejected,
    AIServiceError,
    SmartAutoPartsAIService,
)
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
        and getattr(user, "is_authenticated", False)
        and getattr(user, "is_active", False)
        and getattr(user, "can_administrate", False)
    )


def user_is_authenticated(user) -> bool:
    """Безопасно проверяет активного авторизованного пользователя."""

    return bool(
        user
        and getattr(user, "is_authenticated", False)
        and getattr(user, "is_active", False)
    )


def is_chat_rate_limited(
    request,
    *,
    scope: str,
    limit: int,
    window_seconds: int,
) -> bool:
    """Ограничивает частоту запросов по пользователю и IP."""

    user_marker = (
        f"user:{request.user.pk}"
        if getattr(request.user, "is_authenticated", False)
        else "anonymous"
    )
    ip_address = request.META.get("REMOTE_ADDR", "unknown")
    bucket = int(timezone.now().timestamp()) // max(window_seconds, 1)
    identity = hashlib.sha256(
        f"{user_marker}:{ip_address}".encode("utf-8")
    ).hexdigest()
    key = f"chat-rate:{scope}:{identity}:{bucket}"

    if cache.add(key, 1, timeout=window_seconds + 2):
        return False
    try:
        return cache.incr(key) > limit
    except ValueError:
        cache.set(key, 1, timeout=window_seconds + 2)
        return False


def chat_request_is_limited(request, *, scope: str, limit: int) -> bool:
    """Применяет минутный и короткий burst-лимит."""

    return (
        is_chat_rate_limited(
            request,
            scope=f"{scope}:window",
            limit=limit,
            window_seconds=settings.CHAT_RATE_WINDOW_SECONDS,
        )
        or is_chat_rate_limited(
            request,
            scope=f"{scope}:burst",
            limit=settings.CHAT_BURST_RATE_LIMIT,
            window_seconds=settings.CHAT_BURST_WINDOW_SECONDS,
        )
    )


class ChatMessageRateThrottle(UserRateThrottle):
    """DRF-защита API сообщений от частых запросов."""

    rate = "12/min"


def swagger_empty_queryset(view, model):
    """Возвращает пустой queryset при инспекции представления drf-yasg."""

    if getattr(view, "swagger_fake_view", False):
        return model.objects.none()
    return None


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

    if not user_is_authenticated(user):
        return queryset.none()

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

    if not user_is_authenticated(user):
        return queryset.none()

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

    if not user_is_authenticated(user):
        return queryset.none()

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

    if not user_is_authenticated(user):
        return queryset.none()

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

    if not user_is_authenticated(user):
        return queryset.none()

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

        schema_queryset = swagger_empty_queryset(self, ChatRoom)
        if schema_queryset is not None:
            return schema_queryset

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

        schema_queryset = swagger_empty_queryset(self, ChatRoom)
        if schema_queryset is not None:
            return schema_queryset

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

        schema_queryset = swagger_empty_queryset(self, ChatRoom)
        if schema_queryset is not None:
            return schema_queryset

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

        schema_queryset = swagger_empty_queryset(self, ChatRoom)
        if schema_queryset is not None:
            return schema_queryset

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

        schema_queryset = swagger_empty_queryset(
            self,
            ChatParticipant,
        )
        if schema_queryset is not None:
            return schema_queryset

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
        if not user.has_accepted_user_agreement():
            raise ValidationError(
                "Перед использованием чата примите "
                "пользовательское соглашение."
            )
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

        schema_queryset = swagger_empty_queryset(
            self,
            ChatParticipant,
        )
        if schema_queryset is not None:
            return schema_queryset

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

        schema_queryset = swagger_empty_queryset(
            self,
            ChatParticipant,
        )
        if schema_queryset is not None:
            return schema_queryset

        return manageable_participants_queryset(
            self.request.user,
        )

    def perform_update(self, serializer):
        """
        Проверяет право пользователя
        перенести участника в другую комнату.
        """

        user = self.request.user
        if not user.has_accepted_user_agreement():
            raise ValidationError(
                "Перед использованием чата примите "
                "пользовательское соглашение."
            )
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

        schema_queryset = swagger_empty_queryset(
            self,
            ChatParticipant,
        )
        if schema_queryset is not None:
            return schema_queryset

        if user_can_administrate(user):
            return queryset

        if not user_is_authenticated(user):
            return queryset.none()

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

        schema_queryset = swagger_empty_queryset(self, ChatMessage)
        if schema_queryset is not None:
            return schema_queryset

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
    throttle_classes = [ChatMessageRateThrottle]

    def perform_create(self, serializer):
        """
        Проверяет доступ пользователя
        к выбранной комнате и создаёт
        сообщение от его имени.
        """

        user = self.request.user
        if not user.has_accepted_user_agreement():
            raise ValidationError(
                "Перед использованием чата примите "
                "пользовательское соглашение."
            )
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

        text = serializer.validated_data["message"]
        try:
            decision = SmartAutoPartsAIService().moderate_request(
                user=user,
                text=text,
            )
        except AIServiceError as error:
            raise ValidationError(
                "Не удалось проверить сообщение. Повторите попытку позднее."
            ) from error
        if not decision.allowed:
            raise ValidationError(
                f"Сообщение отклонено автоматической модерацией: "
                f"{decision.reason}"
            )

        serializer.save(user=user)


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

        schema_queryset = swagger_empty_queryset(self, ChatMessage)
        if schema_queryset is not None:
            return schema_queryset

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
    throttle_classes = [ChatMessageRateThrottle]

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

        schema_queryset = swagger_empty_queryset(self, ChatMessage)
        if schema_queryset is not None:
            return schema_queryset

        if user_can_administrate(user):
            return queryset

        if not user_is_authenticated(user):
            return queryset.none()

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
        if not user.has_accepted_user_agreement():
            raise ValidationError(
                "Перед использованием чата примите "
                "пользовательское соглашение."
            )
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

        text = serializer.validated_data["message"]
        try:
            decision = SmartAutoPartsAIService().moderate_request(
                user=user,
                text=text,
            )
        except AIServiceError as error:
            raise ValidationError(
                "Не удалось проверить сообщение. Повторите попытку позднее."
            ) from error
        if not decision.allowed:
            raise ValidationError(
                f"Сообщение отклонено автоматической модерацией: "
                f"{decision.reason}"
            )

        serializer.save(user=instance.user)


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

        schema_queryset = swagger_empty_queryset(self, ChatMessage)
        if schema_queryset is not None:
            return schema_queryset

        if user_can_administrate(user):
            return queryset

        if not user_is_authenticated(user):
            return queryset.none()

        return queryset.filter(
            Q(user=user)
            | Q(room__created_by=user)
        ).distinct()


# ============================================================================
# HTML-интерфейс чата
# ============================================================================


class SubscriberChatAccessMixin(LoginRequiredMixin):
    """Разрешает чат сообщества всем зарегистрированным пользователям."""

    login_url = "users:login"

    @staticmethod
    def has_chat_access(user):
        return bool(
            getattr(user, "is_authenticated", False)
            and getattr(user, "is_active", False)
        )


class ChatRoomPageView(SubscriberChatAccessMixin, View):
    """Показывает доступные комнаты и сообщения выбранной комнаты."""

    template_name = "chat/chat.html"
    moderation_session_key = "community_chat_moderation_notice"

    def get(self, request):
        rooms = available_rooms_queryset(request.user)
        room_id = request.GET.get("room")
        room = None
        if room_id:
            room = get_object_or_404(rooms, pk=room_id)
        elif rooms.exists():
            room = rooms.first()

        room_messages = (
            available_messages_queryset(request.user)
            .filter(room=room)
            .order_by("created_at")
            if room is not None
            else ChatMessage.objects.none()
        )
        return render(
            request,
            self.template_name,
            {
                "rooms": rooms,
                "selected_room": room,
                "room_messages": room_messages,
                "moderation_notice": request.session.pop(
                    self.moderation_session_key,
                    None,
                ),
            },
        )


class ChatRoomCreatePageView(SubscriberChatAccessMixin, View):
    """Создаёт публичную или приватную комнату."""

    def post(self, request):
        name = request.POST.get("name", "").strip()
        if not 3 <= len(name) <= 255:
            messages.error(
                request,
                "Название комнаты должно содержать от 3 до 255 символов.",
            )
            return redirect("chat_web:rooms")

        room = ChatRoom.objects.create(
            name=name,
            is_private=request.POST.get("is_private") == "on",
            created_by=request.user,
        )
        ChatParticipant.objects.get_or_create(
            room=room,
            user=request.user,
        )
        messages.success(request, "Комната создана.")
        return redirect(f"{reverse('chat_web:rooms')}?room={room.pk}")


class ChatMessageCreatePageView(SubscriberChatAccessMixin, View):
    """Модерирует и отправляет сообщение в доступную комнату."""

    moderation_session_key = "community_chat_moderation_notice"

    def post(self, request, room_id):
        room = get_object_or_404(
            available_rooms_queryset(request.user),
            pk=room_id,
        )
        text = request.POST.get("message", "").strip()
        if not 1 <= len(text) <= 500:
            messages.error(
                request,
                "Сообщение должно содержать от 1 до 500 символов.",
            )
            return redirect(f"{reverse('chat_web:rooms')}?room={room.pk}")

        if chat_request_is_limited(
            request,
            scope="community",
            limit=settings.COMMUNITY_CHAT_RATE_LIMIT,
        ):
            messages.error(
                request,
                "Слишком много сообщений. Подождите немного и повторите.",
            )
            return redirect(f"{reverse('chat_web:rooms')}?room={room.pk}")

        try:
            decision = SmartAutoPartsAIService().moderate_request(
                user=request.user,
                text=text,
            )
        except AIRequestRejected as error:
            request.session[self.moderation_session_key] = (
                "Сообщение отклонено автоматической модерацией: "
                f"{error}"
            )
            return redirect(f"{reverse('chat_web:rooms')}?room={room.pk}")
        except (AIAccessDenied, AIServiceError):
            messages.error(
                request,
                "Не удалось проверить сообщение. Повторите попытку позднее.",
            )
            return redirect(f"{reverse('chat_web:rooms')}?room={room.pk}")

        if not decision.allowed:
            request.session[self.moderation_session_key] = (
                "Сообщение отклонено автоматической модерацией: "
                f"{decision.reason}"
            )
            return redirect(f"{reverse('chat_web:rooms')}?room={room.pk}")

        ChatMessage.objects.create(
            room=room,
            user=request.user,
            message=text,
        )
        return redirect(f"{reverse('chat_web:rooms')}?room={room.pk}")
