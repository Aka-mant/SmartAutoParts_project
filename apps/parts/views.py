from rest_framework.generics import (
    CreateAPIView,
    DestroyAPIView,
    ListAPIView,
    RetrieveAPIView,
    UpdateAPIView,
)
from rest_framework.permissions import IsAuthenticated

from .models import Part, PartCategory
from .serializers import (
    PartSerializer,
    PartCreateSerializer,
    PartUpdateSerializer, PartCategoryCreateSerializer, PartCategorySerializer, PartCategoryUpdateSerializer,
)

from users.permissions import (
    IsModerator,
    IsSuperuser,
)


class PartListAPIView(ListAPIView):
    """
    API-представление для получения списка
    автомобильных запчастей.

    Доступно авторизованным пользователям.
    """

    serializer_class = PartSerializer
    permission_classes = [
        IsAuthenticated,
    ]

    def get_queryset(self):
        """
        Возвращает только активные запчасти.
        """
        return Part.objects.filter(
            is_active=True
        )


class PartCreateAPIView(CreateAPIView):
    """
    API-представление для создания
    автомобильной запчасти.

    Доступно модераторам и суперпользователям.
    """

    queryset = Part.objects.all()
    serializer_class = PartCreateSerializer
    permission_classes = [
        IsAuthenticated,
        IsModerator | IsSuperuser,
    ]


class PartRetrieveAPIView(RetrieveAPIView):
    """
    API-представление для получения
    информации о запчасти.

    Доступно авторизованным пользователям.
    """

    serializer_class = PartSerializer
    permission_classes = [
        IsAuthenticated,
    ]

    def get_queryset(self):
        """
        Возвращает активные запчасти.
        """
        return Part.objects.filter(
            is_active=True
        )


class PartUpdateAPIView(UpdateAPIView):
    """
    API-представление для обновления
    информации о запчасти.

    Доступно модераторам и суперпользователям.
    """

    queryset = Part.objects.all()
    serializer_class = PartUpdateSerializer
    permission_classes = [
        IsAuthenticated,
        IsModerator | IsSuperuser,
    ]


class PartDeleteAPIView(DestroyAPIView):
    """
    API-представление для удаления
    запчасти.

    Доступно только суперпользователям Django.
    """

    queryset = Part.objects.all()
    permission_classes = [
        IsAuthenticated,
        IsSuperuser,
    ]


class PartCategoryListAPIView(ListAPIView):
    """
    API-представление для получения списка
    категорий запчастей.

    Доступно авторизованным пользователям.
    """

    queryset = PartCategory.objects.all()
    serializer_class = PartCategorySerializer
    permission_classes = [IsAuthenticated]


class PartCategoryCreateAPIView(CreateAPIView):
    """
    API-представление для создания
    категории запчастей.

    Доступно модераторам и
    суперпользователям Django.
    """

    queryset = PartCategory.objects.all()
    serializer_class = PartCategoryCreateSerializer
    permission_classes = [
        IsAuthenticated,
        IsModerator | IsSuperuser,
    ]


class PartCategoryRetrieveAPIView(RetrieveAPIView):
    """
    API-представление для получения
    информации о категории запчастей.

    Доступно авторизованным пользователям.
    """

    queryset = PartCategory.objects.all()
    serializer_class = PartCategorySerializer
    permission_classes = [IsAuthenticated]


class PartCategoryUpdateAPIView(UpdateAPIView):
    """
    API-представление для обновления
    категории запчастей.

    Доступно модераторам и
    суперпользователям Django.
    """

    queryset = PartCategory.objects.all()
    serializer_class = PartCategoryUpdateSerializer
    permission_classes = [
        IsAuthenticated,
        IsModerator | IsSuperuser,
    ]


class PartCategoryDeleteAPIView(DestroyAPIView):
    """
    API-представление для удаления
    категории запчастей.

    Доступно только системным
    суперпользователям Django.
    """

    queryset = PartCategory.objects.all()
    permission_classes = [
        IsAuthenticated,
        IsSuperuser,
    ]