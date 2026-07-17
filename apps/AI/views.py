from django.db.models import QuerySet

from rest_framework.exceptions import PermissionDenied
from rest_framework.generics import (
    CreateAPIView,
    DestroyAPIView,
    ListAPIView,
    RetrieveAPIView,
    UpdateAPIView,
)
from rest_framework.permissions import IsAuthenticated

from users.permissions import IsOwner

from .models import (
    AIGeneratedInstruction,
    AIImageAnalysis,
    AIRequest,
)
from .serializers import (
    AIGeneratedInstructionCreateSerializer,
    AIGeneratedInstructionSerializer,
    AIGeneratedInstructionUpdateSerializer,
    AIImageAnalysisCreateSerializer,
    AIImageAnalysisSerializer,
    AIImageAnalysisUpdateSerializer,
    AIRequestCreateSerializer,
    AIRequestSerializer,
    AIRequestUpdateSerializer,
)


class UserOwnedQuerySetMixin:
    """
    Ограничивает queryset объектами,
    принадлежащими текущему пользователю.

    Администраторы и системные
    суперпользователи Django получают
    доступ ко всем объектам.

    Поле или путь до владельца задаётся
    через атрибут owner_lookup.
    """

    owner_lookup = "user"

    def get_queryset(self) -> QuerySet:
        """
        Возвращает queryset с учётом
        прав текущего пользователя.
        """

        queryset = super().get_queryset()
        user = self.request.user

        if not user.is_authenticated:
            return queryset.none()

        if user.can_administrate:
            return queryset

        return queryset.filter(
            **{
                self.owner_lookup: user,
            }
        )


class AIRequestOwnedQuerySetMixin(
    UserOwnedQuerySetMixin,
):
    """
    Ограничивает AI-запросы текущим
    пользователем.
    """

    owner_lookup = "user"


class AIGeneratedInstructionOwnedQuerySetMixin(
    UserOwnedQuerySetMixin,
):
    """
    Ограничивает AI-инструкции через
    владельца связанного AI-запроса.
    """

    owner_lookup = "ai_request__user"


class AIImageAnalysisOwnedQuerySetMixin(
    UserOwnedQuerySetMixin,
):
    """
    Ограничивает анализы изображений
    текущим пользователем.
    """

    owner_lookup = "user"


class AIRequestListAPIView(
    AIRequestOwnedQuerySetMixin,
    ListAPIView,
):
    """
    API-представление для получения
    списка AI-запросов.

    Обычный пользователь получает только
    собственные AI-запросы.

    Администраторы и системные
    суперпользователи получают все запросы.
    """

    queryset = AIRequest.objects.select_related(
        "user",
        "part",
        "instruction",
    )
    serializer_class = AIRequestSerializer
    permission_classes = [
        IsAuthenticated,
    ]


class AIRequestCreateAPIView(CreateAPIView):
    """
    API-представление для создания
    AI-запроса.

    Текущий пользователь автоматически
    назначается владельцем запроса.
    """

    queryset = AIRequest.objects.all()
    serializer_class = AIRequestCreateSerializer
    permission_classes = [
        IsAuthenticated,
    ]

    def perform_create(self, serializer):
        """
        Создаёт AI-запрос для текущего
        авторизованного пользователя.

        Значение поля user, переданное
        клиентом, не используется.
        """

        serializer.save(
            user=self.request.user,
        )


class AIRequestRetrieveAPIView(
    AIRequestOwnedQuerySetMixin,
    RetrieveAPIView,
):
    """
    API-представление для получения
    отдельного AI-запроса.

    Обычный пользователь может просматривать
    только собственные запросы.

    Администраторы и системные
    суперпользователи могут просматривать
    любые запросы.
    """

    queryset = AIRequest.objects.select_related(
        "user",
        "part",
        "instruction",
    )
    serializer_class = AIRequestSerializer
    permission_classes = [
        IsAuthenticated,
        IsOwner,
    ]


class AIRequestUpdateAPIView(
    AIRequestOwnedQuerySetMixin,
    UpdateAPIView,
):
    """
    API-представление для обновления
    AI-запроса.

    Обычный пользователь может изменять
    только собственные запросы.

    Администраторы и системные
    суперпользователи могут изменять
    любые запросы.
    """

    queryset = AIRequest.objects.select_related(
        "user",
        "part",
        "instruction",
    )
    serializer_class = AIRequestUpdateSerializer
    permission_classes = [
        IsAuthenticated,
        IsOwner,
    ]

    def perform_update(self, serializer):
        """
        Обновляет AI-запрос, сохраняя
        его текущего владельца.
        """

        instance = self.get_object()

        serializer.save(
            user=instance.user,
        )


class AIRequestDeleteAPIView(
    AIRequestOwnedQuerySetMixin,
    DestroyAPIView,
):
    """
    API-представление для удаления
    AI-запроса.

    Обычный пользователь может удалять
    только собственные запросы.

    Администраторы и системные
    суперпользователи могут удалять
    любые запросы.
    """

    queryset = AIRequest.objects.select_related(
        "user",
    )
    permission_classes = [
        IsAuthenticated,
        IsOwner,
    ]


class AIGeneratedInstructionListAPIView(
    AIGeneratedInstructionOwnedQuerySetMixin,
    ListAPIView,
):
    """
    API-представление для получения списка
    AI-сгенерированных инструкций.

    Обычный пользователь получает только
    инструкции, созданные на основе его
    собственных AI-запросов.

    Администраторы и системные
    суперпользователи получают все записи.
    """

    queryset = AIGeneratedInstruction.objects.select_related(
        "ai_request",
        "ai_request__user",
    )
    serializer_class = AIGeneratedInstructionSerializer
    permission_classes = [
        IsAuthenticated,
    ]


class AIGeneratedInstructionCreateAPIView(
    CreateAPIView,
):
    """
    API-представление для создания
    AI-сгенерированной инструкции.

    Обычный пользователь может создать
    инструкцию только для собственного
    AI-запроса.

    Администраторы и системные
    суперпользователи могут использовать
    любой AI-запрос.
    """

    queryset = AIGeneratedInstruction.objects.all()
    serializer_class = (
        AIGeneratedInstructionCreateSerializer
    )
    permission_classes = [
        IsAuthenticated,
    ]

    def perform_create(self, serializer):
        """
        Проверяет принадлежность выбранного
        AI-запроса текущему пользователю.
        """

        user = self.request.user
        ai_request = serializer.validated_data.get(
            "ai_request"
        )

        if ai_request is None:
            raise PermissionDenied(
                "Необходимо указать AI-запрос."
            )

        if (
            not user.can_administrate
            and ai_request.user_id != user.pk
        ):
            raise PermissionDenied(
                "Вы можете создавать инструкции "
                "только для собственных AI-запросов."
            )

        serializer.save()


class AIGeneratedInstructionRetrieveAPIView(
    AIGeneratedInstructionOwnedQuerySetMixin,
    RetrieveAPIView,
):
    """
    API-представление для получения
    AI-сгенерированной инструкции.

    Обычный пользователь может просматривать
    только инструкции, связанные с его
    AI-запросами.

    Администраторы и системные
    суперпользователи могут просматривать
    любые инструкции.
    """

    queryset = AIGeneratedInstruction.objects.select_related(
        "ai_request",
        "ai_request__user",
    )
    serializer_class = AIGeneratedInstructionSerializer
    permission_classes = [
        IsAuthenticated,
        IsOwner,
    ]


class AIGeneratedInstructionUpdateAPIView(
    AIGeneratedInstructionOwnedQuerySetMixin,
    UpdateAPIView,
):
    """
    API-представление для обновления
    AI-сгенерированной инструкции.

    Обычный пользователь может изменять
    только инструкции, связанные с его
    AI-запросами.

    Администраторы и системные
    суперпользователи могут изменять
    любые инструкции.
    """

    queryset = AIGeneratedInstruction.objects.select_related(
        "ai_request",
        "ai_request__user",
    )
    serializer_class = (
        AIGeneratedInstructionUpdateSerializer
    )
    permission_classes = [
        IsAuthenticated,
        IsOwner,
    ]

    def perform_update(self, serializer):
        """
        Проверяет новый AI-запрос при его
        изменении и запрещает привязывать
        инструкцию к чужому запросу.
        """

        user = self.request.user
        instance = self.get_object()

        ai_request = serializer.validated_data.get(
            "ai_request",
            instance.ai_request,
        )

        if (
            not user.can_administrate
            and ai_request.user_id != user.pk
        ):
            raise PermissionDenied(
                "Нельзя привязать инструкцию "
                "к чужому AI-запросу."
            )

        serializer.save()


class AIGeneratedInstructionDeleteAPIView(
    AIGeneratedInstructionOwnedQuerySetMixin,
    DestroyAPIView,
):
    """
    API-представление для удаления
    AI-сгенерированной инструкции.

    Обычный пользователь может удалять
    только инструкции, связанные с его
    AI-запросами.

    Администраторы и системные
    суперпользователи могут удалять
    любые инструкции.
    """

    queryset = AIGeneratedInstruction.objects.select_related(
        "ai_request",
        "ai_request__user",
    )
    permission_classes = [
        IsAuthenticated,
        IsOwner,
    ]


class AIImageAnalysisListAPIView(
    AIImageAnalysisOwnedQuerySetMixin,
    ListAPIView,
):
    """
    API-представление для получения
    списка анализов изображений.

    Обычный пользователь получает только
    собственные анализы.

    Администраторы и системные
    суперпользователи получают все анализы.
    """

    queryset = AIImageAnalysis.objects.select_related(
        "user",
    )
    serializer_class = AIImageAnalysisSerializer
    permission_classes = [
        IsAuthenticated,
    ]


class AIImageAnalysisCreateAPIView(
    CreateAPIView,
):
    """
    API-представление для создания
    запроса на анализ изображения.

    Текущий пользователь автоматически
    назначается владельцем анализа.
    """

    queryset = AIImageAnalysis.objects.all()
    serializer_class = AIImageAnalysisCreateSerializer
    permission_classes = [
        IsAuthenticated,
    ]

    def perform_create(self, serializer):
        """
        Создаёт запрос на анализ изображения
        для текущего пользователя.

        Значение поля user, переданное
        клиентом, не используется.
        """

        serializer.save(
            user=self.request.user,
        )


class AIImageAnalysisRetrieveAPIView(
    AIImageAnalysisOwnedQuerySetMixin,
    RetrieveAPIView,
):
    """
    API-представление для получения
    информации об анализе изображения.

    Обычный пользователь может просматривать
    только собственные анализы.

    Администраторы и системные
    суперпользователи могут просматривать
    любые анализы.
    """

    queryset = AIImageAnalysis.objects.select_related(
        "user",
    )
    serializer_class = AIImageAnalysisSerializer
    permission_classes = [
        IsAuthenticated,
        IsOwner,
    ]


class AIImageAnalysisUpdateAPIView(
    AIImageAnalysisOwnedQuerySetMixin,
    UpdateAPIView,
):
    """
    API-представление для обновления
    результата анализа изображения.

    Обычный пользователь может изменять
    только собственные анализы.

    Администраторы и системные
    суперпользователи могут изменять
    любые анализы.
    """

    queryset = AIImageAnalysis.objects.select_related(
        "user",
    )
    serializer_class = AIImageAnalysisUpdateSerializer
    permission_classes = [
        IsAuthenticated,
        IsOwner,
    ]

    def perform_update(self, serializer):
        """
        Обновляет анализ изображения,
        сохраняя текущего владельца.
        """

        instance = self.get_object()

        serializer.save(
            user=instance.user,
        )


class AIImageAnalysisDeleteAPIView(
    AIImageAnalysisOwnedQuerySetMixin,
    DestroyAPIView,
):
    """
    API-представление для удаления
    анализа изображения.

    Обычный пользователь может удалять
    только собственные анализы.

    Администраторы и системные
    суперпользователи могут удалять
    любые анализы.
    """

    queryset = AIImageAnalysis.objects.select_related(
        "user",
    )
    permission_classes = [
        IsAuthenticated,
        IsOwner,
    ]
