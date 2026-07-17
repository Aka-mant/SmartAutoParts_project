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


class InstructionRetrieveAPIView(RetrieveAPIView):
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


class InstructionVersionListAPIView(ListAPIView):
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


class InstructionVersionRetrieveAPIView(RetrieveAPIView):
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


class InstructionStepListAPIView(ListAPIView):
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


class InstructionStepRetrieveAPIView(RetrieveAPIView):
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


class InstructionImageListAPIView(ListAPIView):
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


class InstructionImageRetrieveAPIView(RetrieveAPIView):
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


class InstructionToolListAPIView(ListAPIView):
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


class InstructionToolRetrieveAPIView(RetrieveAPIView):
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
