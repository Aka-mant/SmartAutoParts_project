from rest_framework.generics import (
    CreateAPIView,
    DestroyAPIView,
    ListAPIView,
    RetrieveAPIView,
    UpdateAPIView,
)
from rest_framework.permissions import IsAuthenticated

from users.permissions import IsModerator, IsSuperuser

from .models import ToolCategory, Tool, PartTool
from .serializers import (
    ToolCategoryCreateSerializer,
    ToolCategorySerializer,
    ToolCategoryUpdateSerializer, ToolSerializer, ToolCreateSerializer, ToolUpdateSerializer, PartToolSerializer,
    PartToolCreateSerializer, PartToolUpdateSerializer,
)


class ToolCategoryListAPIView(ListAPIView):
    """
    API-представление для получения
    списка категорий инструментов.

    Доступно авторизованным
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

    Доступно модераторам и
    суперпользователям Django.
    """

    queryset = ToolCategory.objects.all()
    serializer_class = ToolCategoryCreateSerializer
    permission_classes = [
        IsAuthenticated,
        IsModerator | IsSuperuser,
    ]


class ToolCategoryRetrieveAPIView(RetrieveAPIView):
    """
    API-представление для получения
    информации о категории инструментов.

    Доступно авторизованным
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

    Доступно модераторам и
    суперпользователям Django.
    """

    queryset = ToolCategory.objects.all()
    serializer_class = ToolCategoryUpdateSerializer
    permission_classes = [
        IsAuthenticated,
        IsModerator | IsSuperuser,
    ]


class ToolCategoryDeleteAPIView(DestroyAPIView):
    """
    API-представление для удаления
    категории инструментов.

    Доступно только системным
    суперпользователям Django.
    """

    queryset = ToolCategory.objects.all()
    permission_classes = [
        IsAuthenticated,
        IsSuperuser,
    ]

class ToolListAPIView(ListAPIView):
    """
    API-представление для получения
    списка инструментов.

    Доступно авторизованным
    пользователям.
    """

    queryset = Tool.objects.all()
    serializer_class = ToolSerializer
    permission_classes = [
        IsAuthenticated,
    ]


class ToolCreateAPIView(CreateAPIView):
    """
    API-представление для создания
    инструмента.

    Доступно модераторам и
    суперпользователям Django.
    """

    queryset = Tool.objects.all()
    serializer_class = ToolCreateSerializer
    permission_classes = [
        IsAuthenticated,
        IsModerator | IsSuperuser,
    ]


class ToolRetrieveAPIView(RetrieveAPIView):
    """
    API-представление для получения
    информации об инструменте.

    Доступно авторизованным
    пользователям.
    """

    queryset = Tool.objects.all()
    serializer_class = ToolSerializer
    permission_classes = [
        IsAuthenticated,
    ]


class ToolUpdateAPIView(UpdateAPIView):
    """
    API-представление для обновления
    инструмента.

    Доступно модераторам и
    суперпользователям Django.
    """

    queryset = Tool.objects.all()
    serializer_class = ToolUpdateSerializer
    permission_classes = [
        IsAuthenticated,
        IsModerator | IsSuperuser,
    ]


class ToolDeleteAPIView(DestroyAPIView):
    """
    API-представление для удаления
    инструмента.

    Доступно только системным
    суперпользователям Django.
    """

    queryset = Tool.objects.all()
    permission_classes = [
        IsAuthenticated,
        IsSuperuser,
    ]

class PartToolListAPIView(ListAPIView):
    """
    API-представление для получения
    списка связей между запчастями
    и инструментами.

    Доступно авторизованным
    пользователям.
    """

    queryset = PartTool.objects.all()
    serializer_class = PartToolSerializer
    permission_classes = [
        IsAuthenticated,
    ]


class PartToolCreateAPIView(CreateAPIView):
    """
    API-представление для создания
    связи между запчастью
    и инструментом.

    Доступно модераторам и
    суперпользователям Django.
    """

    queryset = PartTool.objects.all()
    serializer_class = PartToolCreateSerializer
    permission_classes = [
        IsAuthenticated,
        IsModerator | IsSuperuser,
    ]


class PartToolRetrieveAPIView(RetrieveAPIView):
    """
    API-представление для получения
    информации о связи между
    запчастью и инструментом.

    Доступно авторизованным
    пользователям.
    """

    queryset = PartTool.objects.all()
    serializer_class = PartToolSerializer
    permission_classes = [
        IsAuthenticated,
    ]


class PartToolUpdateAPIView(UpdateAPIView):
    """
    API-представление для обновления
    связи между запчастью
    и инструментом.

    Доступно модераторам и
    суперпользователям Django.
    """

    queryset = PartTool.objects.all()
    serializer_class = PartToolUpdateSerializer
    permission_classes = [
        IsAuthenticated,
        IsModerator | IsSuperuser,
    ]


class PartToolDeleteAPIView(DestroyAPIView):
    """
    API-представление для удаления
    связи между запчастью
    и инструментом.

    Доступно только системным
    суперпользователям Django.
    """

    queryset = PartTool.objects.all()
    permission_classes = [
        IsAuthenticated,
        IsSuperuser,
    ]