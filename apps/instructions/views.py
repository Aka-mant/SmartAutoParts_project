from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.db import transaction
from django.db.models import Count, Prefetch, Q
from django.shortcuts import get_object_or_404, redirect, render
from django.views import View
from django.views.generic import DetailView, ListView

from rest_framework.generics import (
    CreateAPIView,
    DestroyAPIView,
    ListAPIView,
    RetrieveAPIView,
    UpdateAPIView,
)
from rest_framework.permissions import IsAuthenticated

from users.permissions import (
    IsAdmin,
    IsModerator,
)
from apps.subscriptions.access import (
    has_instruction_access,
    has_purchased_instruction,
    is_privileged_user,
    purchased_instruction_ids,
)
from apps.parts.models import PartCategory
from users.models import RepairHistory

from .models import (
    Instruction,
    InstructionImage,
    InstructionStep,
    InstructionTool,
    InstructionVersion,
)
from .serializers import (
    InstructionCreateSerializer,
    InstructionImageCreateSerializer,
    InstructionImageSerializer,
    InstructionImageUpdateSerializer,
    InstructionSerializer,
    InstructionStepCreateSerializer,
    InstructionStepSerializer,
    InstructionStepUpdateSerializer,
    InstructionToolCreateSerializer,
    InstructionToolSerializer,
    InstructionToolUpdateSerializer,
    InstructionUpdateSerializer,
    InstructionVersionCreateSerializer,
    InstructionVersionSerializer,
    InstructionVersionUpdateSerializer,
)


class PublishedInstructionQuerySetMixin:
    """Открывает API только для приобретённых инструкций."""

    def get_queryset(self):
        queryset = super().get_queryset()
        if is_privileged_user(self.request.user):
            return queryset
        if not has_instruction_access(self.request.user):
            return queryset.none()
        return queryset.filter(
            is_published=True,
            pk__in=purchased_instruction_ids(self.request.user),
        )


class InstructionRelatedAccessMixin:
    """Ограничивает вложенные данные доступными инструкциями."""

    def get_queryset(self):
        queryset = super().get_queryset()
        if is_privileged_user(self.request.user):
            return queryset

        if not has_instruction_access(self.request.user):
            return queryset.none()

        queryset = queryset.filter(
            instruction__is_published=True,
            instruction_id__in=purchased_instruction_ids(
                self.request.user
            ),
        )
        return queryset


class InstructionListAPIView(
    PublishedInstructionQuerySetMixin,
    ListAPIView,
):
    """
    API-представление для получения
    списка инструкций.

    Доступно всем авторизованным
    пользователям.
    """

    queryset = Instruction.objects.select_related(
        "part",
        "created_by",
        "updated_by",
    )
    serializer_class = InstructionSerializer
    permission_classes = [
        IsAuthenticated,
    ]


class InstructionCreateAPIView(CreateAPIView):
    """
    API-представление для создания
    инструкции.

    Доступ предоставляется:

    - модераторам;
    - администраторам;
    - системным суперпользователям Django.
    """

    queryset = Instruction.objects.all()
    serializer_class = InstructionCreateSerializer
    permission_classes = [
        IsAuthenticated,
        IsModerator,
    ]

    def perform_create(self, serializer):
        """
        Автоматически назначает текущего
        пользователя автором инструкции
        и последним редактором.
        """

        serializer.save(
            created_by=self.request.user,
            updated_by=self.request.user,
        )


class InstructionRetrieveAPIView(
    PublishedInstructionQuerySetMixin,
    RetrieveAPIView,
):
    """
    API-представление для получения
    информации об одной инструкции.

    Доступно всем авторизованным
    пользователям.
    """

    queryset = Instruction.objects.select_related(
        "part",
        "created_by",
        "updated_by",
    )
    serializer_class = InstructionSerializer
    permission_classes = [
        IsAuthenticated,
    ]


class InstructionUpdateAPIView(UpdateAPIView):
    """
    API-представление для обновления
    инструкции.

    Доступ предоставляется:

    - модераторам;
    - администраторам;
    - системным суперпользователям Django.
    """

    queryset = Instruction.objects.select_related(
        "part",
        "created_by",
        "updated_by",
    )
    serializer_class = InstructionUpdateSerializer
    permission_classes = [
        IsAuthenticated,
        IsModerator,
    ]

    def perform_update(self, serializer):
        """
        Обновляет инструкцию и автоматически
        назначает текущего пользователя
        последним редактором.

        Поле created_by сохраняется без изменений.
        """

        instance = self.get_object()

        serializer.save(
            created_by=instance.created_by,
            updated_by=self.request.user,
        )


class InstructionDeleteAPIView(DestroyAPIView):
    """
    API-представление для удаления
    инструкции.

    Доступ предоставляется:

    - администраторам;
    - системным суперпользователям Django.
    """

    queryset = Instruction.objects.select_related(
        "part",
        "created_by",
        "updated_by",
    )
    permission_classes = [
        IsAuthenticated,
        IsAdmin,
    ]


class InstructionVersionListAPIView(
    InstructionRelatedAccessMixin,
    ListAPIView,
):
    """
    API-представление для получения
    списка версий инструкций.

    Доступно всем авторизованным
    пользователям.
    """

    queryset = InstructionVersion.objects.select_related(
        "instruction",
        "created_by",
    )
    serializer_class = InstructionVersionSerializer
    permission_classes = [
        IsAuthenticated,
    ]


class InstructionVersionCreateAPIView(CreateAPIView):
    """
    API-представление для создания
    новой версии инструкции.

    Доступ предоставляется:

    - модераторам;
    - администраторам;
    - системным суперпользователям Django.
    """

    queryset = InstructionVersion.objects.all()
    serializer_class = InstructionVersionCreateSerializer
    permission_classes = [
        IsAuthenticated,
        IsModerator,
    ]

    def perform_create(self, serializer):
        """
        Создаёт версию инструкции и
        автоматически назначает текущего
        пользователя её автором.
        """

        serializer.save(
            created_by=self.request.user,
        )


class InstructionVersionRetrieveAPIView(
    InstructionRelatedAccessMixin,
    RetrieveAPIView,
):
    """
    API-представление для получения
    информации о версии инструкции.

    Доступно всем авторизованным
    пользователям.
    """

    queryset = InstructionVersion.objects.select_related(
        "instruction",
        "created_by",
    )
    serializer_class = InstructionVersionSerializer
    permission_classes = [
        IsAuthenticated,
    ]


class InstructionVersionUpdateAPIView(UpdateAPIView):
    """
    API-представление для обновления
    версии инструкции.

    Доступ предоставляется:

    - модераторам;
    - администраторам;
    - системным суперпользователям Django.
    """

    queryset = InstructionVersion.objects.select_related(
        "instruction",
        "created_by",
    )
    serializer_class = InstructionVersionUpdateSerializer
    permission_classes = [
        IsAuthenticated,
        IsModerator,
    ]

    def perform_update(self, serializer):
        """
        Обновляет версию инструкции,
        сохраняя её первоначального автора.
        """

        instance = self.get_object()

        serializer.save(
            created_by=instance.created_by,
        )


class InstructionVersionDeleteAPIView(DestroyAPIView):
    """
    API-представление для удаления
    версии инструкции.

    Доступ предоставляется:

    - администраторам;
    - системным суперпользователям Django.
    """

    queryset = InstructionVersion.objects.select_related(
        "instruction",
        "created_by",
    )
    permission_classes = [
        IsAuthenticated,
        IsAdmin,
    ]


class InstructionStepListAPIView(
    InstructionRelatedAccessMixin,
    ListAPIView,
):
    """
    API-представление для получения
    списка шагов инструкций.

    Доступно всем авторизованным
    пользователям.
    """

    queryset = InstructionStep.objects.select_related(
        "instruction",
    )
    serializer_class = InstructionStepSerializer
    permission_classes = [
        IsAuthenticated,
    ]


class InstructionStepCreateAPIView(CreateAPIView):
    """
    API-представление для создания
    шага инструкции.

    Доступ предоставляется:

    - модераторам;
    - администраторам;
    - системным суперпользователям Django.
    """

    queryset = InstructionStep.objects.all()
    serializer_class = InstructionStepCreateSerializer
    permission_classes = [
        IsAuthenticated,
        IsModerator,
    ]


class InstructionStepRetrieveAPIView(
    InstructionRelatedAccessMixin,
    RetrieveAPIView,
):
    """
    API-представление для получения
    информации о шаге инструкции.

    Доступно всем авторизованным
    пользователям.
    """

    queryset = InstructionStep.objects.select_related(
        "instruction",
    )
    serializer_class = InstructionStepSerializer
    permission_classes = [
        IsAuthenticated,
    ]


class InstructionStepUpdateAPIView(UpdateAPIView):
    """
    API-представление для обновления
    шага инструкции.

    Доступ предоставляется:

    - модераторам;
    - администраторам;
    - системным суперпользователям Django.
    """

    queryset = InstructionStep.objects.select_related(
        "instruction",
    )
    serializer_class = InstructionStepUpdateSerializer
    permission_classes = [
        IsAuthenticated,
        IsModerator,
    ]


class InstructionStepDeleteAPIView(DestroyAPIView):
    """
    API-представление для удаления
    шага инструкции.

    Доступ предоставляется:

    - администраторам;
    - системным суперпользователям Django.
    """

    queryset = InstructionStep.objects.select_related(
        "instruction",
    )
    permission_classes = [
        IsAuthenticated,
        IsAdmin,
    ]


class InstructionImageListAPIView(
    InstructionRelatedAccessMixin,
    ListAPIView,
):
    """
    API-представление для получения
    списка изображений инструкций.

    Доступно всем авторизованным
    пользователям.
    """

    queryset = InstructionImage.objects.select_related(
        "instruction",
    )
    serializer_class = InstructionImageSerializer
    permission_classes = [
        IsAuthenticated,
    ]


class InstructionImageCreateAPIView(CreateAPIView):
    """
    API-представление для загрузки
    изображения инструкции.

    Доступ предоставляется:

    - модераторам;
    - администраторам;
    - системным суперпользователям Django.
    """

    queryset = InstructionImage.objects.all()
    serializer_class = InstructionImageCreateSerializer
    permission_classes = [
        IsAuthenticated,
        IsModerator,
    ]


class InstructionImageRetrieveAPIView(
    InstructionRelatedAccessMixin,
    RetrieveAPIView,
):
    """
    API-представление для получения
    информации об изображении инструкции.

    Доступно всем авторизованным
    пользователям.
    """

    queryset = InstructionImage.objects.select_related(
        "instruction",
    )
    serializer_class = InstructionImageSerializer
    permission_classes = [
        IsAuthenticated,
    ]


class InstructionImageUpdateAPIView(UpdateAPIView):
    """
    API-представление для обновления
    изображения инструкции.

    Доступ предоставляется:

    - модераторам;
    - администраторам;
    - системным суперпользователям Django.
    """

    queryset = InstructionImage.objects.select_related(
        "instruction",
    )
    serializer_class = InstructionImageUpdateSerializer
    permission_classes = [
        IsAuthenticated,
        IsModerator,
    ]


class InstructionImageDeleteAPIView(DestroyAPIView):
    """
    API-представление для удаления
    изображения инструкции.

    Доступ предоставляется:

    - администраторам;
    - системным суперпользователям Django.
    """

    queryset = InstructionImage.objects.select_related(
        "instruction",
    )
    permission_classes = [
        IsAuthenticated,
        IsAdmin,
    ]


class InstructionToolListAPIView(
    InstructionRelatedAccessMixin,
    ListAPIView,
):
    """
    API-представление для получения
    списка инструментов инструкций.

    Доступно всем авторизованным
    пользователям.
    """

    queryset = InstructionTool.objects.select_related(
        "instruction",
        "tool",
    )
    serializer_class = InstructionToolSerializer
    permission_classes = [
        IsAuthenticated,
    ]


class InstructionToolCreateAPIView(CreateAPIView):
    """
    API-представление для добавления
    инструмента к инструкции.

    Доступ предоставляется:

    - модераторам;
    - администраторам;
    - системным суперпользователям Django.
    """

    queryset = InstructionTool.objects.all()
    serializer_class = InstructionToolCreateSerializer
    permission_classes = [
        IsAuthenticated,
        IsModerator,
    ]


class InstructionToolRetrieveAPIView(
    InstructionRelatedAccessMixin,
    RetrieveAPIView,
):
    """
    API-представление для получения
    информации об инструменте инструкции.

    Доступно всем авторизованным
    пользователям.
    """

    queryset = InstructionTool.objects.select_related(
        "instruction",
        "tool",
    )
    serializer_class = InstructionToolSerializer
    permission_classes = [
        IsAuthenticated,
    ]


class InstructionToolUpdateAPIView(UpdateAPIView):
    """
    API-представление для обновления
    информации об инструменте инструкции.

    Доступ предоставляется:

    - модераторам;
    - администраторам;
    - системным суперпользователям Django.
    """

    queryset = InstructionTool.objects.select_related(
        "instruction",
        "tool",
    )
    serializer_class = InstructionToolUpdateSerializer
    permission_classes = [
        IsAuthenticated,
        IsModerator,
    ]


class InstructionToolDeleteAPIView(DestroyAPIView):
    """
    API-представление для удаления
    инструмента из инструкции.

    Доступ предоставляется:

    - администраторам;
    - системным суперпользователям Django.
    """

    queryset = InstructionTool.objects.select_related(
        "instruction",
        "tool",
    )
    permission_classes = [
        IsAuthenticated,
        IsAdmin,
    ]


# ============================================================================
# HTML-каталог и пошаговый режим ремонта
# ============================================================================


class InstructionTariffAccessMixin(LoginRequiredMixin):
    """Не допускает к инструкциям пользователя без подходящего тарифа."""

    login_url = "users:login"

    def dispatch(self, request, *args, **kwargs):
        if (
            request.user.is_authenticated
            and not has_instruction_access(request.user)
        ):
            messages.warning(
                request,
                "Доступ к инструкциям доступен по действующему тарифу.",
            )
            return redirect("subscriptions_web:plans")
        return super().dispatch(request, *args, **kwargs)


class InstructionListPageView(InstructionTariffAccessMixin, ListView):
    """Каталог опубликованных инструкций с фильтрацией."""

    login_url = "users:login"
    model = Instruction
    template_name = "instructions/instruction_list.html"
    context_object_name = "instructions"
    paginate_by = 9

    def get_queryset(self):
        queryset = (
            Instruction.objects.filter(is_published=True)
            .select_related("part", "part__category")
            .prefetch_related(
                Prefetch(
                    "images",
                    queryset=InstructionImage.objects.order_by("id"),
                )
            )
            .annotate(steps_count=Count("steps", distinct=True))
            .order_by("-published_at", "title")
        )
        if not is_privileged_user(self.request.user):
            queryset = queryset.filter(
                pk__in=purchased_instruction_ids(self.request.user)
            )

        query = self.request.GET.get("q", "").strip()
        difficulty = self.request.GET.get("difficulty", "").strip()
        category = self.request.GET.get("category", "").strip()

        if query:
            queryset = queryset.filter(
                Q(title__icontains=query)
                | Q(short_description__icontains=query)
                | Q(part__name__icontains=query)
                | Q(part__original_number__icontains=query)
            )
        if difficulty in Instruction.Difficulty.values:
            queryset = queryset.filter(difficulty=difficulty)
        if category:
            queryset = queryset.filter(part__category__slug=category)

        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update(
            {
                "search_query": self.request.GET.get("q", "").strip(),
                "selected_difficulty": self.request.GET.get(
                    "difficulty",
                    "",
                ).strip(),
                "selected_category": self.request.GET.get(
                    "category",
                    "",
                ).strip(),
                "difficulty_options": Instruction.Difficulty.choices,
                "categories": PartCategory.objects.filter(
                    parts__instructions__is_published=True
                ).distinct(),
            }
        )
        return context


class InstructionDetailPageView(
    InstructionTariffAccessMixin,
    DetailView,
):
    """Пошаговая опубликованная инструкция с тарифным доступом."""

    login_url = "users:login"
    model = Instruction
    template_name = "instructions/instruction_detail.html"
    context_object_name = "instruction"
    slug_field = "slug"
    slug_url_kwarg = "slug"

    def get_queryset(self):
        queryset = (
            Instruction.objects.filter(is_published=True)
            .select_related(
                "part",
                "part__category",
                "created_by",
                "updated_by",
            )
            .prefetch_related(
                Prefetch(
                    "steps",
                    queryset=InstructionStep.objects.order_by("step_number"),
                ),
                Prefetch(
                    "images",
                    queryset=InstructionImage.objects.order_by("id"),
                ),
                Prefetch(
                    "instruction_tools",
                    queryset=InstructionTool.objects.select_related(
                        "tool",
                        "tool__category",
                    ).order_by("tool__name"),
                ),
            )
        )
        if not is_privileged_user(self.request.user):
            queryset = queryset.filter(
                pk__in=purchased_instruction_ids(self.request.user)
            )
        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        instruction = context["instruction"]
        can_access = (
            has_instruction_access(self.request.user)
            and has_purchased_instruction(
                self.request.user,
                instruction,
            )
        )
        steps_count = len(instruction.steps.all())
        tools_count = len(instruction.instruction_tools.all())
        active_repair = None
        if getattr(self.request.user, "is_authenticated", False):
            active_repair = (
                RepairHistory.objects.filter(
                    user=self.request.user,
                    instruction=instruction,
                    completed=False,
                )
                .order_by("-progress_updated_at")
                .first()
            )

        context.update(
            {
                "can_access_content": can_access,
                "steps_count": steps_count,
                "tools_count": tools_count,
                "can_start_repair": bool(
                    can_access
                    and self.request.user.is_authenticated
                    and steps_count > 0
                    and tools_count > 0
                ),
                "active_repair": active_repair,
            }
        )
        return context


class InstructionRepairStartView(InstructionTariffAccessMixin, View):
    """Создаёт или возобновляет пошаговый ремонт по инструкции."""

    login_url = "users:login"

    def post(self, request, slug):
        instruction_ids = purchased_instruction_ids(request.user)
        instruction_filters = {
            "slug": slug,
            "is_published": True,
        }
        if instruction_ids is not None:
            instruction_filters["pk__in"] = instruction_ids
        instruction = get_object_or_404(
            Instruction.objects.prefetch_related(
                "steps",
                "instruction_tools",
            ),
            **instruction_filters,
        )
        if not instruction.steps.exists():
            messages.error(
                request,
                "Пошаговый ремонт недоступен: в инструкции нет шагов.",
            )
            return redirect(instruction.get_absolute_url())
        if not instruction.instruction_tools.exists():
            messages.error(
                request,
                "Пошаговый ремонт недоступен: список инструментов не готов.",
            )
            return redirect(instruction.get_absolute_url())

        repair = (
            RepairHistory.objects.filter(
                user=request.user,
                instruction=instruction,
                completed=False,
            )
            .order_by("-progress_updated_at")
            .first()
        )
        if repair is None:
            repair = RepairHistory.objects.create(
                user=request.user,
                instruction=instruction,
                current_step=1,
            )
            messages.success(request, "Пошаговый ремонт начат.")
        else:
            messages.info(request, "Пошаговый ремонт продолжен.")

        return redirect("instructions_web:repair", pk=repair.pk)


class InstructionRepairSessionView(InstructionTariffAccessMixin, View):
    """Показывает один текущий шаг и необходимые инструменты."""

    login_url = "users:login"

    def get(self, request, pk):
        instruction_ids = purchased_instruction_ids(request.user)
        repair_filters = {
            "pk": pk,
            "user": request.user,
            "completed": False,
            "instruction__is_published": True,
        }
        if instruction_ids is not None:
            repair_filters["instruction_id__in"] = instruction_ids
        repair = get_object_or_404(
            RepairHistory.objects.select_related(
                "instruction",
                "instruction__part",
            ).prefetch_related(
                "instruction__steps",
                "instruction__instruction_tools__tool",
            ),
            **repair_filters,
        )
        steps = list(repair.instruction.steps.all())
        total_steps = len(steps)
        if total_steps == 0:
            messages.error(request, "В инструкции пока нет шагов.")
            return redirect(repair.instruction.get_absolute_url())

        current_number = min(max(repair.current_step, 1), total_steps)
        if current_number != repair.current_step:
            repair.current_step = current_number
            repair.save(
                update_fields=("current_step", "progress_updated_at")
            )

        return render(
            request,
            "instructions/repair_session.html",
            {
                "repair": repair,
                "instruction": repair.instruction,
                "step": steps[current_number - 1],
                "current_step": current_number,
                "total_steps": total_steps,
                "progress_percent": round(
                    current_number / total_steps * 100
                ),
                "tools": repair.instruction.instruction_tools.all(),
            },
        )


class InstructionRepairNavigateView(InstructionTariffAccessMixin, View):
    """Переключает шаг или завершает ремонт."""

    login_url = "users:login"

    def post(self, request, pk):
        with transaction.atomic():
            instruction_ids = purchased_instruction_ids(request.user)
            repair_filters = {
                "pk": pk,
                "user": request.user,
                "completed": False,
                "instruction__is_published": True,
            }
            if instruction_ids is not None:
                repair_filters["instruction_id__in"] = instruction_ids
            repair = get_object_or_404(
                RepairHistory.objects.select_for_update().select_related(
                    "instruction"
                ),
                **repair_filters,
            )
            total_steps = repair.instruction.steps.count()
            if total_steps < 1:
                messages.error(request, "В инструкции пока нет шагов.")
                return redirect(repair.instruction.get_absolute_url())

            current_step = min(max(repair.current_step, 1), total_steps)
            action = request.POST.get("action")

            if action == "previous":
                repair.current_step = max(1, current_step - 1)
            elif action == "next":
                repair.current_step = min(total_steps, current_step + 1)
            elif action == "complete":
                if current_step < total_steps:
                    messages.warning(
                        request,
                        "Перед завершением откройте последний шаг.",
                    )
                    return redirect(
                        "instructions_web:repair",
                        pk=repair.pk,
                    )
                repair.completed = True
            else:
                messages.error(request, "Неизвестное действие навигации.")
                return redirect(
                    "instructions_web:repair",
                    pk=repair.pk,
                )

            repair.save(
                update_fields=(
                    "current_step",
                    "completed",
                    "progress_updated_at",
                )
            )

        if repair.completed:
            messages.success(request, "Ремонт отмечен как завершённый.")
            return redirect(repair.instruction.get_absolute_url())

        return redirect("instructions_web:repair", pk=repair.pk)
