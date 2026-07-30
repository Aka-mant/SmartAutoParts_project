"""
Настройки Django для проекта SmartAutoParts.

Файл создан командой ``django-admin startproject`` для Django 6.0.6.
Описание настроек:
https://docs.djangoproject.com/en/6.0/topics/settings/
Полный перечень параметров:
https://docs.djangoproject.com/en/6.0/ref/settings/
"""

from pathlib import Path
import os

from dotenv import load_dotenv
from datetime import timedelta

load_dotenv()

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent
PROJECT_ROOT = BASE_DIR


def env_bool(name, default=False):
    """Возвращает логическое значение переменной окружения."""

    value = os.getenv(name)
    if value is None:
        return default
    return value.strip().lower() in {"1", "true", "yes", "on"}


def env_list(name, default=""):
    """Возвращает список значений переменной окружения через запятую."""

    return [
        item.strip()
        for item in os.getenv(name, default).split(",")
        if item.strip()
    ]


# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/6.0/howto/deployment/checklist/

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = os.getenv(
    "DJANGO_SECRET_KEY",
    (
        "django-insecure-1i(l)7er!iq4u9fbep(55avmz^k%8#g$+"
        "ra@8nbi0f(b==1+&z"
    ),
)

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = env_bool("DJANGO_DEBUG", True)

ALLOWED_HOSTS = env_list(
    "DJANGO_ALLOWED_HOSTS",
    "127.0.0.1,localhost",
)
CSRF_TRUSTED_ORIGINS = env_list("DJANGO_CSRF_TRUSTED_ORIGINS")


# Application definition

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',

    'rest_framework',
    'django_filters',
    'drf_yasg',

    # appa
    'users',
    'apps.instructions',
    'apps.parts',
    'apps.tools',
    'apps.subscriptions',
    'apps.AI',
    'apps.chat',
    'apps.analytics',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'users.middleware.UserAgreementRequiredMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'config.urls'

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [PROJECT_ROOT / "templates"],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.debug",
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    },
]

WSGI_APPLICATION = 'config.wsgi.application'


# Database
# https://docs.djangoproject.com/en/6.0/ref/settings/#databases

if os.getenv("DB_ENGINE", "sqlite").lower() == "postgresql":
    DATABASES = {
        "default": {
            "ENGINE": "django.db.backends.postgresql",
            "NAME": os.getenv("POSTGRES_DB", "smartautoparts"),
            "USER": os.getenv("POSTGRES_USER", "smartautoparts"),
            "PASSWORD": os.getenv(
                "POSTGRES_PASSWORD",
                "smartautoparts",
            ),
            "HOST": os.getenv("POSTGRES_HOST", "postgres"),
            "PORT": os.getenv("POSTGRES_PORT", "5432"),
            "CONN_MAX_AGE": int(os.getenv("DB_CONN_MAX_AGE", "60")),
            "OPTIONS": {
                "connect_timeout": int(
                    os.getenv("DB_CONNECT_TIMEOUT", "10")
                ),
            },
        }
    }
else:
    DATABASES = {
        "default": {
            "ENGINE": "django.db.backends.sqlite3",
            "NAME": BASE_DIR / "db.sqlite3",
        }
    }

REDIS_URL = os.getenv("REDIS_URL")
if REDIS_URL:
    CACHES = {
        "default": {
            "BACKEND": "django.core.cache.backends.redis.RedisCache",
            "LOCATION": REDIS_URL,
            "TIMEOUT": int(os.getenv("CACHE_TIMEOUT", "300")),
            "KEY_PREFIX": os.getenv(
                "CACHE_KEY_PREFIX",
                "smartautoparts",
            ),
        }
    }
else:
    CACHES = {
        "default": {
            "BACKEND": (
                "django.core.cache.backends.locmem.LocMemCache"
            ),
            "LOCATION": "smartautoparts-local",
        }
    }

# Password validation
# https://docs.djangoproject.com/en/6.0/ref/settings/#auth-password-validators

AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': (
            'django.contrib.auth.password_validation.'
            'UserAttributeSimilarityValidator'
        ),
    },
    {
        'NAME': (
            'django.contrib.auth.password_validation.'
            'MinimumLengthValidator'
        ),
    },
    {
        'NAME': (
            'django.contrib.auth.password_validation.'
            'CommonPasswordValidator'
        ),
    },
    {
        'NAME': (
            'django.contrib.auth.password_validation.'
            'NumericPasswordValidator'
        ),
    },
]

AUTH_USER_MODEL = 'users.User'


# Internationalization
# https://docs.djangoproject.com/en/6.0/topics/i18n/

LANGUAGE_CODE = 'ru-ru'

TIME_ZONE = 'Europe/Moscow'

USE_I18N = True

USE_TZ = True


# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/6.0/howto/static-files/

MEDIA_URL = "/media/"

MEDIA_ROOT = Path(
    os.getenv(
        "MEDIA_ROOT",
        BASE_DIR / "media",
    )
)
SERVE_MEDIA_FILES = env_bool(
    "SERVE_MEDIA_FILES",
    DEBUG,
)


STATIC_URL = "/static/"

STATICFILES_DIRS = [
    BASE_DIR / "static",
]

STATIC_ROOT = BASE_DIR / "staticfiles"

STORAGES = {
    "default": {
        "BACKEND": (
            "django.core.files.storage.FileSystemStorage"
        ),
    },
    "staticfiles": {
        "BACKEND": (
            "whitenoise.storage.CompressedStaticFilesStorage"
        ),
    },
}

LOGIN_URL = "users:login"

LOGIN_REDIRECT_URL = "users:dashboard"

LOGOUT_REDIRECT_URL = "users:login"

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

USER_AGREEMENT_VERSION = os.getenv(
    "USER_AGREEMENT_VERSION",
    "2026-07-26",
)

COMMUNITY_CHAT_RATE_LIMIT = int(
    os.getenv("COMMUNITY_CHAT_RATE_LIMIT", "12")
)
AI_CHAT_RATE_LIMIT = int(os.getenv("AI_CHAT_RATE_LIMIT", "6"))
CHAT_BURST_RATE_LIMIT = int(os.getenv("CHAT_BURST_RATE_LIMIT", "4"))
CHAT_RATE_WINDOW_SECONDS = int(
    os.getenv("CHAT_RATE_WINDOW_SECONDS", "60")
)
CHAT_BURST_WINDOW_SECONDS = int(
    os.getenv("CHAT_BURST_WINDOW_SECONDS", "10")
)
REST_FRAMEWORK = {
    'default_filter_backends': [
        'django_filters.rest_framework.DjangoFilterBackend'
    ],
    'DEFAULT_AUTHENTICATION_CLASSES': (
        # "rest_framework.authentication.SessionAuthentication",
        'rest_framework_simplejwt.authentication.JWTAuthentication',
    ),
    'DEFAULT_PERMISSION_CLASSES': (
        'rest_framework.permissions.IsAuthenticated',
    ),
    # "DEFAULT_PERMISSION_CLASSES": [
    #     "rest_framework.permissions.AllowAny",
    # ],
    'DEFAULT_PAGINATION_CLASS': (
        'rest_framework.pagination.PageNumberPagination'
    ),
    'PAGE_SIZE': 10,
    "TEST_REQUEST_DEFAULT_FORMAT": "json",
    "TEST_REQUEST_RENDERER_CLASSES": (
        "rest_framework.renderers.JSONRenderer",
        "rest_framework.renderers.MultiPartRenderer",
        "rest_framework.renderers.TemplateHTMLRenderer",
    )


}

SIMPLE_JWT = {
    'ACCESS_TOKEN_LIFETIME': timedelta(minutes=60),
    "REFRESH_TOKEN_LIFETIME": timedelta(days=7),
}

# Срок актуальности опубликованной ремонтной инструкции. Повторная выдача
# до истечения срока всё равно создаёт AIRequest и расходует лимит тарифа.
AI_INSTRUCTION_CACHE_TTL_DAYS = int(
    os.getenv("AI_INSTRUCTION_CACHE_TTL_DAYS", "365")
)
AI_IMAGE_MAX_BYTES = int(
    os.getenv("AI_IMAGE_MAX_BYTES", str(5 * 1024 * 1024))
)

# Серверная конфигурация OpenAI. Ключ не должен попадать в HTML/JavaScript.
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
OPENAI_AI_MODEL = os.getenv("OPENAI_AI_MODEL", "gpt-5.6-sol")
OPENAI_MODERATION_MODEL = os.getenv(
    "OPENAI_MODERATION_MODEL",
    "omni-moderation-latest",
)
OPENAI_TOOL_REASONING_EFFORT = os.getenv(
    "OPENAI_TOOL_REASONING_EFFORT",
    "low",
)
OPENAI_TOOL_MAX_OUTPUT_TOKENS = int(
    os.getenv("OPENAI_TOOL_MAX_OUTPUT_TOKENS", "3000")
)
OPENAI_TOOL_VERBOSITY = os.getenv(
    "OPENAI_TOOL_VERBOSITY",
    "medium",
)

CORS_ALLOWED_ORIGINS = [
    "http://read-only.example.com",
    "http://read-and-write.example.com",
]

CORS_TRUSTED_ORIGINS = [
    "http://read-only.example.com",
]
