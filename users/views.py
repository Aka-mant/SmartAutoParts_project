from datetime import timedelta
import re

from django.conf import settings
from django.contrib.auth import views as auth_views
from django.contrib.auth.forms import AuthenticationForm
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import DetailView, ListView, TemplateView
from django.urls import reverse_lazy
from django.shortcuts import get_object_or_404, redirect, render
from django.contrib.auth.mixins import UserPassesTestMixin
from django.core.exceptions import FieldError
from django.db import transaction
from django.db.models import CharField, Count, Q
from django.db.models.functions import Cast
from django.utils import timezone
from django.utils.http import url_has_allowed_host_and_scheme
from django.views import View
from django.contrib import messages


from rest_framework.generics import (
    CreateAPIView,
    DestroyAPIView,
    ListAPIView,
    RetrieveAPIView,
    UpdateAPIView,
)
from rest_framework.permissions import (
    AllowAny,
    IsAuthenticated,
)
from rest_framework_simplejwt.views import TokenObtainPairView

from apps.AI.models import AIRequest
from apps.parts.models import Part
from apps.subscriptions.models import UserSubscription
from apps.subscriptions.access import (
    has_unlimited_ai_access,
    has_part_card_access,
    is_moderator_only,
)

from .mixins.mixins import UserOwnedQuerySetMixin
from .models import (
    Profile,
    RepairHistory,
    SearchHistory,
    User,
    UserAgreementAcceptance,
)
from .permissions import (
    IsAdmin,
    IsModerator,
    IsOwner,
)
from .serializers import (
    ProfileSerializer,
    ProfileUpdateSerializer,
    RepairHistoryCreateSerializer,
    RepairHistorySerializer,
    RepairHistoryUpdateSerializer,
    SearchHistorySerializer,
    UserCreateSerializer,
    UserSerializer,
    UserTokenObtainSerializer,
    UserUpdateSerializer,
)
from .forms import (
    ProfileUpdateForm,
    UserProfileUpdateForm,
)


class UserAgreementView(View):
    """Показывает соглашение и фиксирует принятие текущей редакции."""

    template_name = "legal/user_agreement.html"

    def get(self, request):
        version = settings.USER_AGREEMENT_VERSION
        agreement_not_required = bool(
            request.user.is_authenticated
            and (
                request.user.is_superuser
                or request.user.can_administrate
            )
        )
        accepted = bool(
            request.user.is_authenticated
            and request.user.has_accepted_user_agreement(version)
        )
        return render(
            request,
            self.template_name,
            {
                "agreement_version": version,
                "agreement_already_accepted": accepted,
                "agreement_not_required": agreement_not_required,
                "next_url": request.GET.get("next", ""),
            },
        )

    def post(self, request):
        if not request.user.is_authenticated:
            login_url = reverse_lazy("users:login")
            messages.warning(
                request,
                "Войдите в аккаунт, чтобы принять соглашение.",
            )
            return redirect(f"{login_url}?next={request.get_full_path()}")

        if request.user.is_superuser or request.user.can_administrate:
            return redirect("users:dashboard")

        if request.POST.get("agreement_accepted") != "on":
            messages.error(
                request,
                "Для продолжения необходимо принять "
                "пользовательское соглашение.",
            )
            return self.get(request)

        version = settings.USER_AGREEMENT_VERSION
        UserAgreementAcceptance.objects.get_or_create(
            user=request.user,
            agreement_version=version,
            defaults={
                "ip_address": request.META.get("REMOTE_ADDR") or None,
                "user_agent": request.META.get(
                    "HTTP_USER_AGENT",
                    "",
                )[:500],
            },
        )
        request.session[
            "accepted_user_agreement_version"
        ] = version

        next_url = request.POST.get("next", "")
        if not url_has_allowed_host_and_scheme(
            next_url,
            allowed_hosts={request.get_host()},
            require_https=request.is_secure(),
        ):
            next_url = reverse_lazy("users:dashboard")

        messages.success(
            request,
            "Пользовательское соглашение принято.",
        )
        return redirect(next_url)


class UserDashboardView(LoginRequiredMixin, TemplateView):
    """
    HTML-представление личного кабинета пользователя.

    Отображает профиль, активную подписку, доступные
    возможности тарифа, последние поиски, историю ремонтов,
    незавершённый ремонт, AI-запросы и рекомендации деталей.
    """

    template_name = "users/dashboard.html"
    login_url = reverse_lazy("users:login")
    redirect_field_name = "next"

    free_search_limit = 10
    free_ai_limit = 0

    recent_searches_limit = 4
    recent_repairs_limit = 4
    recommended_parts_limit = 3

    def get_subscription(self):
        """
        Возвращает последнюю действующую подписку пользователя.
        """

        return (
            UserSubscription.objects
            .filter(
                user=self.request.user,
                is_active=True,
                start_date__lte=timezone.now(),
                end_date__gte=timezone.now(),
            )
            .select_related("plan")
            .order_by("-end_date")
            .first()
        )

    def get_recent_searches(self):
        """
        Возвращает последние поисковые запросы пользователя.
        """

        return (
            SearchHistory.objects
            .filter(user=self.request.user)
            .order_by("-searched_at")[:self.recent_searches_limit]
        )

    def get_recent_repairs(self):
        """
        Возвращает последние записи истории ремонта.

        Обычный пользователь видит только собственные записи.
        Администратор, модератор и суперпользователь
        видят записи всех пользователей.
        """

        queryset = (
            RepairHistory.objects
            .select_related(
                "user",
                "instruction",
                "instruction__part",
            )
            .order_by("-created_at")
        )

        can_view_all = (
            self.request.user.is_superuser
            or self.request.user.is_staff

        )

        if not can_view_all:
            queryset = queryset.filter(
                user=self.request.user,
            )

        return queryset[:self.recent_repairs_limit]

    def get_active_repair(self):
        """
        Возвращает последний незавершённый ремонт.
        """

        repair = (
            RepairHistory.objects
            .filter(
                user=self.request.user,
                completed=False,
            )
            .select_related(
                "instruction",
                "instruction__part",
            )
            .order_by("-created_at")
            .first()
        )

        if repair is None:
            return None

        total_steps = self.get_instruction_steps_count(
            repair.instruction,
        )
        current_step = self.get_current_repair_step(
            repair=repair,
            total_steps=total_steps,
        )

        return {
            "object": repair,
            "instruction": repair.instruction,
            "part": repair.instruction.part,
            "current_step": current_step,
            "total_steps": total_steps,
            "progress_percent": self.calculate_percent(
                used=current_step,
                limit=total_steps,
            ),
            "created_at": repair.created_at,
        }

    @staticmethod
    def get_instruction_steps_count(instruction):
        """
        Возвращает количество шагов инструкции.
        """

        related_names = (
            "steps",
            "instruction_steps",
            "instructionstep_set",
        )

        for related_name in related_names:
            related_manager = getattr(
                instruction,
                related_name,
                None,
            )

            if related_manager is None:
                continue

            try:
                return related_manager.count()
            except (AttributeError, TypeError):
                continue

        return 0

    @staticmethod
    def get_current_repair_step(repair, total_steps):
        """
        Возвращает текущий шаг ремонта.
        """

        current_step = getattr(repair, "current_step", None)

        if current_step is not None:
            if total_steps <= 0:
                return 0
            return min(max(current_step, 1), total_steps)

        return 1 if total_steps > 0 else 0

    def get_ai_requests_queryset(self):
        """
        Возвращает AI-запросы текущего пользователя.
        """

        return (
            AIRequest.objects
            .filter(user=self.request.user)
            .exclude(request_type__endswith="_blocked")
            .order_by("-created_at")
        )

    def get_ai_requests_used(self, subscription):
        """
        Возвращает количество AI-запросов за текущий период.
        """

        queryset = self.get_ai_requests_queryset()

        if subscription is not None:
            return queryset.filter(
                created_at__gte=subscription.start_date,
                created_at__lte=subscription.end_date,
            ).count()

        return queryset.filter(
            created_at__date=timezone.localdate(),
        ).count()

    def get_image_analysis_used(self, subscription):
        """
        Возвращает количество запросов анализа изображений.
        """

        queryset = self.get_ai_requests_queryset().filter(
            request_type__in=(
                "image_analysis",
                "image_analysis_rejected",
            ),
        )

        if subscription is not None:
            queryset = queryset.filter(
                created_at__gte=subscription.start_date,
                created_at__lte=subscription.end_date,
            )
        else:
            queryset = queryset.filter(
                created_at__date=timezone.localdate(),
            )

        return queryset.count()

    def get_feature_requests_used(self, subscription, feature):
        """Возвращает расход лимита отдельной AI-функции."""

        queryset = self.get_ai_requests_queryset()
        if feature == "chat":
            queryset = queryset.filter(
                Q(request_type="chat")
                | Q(request_type__startswith="tool_recommendation")
            )
        elif feature == "instruction":
            queryset = queryset.filter(
                request_type__startswith="repair_instruction",
            )
        elif feature == "image_analysis":
            queryset = queryset.filter(
                request_type__in=(
                    "image_analysis",
                    "image_analysis_rejected",
                )
            )
        else:
            return 0

        if subscription is not None:
            queryset = queryset.filter(
                created_at__gte=subscription.start_date,
                created_at__lt=subscription.end_date,
            )
        else:
            queryset = queryset.filter(
                created_at__date=timezone.localdate(),
            )
        return queryset.count()

    def get_searches_used(self):
        """
        Возвращает количество поисков за текущий день.
        """

        return (
            SearchHistory.objects
            .filter(
                user=self.request.user,
                searched_at__date=timezone.localdate(),
            )
            .count()
        )

    @staticmethod
    def calculate_percent(used, limit):
        """
        Рассчитывает процент использования лимита.
        """

        if limit <= 0:
            return 0

        percent = round(used / limit * 100)
        return min(max(percent, 0), 100)

    @staticmethod
    def calculate_remaining(used, limit):
        """
        Возвращает количество оставшихся операций.
        """

        if limit <= 0:
            return 0

        return max(limit - used, 0)

    @staticmethod
    def is_subscription_expiring(subscription):
        """
        Проверяет, истекает ли подписка в ближайшие семь дней.
        """

        if subscription is None:
            return False

        now = timezone.now()
        return now <= subscription.end_date <= now + timedelta(days=7)

    def get_recommended_parts(self):
        """
        Возвращает детали, совместимые с автомобилем профиля.

        Если совместимость определить нельзя, возвращает
        последние активные детали.
        """

        queryset = (
            Part.objects
            .filter(is_active=True)
            .select_related("category")
        )

        profile = getattr(self.request.user, "profile", None)

        if profile is None:
            return queryset.order_by(
                "-created_at",
            )[:self.recommended_parts_limit]

        car_brand = profile.car_brand.strip()
        car_model = profile.car_model.strip()
        car_year = profile.car_year

        if not car_brand and not car_model:
            return queryset.order_by(
                "-created_at",
            )[:self.recommended_parts_limit]

        compatibility_filter = Q()

        if car_brand:
            compatibility_filter &= Q(
                compatibilities__brand__iexact=car_brand,
            )

        if car_model:
            compatibility_filter &= Q(
                compatibilities__model__iexact=car_model,
            )

        if car_year:
            compatibility_filter &= (
                Q(compatibilities__year_from__isnull=True)
                | Q(compatibilities__year_from__lte=car_year)
            )
            compatibility_filter &= (
                Q(compatibilities__year_to__isnull=True)
                | Q(compatibilities__year_to__gte=car_year)
            )

        try:
            recommended_parts = list(
                queryset
                .filter(compatibility_filter)
                .distinct()
                .order_by("-created_at")[:self.recommended_parts_limit]
            )
        except FieldError:
            recommended_parts = []

        if recommended_parts:
            return recommended_parts

        return queryset.order_by(
            "-created_at",
        )[:self.recommended_parts_limit]

    def get_context_data(self, **kwargs):
        """
        Формирует контекст страницы личного кабинета.
        """

        context = super().get_context_data(**kwargs)

        user = self.request.user
        profile, _ = Profile.objects.get_or_create(user=user)
        subscription = self.get_subscription()
        privileged = has_unlimited_ai_access(user)
        moderator_only = is_moderator_only(user)

        has_active_subscription = subscription is not None
        searches_used = self.get_searches_used()
        ai_requests_used = self.get_ai_requests_used(subscription)
        image_analysis_used = self.get_image_analysis_used(
            subscription,
        )
        chat_requests_used = self.get_feature_requests_used(
            subscription,
            "chat",
        )
        instruction_requests_used = self.get_feature_requests_used(
            subscription,
            "instruction",
        )

        if privileged:
            ai_limit = 0
            chat_limit = 0
            instruction_limit = 0
            image_analysis_limit = 0
            has_chat_access = True
            has_instruction_access = True
            has_image_analysis_access = True
        elif moderator_only:
            ai_limit = 0
            chat_limit = 0
            instruction_limit = 0
            image_analysis_limit = 0
            has_chat_access = False
            has_instruction_access = False
            has_image_analysis_access = False
        elif subscription is not None:
            ai_limit = subscription.plan.max_ai_requests
            chat_limit = subscription.plan.get_feature_limit("chat")
            instruction_limit = subscription.plan.get_feature_limit(
                "instruction"
            )
            image_analysis_limit = subscription.plan.get_feature_limit(
                "image_analysis"
            )
            has_chat_access = subscription.plan.has_chat_access
            has_instruction_access = (
                subscription.plan.has_instruction_generation
            )
            has_image_analysis_access = (
                subscription.plan.has_image_analysis
            )
        else:
            ai_limit = self.free_ai_limit
            chat_limit = 0
            instruction_limit = 0
            image_analysis_limit = 0
            has_chat_access = False
            has_instruction_access = False
            has_image_analysis_access = False

        context.update(
            {
                "dashboard_user": user,
                "is_service_privileged": privileged,
                "is_ai_moderator": moderator_only,
                "has_community_chat_access": True,
                "profile": profile,
                "has_active_subscription": (
                    has_active_subscription
                ),
                "subscription": subscription,
                "subscription_plan": (
                    subscription.plan
                    if subscription is not None
                    else None
                ),
                "subscription_end_date": (
                    subscription.end_date
                    if subscription is not None
                    else None
                ),
                "subscription_is_expiring": (
                    self.is_subscription_expiring(subscription)
                ),
                "auto_renew": (
                    subscription.auto_renew
                    if subscription is not None
                    else False
                ),
                "has_chat_access": has_chat_access,
                "has_instruction_access": has_instruction_access,
                "has_image_analysis_access": (
                    has_image_analysis_access
                ),
                "recent_searches": self.get_recent_searches(),
                "recent_repairs": self.get_recent_repairs(),
                "active_repair": self.get_active_repair(),
                "searches_used": searches_used,
                "search_limit": self.free_search_limit,
                "searches_remaining": self.calculate_remaining(
                    used=searches_used,
                    limit=self.free_search_limit,
                ),
                "searches_percent": self.calculate_percent(
                    used=searches_used,
                    limit=self.free_search_limit,
                ),
                "ai_requests_used": ai_requests_used,
                "ai_limit": ai_limit,
                "ai_requests_remaining": self.calculate_remaining(
                    used=ai_requests_used,
                    limit=ai_limit,
                ),
                "ai_requests_percent": self.calculate_percent(
                    used=ai_requests_used,
                    limit=ai_limit,
                ),
                "image_analysis_used": image_analysis_used,
                "chat_requests_used": chat_requests_used,
                "chat_limit": chat_limit,
                "chat_requests_remaining": self.calculate_remaining(
                    used=chat_requests_used,
                    limit=chat_limit,
                ),
                "chat_requests_percent": self.calculate_percent(
                    used=chat_requests_used,
                    limit=chat_limit,
                ),
                "instruction_requests_used": instruction_requests_used,
                "instruction_limit": instruction_limit,
                "instruction_requests_remaining": self.calculate_remaining(
                    used=instruction_requests_used,
                    limit=instruction_limit,
                ),
                "instruction_requests_percent": self.calculate_percent(
                    used=instruction_requests_used,
                    limit=instruction_limit,
                ),
                "image_analysis_limit": image_analysis_limit,
                "image_analysis_remaining": self.calculate_remaining(
                    used=image_analysis_used,
                    limit=image_analysis_limit,
                ),
                "image_analysis_percent": self.calculate_percent(
                    used=image_analysis_used,
                    limit=image_analysis_limit,
                ),
                "last_ai_request": (
                    self.get_ai_requests_queryset().first()
                ),
                "recommended_parts": (
                    self.get_recommended_parts()
                    if has_active_subscription
                    else []
                ),
            }
        )

        return context


class UserListAPIView(ListAPIView):
    """
    API-представление для получения
    списка пользователей.

    Доступ предоставляется:

    - модераторам;
    - администраторам;
    - системным суперпользователям Django.
    """

    queryset = User.objects.all()
    serializer_class = UserSerializer
    permission_classes = [
        IsAuthenticated,
        IsModerator,
    ]


class UserCreateAPIView(CreateAPIView):
    """
    API-представление для регистрации
    нового пользователя.

    Доступно без авторизации.
    """

    queryset = User.objects.all()
    serializer_class = UserCreateSerializer
    permission_classes = [
        AllowAny,
    ]


class UserRetrieveAPIView(RetrieveAPIView):
    """
    API-представление для получения
    информации о пользователе.

    Обычный пользователь может просматривать
    только собственную учётную запись.

    Администраторы и системные суперпользователи
    могут просматривать любую учётную запись.
    """

    queryset = User.objects.all()
    serializer_class = UserSerializer
    permission_classes = [
        IsAuthenticated,
        IsOwner,
    ]


class UserUpdateAPIView(UpdateAPIView):
    """
    API-представление для обновления
    данных пользователя.

    Обычный пользователь может изменять
    только собственную учётную запись.

    Администраторы и системные суперпользователи
    могут изменять любую учётную запись.
    """

    queryset = User.objects.all()
    serializer_class = UserUpdateSerializer
    permission_classes = [
        IsAuthenticated,
        IsOwner,
    ]


class UserDeleteAPIView(DestroyAPIView):
    """
    API-представление для удаления
    пользователя.

    Доступ предоставляется:

    - пользователям с ролью администратора;
    - системным суперпользователям Django.
    """

    queryset = User.objects.all()
    permission_classes = [
        IsAuthenticated,
        IsAdmin,
    ]

    def perform_destroy(self, instance):
        """
        Удаляет выбранного пользователя.

        Запрещает администратору или
        суперпользователю удалить самого себя
        через этот endpoint.
        """

        if instance.pk == self.request.user.pk:
            from rest_framework.exceptions import PermissionDenied

            raise PermissionDenied(
                "Нельзя удалить собственную "
                "учётную запись через этот endpoint."
            )

        instance.delete()


class UserTokenObtainPairView(TokenObtainPairView):
    """
    API-представление для получения
    JWT access и refresh токенов.
    """

    serializer_class = UserTokenObtainSerializer
    permission_classes = [
        AllowAny,
    ]


class ProfileRetrieveAPIView(
    UserOwnedQuerySetMixin,
    RetrieveAPIView,
):
    """
    API-представление для получения
    профиля пользователя.

    Обычный пользователь может просматривать
    только собственный профиль.

    Администраторы и системные суперпользователи
    могут просматривать любой профиль.
    """

    queryset = Profile.objects.select_related(
        "user",
    )
    serializer_class = ProfileSerializer
    permission_classes = [
        IsAuthenticated,
        IsOwner,
    ]


class ProfileUpdateAPIView(
    UserOwnedQuerySetMixin,
    UpdateAPIView,
):
    """
    API-представление для изменения
    профиля пользователя.

    Обычный пользователь может изменять
    только собственный профиль.

    Администраторы и системные суперпользователи
    могут изменять любой профиль.
    """

    queryset = Profile.objects.select_related(
        "user",
    )
    serializer_class = ProfileUpdateSerializer
    permission_classes = [
        IsAuthenticated,
        IsOwner,
    ]


class SearchHistoryListAPIView(
    UserOwnedQuerySetMixin,
    ListAPIView,
):
    """
    API-представление для получения
    истории поисковых запросов.

    Обычный пользователь получает только
    собственную историю поиска.

    Администраторы и системные суперпользователи
    получают историю всех пользователей.
    """

    queryset = SearchHistory.objects.select_related(
        "user",
    )
    serializer_class = SearchHistorySerializer
    permission_classes = [
        IsAuthenticated,
    ]


class RepairHistoryListAPIView(
    UserOwnedQuerySetMixin,
    ListAPIView,
):
    """
    API-представление для получения
    истории ремонтов.

    Обычный пользователь получает только
    собственную историю ремонтов.

    Администраторы и системные суперпользователи
    получают историю всех пользователей.
    """

    queryset = RepairHistory.objects.select_related(
        "user",
        "instruction",
    )
    serializer_class = RepairHistorySerializer
    permission_classes = [
        IsAuthenticated,
    ]


class RepairHistoryCreateAPIView(CreateAPIView):
    """
    API-представление для создания
    записи истории ремонта.

    Доступно активным авторизованным
    пользователям.
    """

    queryset = RepairHistory.objects.all()
    serializer_class = RepairHistoryCreateSerializer
    permission_classes = [
        IsAuthenticated,
    ]

    def perform_create(self, serializer):
        """
        Создаёт запись истории ремонта
        для текущего пользователя.

        Значение поля user, переданное клиентом,
        игнорируется.
        """

        serializer.save(
            user=self.request.user,
        )


class RepairHistoryRetrieveAPIView(
    UserOwnedQuerySetMixin,
    RetrieveAPIView,
):
    """
    API-представление для получения
    отдельной записи истории ремонта.

    Обычный пользователь может просматривать
    только собственные записи.

    Администраторы и системные суперпользователи
    могут просматривать любые записи.
    """

    queryset = RepairHistory.objects.select_related(
        "user",
        "instruction",
    )
    serializer_class = RepairHistorySerializer
    permission_classes = [
        IsAuthenticated,
        IsOwner,
    ]


class RepairHistoryUpdateAPIView(
    UserOwnedQuerySetMixin,
    UpdateAPIView,
):
    """
    API-представление для изменения
    записи истории ремонта.

    Обычный пользователь может изменять
    только собственные записи.

    Администраторы и системные суперпользователи
    могут изменять любые записи.
    """

    queryset = RepairHistory.objects.select_related(
        "user",
        "instruction",
    )
    serializer_class = RepairHistoryUpdateSerializer
    permission_classes = [
        IsAuthenticated,
        IsOwner,
    ]

    def perform_update(self, serializer):
        """
        Обновляет запись, не позволяя
        изменить её владельца через API.
        """

        serializer.save(
            user=self.get_object().user,
        )


class RepairHistoryDeleteAPIView(
    UserOwnedQuerySetMixin,
    DestroyAPIView,
):
    """
    API-представление для удаления
    записи истории ремонта.

    Обычный пользователь может удалять
    только собственные записи.

    Администраторы и системные суперпользователи
    могут удалять любые записи.
    """

    queryset = RepairHistory.objects.select_related(
        "user",
        "instruction",
    )
    permission_classes = [
        IsAuthenticated,
        IsOwner,
    ]


class UserLoginView(auth_views.LoginView):
    """
    Представление для входа зарегистрированного пользователя.

    Использует стандартную сессионную авторизацию Django.
    После успешного входа перенаправляет пользователя
    на главную страницу приложения.
    """

    template_name = "users/login.html"
    authentication_form = AuthenticationForm
    redirect_authenticated_user = True
    next_page = reverse_lazy("users:dashboard")

    def get_form(self, form_class=None):
        """
        Добавляет оформление полям формы авторизации.
        """
        form = super().get_form(form_class)

        form.fields["username"].widget.attrs.update(
            {
                "class": "form-control form-control-lg",
                "placeholder": "Введите имя пользователя",
                "autocomplete": "username",
                "autofocus": True,
            }
        )

        form.fields["password"].widget.attrs.update(
            {
                "class": "form-control form-control-lg",
                "placeholder": "Введите пароль",
                "autocomplete": "current-password",
            }
        )

        return form


class UserLogoutView(auth_views.LogoutView):
    """
    Представление для выхода пользователя из системы.
    """

    next_page = reverse_lazy("users:login")


class ProfileDetailView(LoginRequiredMixin, DetailView):
    """
    HTML-представление личного профиля пользователя.

    Показывает профиль только текущего
    авторизованного пользователя.
    """

    model = Profile
    template_name = "users/profile_detail.html"
    context_object_name = "profile"
    login_url = "users:login"

    def get_object(self, queryset=None):
        """
        Возвращает профиль текущего пользователя.

        Если профиль ещё не создан, он будет
        автоматически создан.
        """
        profile, _ = Profile.objects.get_or_create(
            user=self.request.user,
        )
        return profile


class SearchHistoryPageView(LoginRequiredMixin, ListView):
    """
    HTML-представление истории поиска пользователя.

    Обычный пользователь видит только собственную
    историю. Суперпользователь видит все записи.
    """

    model = SearchHistory
    template_name = "users/search_history.html"
    context_object_name = "search_history"
    paginate_by = 10
    login_url = "users:login"

    def get_queryset(self):
        """
        Возвращает доступную пользователю историю поиска.
        """
        queryset = (
            SearchHistory.objects
            .select_related("user")
            .order_by("-searched_at")
        )

        if self.request.user.is_superuser:
            return queryset

        return queryset.filter(user=self.request.user)


class RepairHistoryPageView(LoginRequiredMixin, ListView):
    """
    HTML-представление истории ремонта пользователя.

    Обычный пользователь видит только собственные
    записи. Суперпользователь видит все записи.
    """

    model = RepairHistory
    template_name = "users/repair_history.html"
    context_object_name = "repair_history"
    paginate_by = 10
    login_url = "users:login"

    def get_queryset(self):
        """
        Возвращает доступную пользователю историю ремонта.
        """
        queryset = (
            RepairHistory.objects
            .select_related(
                "user",
                "instruction",
                "instruction__part",
            )
            .annotate(total_steps=Count("instruction__steps", distinct=True))
            .order_by("-created_at")
        )

        if self.request.user.is_superuser:
            return queryset

        return queryset.filter(user=self.request.user)


class RepairStepNavigationView(LoginRequiredMixin, View):
    """
    Переключает текущий шаг незавершённого ремонта.

    Обычный пользователь может изменять только собственный ремонт,
    суперпользователь — любую запись.
    """

    login_url = "users:login"

    def post(self, request, pk):
        with transaction.atomic():
            queryset = (
                RepairHistory.objects
                .select_for_update()
                .select_related("instruction")
                .filter(completed=False)
            )

            if not request.user.is_superuser:
                queryset = queryset.filter(user=request.user)

            repair = get_object_or_404(queryset, pk=pk)
            total_steps = repair.instruction.steps.count()

            if total_steps < 1:
                messages.error(
                    request,
                    "В инструкции пока нет шагов.",
                )
                return self._redirect_back(request)

            current_step = min(
                max(repair.current_step, 1),
                total_steps,
            )
            action = request.POST.get("action")

            if action == "previous":
                new_step = max(1, current_step - 1)
            elif action == "next":
                new_step = min(total_steps, current_step + 1)
            elif action == "complete":
                repair.current_step = total_steps
                repair.completed = True
                repair.save(
                    update_fields=(
                        "current_step",
                        "completed",
                        "progress_updated_at",
                    )
                )
                completed = True
            else:
                messages.error(
                    request,
                    "Неизвестное действие навигации.",
                )
                return self._redirect_back(request)

            if action != "complete":
                repair.current_step = new_step
                repair.save(
                    update_fields=(
                        "current_step",
                        "progress_updated_at",
                    )
                )
                completed = False

        if completed:
            messages.success(
                request,
                "Ремонт отмечен как завершённый.",
            )
        else:
            messages.success(
                request,
                f"Открыт шаг {new_step} из {total_steps}.",
            )
        return self._redirect_back(request)

    @staticmethod
    def _redirect_back(request):
        next_url = request.POST.get("next", "")

        if next_url and url_has_allowed_host_and_scheme(
            next_url,
            allowed_hosts={request.get_host()},
            require_https=request.is_secure(),
        ):
            return redirect(next_url)

        return redirect("users:dashboard")


class UserRegistrationPageView(
    UserPassesTestMixin,
    View,
):
    """
    HTML-страница регистрации нового пользователя.

    Уже авторизованный пользователь перенаправляется
    на страницу профиля.
    """

    template_name = "users/register.html"

    def test_func(self):
        return not self.request.user.is_authenticated

    def handle_no_permission(self):
        return redirect("users:profile_detail")

    def get(self, request, *args, **kwargs):
        """Отображает форму регистрации."""

        return render(request, self.template_name)

    def post(self, request, *args, **kwargs):
        """Проверяет форму и создаёт новую учётную запись."""

        form_data = {
            "username": request.POST.get("username", "").strip(),
            "email": request.POST.get("email", "").strip(),
            "password": request.POST.get("password", ""),
        }
        password_confirm = request.POST.get("password_confirm", "")

        if form_data["password"] != password_confirm:
            return render(
                request,
                self.template_name,
                {
                    "registration_errors": {
                        "password_confirm": (
                            "Пароли не совпадают.",
                        ),
                    },
                    "registration_data": form_data,
                },
                status=400,
            )

        serializer = UserCreateSerializer(data=form_data)
        if not serializer.is_valid():
            return render(
                request,
                self.template_name,
                {
                    "registration_errors": serializer.errors,
                    "registration_data": form_data,
                },
                status=400,
            )

        serializer.save()
        messages.success(
            request,
            "Регистрация завершена. Теперь войдите в аккаунт.",
        )
        return redirect("users:login")


class ProfileUpdatePageView(LoginRequiredMixin, View):
    """
    HTML-представление для редактирования профиля.

    Позволяет одновременно изменить данные пользователя
    и дополнительную информацию его профиля.
    """

    template_name = "users/profile_update.html"
    login_url = reverse_lazy("users:login")

    def get_profile(self):
        """
        Возвращает профиль текущего пользователя.

        Если профиль отсутствует, создаёт его.
        """
        profile, _ = Profile.objects.get_or_create(
            user=self.request.user,
        )

        return profile

    def get(self, request, *args, **kwargs):
        """
        Отображает страницу редактирования профиля.
        """
        profile = self.get_profile()

        user_form = UserProfileUpdateForm(
            instance=request.user,
        )

        profile_form = ProfileUpdateForm(
            instance=profile,
        )

        context = {
            "user_form": user_form,
            "profile_form": profile_form,
        }

        return self.render_page(
            request=request,
            context=context,
        )

    def post(self, request, *args, **kwargs):
        """
        Проверяет и сохраняет обе формы.
        """
        profile = self.get_profile()

        user_form = UserProfileUpdateForm(
            request.POST,
            request.FILES,
            instance=request.user,
        )

        profile_form = ProfileUpdateForm(
            request.POST,
            instance=profile,
        )

        if user_form.is_valid() and profile_form.is_valid():
            with transaction.atomic():
                user_form.save()
                profile_form.save()

            messages.success(
                request,
                "Профиль успешно обновлён.",
            )

            return redirect(
                "users:profile_detail",
            )

        context = {
            "user_form": user_form,
            "profile_form": profile_form,
        }

        return self.render_page(
            request=request,
            context=context,
        )

    def render_page(self, request, context):
        """
        Рендерит шаблон страницы.
        """
        from django.shortcuts import render

        return render(
            request,
            self.template_name,
            context,
        )


class PartSearchPageView(ListView):
    """
    Страница поиска автомобильных запчастей.

    Выполняет поиск по OEM-номеру, названию,
    производителю и описанию запчасти.

    Для авторизованного пользователя сохраняет
    поисковый запрос в истории.
    """

    model = Part
    template_name = "users/part_search_results.html"
    context_object_name = "parts"
    paginate_by = 12

    def get_queryset(self):
        """
        Возвращает детали по любым доступным атрибутам.
        """

        search_query = self.request.GET.get("q", "").strip()

        if not search_query:
            return Part.objects.none()

        normalized_query = self.normalize_search_query(search_query)

        queryset = (
            Part.objects.filter(is_active=True)
            .annotate(
                searchable_weight=Cast("weight", CharField()),
                searchable_dimensions=Cast("dimensions", CharField()),
            )
            .select_related("category")
            .prefetch_related("images")
            .distinct()
        )

        search_fields = (
            "name__icontains",
            "slug__icontains",
            "original_number__icontains",
            "manufacturer__icontains",
            "description__icontains",
            "seo_title__icontains",
            "seo_description__icontains",
            "seo_keywords__icontains",
            "category__name__icontains",
            "category__slug__icontains",
            "category__description__icontains",
            "oem_numbers__number__icontains",
            "oem_numbers__manufacturer__icontains",
            "compatibilities__brand__icontains",
            "compatibilities__model__icontains",
            "compatibilities__generation__icontains",
            "compatibilities__engine__icontains",
            "instructions__title__icontains",
            "instructions__short_description__icontains",
            "instructions__content__icontains",
            "part_tools__tool__name__icontains",
            "part_tools__tool__description__icontains",
            "part_tools__tool__size__icontains",
            "part_tools__tool__category__name__icontains",
            "searchable_weight__icontains",
            "searchable_dimensions__icontains",
        )
        search_tokens = re.findall(r"[\w-]+", search_query, flags=re.UNICODE)
        if not search_tokens:
            self.save_search_history(
                search_query=search_query,
                result_found=False,
            )
            return Part.objects.none()

        for token in search_tokens:
            token_filter = Q(
                normalized_original_number__icontains=normalized_query
            )
            token_variants = {
                token,
                token.lower(),
                token.upper(),
                token.capitalize(),
                token.title(),
            }
            for variant in token_variants:
                for field_name in search_fields:
                    token_filter |= Q(**{field_name: variant})

            if token.isdigit():
                numeric_value = int(token)
                token_filter |= (
                    Q(compatibilities__year_from=numeric_value)
                    | Q(compatibilities__year_to=numeric_value)
                )

            queryset = queryset.filter(token_filter)

        self.save_search_history(
            search_query=search_query,
            result_found=queryset.exists(),
        )

        return queryset

    def get_context_data(self, **kwargs):
        """
        Добавляет данные поиска в контекст шаблона.
        """

        context = super().get_context_data(**kwargs)

        search_query = self.request.GET.get("q", "").strip()

        context["search_query"] = search_query
        context["search_performed"] = bool(search_query)
        context["result_count"] = (
            context["paginator"].count
            if context.get("paginator")
            else 0
        )
        context["can_view_part_cards"] = has_part_card_access(
            self.request.user
        )
        for part in context.get("parts", ()):
            part.search_gallery_images = [
                {
                    "url": image.image.url,
                    "alt": image.alt_text or part.name,
                }
                for image in part.images.all()
                if image.image_exists
            ]

        return context

    def save_search_history(
        self,
        search_query: str,
        result_found: bool,
    ) -> None:
        """
        Сохраняет запрос авторизованного пользователя.

        При переходе по страницам пагинации повторная
        запись истории не создаётся.
        """

        user = self.request.user

        if not user.is_authenticated:
            return

        if self.request.GET.get("page"):
            return

        SearchHistory.objects.create(
            user=user,
            original_number=search_query,
            search_query=search_query,
            result_found=result_found,
        )

    @staticmethod
    def normalize_search_query(search_query: str) -> str:
        """
        Удаляет пробелы и разделители из OEM-номера.
        """

        return (
            search_query
            .replace("-", "")
            .replace(" ", "")
            .replace(".", "")
            .upper()
        )
