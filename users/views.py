from django.contrib.auth import views as auth_views
from django.contrib.auth.forms import AuthenticationForm
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import DetailView, ListView, TemplateView
from django.urls import reverse_lazy
from django.shortcuts import redirect, render
from django.contrib.auth.mixins import UserPassesTestMixin
from django.db import transaction
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

from .mixins.mixins import UserOwnedQuerySetMixin
from .models import (
    Profile,
    RepairHistory,
    SearchHistory,
    User,
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
    next_page = reverse_lazy("users:profile_detail")


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
            )
            .order_by("-created_at")
        )

        if self.request.user.is_superuser:
            return queryset

        return queryset.filter(user=self.request.user)


class UserRegistrationPageView(
    UserPassesTestMixin,
    TemplateView,
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

class ProfileUpdatePageView(LoginRequiredMixin, View):
    """
    HTML-представление страницы редактирования профиля.

    Обрабатывает две формы:

    - данные модели пользователя;
    - дополнительные данные модели профиля.
    """

    template_name = "users/profile_update.html"
    login_url = reverse_lazy("users:login")

    def get_profile(self):
        """
        Получает или создаёт профиль
        текущего пользователя.
        """
        profile, _ = Profile.objects.get_or_create(
            user=self.request.user,
        )

        return profile

    def get(self, request, *args, **kwargs):
        """
        Отображает заполненные формы.
        """
        profile = self.get_profile()

        context = {
            "user_form": UserProfileUpdateForm(
                instance=request.user,
            ),
            "profile_form": ProfileUpdateForm(
                instance=profile,
            ),
        }

        return render(
            request,
            self.template_name,
            context,
        )

    def post(self, request, *args, **kwargs):
        """
        Сохраняет изменения пользователя и профиля.
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
                "Данные профиля успешно обновлены.",
            )

            return redirect(
                "users:profile_detail",
            )

        context = {
            "user_form": user_form,
            "profile_form": profile_form,
        }

        return render(
            request,
            self.template_name,
            context,
        )