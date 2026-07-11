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


class InstructionListAPIView(ListAPIView):
    """
    API-представление для получения
    списка инструкций.

    Доступно авторизованным
    пользователям.
    """

    queryset = Instruction.objects.all()
    serializer_class = InstructionSerializer
    permission_classes = [
        IsAuthenticated,
    ]


class InstructionCreateAPIView(CreateAPIView):
    """
    API-представление для создания
    инструкции.

    Доступно модераторам и
    суперпользователям Django.
    """

    queryset = Instruction.objects.all()
    serializer_class = InstructionCreateSerializer
    permission_classes = [
        IsAuthenticated,
        IsModerator | IsSuperuser,
    ]

    def perform_create(self, serializer):
        """
        Автоматически назначает текущего
        пользователя автором инструкции.
        """
        serializer.save(
            created_by=self.request.user,
        )


class InstructionRetrieveAPIView(RetrieveAPIView):
    """
    API-представление для получения
    информации об одной инструкции.

    Доступно авторизованным
    пользователям.
    """

    queryset = Instruction.objects.all()
    serializer_class = InstructionSerializer
    permission_classes = [
        IsAuthenticated,
    ]


class InstructionUpdateAPIView(UpdateAPIView):
    """
    API-представление для обновления
    инструкции.

    Доступно модераторам и
    суперпользователям Django.
    """

    queryset = Instruction.objects.all()
    serializer_class = InstructionUpdateSerializer
    permission_classes = [
        IsAuthenticated,
        IsModerator | IsSuperuser,
    ]


class InstructionDeleteAPIView(DestroyAPIView):
    """
    API-представление для удаления
    инструкции.

    Доступно только системным
    суперпользователям Django.
    """

    queryset = Instruction.objects.all()
    permission_classes = [
        IsAuthenticated,
        IsSuperuser,
    ]


class InstructionVersionListAPIView(ListAPIView):
    """
    API-представление для получения
    списка версий инструкций.

    Доступно авторизованным
    пользователям.
    """

    queryset = InstructionVersion.objects.all()
    serializer_class = InstructionVersionSerializer
    permission_classes = [
        IsAuthenticated,
    ]


class InstructionVersionCreateAPIView(CreateAPIView):
    """
    API-представление для создания
    новой версии инструкции.

    Доступно модераторам и
    суперпользователям Django.
    """

    queryset = InstructionVersion.objects.all()
    serializer_class = InstructionVersionCreateSerializer
    permission_classes = [
        IsAuthenticated,
        IsModerator | IsSuperuser,
    ]


class InstructionVersionRetrieveAPIView(RetrieveAPIView):
    """
    API-представление для получения
    информации о версии инструкции.

    Доступно авторизованным
    пользователям.
    """

    queryset = InstructionVersion.objects.all()
    serializer_class = InstructionVersionSerializer
    permission_classes = [
        IsAuthenticated,
    ]


class InstructionVersionUpdateAPIView(UpdateAPIView):
    """
    API-представление для обновления
    версии инструкции.

    Доступно модераторам и
    суперпользователям Django.
    """

    queryset = InstructionVersion.objects.all()
    serializer_class = InstructionVersionUpdateSerializer
    permission_classes = [
        IsAuthenticated,
        IsModerator | IsSuperuser,
    ]


class InstructionVersionDeleteAPIView(DestroyAPIView):
    """
    API-представление для удаления
    версии инструкции.

    Доступно только системным
    суперпользователям Django.
    """

    queryset = InstructionVersion.objects.all()
    permission_classes = [
        IsAuthenticated,
        IsSuperuser,
    ]


class InstructionStepListAPIView(ListAPIView):
    """
    API-представление для получения
    списка шагов инструкций.

    Доступно авторизованным
    пользователям.
    """

    queryset = InstructionStep.objects.all()
    serializer_class = InstructionStepSerializer
    permission_classes = [
        IsAuthenticated,
    ]


class InstructionStepCreateAPIView(CreateAPIView):
    """
    API-представление для создания
    шага инструкции.

    Доступно модераторам и
    суперпользователям Django.
    """

    queryset = InstructionStep.objects.all()
    serializer_class = InstructionStepCreateSerializer
    permission_classes = [
        IsAuthenticated,
        IsModerator | IsSuperuser,
    ]


class InstructionStepRetrieveAPIView(RetrieveAPIView):
    """
    API-представление для получения
    информации о шаге инструкции.

    Доступно авторизованным
    пользователям.
    """

    queryset = InstructionStep.objects.all()
    serializer_class = InstructionStepSerializer
    permission_classes = [
        IsAuthenticated,
    ]


class InstructionStepUpdateAPIView(UpdateAPIView):
    """
    API-представление для обновления
    шага инструкции.

    Доступно модераторам и
    суперпользователям Django.
    """

    queryset = InstructionStep.objects.all()
    serializer_class = InstructionStepUpdateSerializer
    permission_classes = [
        IsAuthenticated,
        IsModerator | IsSuperuser,
    ]


class InstructionStepDeleteAPIView(DestroyAPIView):
    """
    API-представление для удаления
    шага инструкции.

    Доступно только системным
    суперпользователям Django.
    """

    queryset = InstructionStep.objects.all()
    permission_classes = [
        IsAuthenticated,
        IsSuperuser,
    ]


class InstructionImageListAPIView(ListAPIView):
    """
    API-представление для получения
    списка изображений инструкций.

    Доступно авторизованным
    пользователям.
    """

    queryset = InstructionImage.objects.all()
    serializer_class = InstructionImageSerializer
    permission_classes = [
        IsAuthenticated,
    ]


class InstructionImageCreateAPIView(CreateAPIView):
    """
    API-представление для загрузки
    изображения инструкции.

    Доступно модераторам и
    суперпользователям Django.
    """

    queryset = InstructionImage.objects.all()
    serializer_class = InstructionImageCreateSerializer
    permission_classes = [
        IsAuthenticated,
        IsModerator | IsSuperuser,
    ]


class InstructionImageRetrieveAPIView(RetrieveAPIView):
    """
    API-представление для получения
    информации об изображении
    инструкции.

    Доступно авторизованным
    пользователям.
    """

    queryset = InstructionImage.objects.all()
    serializer_class = InstructionImageSerializer
    permission_classes = [
        IsAuthenticated,
    ]


class InstructionImageUpdateAPIView(UpdateAPIView):
    """
    API-представление для обновления
    изображения инструкции.

    Доступно модераторам и
    суперпользователям Django.
    """

    queryset = InstructionImage.objects.all()
    serializer_class = InstructionImageUpdateSerializer
    permission_classes = [
        IsAuthenticated,
        IsModerator | IsSuperuser,
    ]


class InstructionImageDeleteAPIView(DestroyAPIView):
    """
    API-представление для удаления
    изображения инструкции.

    Доступно только системным
    суперпользователям Django.
    """

    queryset = InstructionImage.objects.all()
    permission_classes = [
        IsAuthenticated,
        IsSuperuser,
    ]


class InstructionToolListAPIView(ListAPIView):
    """
    API-представление для получения
    списка инструментов инструкций.

    Доступно авторизованным
    пользователям.
    """

    queryset = InstructionTool.objects.all()
    serializer_class = InstructionToolSerializer
    permission_classes = [
        IsAuthenticated,
    ]


class InstructionToolCreateAPIView(CreateAPIView):
    """
    API-представление для добавления
    инструмента к инструкции.

    Доступно модераторам и
    суперпользователям Django.
    """

    queryset = InstructionTool.objects.all()
    serializer_class = InstructionToolCreateSerializer
    permission_classes = [
        IsAuthenticated,
        IsModerator | IsSuperuser,
    ]


class InstructionToolRetrieveAPIView(RetrieveAPIView):
    """
    API-представление для получения
    информации об инструменте
    инструкции.

    Доступно авторизованным
    пользователям.
    """

    queryset = InstructionTool.objects.all()
    serializer_class = InstructionToolSerializer
    permission_classes = [
        IsAuthenticated,
    ]


class InstructionToolUpdateAPIView(UpdateAPIView):
    """
    API-представление для обновления
    информации об инструменте
    инструкции.

    Доступно модераторам и
    суперпользователям Django.
    """

    queryset = InstructionTool.objects.all()
    serializer_class = InstructionToolUpdateSerializer
    permission_classes = [
        IsAuthenticated,
        IsModerator | IsSuperuser,
    ]


class InstructionToolDeleteAPIView(DestroyAPIView):
    """
    API-представление для удаления
    инструмента из инструкции.

    Доступно только системным
    суперпользователям Django.
    """

    queryset = InstructionTool.objects.all()
    permission_classes = [
        IsAuthenticated,
        IsSuperuser,
    ]

