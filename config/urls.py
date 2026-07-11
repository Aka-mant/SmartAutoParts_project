

from django.contrib import admin
from django.urls import path, include
from django.conf.urls.static import static
from django.conf import settings


from drf_yasg import openapi
from drf_yasg.views import get_schema_view

from rest_framework import permissions








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
    path('api/instructions/', include('apps.instructions.urls'), name='instructions'),
    path('api/parts/', include('apps.parts.urls'), name='parts'),

    #




    #documentation

    path('swagger<str:format>/', schema_view.without_ui('swagger'), name='schema-json'),
    path('swagger/', schema_view.with_ui('swagger', cache_timeout=0), name='schema-swagger-ui'),
    path('redoc/', schema_view.with_ui('redoc', cache_timeout=0), name='schema-redoc'),
]+ static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
