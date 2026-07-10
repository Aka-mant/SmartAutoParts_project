from rest_framework.generics import (
    CreateAPIView,
    DestroyAPIView,
    ListAPIView,
    RetrieveAPIView,
    UpdateAPIView,
)
from rest_framework.permissions import IsAuthenticated

from .models import Instruction
from .serializers import (
    InstructionSerializer,
    InstructionCreateSerializer,
    InstructionUpdateSerializer,
)
from users.permissions import IsModerator, IsSuperuser


class InstructionListAPIView(ListAPIView):
    """
    API-представление для получения списка инструкций.

    Доступно авторизованным пользователям.
    """

    queryset = Instruction.objects.all()
    serializer_class = InstructionSerializer
    permission_classes = [IsAuthenticated]


class InstructionCreateAPIView(CreateAPIView):
    """
    API-представление для создания инструкции.

    Доступно модераторам и суперпользователям.
    """

    queryset = Instruction.objects.all()
    serializer_class = InstructionCreateSerializer
    permission_classes = [
        IsAuthenticated,
        IsModerator | IsSuperuser,
    ]

    def perform_create(self, serializer):
        """
        Автоматически назначает автора
        создаваемой инструкции.
        """
        serializer.save(
            created_by=self.request.user
        )


class InstructionRetrieveAPIView(RetrieveAPIView):
    """
    API-представление для получения
    одной инструкции.

    Доступно авторизованным пользователям.
    """

    queryset = Instruction.objects.all()
    serializer_class = InstructionSerializer
    permission_classes = [IsAuthenticated]


class InstructionUpdateAPIView(UpdateAPIView):
    """
    API-представление для обновления инструкции.

    Доступно модераторам и суперпользователям.
    """

    queryset = Instruction.objects.all()
    serializer_class = InstructionUpdateSerializer
    permission_classes = [
        IsAuthenticated,
        IsModerator | IsSuperuser,
    ]


class InstructionDeleteAPIView(DestroyAPIView):
    """
    API-представление для удаления инструкции.

    Доступно только суперпользователям Django.
    """

    queryset = Instruction.objects.all()
    permission_classes = [
        IsAuthenticated,
        IsSuperuser,
    ]

