from django.contrib import admin
from django.urls import path, include
from django.conf.urls.static import static
from django.conf import settings
from django.views.generic import RedirectView, TemplateView


from drf_yasg import openapi
from drf_yasg.views import get_schema_view

from rest_framework import permissions

from apps.instructions import urls as instruction_urls
from apps.parts import urls as part_urls
from apps.subscriptions import urls as subscription_urls
from apps.AI import urls as ai_urls
from apps.chat import urls as chat_urls

schema_view = get_schema_view(
    openapi.Info(
        title="My cool Api for SmartAutoParts",
        default_version='v0.1',
        description="My cool Api description",
        terms_of_service="https://www.google.com/policies/terms/",
        contact=openapi.Contact(email="aka-mant@mail.ru"),
        license=openapi.License(name="BSD License"),
    ),
    public=True,
    permission_classes=[permissions.AllowAny,],

)



urlpatterns = [

    path('admin/', admin.site.urls),

    # my apps
    path('users/', include('users.urls'), name='users'),
    path(
        "instructions/",
        include(
            (instruction_urls.web_urlpatterns, "instructions_web"),
            namespace="instructions_web",
        ),
    ),
    path(
        "parts/",
        include(
            (part_urls.web_urlpatterns, "parts_web"),
            namespace="parts_web",
        ),
    ),
    path(
        "subscriptions/",
        include(
            (subscription_urls.web_urlpatterns, "subscriptions_web"),
            namespace="subscriptions_web",
        ),
    ),
    path(
        "ai/",
        include(
            (ai_urls.web_urlpatterns, "ai_web"),
            namespace="ai_web",
        ),
    ),
    path(
        "chat/",
        include(
            (chat_urls.web_urlpatterns, "chat_web"),
            namespace="chat_web",
        ),
    ),
    path(
        "api/instructions/",
        include(
            (instruction_urls.api_urlpatterns, "instructions_api"),
            namespace="instructions_api",
        ),
        name="instructions",
    ),
    path(
        "api/parts/",
        include(
            (part_urls.api_urlpatterns, "parts_api"),
            namespace="parts_api",
        ),
        name="parts",
    ),
    path('api/tools/', include('apps.tools.urls'), name='tools'),
    path(
        "api/subscriptions/",
        include(
            (
                subscription_urls.api_urlpatterns,
                "subscriptions_api",
            ),
            namespace="subscriptions_api",
        ),
        name="subscriptions",
    ),
    path(
        "api/AI/",
        include(
            (ai_urls.api_urlpatterns, "apps.AI"),
            namespace="apps.AI",
        ),
        name="AI",
    ),
    path(
        "api/chat/",
        include(
            (chat_urls.api_urlpatterns, "apps.chat"),
            namespace="apps.chat",
        ),
        name="chat",
    ),
    path('api/analytics/', include('apps.analytics.urls'), name='analytics'),


    #
    path("", TemplateView.as_view(template_name="base.html",), name="home",),
    path(
        "user-agreement/",
        RedirectView.as_view(
            pattern_name="users:user_agreement",
            permanent=False,
        ),
        name="user_agreement",
    ),
    path(
        "license-agreement/",
        RedirectView.as_view(
            pattern_name="users:user_agreement",
            permanent=False,
        ),
        name="license_agreement",
    ),








    #documentation

    path(
        'swagger<str:format>/',
        schema_view.without_ui(cache_timeout=0),
        name='schema-json',
    ),
    path('swagger/', schema_view.with_ui('swagger', cache_timeout=0), name='schema-swagger-ui'),
    path('redoc/', schema_view.with_ui('redoc', cache_timeout=0), name='schema-redoc'),
]
if settings.DEBUG:
    urlpatterns += static(
        settings.MEDIA_URL,
        document_root=settings.MEDIA_ROOT,
    )

