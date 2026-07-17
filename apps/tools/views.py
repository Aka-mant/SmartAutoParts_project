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

from .models import (
    PartTool,
    Tool,
    ToolCategory,
)
from .serializers import (
    PartToolCreateSerializer,
    PartToolSerializer,
    PartToolUpdateSerializer,
    ToolCategoryCreateSerializer,
    ToolCategorySerializer,
    ToolCategoryUpdateSerializer,
    ToolCreateSerializer,
    ToolSerializer,
    ToolUpdateSerializer,
)


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
    )
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

    queryset = Tool.objects.select_related(
        "category",
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


class PartToolListAPIView(ListAPIView):
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


class PartToolRetrieveAPIView(RetrieveAPIView):
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
