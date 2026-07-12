from rest_framework.generics import (
    CreateAPIView,
    DestroyAPIView,
    ListAPIView,
    RetrieveAPIView,
    UpdateAPIView,
)
from rest_framework.permissions import IsAuthenticated

from users.permissions import IsOwner, IsSuperuser

from .models import AIRequest, AIGeneratedInstruction, AIImageAnalysis
from .serializers import (
    AIRequestSerializer,
    AIRequestCreateSerializer,
    AIRequestUpdateSerializer,
    AIGeneratedInstructionSerializer,
    AIGeneratedInstructionCreateSerializer,
    AIGeneratedInstructionUpdateSerializer, AIImageAnalysisSerializer, AIImageAnalysisCreateSerializer,
    AIImageAnalysisUpdateSerializer,
)


class AIRequestListAPIView(ListAPIView):
    """
    API-представление для получения
    списка AI-запросов.

    Пользователь может просматривать
    только собственные запросы.

    Суперпользователь Django имеет
    доступ ко всем запросам.
    """

    serializer_class = AIRequestSerializer
    permission_classes = [
        IsAuthenticated,
    ]

    def get_queryset(self):
        """
        Возвращает AI-запросы текущего
        пользователя.

        Суперпользователь получает
        полный список запросов.
        """
        if self.request.user.is_superuser:
            return AIRequest.objects.all()

        return AIRequest.objects.filter(
            user=self.request.user,
        )


class AIRequestCreateAPIView(CreateAPIView):
    """
    API-представление для создания
    AI-запроса.

    Пользователь автоматически
    назначается владельцем запроса.
    """

    queryset = AIRequest.objects.all()
    serializer_class = AIRequestCreateSerializer
    permission_classes = [
        IsAuthenticated,
    ]

    def perform_create(self, serializer):
        """
        Создает AI-запрос для текущего
        авторизованного пользователя.
        """
        serializer.save(
            user=self.request.user,
        )


class AIRequestRetrieveAPIView(RetrieveAPIView):
    """
    API-представление для получения
    информации об AI-запросе.

    Пользователь может просматривать
    только собственные запросы.

    Суперпользователь Django имеет
    доступ ко всем запросам.
    """

    serializer_class = AIRequestSerializer
    permission_classes = [
        IsAuthenticated,
        IsOwner | IsSuperuser,
    ]

    def get_queryset(self):
        """
        Возвращает AI-запросы текущего
        пользователя.

        Суперпользователь получает
        доступ ко всем запросам.
        """
        if self.request.user.is_superuser:
            return AIRequest.objects.all()

        return AIRequest.objects.filter(
            user=self.request.user,
        )


class AIRequestUpdateAPIView(UpdateAPIView):
    """
    API-представление для обновления
    AI-запроса.

    Пользователь может изменять
    только собственные запросы.

    Суперпользователь Django имеет
    доступ ко всем запросам.
    """

    serializer_class = AIRequestUpdateSerializer
    permission_classes = [
        IsAuthenticated,
        IsOwner | IsSuperuser,
    ]

    def get_queryset(self):
        """
        Возвращает AI-запросы текущего
        пользователя.

        Суперпользователь получает
        доступ ко всем запросам.
        """
        if self.request.user.is_superuser:
            return AIRequest.objects.all()

        return AIRequest.objects.filter(
            user=self.request.user,
        )


class AIRequestDeleteAPIView(DestroyAPIView):
    """
    API-представление для удаления
    AI-запроса.

    Пользователь может удалять
    только собственные запросы.

    Суперпользователь Django имеет
    доступ ко всем запросам.
    """

    permission_classes = [
        IsAuthenticated,
        IsOwner | IsSuperuser,
    ]

    def get_queryset(self):
        """
        Возвращает AI-запросы текущего
        пользователя.

        Суперпользователь получает
        доступ ко всем запросам.
        """
        if self.request.user.is_superuser:
            return AIRequest.objects.all()

        return AIRequest.objects.filter(
            user=self.request.user,
        )


class AIGeneratedInstructionListAPIView(ListAPIView):
    """
    API-представление для получения
    списка AI-сгенерированных инструкций.

    Пользователь может просматривать
    только инструкции, созданные на
    основе собственных AI-запросов.

    Суперпользователь Django имеет
    доступ ко всем записям.
    """

    serializer_class = (
        AIGeneratedInstructionSerializer
    )
    permission_classes = [
        IsAuthenticated,
    ]

    def get_queryset(self):
        """
        Возвращает инструкции,
        созданные по AI-запросам
        текущего пользователя.

        Суперпользователь получает
        полный список записей.
        """
        if self.request.user.is_superuser:
            return AIGeneratedInstruction.objects.all()

        return AIGeneratedInstruction.objects.filter(
            ai_request__user=self.request.user,
        )


class AIGeneratedInstructionCreateAPIView(CreateAPIView):
    """
    API-представление для создания
    AI-сгенерированной инструкции.

    Доступно авторизованным
    пользователям.
    """

    queryset = AIGeneratedInstruction.objects.all()
    serializer_class = (
        AIGeneratedInstructionCreateSerializer
    )
    permission_classes = [
        IsAuthenticated,
    ]


class AIGeneratedInstructionRetrieveAPIView(RetrieveAPIView):
    """
    API-представление для получения
    информации о AI-сгенерированной
    инструкции.

    Пользователь может просматривать
    только собственные записи.

    Суперпользователь Django имеет
    доступ ко всем записям.
    """

    serializer_class = (
        AIGeneratedInstructionSerializer
    )
    permission_classes = [
        IsAuthenticated,
        IsOwner | IsSuperuser,
    ]

    def get_queryset(self):
        """
        Возвращает инструкции,
        созданные по AI-запросам
        текущего пользователя.

        Суперпользователь получает
        доступ ко всем записям.
        """
        if self.request.user.is_superuser:
            return AIGeneratedInstruction.objects.all()

        return AIGeneratedInstruction.objects.filter(
            ai_request__user=self.request.user,
        )


class AIGeneratedInstructionUpdateAPIView(UpdateAPIView):
    """
    API-представление для обновления
    AI-сгенерированной инструкции.

    Пользователь может изменять
    только собственные записи.

    Суперпользователь Django имеет
    доступ ко всем записям.
    """

    serializer_class = (
        AIGeneratedInstructionUpdateSerializer
    )
    permission_classes = [
        IsAuthenticated,
        IsOwner | IsSuperuser,
    ]

    def get_queryset(self):
        """
        Возвращает инструкции,
        созданные по AI-запросам
        текущего пользователя.

        Суперпользователь получает
        доступ ко всем записям.
        """
        if self.request.user.is_superuser:
            return AIGeneratedInstruction.objects.all()

        return AIGeneratedInstruction.objects.filter(
            ai_request__user=self.request.user,
        )


class AIGeneratedInstructionDeleteAPIView(DestroyAPIView):
    """
    API-представление для удаления
    AI-сгенерированной инструкции.

    Пользователь может удалять
    только собственные записи.

    Суперпользователь Django имеет
    доступ ко всем записям.
    """

    permission_classes = [
        IsAuthenticated,
        IsOwner | IsSuperuser,
    ]

    def get_queryset(self):
        """
        Возвращает инструкции,
        созданные по AI-запросам
        текущего пользователя.

        Суперпользователь получает
        доступ ко всем записям.
        """
        if self.request.user.is_superuser:
            return AIGeneratedInstruction.objects.all()

        return AIGeneratedInstruction.objects.filter(
            ai_request__user=self.request.user,
        )


class AIImageAnalysisListAPIView(ListAPIView):
    """
    API-представление для получения
    списка анализов изображений.

    Пользователь может просматривать
    только собственные анализы.

    Суперпользователь Django имеет
    доступ ко всем анализам.
    """

    serializer_class = AIImageAnalysisSerializer
    permission_classes = [
        IsAuthenticated,
    ]

    def get_queryset(self):
        """
        Возвращает анализы изображений
        текущего пользователя.

        Суперпользователь получает
        полный список анализов.
        """
        if self.request.user.is_superuser:
            return AIImageAnalysis.objects.all()

        return AIImageAnalysis.objects.filter(
            user=self.request.user,
        )


class AIImageAnalysisCreateAPIView(CreateAPIView):
    """
    API-представление для создания
    запроса на анализ изображения.

    Пользователь автоматически
    назначается владельцем анализа.
    """

    queryset = AIImageAnalysis.objects.all()
    serializer_class = AIImageAnalysisCreateSerializer
    permission_classes = [
        IsAuthenticated,
    ]

    def perform_create(self, serializer):
        """
        Создает запрос на анализ
        изображения для текущего
        авторизованного пользователя.
        """
        serializer.save(
            user=self.request.user,
        )


class AIImageAnalysisRetrieveAPIView(RetrieveAPIView):
    """
    API-представление для получения
    информации об анализе изображения.

    Пользователь может просматривать
    только собственные анализы.

    Суперпользователь Django имеет
    доступ ко всем анализам.
    """

    serializer_class = AIImageAnalysisSerializer
    permission_classes = [
        IsAuthenticated,
        IsOwner | IsSuperuser,
    ]

    def get_queryset(self):
        """
        Возвращает анализы изображений
        текущего пользователя.

        Суперпользователь получает
        доступ ко всем анализам.
        """
        if self.request.user.is_superuser:
            return AIImageAnalysis.objects.all()

        return AIImageAnalysis.objects.filter(
            user=self.request.user,
        )


class AIImageAnalysisUpdateAPIView(UpdateAPIView):
    """
    API-представление для обновления
    результата анализа изображения.

    Пользователь может изменять
    только собственные анализы.

    Суперпользователь Django имеет
    доступ ко всем анализам.
    """

    serializer_class = AIImageAnalysisUpdateSerializer
    permission_classes = [
        IsAuthenticated,
        IsOwner | IsSuperuser,
    ]

    def get_queryset(self):
        """
        Возвращает анализы изображений
        текущего пользователя.

        Суперпользователь получает
        доступ ко всем анализам.
        """
        if self.request.user.is_superuser:
            return AIImageAnalysis.objects.all()

        return AIImageAnalysis.objects.filter(
            user=self.request.user,
        )


class AIImageAnalysisDeleteAPIView(DestroyAPIView):
    """
    API-представление для удаления
    анализа изображения.

    Пользователь может удалять
    только собственные анализы.

    Суперпользователь Django имеет
    доступ ко всем анализам.
    """

    permission_classes = [
        IsAuthenticated,
        IsOwner | IsSuperuser,
    ]

    def get_queryset(self):
        """
        Возвращает анализы изображений
        текущего пользователя.

        Суперпользователь получает
        доступ ко всем анализам.
        """
        if self.request.user.is_superuser:
            return AIImageAnalysis.objects.all()

        return AIImageAnalysis.objects.filter(
            user=self.request.user,
        )