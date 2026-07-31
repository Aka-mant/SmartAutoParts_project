from rest_framework.generics import (
    CreateAPIView,
    DestroyAPIView,
    ListAPIView,
    RetrieveAPIView,
    UpdateAPIView,
)
from rest_framework.permissions import IsAuthenticated

from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import redirect
from django.views.generic import DetailView

from users.permissions import (
    IsAdmin,
    IsModerator,
)
from apps.AI.models import AIContentPurchase
from apps.subscriptions.access import (
    has_part_card_access,
    is_privileged_user,
)

from .models import (
    PartTool,
    Tool,
    ToolCategory,
    ToolImage,
)
from .serializers import (
    PartToolCreateSerializer,
    PartToolSerializer,
    PartToolUpdateSerializer,
    ToolCategoryCreateSerializer,
    ToolCategorySerializer,
    ToolCategoryUpdateSerializer,
    ToolCreateSerializer,
    ToolImageCreateSerializer,
    ToolImageSerializer,
    ToolImageUpdateSerializer,
    ToolSerializer,
    ToolUpdateSerializer,
)


class PurchasedPartToolQuerySetMixin:
    """Открывает связи детали с инструментами после первичной покупки."""

    def get_queryset(self):
        queryset = super().get_queryset()
        if is_privileged_user(self.request.user):
            return queryset
        if not self.request.user.is_authenticated:
            return queryset.none()
        purchased_part_ids = AIContentPurchase.objects.filter(
            user=self.request.user,
            content_type=AIContentPurchase.ContentType.TOOLS,
            part_id__isnull=False,
        ).values_list("part_id", flat=True)
        return queryset.filter(part_id__in=purchased_part_ids)


class ToolCategoryListAPIView(ListAPIView):
    """
    API-представление для получения
    списка категорий инструментов.

    Доступно всем авторизованным
    пользователям.
    """

    queryset = ToolCategory.objects.all()
    serializer_class = ToolCategorySerializer
    permission_classes = [
        IsAuthenticated,
    ]


class ToolCategoryCreateAPIView(CreateAPIView):
    """
    API-представление для создания
    категории инструментов.

    Доступ предоставляется:

    - модераторам;
    - администраторам;
    - системным суперпользователям Django.
    """

    queryset = ToolCategory.objects.all()
    serializer_class = ToolCategoryCreateSerializer
    permission_classes = [
        IsAuthenticated,
        IsModerator,
    ]


class ToolCategoryRetrieveAPIView(RetrieveAPIView):
    """
    API-представление для получения
    информации о категории инструментов.

    Доступно всем авторизованным
    пользователям.
    """

    queryset = ToolCategory.objects.all()
    serializer_class = ToolCategorySerializer
    permission_classes = [
        IsAuthenticated,
    ]


class ToolCategoryUpdateAPIView(UpdateAPIView):
    """
    API-представление для обновления
    категории инструментов.

    Доступ предоставляется:

    - модераторам;
    - администраторам;
    - системным суперпользователям Django.
    """

    queryset = ToolCategory.objects.all()
    serializer_class = ToolCategoryUpdateSerializer
    permission_classes = [
        IsAuthenticated,
        IsModerator,
    ]


class ToolCategoryDeleteAPIView(DestroyAPIView):
    """
    API-представление для удаления
    категории инструментов.

    Доступ предоставляется:

    - администраторам;
    - системным суперпользователям Django.
    """

    queryset = ToolCategory.objects.all()
    permission_classes = [
        IsAuthenticated,
        IsAdmin,
    ]


class ToolListAPIView(ListAPIView):
    """
    API-представление для получения
    списка инструментов.

    Доступно всем авторизованным
    пользователям.
    """

    queryset = Tool.objects.select_related(
        "category",
    ).prefetch_related("images")
    serializer_class = ToolSerializer
    permission_classes = [
        IsAuthenticated,
    ]


class ToolCreateAPIView(CreateAPIView):
    """
    API-представление для создания
    инструмента.

    Доступ предоставляется:

    - модераторам;
    - администраторам;
    - системным суперпользователям Django.
    """

    queryset = Tool.objects.all()
    serializer_class = ToolCreateSerializer
    permission_classes = [
        IsAuthenticated,
        IsModerator,
    ]


class ToolRetrieveAPIView(RetrieveAPIView):
    """
    API-представление для получения
    информации об инструменте.

    Доступно всем авторизованным
    пользователям.
    """

    queryset = Tool.objects.select_related("category").prefetch_related(
        "images",
    )
    serializer_class = ToolSerializer
    permission_classes = [
        IsAuthenticated,
    ]


class ToolUpdateAPIView(UpdateAPIView):
    """
    API-представление для обновления
    инструмента.

    Доступ предоставляется:

    - модераторам;
    - администраторам;
    - системным суперпользователям Django.
    """

    queryset = Tool.objects.select_related(
        "category",
    )
    serializer_class = ToolUpdateSerializer
    permission_classes = [
        IsAuthenticated,
        IsModerator,
    ]


class ToolDeleteAPIView(DestroyAPIView):
    """
    API-представление для удаления
    инструмента.

    Доступ предоставляется:

    - администраторам;
    - системным суперпользователям Django.
    """

    queryset = Tool.objects.select_related(
        "category",
    )
    permission_classes = [
        IsAuthenticated,
        IsAdmin,
    ]


class ToolImageListAPIView(ListAPIView):
    """Возвращает изображения инструментов."""

    queryset = ToolImage.objects.select_related("tool")
    serializer_class = ToolImageSerializer
    permission_classes = [IsAuthenticated]


class ToolImageCreateAPIView(CreateAPIView):
    """Создаёт изображение инструмента."""

    queryset = ToolImage.objects.all()
    serializer_class = ToolImageCreateSerializer
    permission_classes = [IsAuthenticated, IsModerator]


class ToolImageRetrieveAPIView(RetrieveAPIView):
    """Возвращает выбранное изображение инструмента."""

    queryset = ToolImage.objects.select_related("tool")
    serializer_class = ToolImageSerializer
    permission_classes = [IsAuthenticated]


class ToolImageUpdateAPIView(UpdateAPIView):
    """Обновляет выбранное изображение инструмента."""

    queryset = ToolImage.objects.select_related("tool")
    serializer_class = ToolImageUpdateSerializer
    permission_classes = [IsAuthenticated, IsModerator]


class ToolImageDeleteAPIView(DestroyAPIView):
    """Удаляет выбранное изображение инструмента."""

    queryset = ToolImage.objects.select_related("tool")
    permission_classes = [IsAuthenticated, IsAdmin]


class PartToolListAPIView(PurchasedPartToolQuerySetMixin, ListAPIView):
    """
    API-представление для получения
    списка связей между запчастями
    и инструментами.

    Доступно всем авторизованным
    пользователям.
    """

    queryset = PartTool.objects.select_related(
        "part",
        "tool",
    )
    serializer_class = PartToolSerializer
    permission_classes = [
        IsAuthenticated,
    ]


class PartToolCreateAPIView(CreateAPIView):
    """
    API-представление для создания
    связи между запчастью
    и инструментом.

    Доступ предоставляется:

    - модераторам;
    - администраторам;
    - системным суперпользователям Django.
    """

    queryset = PartTool.objects.all()
    serializer_class = PartToolCreateSerializer
    permission_classes = [
        IsAuthenticated,
        IsModerator,
    ]


class PartToolRetrieveAPIView(
    PurchasedPartToolQuerySetMixin,
    RetrieveAPIView,
):
    """
    API-представление для получения
    информации о связи между
    запчастью и инструментом.

    Доступно всем авторизованным
    пользователям.
    """

    queryset = PartTool.objects.select_related(
        "part",
        "tool",
    )
    serializer_class = PartToolSerializer
    permission_classes = [
        IsAuthenticated,
    ]


class PartToolUpdateAPIView(UpdateAPIView):
    """
    API-представление для обновления
    связи между запчастью
    и инструментом.

    Доступ предоставляется:

    - модераторам;
    - администраторам;
    - системным суперпользователям Django.
    """

    queryset = PartTool.objects.select_related(
        "part",
        "tool",
    )
    serializer_class = PartToolUpdateSerializer
    permission_classes = [
        IsAuthenticated,
        IsModerator,
    ]


class PartToolDeleteAPIView(DestroyAPIView):
    """
    API-представление для удаления
    связи между запчастью
    и инструментом.

    Доступ предоставляется:

    - администраторам;
    - системным суперпользователям Django.
    """

    queryset = PartTool.objects.select_related(
        "part",
        "tool",
    )
    permission_classes = [
        IsAuthenticated,
        IsAdmin,
    ]


class ToolDetailPageView(LoginRequiredMixin, DetailView):
    """Показывает полное описание и галерею инструмента."""

    login_url = "users:login"
    model = Tool
    template_name = "tools/tool_detail.html"
    context_object_name = "tool"

    def dispatch(self, request, *args, **kwargs):
        if (
            request.user.is_authenticated
            and not has_part_card_access(request.user)
        ):
            messages.warning(
                request,
                "Для просмотра карточки инструмента выберите тариф.",
            )
            return redirect("subscriptions_web:plans")
        return super().dispatch(request, *args, **kwargs)

    def get_queryset(self):
        return (
            Tool.objects.select_related("category")
            .prefetch_related(
                "images",
                "tool_parts__part__category",
            )
        )

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        gallery = []
        if self.object.image_exists:
            gallery.append(
                {
                    "url": self.object.image.url,
                    "alt": self.object.name,
                }
            )
        gallery.extend(
            {
                "url": item.image.url,
                "alt": item.alt_text or self.object.name,
            }
            for item in self.object.images.all()
            if item.image_exists
        )
        context["tool_gallery_images"] = gallery
        return context
