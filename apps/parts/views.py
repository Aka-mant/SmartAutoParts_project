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
    Compatibility,
    OEMNumber,
    Part,
    PartCategory,
    PartImage,
)
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
