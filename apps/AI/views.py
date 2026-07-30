import logging

from django.conf import settings
from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import redirect, render
from django.views import View

from django.db.models import Q, QuerySet

from rest_framework import status
from rest_framework.exceptions import (
    APIException,
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
from rest_framework.response import Response

from users.permissions import IsOwner
from apps.parts.models import Part
from apps.subscriptions.access import (
    get_active_subscription,
    has_unlimited_ai_access,
    is_moderator_only,
    is_privileged_user,
)
from apps.chat.views import chat_request_is_limited

from .services import (
    AIAccessDenied,
    AIImageValidationError,
    AIRequestRejected,
    AIServiceError,
    AIQuotaService,
    SmartAutoPartsAIService,
)
from .models import (
    AIContentPurchase,
    AIGeneratedInstruction,
    AIImageAnalysis,
    AIRequest,
)
from .serializers import (
    AIGeneratedInstructionCreateSerializer,
    AIGeneratedInstructionSerializer,
    AIGeneratedInstructionUpdateSerializer,
    AIImageAnalysisCreateSerializer,
    AIImageAnalysisSerializer,
    AIImageAnalysisUpdateSerializer,
    AIRequestCreateSerializer,
    AIRequestSerializer,
    AIRequestUpdateSerializer,
)


logger = logging.getLogger(__name__)


class UserOwnedQuerySetMixin:
    """
    Ограничивает queryset объектами,
    принадлежащими текущему пользователю.

    Администраторы и системные
    суперпользователи Django получают
    доступ ко всем объектам.

    Поле или путь до владельца задаётся
    через атрибут owner_lookup.
    """

    owner_lookup = "user"

    def get_queryset(self) -> QuerySet:
        """
        Возвращает queryset с учётом
        прав текущего пользователя.
        """

        queryset = super().get_queryset()
        user = self.request.user

        if not user.is_authenticated:
            return queryset.none()

        if user.can_administrate:
            return queryset

        return queryset.filter(
            **{
                self.owner_lookup: user,
            }
        )


class AIRequestOwnedQuerySetMixin(
    UserOwnedQuerySetMixin,
):
    """
    Ограничивает AI-запросы текущим
    пользователем.
    """

    owner_lookup = "user"

    def get_queryset(self):
        queryset = super().get_queryset()
        user = self.request.user
        if is_privileged_user(user):
            return queryset
        if not getattr(user, "is_authenticated", False):
            return queryset.none()
        return (
            queryset.filter(
                ~Q(request_type__in=("chat", "chat_blocked"))
                | Q(
                    content_purchases__user=user,
                    content_purchases__content_type=(
                        AIContentPurchase.ContentType.CHAT
                    ),
                )
            )
            .distinct()
        )


class AIGeneratedInstructionOwnedQuerySetMixin(
    UserOwnedQuerySetMixin,
):
    """
    Ограничивает AI-инструкции через
    владельца связанного AI-запроса.
    """

    owner_lookup = "ai_request__user"


class AIImageAnalysisOwnedQuerySetMixin(
    UserOwnedQuerySetMixin,
):
    """
    Ограничивает анализы изображений
    текущим пользователем.
    """

    owner_lookup = "user"


class AIRequestListAPIView(
    AIRequestOwnedQuerySetMixin,
    ListAPIView,
):
    """
    API-представление для получения
    списка AI-запросов.

    Обычный пользователь получает только
    собственные AI-запросы.

    Администраторы и системные
    суперпользователи получают все запросы.
    """

    queryset = AIRequest.objects.select_related(
        "user",
        "part",
        "tool_recommendation",
    )
    serializer_class = AIRequestSerializer
    permission_classes = [
        IsAuthenticated,
    ]


class AIRequestCreateAPIView(CreateAPIView):
    """
    API-представление для создания
    AI-запроса.

    Текущий пользователь автоматически
    назначается владельцем запроса.
    """

    queryset = AIRequest.objects.all()
    serializer_class = AIRequestCreateSerializer
    permission_classes = [
        IsAuthenticated,
    ]

    def perform_create(self, serializer):
        """
        Создаёт AI-запрос для текущего
        авторизованного пользователя.

        Значение поля user, переданное
        клиентом, не используется.
        """

        AIQuotaService().check(
            self.request.user,
            feature="chat",
        )
        serializer.save(
            user=self.request.user,
        )


class AIRequestRetrieveAPIView(
    AIRequestOwnedQuerySetMixin,
    RetrieveAPIView,
):
    """
    API-представление для получения
    отдельного AI-запроса.

    Обычный пользователь может просматривать
    только собственные запросы.

    Администраторы и системные
    суперпользователи могут просматривать
    любые запросы.
    """

    queryset = AIRequest.objects.select_related(
        "user",
        "part",
        "tool_recommendation",
    )
    serializer_class = AIRequestSerializer
    permission_classes = [
        IsAuthenticated,
        IsOwner,
    ]


class AIRequestUpdateAPIView(
    AIRequestOwnedQuerySetMixin,
    UpdateAPIView,
):
    """
    API-представление для обновления
    AI-запроса.

    Обычный пользователь может изменять
    только собственные запросы.

    Администраторы и системные
    суперпользователи могут изменять
    любые запросы.
    """

    queryset = AIRequest.objects.select_related(
        "user",
        "part",
        "tool_recommendation",
    )
    serializer_class = AIRequestUpdateSerializer
    permission_classes = [
        IsAuthenticated,
        IsOwner,
    ]

    def perform_update(self, serializer):
        """
        Обновляет AI-запрос, сохраняя
        его текущего владельца.
        """

        instance = self.get_object()

        serializer.save(
            user=instance.user,
        )


class AIRequestDeleteAPIView(
    AIRequestOwnedQuerySetMixin,
    DestroyAPIView,
):
    """
    API-представление для удаления
    AI-запроса.

    Обычный пользователь может удалять
    только собственные запросы.

    Администраторы и системные
    суперпользователи могут удалять
    любые запросы.
    """

    queryset = AIRequest.objects.select_related(
        "user",
    )
    permission_classes = [
        IsAuthenticated,
        IsOwner,
    ]


class AIGeneratedInstructionListAPIView(
    AIGeneratedInstructionOwnedQuerySetMixin,
    ListAPIView,
):
    """
    API-представление для получения списка
    AI-сгенерированных инструкций.

    Обычный пользователь получает только
    инструкции, созданные на основе его
    собственных AI-запросов.

    Администраторы и системные
    суперпользователи получают все записи.
    """

    queryset = AIGeneratedInstruction.objects.select_related(
        "ai_request",
        "ai_request__user",
    )
    serializer_class = AIGeneratedInstructionSerializer
    permission_classes = [
        IsAuthenticated,
    ]


class AIGeneratedInstructionCreateAPIView(
    CreateAPIView,
):
    """
    API-представление для создания
    AI-сгенерированной инструкции.

    Обычный пользователь может создать
    инструкцию только для собственного
    AI-запроса.

    Администраторы и системные
    суперпользователи могут использовать
    любой AI-запрос.
    """

    queryset = AIGeneratedInstruction.objects.all()
    serializer_class = (
        AIGeneratedInstructionCreateSerializer
    )
    permission_classes = [
        IsAuthenticated,
    ]

    def perform_create(self, serializer):
        """
        Проверяет принадлежность выбранного
        AI-запроса текущему пользователю.
        """

        user = self.request.user
        ai_request = serializer.validated_data.get(
            "ai_request"
        )

        if ai_request is None:
            raise PermissionDenied(
                "Необходимо указать AI-запрос."
            )

        if (
            not user.can_administrate
            and ai_request.user_id != user.pk
        ):
            raise PermissionDenied(
                "Вы можете создавать инструкции "
                "только для собственных AI-запросов."
            )

        serializer.save()


class AIGeneratedInstructionRetrieveAPIView(
    AIGeneratedInstructionOwnedQuerySetMixin,
    RetrieveAPIView,
):
    """
    API-представление для получения
    AI-сгенерированной инструкции.

    Обычный пользователь может просматривать
    только инструкции, связанные с его
    AI-запросами.

    Администраторы и системные
    суперпользователи могут просматривать
    любые инструкции.
    """

    queryset = AIGeneratedInstruction.objects.select_related(
        "ai_request",
        "ai_request__user",
    )
    serializer_class = AIGeneratedInstructionSerializer
    permission_classes = [
        IsAuthenticated,
        IsOwner,
    ]


class AIGeneratedInstructionUpdateAPIView(
    AIGeneratedInstructionOwnedQuerySetMixin,
    UpdateAPIView,
):
    """
    API-представление для обновления
    AI-сгенерированной инструкции.

    Обычный пользователь может изменять
    только инструкции, связанные с его
    AI-запросами.

    Администраторы и системные
    суперпользователи могут изменять
    любые инструкции.
    """

    queryset = AIGeneratedInstruction.objects.select_related(
        "ai_request",
        "ai_request__user",
    )
    serializer_class = (
        AIGeneratedInstructionUpdateSerializer
    )
    permission_classes = [
        IsAuthenticated,
        IsOwner,
    ]

    def perform_update(self, serializer):
        """
        Проверяет новый AI-запрос при его
        изменении и запрещает привязывать
        инструкцию к чужому запросу.
        """

        user = self.request.user
        instance = self.get_object()

        ai_request = serializer.validated_data.get(
            "ai_request",
            instance.ai_request,
        )

        if (
            not user.can_administrate
            and ai_request.user_id != user.pk
        ):
            raise PermissionDenied(
                "Нельзя привязать инструкцию "
                "к чужому AI-запросу."
            )

        serializer.save()


class AIGeneratedInstructionDeleteAPIView(
    AIGeneratedInstructionOwnedQuerySetMixin,
    DestroyAPIView,
):
    """
    API-представление для удаления
    AI-сгенерированной инструкции.

    Обычный пользователь может удалять
    только инструкции, связанные с его
    AI-запросами.

    Администраторы и системные
    суперпользователи могут удалять
    любые инструкции.
    """

    queryset = AIGeneratedInstruction.objects.select_related(
        "ai_request",
        "ai_request__user",
    )
    permission_classes = [
        IsAuthenticated,
        IsOwner,
    ]


class AIImageAnalysisListAPIView(
    AIImageAnalysisOwnedQuerySetMixin,
    ListAPIView,
):
    """
    API-представление для получения
    списка анализов изображений.

    Обычный пользователь получает только
    собственные анализы.

    Администраторы и системные
    суперпользователи получают все анализы.
    """

    queryset = AIImageAnalysis.objects.select_related(
        "user",
    )
    serializer_class = AIImageAnalysisSerializer
    permission_classes = [
        IsAuthenticated,
    ]


class AIImageAnalysisCreateAPIView(
    CreateAPIView,
):
    """
    API-представление для создания
    запроса на анализ изображения.

    Текущий пользователь автоматически
    назначается владельцем анализа.
    """

    queryset = AIImageAnalysis.objects.all()
    serializer_class = AIImageAnalysisCreateSerializer
    permission_classes = [
        IsAuthenticated,
    ]

    def create(self, request, *args, **kwargs):
        """
        Валидирует тариф и файл, выполняет автоматическую мультимодальную
        модерацию и только затем сохраняет результат распознавания.
        """

        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        try:
            result = SmartAutoPartsAIService().analyze_part_image(
                user=request.user,
                image=serializer.validated_data["image"],
            )
        except AIRequestRejected as error:
            raise ValidationError(
                {
                    "image": [
                        "Изображение отклонено автоматической модерацией: "
                        f"{error}"
                    ]
                }
            ) from error
        except AIAccessDenied as error:
            raise PermissionDenied(str(error)) from error
        except AIImageValidationError as error:
            raise ValidationError({"image": [str(error)]}) from error
        except AIServiceError as error:
            provider_error = APIException(
                "AI-сервис временно недоступен. Повторите запрос позднее."
            )
            provider_error.status_code = status.HTTP_503_SERVICE_UNAVAILABLE
            raise provider_error from error

        response_serializer = AIImageAnalysisSerializer(
            result.image_analysis,
            context=self.get_serializer_context(),
        )
        return Response(
            response_serializer.data,
            status=status.HTTP_201_CREATED,
        )


class AIImageAnalysisRetrieveAPIView(
    AIImageAnalysisOwnedQuerySetMixin,
    RetrieveAPIView,
):
    """
    API-представление для получения
    информации об анализе изображения.

    Обычный пользователь может просматривать
    только собственные анализы.

    Администраторы и системные
    суперпользователи могут просматривать
    любые анализы.
    """

    queryset = AIImageAnalysis.objects.select_related(
        "user",
    )
    serializer_class = AIImageAnalysisSerializer
    permission_classes = [
        IsAuthenticated,
        IsOwner,
    ]


class AIImageAnalysisUpdateAPIView(
    AIImageAnalysisOwnedQuerySetMixin,
    UpdateAPIView,
):
    """
    API-представление для обновления
    результата анализа изображения.

    Обычный пользователь может изменять
    только собственные анализы.

    Администраторы и системные
    суперпользователи могут изменять
    любые анализы.
    """

    queryset = AIImageAnalysis.objects.select_related(
        "user",
    )
    serializer_class = AIImageAnalysisUpdateSerializer
    permission_classes = [
        IsAuthenticated,
        IsOwner,
    ]

    def perform_update(self, serializer):
        """
        Обновляет анализ изображения,
        сохраняя текущего владельца.
        """

        instance = self.get_object()

        serializer.save(
            user=instance.user,
        )


class AIImageAnalysisDeleteAPIView(
    AIImageAnalysisOwnedQuerySetMixin,
    DestroyAPIView,
):
    """
    API-представление для удаления
    анализа изображения.

    Обычный пользователь может удалять
    только собственные анализы.

    Администраторы и системные
    суперпользователи могут удалять
    любые анализы.
    """

    queryset = AIImageAnalysis.objects.select_related(
        "user",
    )
    permission_classes = [
        IsAuthenticated,
        IsOwner,
    ]


# ============================================================================
# HTML-интерфейс AI-помощника
# ============================================================================


class AIChatPageView(LoginRequiredMixin, View):
    """Показывает AI-чат и обрабатывает новый модерируемый запрос."""

    login_url = "users:login"
    template_name = "AI/chat.html"
    moderation_session_key = "ai_chat_moderation_notice"

    @staticmethod
    def has_access(user):
        if is_moderator_only(user):
            return False
        if has_unlimited_ai_access(user):
            return True
        subscription = get_active_subscription(user)
        return bool(
            subscription
            and subscription.plan.has_chat_access
            and subscription.plan.get_feature_limit("chat") > 0
        )

    def dispatch(self, request, *args, **kwargs):
        if (
            request.user.is_authenticated
            and not self.has_access(request.user)
        ):
            if is_moderator_only(request.user):
                messages.info(
                    request,
                    "Модератор проверяет ответы AI, "
                    "но не отправляет AI-запросы.",
                )
                return redirect("users:dashboard")
            messages.warning(
                request,
                "AI-помощник недоступен на текущем тарифе.",
            )
            return redirect("subscriptions_web:plans")
        return super().dispatch(request, *args, **kwargs)

    def get(self, request):
        privileged = has_unlimited_ai_access(request.user)
        subscription = get_active_subscription(request.user)
        conversation_queryset = AIRequest.objects.filter(
            user=request.user,
            request_type="chat",
        )
        if not privileged:
            conversation_queryset = conversation_queryset.filter(
                content_purchases__user=request.user,
                content_purchases__content_type=(
                    AIContentPurchase.ContentType.CHAT
                ),
            )
        conversations = list(
            conversation_queryset.select_related("part")
            .distinct()
            .order_by("-created_at")[:30]
        )
        conversations.reverse()

        quota_context = {
            "ai_unlimited": privileged,
            "ai_total_used": 0,
            "ai_total_limit": 0,
            "ai_total_remaining": 0,
            "ai_chat_used": 0,
            "ai_chat_limit": 0,
            "ai_chat_remaining": 0,
        }
        if subscription is not None and not privileged:
            period_requests = AIRequest.objects.filter(
                user=request.user,
                created_at__gte=subscription.start_date,
                created_at__lt=subscription.end_date,
            ).exclude(request_type__endswith="_blocked")
            chat_requests = period_requests.filter(
                Q(request_type="chat")
                | Q(request_type__startswith="tool_recommendation")
            )
            total_limit = int(subscription.plan.max_ai_requests)
            chat_limit = subscription.plan.get_feature_limit("chat")
            total_used = period_requests.count()
            chat_used = chat_requests.count()
            quota_context.update(
                {
                    "ai_total_used": total_used,
                    "ai_total_limit": total_limit,
                    "ai_total_remaining": max(
                        total_limit - total_used,
                        0,
                    ),
                    "ai_chat_used": chat_used,
                    "ai_chat_limit": chat_limit,
                    "ai_chat_remaining": max(
                        chat_limit - chat_used,
                        0,
                    ),
                }
            )

        return render(
            request,
            self.template_name,
            {
                "conversations": conversations,
                "subscription": subscription,
                "parts": Part.objects.filter(is_active=True).order_by(
                    "name"
                )[:200],
                "moderation_notice": request.session.pop(
                    self.moderation_session_key,
                    None,
                ),
                **quota_context,
            },
        )

    def post(self, request):
        message = request.POST.get("message", "").strip()
        part_query = request.POST.get("part_query", "").strip()
        if not 3 <= len(message) <= 500:
            messages.error(
                request,
                "Вопрос должен содержать от 3 до 500 символов.",
            )
            return redirect("ai_web:chat")

        if chat_request_is_limited(
            request,
            scope="ai",
            limit=settings.AI_CHAT_RATE_LIMIT,
        ):
            messages.error(
                request,
                "Слишком много запросов. Подождите немного и повторите.",
            )
            return redirect("ai_web:chat")

        part = None
        if part_query:
            part = self.resolve_part_query(part_query)

        try:
            SmartAutoPartsAIService().answer_chat(
                user=request.user,
                message=message,
                part=part,
            )
            if part_query and part is None:
                messages.info(
                    request,
                    "Связанная деталь в базе не найдена. Запрос обработан "
                    "без привязки к карточке; номера из сообщения учтены.",
                )
        except AIRequestRejected as error:
            request.session[self.moderation_session_key] = (
                f"Запрос отклонён: {error}"
            )
        except AIAccessDenied as error:
            messages.warning(request, str(error))
        except AIServiceError as error:
            logger.exception("AI chat request failed", exc_info=error)
            messages.error(
                request,
                "AI-помощник временно недоступен. Повторите запрос позднее.",
            )

        return redirect("ai_web:chat")

    @staticmethod
    def resolve_part_query(query):
        """Ищет связанную деталь только в существующем каталоге."""

        cleaned = query.strip()
        if not cleaned:
            return None
        normalized = "".join(
            character
            for character in cleaned.upper()
            if character.isalnum()
        )
        queryset = Part.objects.filter(is_active=True)

        exact = queryset.filter(
            Q(original_number__iexact=cleaned)
            | Q(normalized_original_number=normalized)
            | Q(oem_numbers__number__iexact=cleaned)
        ).first()
        if exact is not None:
            return exact

        return (
            queryset.filter(
                Q(name__icontains=cleaned)
                | Q(manufacturer__icontains=cleaned)
                | Q(original_number__icontains=cleaned)
                | Q(oem_numbers__number__icontains=cleaned)
            )
            .distinct()
            .order_by("name", "pk")
            .first()
        )
