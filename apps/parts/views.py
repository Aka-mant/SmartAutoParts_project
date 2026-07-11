from rest_framework.generics import (
    CreateAPIView,
    DestroyAPIView,
    ListAPIView,
    RetrieveAPIView,
    UpdateAPIView,
)
from rest_framework.permissions import IsAuthenticated

from users.permissions import IsModerator, IsSuperuser

from .models import (
    PartCategory,
    Part,
    OEMNumber,
    Compatibility,
    PartImage
)
from .serializers import (
    PartCategorySerializer,
    PartCategoryCreateSerializer,
    PartCategoryUpdateSerializer,
    PartSerializer,
    PartCreateSerializer,
    PartUpdateSerializer,
    OEMNumberSerializer,
    OEMNumberCreateSerializer,
    OEMNumberUpdateSerializer,
    CompatibilitySerializer,
    CompatibilityCreateSerializer,
    CompatibilityUpdateSerializer,
    PartImageSerializer,
    PartImageCreateSerializer,
    PartImageUpdateSerializer,
)


class PartCategoryListAPIView(ListAPIView):
    """
    API-представление для получения
    списка категорий запчастей.

    Доступно авторизованным
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

    Доступно авторизованным
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

class PartListAPIView(ListAPIView):
    """
    API-представление для получения
    списка автомобильных запчастей.

    Доступно авторизованным
    пользователям.
    """

    queryset = Part.objects.all()
    serializer_class = PartSerializer
    permission_classes = [
        IsAuthenticated,
    ]


class PartCreateAPIView(CreateAPIView):
    """
    API-представление для создания
    автомобильной запчасти.

    Доступно модераторам и
    суперпользователям Django.
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
    информации об автомобильной
    запчасти.

    Доступно авторизованным
    пользователям.
    """

    queryset = Part.objects.all()
    serializer_class = PartSerializer
    permission_classes = [
        IsAuthenticated,
    ]


class PartUpdateAPIView(UpdateAPIView):
    """
    API-представление для обновления
    автомобильной запчасти.

    Доступно модераторам и
    суперпользователям Django.
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
    автомобильной запчасти.

    Доступно только системным
    суперпользователям Django.
    """

    queryset = Part.objects.all()
    permission_classes = [
        IsAuthenticated,
        IsSuperuser,
    ]

class OEMNumberListAPIView(ListAPIView):
    """
    API-представление для получения
    списка OEM-номеров.

    Доступно авторизованным
    пользователям.
    """

    queryset = OEMNumber.objects.all()
    serializer_class = OEMNumberSerializer
    permission_classes = [
        IsAuthenticated,
    ]


class OEMNumberCreateAPIView(CreateAPIView):
    """
    API-представление для создания
    OEM-номера.

    Доступно модераторам и
    суперпользователям Django.
    """

    queryset = OEMNumber.objects.all()
    serializer_class = OEMNumberCreateSerializer
    permission_classes = [
        IsAuthenticated,
        IsModerator | IsSuperuser,
    ]


class OEMNumberRetrieveAPIView(RetrieveAPIView):
    """
    API-представление для получения
    информации об OEM-номере.

    Доступно авторизованным
    пользователям.
    """

    queryset = OEMNumber.objects.all()
    serializer_class = OEMNumberSerializer
    permission_classes = [
        IsAuthenticated,
    ]


class OEMNumberUpdateAPIView(UpdateAPIView):
    """
    API-представление для обновления
    OEM-номера.

    Доступно модераторам и
    суперпользователям Django.
    """

    queryset = OEMNumber.objects.all()
    serializer_class = OEMNumberUpdateSerializer
    permission_classes = [
        IsAuthenticated,
        IsModerator | IsSuperuser,
    ]


class OEMNumberDeleteAPIView(DestroyAPIView):
    """
    API-представление для удаления
    OEM-номера.

    Доступно только системным
    суперпользователям Django.
    """

    queryset = OEMNumber.objects.all()
    permission_classes = [
        IsAuthenticated,
        IsSuperuser,
    ]


class CompatibilityListAPIView(ListAPIView):
    """
    API-представление для получения
    списка совместимостей запчастей.

    Доступно авторизованным
    пользователям.
    """

    queryset = Compatibility.objects.all()
    serializer_class = CompatibilitySerializer
    permission_classes = [
        IsAuthenticated,
    ]


class CompatibilityCreateAPIView(CreateAPIView):
    """
    API-представление для создания
    записи совместимости.

    Доступно модераторам и
    суперпользователям Django.
    """

    queryset = Compatibility.objects.all()
    serializer_class = CompatibilityCreateSerializer
    permission_classes = [
        IsAuthenticated,
        IsModerator | IsSuperuser,
    ]


class CompatibilityRetrieveAPIView(RetrieveAPIView):
    """
    API-представление для получения
    информации о совместимости
    запчасти.

    Доступно авторизованным
    пользователям.
    """

    queryset = Compatibility.objects.all()
    serializer_class = CompatibilitySerializer
    permission_classes = [
        IsAuthenticated,
    ]


class CompatibilityUpdateAPIView(UpdateAPIView):
    """
    API-представление для обновления
    записи совместимости.

    Доступно модераторам и
    суперпользователям Django.
    """

    queryset = Compatibility.objects.all()
    serializer_class = CompatibilityUpdateSerializer
    permission_classes = [
        IsAuthenticated,
        IsModerator | IsSuperuser,
    ]


class CompatibilityDeleteAPIView(DestroyAPIView):
    """
    API-представление для удаления
    записи совместимости.

    Доступно только системным
    суперпользователям Django.
    """

    queryset = Compatibility.objects.all()
    permission_classes = [
        IsAuthenticated,
        IsSuperuser,
    ]


class PartImageListAPIView(ListAPIView):
    """
    API-представление для получения
    списка изображений запчастей.

    Доступно авторизованным
    пользователям.
    """

    queryset = PartImage.objects.all()
    serializer_class = PartImageSerializer
    permission_classes = [
        IsAuthenticated,
    ]


class PartImageCreateAPIView(CreateAPIView):
    """
    API-представление для создания
    изображения запчасти.

    Доступно модераторам и
    суперпользователям Django.
    """

    queryset = PartImage.objects.all()
    serializer_class = PartImageCreateSerializer
    permission_classes = [
        IsAuthenticated,
        IsModerator | IsSuperuser,
    ]


class PartImageRetrieveAPIView(RetrieveAPIView):
    """
    API-представление для получения
    информации об изображении
    запчасти.

    Доступно авторизованным
    пользователям.
    """

    queryset = PartImage.objects.all()
    serializer_class = PartImageSerializer
    permission_classes = [
        IsAuthenticated,
    ]


class PartImageUpdateAPIView(UpdateAPIView):
    """
    API-представление для обновления
    изображения запчасти.

    Доступно модераторам и
    суперпользователям Django.
    """

    queryset = PartImage.objects.all()
    serializer_class = PartImageUpdateSerializer
    permission_classes = [
        IsAuthenticated,
        IsModerator | IsSuperuser,
    ]


class PartImageDeleteAPIView(DestroyAPIView):
    """
    API-представление для удаления
    изображения запчасти.

    Доступно только системным
    суперпользователям Django.
    """

    queryset = PartImage.objects.all()
    permission_classes = [
        IsAuthenticated,
        IsSuperuser,
    ]


