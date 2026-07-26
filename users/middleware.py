from urllib.parse import urlencode

from django.conf import settings
from django.shortcuts import redirect
from django.urls import reverse

from .models import UserAgreementAcceptance


class UserAgreementRequiredMiddleware:
    """Запрашивает согласие при первом использовании функций сервиса."""

    session_key = "accepted_user_agreement_version"
    protected_prefixes = (
        "/users/dashboard/",
        "/users/search/",
        "/users/profile/",
        "/users/search-history/",
        "/users/repair-history/",
        "/parts/",
        "/instructions/",
        "/subscriptions/",
        "/ai/",
        "/chat/",
    )

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if self._requires_acceptance(request):
            version = settings.USER_AGREEMENT_VERSION
            if request.session.get(self.session_key) != version:
                accepted = UserAgreementAcceptance.objects.filter(
                    user=request.user,
                    agreement_version=version,
                ).exists()
                if accepted:
                    request.session[self.session_key] = version
                else:
                    agreement_url = reverse("users:user_agreement")
                    query = urlencode({"next": request.get_full_path()})
                    return redirect(f"{agreement_url}?{query}")

        return self.get_response(request)

    def _requires_acceptance(self, request):
        user = getattr(request, "user", None)
        if not getattr(user, "is_authenticated", False):
            return False

        agreement_path = reverse("users:user_agreement")
        if request.path == agreement_path:
            return False

        return any(
            request.path.startswith(prefix)
            for prefix in self.protected_prefixes
        )
