from rest_framework.generics import (
    CreateAPIView,
    DestroyAPIView,
    ListAPIView,
    RetrieveAPIView,
    UpdateAPIView,
)
from rest_framework.permissions import IsAuthenticated

from .models import Part
from .serializers import (
    PartSerializer,
    PartCreateSerializer,
    PartUpdateSerializer,
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

