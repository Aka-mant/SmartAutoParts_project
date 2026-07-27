import logging

from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.db.models import Prefetch
from django.shortcuts import get_object_or_404, redirect
from django.views import View
from django.views.generic import DetailView, FormView

from rest_framework.generics import (
    CreateAPIView,
    DestroyAPIView,
    ListAPIView,
    RetrieveAPIView,
    UpdateAPIView,
)
from rest_framework.permissions import IsAuthenticated
from rest_framework.permissions import BasePermission

from users.permissions import (
    IsAdmin,
    IsModerator,
)

from apps.AI.models import (
    AIContentPurchase,
    AIGeneratedInstruction,
    AIImageAnalysis,
    AIToolRecommendation,
)
from apps.AI.services import (
    AIAccessDenied,
    AIRequestRejected,
    AIServiceError,
    SmartAutoPartsAIService,
)
from apps.instructions.models import Instruction
from apps.subscriptions.access import (
    get_active_subscription,
    has_unlimited_ai_access,
    has_part_card_access,
    is_moderator_only,
    is_privileged_user,
    purchased_instruction_ids,
)

from .forms import PartImageAnalysisUploadForm
from .models import (
    Compatibility,
    OEMNumber,
    Part,
    PartCategory,
    PartImage,
)


logger = logging.getLogger(__name__)
from .serializers import (
    CompatibilityCreateSerializer,
    CompatibilitySerializer,
    CompatibilityUpdateSerializer,
    OEMNumberCreateSerializer,
    OEMNumberSerializer,
    OEMNumberUpdateSerializer,
    PartCategoryCreateSerializer,
    PartCategorySerializer,
    PartCategoryUpdateSerializer,
    PartCreateSerializer,
    PartImageCreateSerializer,
    PartImageSerializer,
    PartImageUpdateSerializer,
    PartSerializer,
    PartUpdateSerializer,
)


class HasPartCardAccess(BasePermission):
    """Разрешает API-карточку только при действующем тарифе."""

    message = "Для просмотра карточки детали выберите действующий тариф."

    def has_permission(self, request, view):
        return has_part_card_access(request.user)


class PartCategoryListAPIView(ListAPIView):
    """
    API-представление для получения
    списка категорий запчастей.

    Доступно всем авторизованным
    пользователям.
    """

    queryset = PartCategory.objects.all()
    serializer_class = PartCategorySerializer
    permission_classes = [
        IsAuthenticated,
    ]


class PartCategoryCreateAPIView(CreateAPIView):
    """
    API-представление для создания
    категории запчастей.

    Доступ предоставляется:

    - модераторам;
    - администраторам;
    - системным суперпользователям Django.
    """

    queryset = PartCategory.objects.all()
    serializer_class = PartCategoryCreateSerializer
    permission_classes = [
        IsAuthenticated,
        IsModerator,
    ]


class PartCategoryRetrieveAPIView(RetrieveAPIView):
    """
    API-представление для получения
    информации о категории запчастей.

    Доступно всем авторизованным
    пользователям.
    """

    queryset = PartCategory.objects.all()
    serializer_class = PartCategorySerializer
    permission_classes = [
        IsAuthenticated,
    ]


class PartCategoryUpdateAPIView(UpdateAPIView):
    """
    API-представление для обновления
    категории запчастей.

    Доступ предоставляется:

    - модераторам;
    - администраторам;
    - системным суперпользователям Django.
    """

    queryset = PartCategory.objects.all()
    serializer_class = PartCategoryUpdateSerializer
    permission_classes = [
        IsAuthenticated,
        IsModerator,
    ]


class PartCategoryDeleteAPIView(DestroyAPIView):
    """
    API-представление для удаления
    категории запчастей.

    Доступ предоставляется:

    - администраторам;
    - системным суперпользователям Django.
    """

    queryset = PartCategory.objects.all()
    permission_classes = [
        IsAuthenticated,
        IsAdmin,
    ]


class PartListAPIView(ListAPIView):
    """
    API-представление для получения
    списка автомобильных запчастей.

    Доступно всем авторизованным
    пользователям.
    """

    queryset = Part.objects.select_related(
        "category",
    )
    serializer_class = PartSerializer
    permission_classes = [
        IsAuthenticated,
    ]


class PartCreateAPIView(CreateAPIView):
    """
    API-представление для создания
    автомобильной запчасти.

    Доступ предоставляется:

    - модераторам;
    - администраторам;
    - системным суперпользователям Django.
    """

    queryset = Part.objects.all()
    serializer_class = PartCreateSerializer
    permission_classes = [
        IsAuthenticated,
        IsModerator,
    ]


class PartRetrieveAPIView(RetrieveAPIView):
    """
    API-представление для получения
    информации об автомобильной запчасти.

    Доступно всем авторизованным
    пользователям.
    """

    queryset = Part.objects.select_related(
        "category",
    )
    serializer_class = PartSerializer
    permission_classes = [
        IsAuthenticated,
        HasPartCardAccess,
    ]


class PartUpdateAPIView(UpdateAPIView):
    """
    API-представление для обновления
    автомобильной запчасти.

    Доступ предоставляется:

    - модераторам;
    - администраторам;
    - системным суперпользователям Django.
    """

    queryset = Part.objects.select_related(
        "category",
    )
    serializer_class = PartUpdateSerializer
    permission_classes = [
        IsAuthenticated,
        IsModerator,
    ]


class PartDeleteAPIView(DestroyAPIView):
    """
    API-представление для удаления
    автомобильной запчасти.

    Доступ предоставляется:

    - администраторам;
    - системным суперпользователям Django.
    """

    queryset = Part.objects.select_related(
        "category",
    )
    permission_classes = [
        IsAuthenticated,
        IsAdmin,
    ]


class OEMNumberListAPIView(ListAPIView):
    """
    API-представление для получения
    списка OEM-номеров.

    Доступно всем авторизованным
    пользователям.
    """

    queryset = OEMNumber.objects.select_related(
        "part",
    )
    serializer_class = OEMNumberSerializer
    permission_classes = [
        IsAuthenticated,
    ]


class OEMNumberCreateAPIView(CreateAPIView):
    """
    API-представление для создания
    OEM-номера.

    Доступ предоставляется:

    - модераторам;
    - администраторам;
    - системным суперпользователям Django.
    """

    queryset = OEMNumber.objects.all()
    serializer_class = OEMNumberCreateSerializer
    permission_classes = [
        IsAuthenticated,
        IsModerator,
    ]


class OEMNumberRetrieveAPIView(RetrieveAPIView):
    """
    API-представление для получения
    информации об OEM-номере.

    Доступно всем авторизованным
    пользователям.
    """

    queryset = OEMNumber.objects.select_related(
        "part",
    )
    serializer_class = OEMNumberSerializer
    permission_classes = [
        IsAuthenticated,
    ]


class OEMNumberUpdateAPIView(UpdateAPIView):
    """
    API-представление для обновления
    OEM-номера.

    Доступ предоставляется:

    - модераторам;
    - администраторам;
    - системным суперпользователям Django.
    """

    queryset = OEMNumber.objects.select_related(
        "part",
    )
    serializer_class = OEMNumberUpdateSerializer
    permission_classes = [
        IsAuthenticated,
        IsModerator,
    ]


class OEMNumberDeleteAPIView(DestroyAPIView):
    """
    API-представление для удаления
    OEM-номера.

    Доступ предоставляется:

    - администраторам;
    - системным суперпользователям Django.
    """

    queryset = OEMNumber.objects.select_related(
        "part",
    )
    permission_classes = [
        IsAuthenticated,
        IsAdmin,
    ]


class CompatibilityListAPIView(ListAPIView):
    """
    API-представление для получения
    списка совместимостей запчастей.

    Доступно всем авторизованным
    пользователям.
    """

    queryset = Compatibility.objects.select_related(
        "part",
    )
    serializer_class = CompatibilitySerializer
    permission_classes = [
        IsAuthenticated,
    ]


class CompatibilityCreateAPIView(CreateAPIView):
    """
    API-представление для создания
    записи совместимости.

    Доступ предоставляется:

    - модераторам;
    - администраторам;
    - системным суперпользователям Django.
    """

    queryset = Compatibility.objects.all()
    serializer_class = CompatibilityCreateSerializer
    permission_classes = [
        IsAuthenticated,
        IsModerator,
    ]


class CompatibilityRetrieveAPIView(RetrieveAPIView):
    """
    API-представление для получения
    информации о совместимости запчасти.

    Доступно всем авторизованным
    пользователям.
    """

    queryset = Compatibility.objects.select_related(
        "part",
    )
    serializer_class = CompatibilitySerializer
    permission_classes = [
        IsAuthenticated,
    ]


class CompatibilityUpdateAPIView(UpdateAPIView):
    """
    API-представление для обновления
    записи совместимости.

    Доступ предоставляется:

    - модераторам;
    - администраторам;
    - системным суперпользователям Django.
    """

    queryset = Compatibility.objects.select_related(
        "part",
    )
    serializer_class = CompatibilityUpdateSerializer
    permission_classes = [
        IsAuthenticated,
        IsModerator,
    ]


class CompatibilityDeleteAPIView(DestroyAPIView):
    """
    API-представление для удаления
    записи совместимости.

    Доступ предоставляется:

    - администраторам;
    - системным суперпользователям Django.
    """

    queryset = Compatibility.objects.select_related(
        "part",
    )
    permission_classes = [
        IsAuthenticated,
        IsAdmin,
    ]


class PartImageListAPIView(ListAPIView):
    """
    API-представление для получения
    списка изображений запчастей.

    Доступно всем авторизованным
    пользователям.
    """

    queryset = PartImage.objects.select_related(
        "part",
    )
    serializer_class = PartImageSerializer
    permission_classes = [
        IsAuthenticated,
    ]


class PartImageCreateAPIView(CreateAPIView):
    """
    API-представление для загрузки
    изображения запчасти.

    Доступ предоставляется:

    - модераторам;
    - администраторам;
    - системным суперпользователям Django.
    """

    queryset = PartImage.objects.all()
    serializer_class = PartImageCreateSerializer
    permission_classes = [
        IsAuthenticated,
        IsModerator,
    ]


class PartImageRetrieveAPIView(RetrieveAPIView):
    """
    API-представление для получения
    информации об изображении запчасти.

    Доступно всем авторизованным
    пользователям.
    """

    queryset = PartImage.objects.select_related(
        "part",
    )
    serializer_class = PartImageSerializer
    permission_classes = [
        IsAuthenticated,
    ]


class PartImageUpdateAPIView(UpdateAPIView):
    """
    API-представление для обновления
    изображения запчасти.

    Доступ предоставляется:

    - модераторам;
    - администраторам;
    - системным суперпользователям Django.
    """

    queryset = PartImage.objects.select_related(
        "part",
    )
    serializer_class = PartImageUpdateSerializer
    permission_classes = [
        IsAuthenticated,
        IsModerator,
    ]


class PartImageDeleteAPIView(DestroyAPIView):
    """
    API-представление для удаления
    изображения запчасти.

    Доступ предоставляется:

    - администраторам;
    - системным суперпользователям Django.
    """

    queryset = PartImage.objects.select_related(
        "part",
    )
    permission_classes = [
        IsAuthenticated,
        IsAdmin,
    ]


# ============================================================================
# HTML-каталог и пользовательские AI-действия
# ============================================================================


class PartDetailPageView(LoginRequiredMixin, DetailView):
    """Карточка активной автомобильной детали."""

    login_url = "users:login"
    model = Part
    template_name = "parts/part_detail.html"
    context_object_name = "part"
    slug_field = "slug"
    slug_url_kwarg = "slug"

    def dispatch(self, request, *args, **kwargs):
        if (
            request.user.is_authenticated
            and not has_part_card_access(request.user)
        ):
            messages.warning(
                request,
                "Для просмотра карточки детали выберите действующий тариф.",
            )
            return redirect("subscriptions_web:plans")
        return super().dispatch(request, *args, **kwargs)

    def get_queryset(self):
        instruction_queryset = Instruction.objects.filter(
            is_published=True
        ).order_by("title")
        purchased_ids = purchased_instruction_ids(self.request.user)
        if purchased_ids is not None:
            instruction_queryset = instruction_queryset.filter(
                pk__in=purchased_ids
            )

        return (
            Part.objects.filter(is_active=True)
            .select_related("category")
            .prefetch_related(
                "images",
                "oem_numbers",
                "compatibilities",
                "part_tools__tool__category",
                Prefetch(
                    "instructions",
                    queryset=instruction_queryset,
                    to_attr="public_instructions",
                ),
            )
        )

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.request.user
        content_privileged = is_privileged_user(user)
        ai_unlimited = has_unlimited_ai_access(user)
        moderator_only = is_moderator_only(user)
        subscription = get_active_subscription(user)
        actual_tools_purchase = AIContentPurchase.objects.filter(
            user=user,
            content_type=AIContentPurchase.ContentType.TOOLS,
            part=self.object,
        ).exists()
        instruction_pending_queryset = AIGeneratedInstruction.objects.filter(
            ai_request__part=self.object,
            moderation_status=(
                AIGeneratedInstruction.ModerationStatus.PENDING
            ),
        )
        tools_pending_queryset = AIToolRecommendation.objects.filter(
            ai_request__part=self.object,
            moderation_status=(
                AIToolRecommendation.ModerationStatus.PENDING
            ),
        )
        if not content_privileged:
            instruction_pending_queryset = instruction_pending_queryset.filter(
                ai_request__user=user
            )
            tools_pending_queryset = tools_pending_queryset.filter(
                ai_request__user=user
            )
        instruction_request_pending = instruction_pending_queryset.exists()
        tools_request_pending = tools_pending_queryset.exists()
        tools_purchased = content_privileged or actual_tools_purchase
        tools_selected = bool(
            actual_tools_purchase
            or tools_request_pending
            or (
                content_privileged
                and self.object.part_tools.exists()
            )
        )
        instruction_purchase = None
        if content_privileged:
            purchased_instruction = next(
                iter(self.object.public_instructions),
                None,
            )
        else:
            instruction_purchase = (
                AIContentPurchase.objects.select_related("instruction")
                .filter(
                    user=user,
                    content_type=(
                        AIContentPurchase.ContentType.INSTRUCTION
                    ),
                    part=self.object,
                )
                .order_by("-purchased_at")
                .first()
            )
            purchased_instruction = (
                instruction_purchase.instruction
                if instruction_purchase is not None
                and instruction_purchase.instruction is not None
                and instruction_purchase.instruction.is_published
                else None
            )

        context.update(
            {
                "is_ai_privileged": ai_unlimited,
                "has_unrestricted_content": content_privileged,
                "is_ai_moderator": moderator_only,
                "can_request_instruction": bool(
                    not moderator_only
                    and (
                    ai_unlimited
                    or (
                        subscription
                        and subscription.plan.has_instruction_generation
                        and subscription.plan.get_feature_limit(
                            "instruction"
                        )
                        > 0
                    )
                    )
                ),
                "can_request_tools": bool(
                    not moderator_only
                    and (
                    ai_unlimited
                    or (
                        subscription
                        and subscription.plan.has_chat_access
                        and subscription.plan.get_feature_limit("chat") > 0
                    )
                    )
                ),
                "can_analyze_image": bool(
                    not moderator_only
                    and (
                    ai_unlimited
                    or (
                        subscription
                        and subscription.plan.has_image_analysis
                        and subscription.plan.get_feature_limit(
                            "image_analysis"
                        )
                        > 0
                    )
                    )
                ),
                "tools_purchased": tools_purchased,
                "tools_selected": tools_selected,
                "tools_request_pending": tools_request_pending,
                "instruction_purchased": bool(
                    (
                        content_privileged
                        and purchased_instruction is not None
                    )
                    or instruction_purchase is not None
                ),
                "instruction_request_pending": (
                    instruction_request_pending
                ),
                "purchased_instruction": purchased_instruction,
                "moderation_average_minutes": 30,
            }
        )

        if (
            getattr(user, "is_authenticated", False)
            and tools_purchased
        ):
            approved_recommendations = (
                AIToolRecommendation.objects.select_related(
                    "ai_request",
                    "reviewed_by",
                )
                .filter(
                    ai_request__part=self.object,
                    moderation_status=(
                        AIToolRecommendation.ModerationStatus.APPROVED
                    ),
                )
            )
            if not content_privileged:
                approved_recommendations = approved_recommendations.filter(
                    ai_request__user=user
                )
            context["approved_tool_recommendation"] = (
                approved_recommendations
                .order_by("-reviewed_at", "-created_at")
                .first()
            )

        return context


class PartAIRequestMixin(LoginRequiredMixin):
    """Общая безопасная обработка AI-запросов карточки детали."""

    login_url = "users:login"

    def get_part(self):
        return get_object_or_404(
            Part,
            slug=self.kwargs["slug"],
            is_active=True,
        )

    @staticmethod
    def redirect_to_part(part):
        return redirect(f"{part.get_absolute_url()}#ai-requests")

    def handle_ai_error(self, *, request, part, error):
        if isinstance(error, AIRequestRejected):
            messages.error(
                request,
                f"Запрос отклонён модерацией: {error}",
            )
        elif isinstance(error, AIAccessDenied):
            messages.warning(request, str(error))
        else:
            logger.exception(
                "Part AI request failed",
                exc_info=error,
            )
            messages.error(
                request,
                "AI-сервис временно недоступен. Повторите запрос позднее.",
            )
        return self.redirect_to_part(part)


class PartInstructionRequestView(PartAIRequestMixin, View):
    """Запрашивает проверенную или новую AI-инструкцию для детали."""

    def post(self, request, *args, **kwargs):
        part = self.get_part()
        if not has_unlimited_ai_access(request.user):
            purchase = (
                AIContentPurchase.objects.select_related("instruction")
                .filter(
                    user=request.user,
                    content_type=(
                        AIContentPurchase.ContentType.INSTRUCTION
                    ),
                    part=part,
                )
                .order_by("-purchased_at")
                .first()
            )
            if purchase is not None:
                if (
                    purchase.instruction is not None
                    and purchase.instruction.is_published
                ):
                    messages.info(
                        request,
                        "Эта инструкция уже приобретена.",
                    )
                    return redirect(
                        purchase.instruction.get_absolute_url()
                    )
                messages.info(
                    request,
                    "Приобретённая инструкция находится на модерации.",
                )
                return self.redirect_to_part(part)

        instruction = (
            Instruction.objects.filter(
                part=part,
                is_published=True,
            )
            .order_by("-updated_at", "-version", "pk")
            .first()
        )
        goal = (
            "На основе проверяемых данных SmartAutoParts подготовь безопасную "
            "пошаговую инструкцию по диагностике, снятию, установке и "
            f"финальной проверке детали ID {part.pk}: {part.name}, "
            f"OEM {part.original_number}. Используй совместимости, "
            "инструменты, профиль автомобиля и опубликованные инструкции "
            "из контекста проекта. Не используй пользовательский текст и "
            "не выдумывай отсутствующие технические значения."
        )

        try:
            result = SmartAutoPartsAIService().generate_repair_instruction(
                user=request.user,
                part=part,
                goal=goal,
                instruction=instruction,
            )
        except (AIServiceError, ValueError) as error:
            return self.handle_ai_error(
                request=request,
                part=part,
                error=error,
            )

        if result.cached and result.generated_instruction.instruction:
            messages.success(
                request,
                "Проверенная инструкция готова к использованию.",
            )
            return redirect(
                result.generated_instruction.instruction.get_absolute_url()
            )

        messages.success(
            request,
            "Инструкция отправлена техническому модератору. "
            "Среднее время проверки — до 30 минут.",
        )
        return self.redirect_to_part(part)


class PartToolRecommendationRequestView(PartAIRequestMixin, View):
    """Выполняет модерируемый AI-подбор инструментов для детали."""

    def post(self, request, *args, **kwargs):
        part = self.get_part()
        if (
            not has_unlimited_ai_access(request.user)
            and AIContentPurchase.objects.filter(
                user=request.user,
                content_type=AIContentPurchase.ContentType.TOOLS,
                part=part,
            ).exists()
        ):
            messages.info(
                request,
                "Инструменты для этой детали уже приобретены.",
            )
            return self.redirect_to_part(part)

        goal = (
            "На основе проверяемых данных SmartAutoParts подбери обязательные "
            "и рекомендуемые инструменты, средства защиты и расходные "
            f"материалы для детали ID {part.pk}: {part.name}, "
            f"OEM {part.original_number}. Используй связи PartTool, Tool, "
            "InstructionTool, совместимости и опубликованные инструкции "
            "из контекста проекта. Не используй пользовательский текст и "
            "не выдумывай отсутствующие размеры или технические значения."
        )

        try:
            service = SmartAutoPartsAIService()
            cached_request = None
            if not has_unlimited_ai_access(request.user):
                cached_request = service.purchase_stored_part_tools(
                    user=request.user,
                    part=part,
                )
            if cached_request is not None:
                messages.success(
                    request,
                    "Проверенный список инструментов приобретён "
                    "и открыт в карточке детали.",
                )
                return redirect(
                    f"{part.get_absolute_url()}#part-tools"
                )

            service.recommend_part_tools(
                user=request.user,
                part=part,
                goal=goal,
            )
        except (AIServiceError, ValueError) as error:
            return self.handle_ai_error(
                request=request,
                part=part,
                error=error,
            )

        messages.success(
            request,
            "Контент приобретён. Проверенные инструменты из каталога "
            "уже доступны; AI-рекомендация отправлена на модерацию. "
            "Среднее время проверки — до 30 минут.",
        )
        return self.redirect_to_part(part)


class PartImageAnalysisUploadView(LoginRequiredMixin, FormView):
    """Модерирует фотографию и распознаёт запчасть или инструмент."""

    template_name = "parts/image_analysis_form.html"
    form_class = PartImageAnalysisUploadForm
    login_url = "users:login"
    moderation_session_key = "image_analysis_moderation_notice"

    def dispatch(self, request, *args, **kwargs):
        if request.user.is_authenticated and is_moderator_only(request.user):
            messages.info(
                request,
                "Модератор может проверять результаты AI, "
                "но не отправлять изображения на анализ.",
            )
            return redirect("users:dashboard")
        return super().dispatch(request, *args, **kwargs)

    def post(self, request, *args, **kwargs):
        request.session.pop(self.moderation_session_key, None)
        return super().post(request, *args, **kwargs)

    def form_valid(self, form):
        try:
            result = SmartAutoPartsAIService().analyze_part_image(
                user=self.request.user,
                image=form.cleaned_data["image"],
            )
        except AIRequestRejected as error:
            self.request.session[self.moderation_session_key] = (
                "Изображение отклонено автоматической модерацией: "
                f"{error}"
            )
            return redirect("parts_web:image_analysis")
        except AIAccessDenied as error:
            messages.warning(self.request, str(error))
            return redirect("subscriptions_web:plans")
        except (AIServiceError, ValueError) as error:
            logger.exception(
                "Part image analysis failed",
                exc_info=error,
            )
            messages.error(
                self.request,
                "Не удалось проверить и распознать изображение. "
                "Проверьте формат файла и повторите попытку.",
            )
            return redirect("parts_web:image_analysis")

        messages.success(
            self.request,
            "Проверка фотографии завершена.",
        )
        return redirect(
            "parts_web:image_analysis_result",
            pk=result.image_analysis.pk,
        )

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.request.user
        privileged = has_unlimited_ai_access(user)
        subscription = get_active_subscription(user)
        context["is_ai_privileged"] = privileged
        context["moderation_notice"] = self.request.session.get(
            self.moderation_session_key
        )
        context["can_analyze_image"] = bool(
            not is_moderator_only(user)
            and (
            privileged
            or (
                subscription
                and subscription.plan.has_image_analysis
                and subscription.plan.get_feature_limit(
                    "image_analysis"
                )
                > 0
            )
            )
        )
        return context


class PartImageAnalysisResultView(LoginRequiredMixin, DetailView):
    """Показывает владельцу результат безопасного анализа фотографии."""

    model = AIImageAnalysis
    template_name = "parts/image_analysis_result.html"
    context_object_name = "analysis"
    login_url = "users:login"

    def get_queryset(self):
        queryset = AIImageAnalysis.objects.select_related(
            "user",
            "detected_part",
        )
        if is_privileged_user(self.request.user):
            return queryset
        return queryset.filter(user=self.request.user)
