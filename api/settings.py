"""
Django settings for Laboratory Management System with Clean Architecture.

This configuration follows Clean Architecture principles and uses environment variables
for sensitive data management.
"""

import os
from datetime import timedelta
from pathlib import Path

import pymysql
from dotenv import load_dotenv

pymysql.install_as_MySQLdb()
# load_dotenv()

BASE_DIR = Path(__file__).resolve().parent.parent

# =============================================================================
# SECURITY SETTINGS
# =============================================================================

SECRET_KEY = os.getenv("SECRET_KEY")
DEBUG = os.getenv("DEBUG", "False").lower() == "true"
ALLOWED_HOSTS = os.getenv("ALLOWED_HOSTS", "*").split(",")

CSRF_TRUSTED_ORIGINS = (
    os.getenv("CSRF_TRUSTED_ORIGINS", "").split(",")
    if os.getenv("CSRF_TRUSTED_ORIGINS")
    else []
)
CSRF_COOKIE_SECURE = os.getenv("CSRF_COOKIE_SECURE", "False").lower() == "true"
SESSION_COOKIE_SECURE = os.getenv("SESSION_COOKIE_SECURE", "False").lower() == "true"
SECURE_SSL_REDIRECT = os.getenv("SECURE_SSL_REDIRECT", "False").lower() == "true"

# =============================================================================
# APPLICATION DEFINITION
# =============================================================================

DJANGO_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
]

THIRD_PARTY_APPS = [
    "rest_framework",
    "rest_framework_simplejwt",
    "rest_framework_api_key",
    "drf_spectacular",
    "django_filters",
    "corsheaders",
    "guardian",
    "import_export",
    "channels",
]

LOCAL_APPS = [
    "custom_auth",
    "lab_schedule",
    "lab_allocation",
    "room_booking",
    "duty_schedule",
]

INSTALLED_APPS = LOCAL_APPS + DJANGO_APPS + THIRD_PARTY_APPS

# =============================================================================
# MIDDLEWARE CONFIGURATION
# =============================================================================

MIDDLEWARE = [
    "whitenoise.middleware.WhiteNoiseMiddleware",
    "corsheaders.middleware.CorsMiddleware",
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.locale.LocaleMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
    "shared.middleware.LanguageParameterMiddleware",
]

ROOT_URLCONF = "api.urls"

# =============================================================================
# TEMPLATE CONFIGURATION
# =============================================================================

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [BASE_DIR / "templates"],
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

WSGI_APPLICATION = "api.wsgi.application"
ASGI_APPLICATION = "api.asgi.application"


# =============================================================================
# DATABASE CONFIGURATION
# =============================================================================

DATABASES = {
    "default": {
        "ENGINE": os.getenv("DB_ENGINE"),
        "NAME": os.getenv("DB_NAME"),
        "USER": os.getenv("DB_USER"),
        "PASSWORD": os.getenv("DB_PASSWORD"),
        "HOST": os.getenv("DB_HOST"),
        "PORT": os.getenv("DB_PORT"),
    }
}


# =============================================================================
# DJANGO CHANNELS CONFIGURATION
# =============================================================================

CHANNEL_LAYERS = {
    "default": {
        "BACKEND": "channels_redis.core.RedisChannelLayer",
        "CONFIG": {
            "hosts": [("127.0.0.1", 6379)],
        },
    },
}

# Fallback to in-memory channel layer for development without Redis
if os.getenv("USE_REDIS_CHANNELS", "true").lower() == "false":
    CHANNEL_LAYERS = {"default": {"BACKEND": "channels.layers.InMemoryChannelLayer"}}


# =============================================================================
# PASSWORD VALIDATION
# =============================================================================

AUTH_PASSWORD_VALIDATORS = [
    {
        "NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.MinimumLengthValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.CommonPasswordValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.NumericPasswordValidator",
    },
]


# =============================================================================
# INTERNATIONALIZATION
# =============================================================================

LANGUAGE_CODE = os.getenv("LANGUAGE_CODE", "id")
TIME_ZONE = os.getenv("TIME_ZONE", "UTC")
USE_I18N = True
USE_TZ = True

LANGUAGES = [
    ("en", "English"),
    ("id", "Bahasa Indonesia"),
]

LOCALE_PATHS = [
    BASE_DIR / "locales",
]

# =============================================================================
# STATIC FILES AND MEDIA CONFIGURATION
# =============================================================================

STATIC_URL = "/static/"
# STATIC_ROOT = BASE_DIR / "staticfiles"
STATICFILES_DIRS = [
    BASE_DIR / "static",
]
# STATICFILES_STORAGE = "whitenoise.storage.CompressedManifestStaticFilesStorage"

MEDIA_URL = "/media/"
MEDIA_ROOT = BASE_DIR / "media"

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

# =============================================================================
# DJANGO REST FRAMEWORK CONFIGURATION
# =============================================================================

REST_FRAMEWORK = {
    "DEFAULT_PAGINATION_CLASS": "shared.pagination.custom_pagination.CustomPagination",
    "DEFAULT_AUTHENTICATION_CLASSES": [
        "rest_framework_simplejwt.authentication.JWTAuthentication",
    ],
    "DEFAULT_SCHEMA_CLASS": "drf_spectacular.openapi.AutoSchema",
    "DEFAULT_PERMISSION_CLASSES": (
        "rest_framework.permissions.IsAuthenticated",
        "rest_framework_api_key.permissions.HasAPIKey",
    ),
    "DEFAULT_VERSIONING_CLASS": "rest_framework.versioning.AcceptHeaderVersioning",
    "ALLOWED_VERSIONS": ["v1"],
    "VERSION_PARAM": "version",
    "DEFAULT_VERSION": "v1",
    "DEFAULT_FILTER_BACKENDS": ["django_filters.rest_framework.DjangoFilterBackend"],
    "EXCEPTION_HANDLER": "shared.handler.exception_handler.custom_exception_handler",
}

APPEND_SLASH = False

# =============================================================================
# CORS CONFIGURATION
# =============================================================================

CORS_ALLOW_ALL_ORIGINS = True

# =============================================================================
# AUTHENTICATION CONFIGURATION
# =============================================================================

AUTHENTICATION_BACKENDS = (
    "django.contrib.auth.backends.ModelBackend",
    "guardian.backends.ObjectPermissionBackend",
)

AUTH_USER_MODEL = "custom_auth.CustomUserModel"

# =============================================================================
# DRF SPECTACULAR (OpenAPI) CONFIGURATION
# =============================================================================

SPECTACULAR_SETTINGS = {
    "TITLE": "Laboratory API",
    "DESCRIPTION": "API for Laboratory",
    "VERSION": "1.0.0",
    "SERVE_INCLUDE_SCHEMA": False,
    "SCHEMA_PATH_PREFIX": "/api/v1/",
    "DEFAULT_PAGINATION_CLASS": None,
    "APPEND_COMPONENTS": {
        "securitySchemes": {
            "ApiKeyAuth": {
                "type": "apiKey",
                "in": "header",
                "name": "X-Api-Key",
            },
        }
    },
    "SECURITY": [
        {"ApiKeyAuth": []},
    ],
    "SWAGGER_UI_SETTINGS": {
        "persistAuthorization": True,
        "defaultModelsExpandDepth": -1,
    },
}

# =============================================================================
# API KEY CONFIGURATION
# =============================================================================

API_KEY_CUSTOM_HEADER = os.getenv("API_KEY_CUSTOM_HEADER", "HTTP_X_API_KEY")

# =============================================================================
# IMPORT/EXPORT CONFIGURATION
# =============================================================================

try:
    from import_export.formats.base_formats import CSV, XLSX

    IMPORT_EXPORT_FORMATS = [CSV, XLSX]
    IMPORT_EXPORT_USE_TRANSACTIONS = True
    IMPORT_EXPORT_SKIP_ADMIN_LOG = False
except ImportError:
    pass

# =============================================================================
# JWT AUTHENTICATION CONFIGURATION
# =============================================================================

SIMPLE_JWT = {
    "ACCESS_TOKEN_LIFETIME": timedelta(days=7),
    "REFRESH_TOKEN_LIFETIME": timedelta(weeks=2),
    "ROTATE_REFRESH_TOKENS": False,
    "BLACKLIST_AFTER_ROTATION": True,
    "ALGORITHM": "HS256",
    "SIGNING_KEY": SECRET_KEY,
    "AUTH_HEADER_TYPES": ("Bearer",),
}

# =============================================================================
# LOGGING CONFIGURATION
# =============================================================================

LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "verbose": {
            "format": "{levelname} {asctime} {module} {process:d} {thread:d} {message}",
            "style": "{",
        },
        "simple": {
            "format": "{levelname} {message}",
            "style": "{",
        },
    },
    "handlers": {
        "console": {
            "class": "logging.StreamHandler",
            "formatter": "verbose",
        },
        "file": {
            "class": "logging.FileHandler",
            "filename": os.getenv("LOG_FILE", "logs/django.log"),
            "formatter": "verbose",
        },
    },
    "root": {
        "handlers": ["console"],
        "level": os.getenv("LOG_LEVEL", "INFO"),
    },
    "loggers": {
        "django": {
            "handlers": ["console", "file"],
            "level": os.getenv("LOG_LEVEL", "INFO"),
            "propagate": False,
        },
        "application": {
            "handlers": ["console", "file"],
            "level": "DEBUG",
            "propagate": False,
        },
        "infrastructure": {
            "handlers": ["console", "file"],
            "level": "DEBUG",
            "propagate": False,
        },
        "shared.format": {
            "handlers": ["console", "file"],
            "level": "DEBUG",
            "propagate": False,
        },
    },
}

# =============================================================================
# LOGGING CONFIGURATION CONTINUED
# =============================================================================

LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "verbose": {
            "format": "{levelname} {asctime} {module} {process:d} {thread:d} {message}",
            "style": "{",
        },
        "simple": {
            "format": "{levelname} {message}",
            "style": "{",
        },
    },
    "handlers": {
        "console": {
            "class": "logging.StreamHandler",
            "formatter": "verbose",
        },
        "file": {
            "class": "logging.FileHandler",
            "filename": os.getenv("LOG_FILE", "logs/django.log"),
            "formatter": "verbose",
        },
    },
    "root": {
        "handlers": ["console"],
        "level": os.getenv("LOG_LEVEL", "INFO"),
    },
    "loggers": {
        "django": {
            "handlers": ["console", "file"],
            "level": os.getenv("LOG_LEVEL", "INFO"),
            "propagate": False,
        },
        "application": {
            "handlers": ["console", "file"],
            "level": "DEBUG",
            "propagate": False,
        },
        "infrastructure": {
            "handlers": ["console", "file"],
            "level": "DEBUG",
            "propagate": False,
        },
        "shared.format": {
            "handlers": ["console", "file"],
            "level": "DEBUG",
            "propagate": False,
        },
    },
}
