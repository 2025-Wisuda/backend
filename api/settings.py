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
load_dotenv()

BASE_DIR = Path(__file__).resolve().parent.parent

# =============================================================================
# SECURITY SETTINGS
# =============================================================================

SECRET_KEY = os.getenv("SECRET_KEY")
DEBUG = os.getenv("DEBUG", "True").lower() == "true"
ALLOWED_HOSTS = [
    "backend.2025wisuda.me",
    "ai.2025wisuda.me",
    "167.71.212.171",
    "localhost",
    "127.0.0.1",
    "0.0.0.0",
]

CSRF_TRUSTED_ORIGINS = [
    "https://backend.2025wisuda.me",
    "https://ai.2025wisuda.me",
    "http://localhost:3000",  # For local frontend development
] + (
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
    "rest_framework_simplejwt.token_blacklist",
    "rest_framework_api_key",
    "drf_spectacular",
    "django_filters",
    "corsheaders",
    "guardian",
    "import_export",
    "channels",
    "django_extensions",
    "django_celery_beat",  # Required for Celery Beat scheduler
]

LOCAL_APPS = [
    "shared",
    "custom_auth",
    "lab_schedule",
    "lab_allocation",
    "room_booking",
    "duty_schedule",
    "course",
    "guest_visit",
    "fcm_notifications",
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
    "shared.middleware.anonymous_user_fix.AnonymousUserFixMiddleware",
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
ASGI_APPLICATION = "api.routing.application"


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
        "OPTIONS": {
            "charset": "utf8mb4",
        },
    }
}


# =============================================================================
# DJANGO CHANNELS CONFIGURATION
# =============================================================================

CHANNEL_LAYERS = {
    "default": {
        "BACKEND": "channels_redis.core.RedisChannelLayer",
        "CONFIG": {
            "hosts": [
                (
                    os.getenv("REDIS_HOST", "127.0.0.1"),
                    int(os.getenv("REDIS_PORT", "6379")),
                )
            ],
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

# Force Django admin to use Indonesian
USE_L10N = True
TIME_ZONE = os.getenv("TIME_ZONE", "Asia/Jakarta")
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
STATIC_ROOT = BASE_DIR / "staticfiles"
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

# Create logs directory if it doesn't exist
LOG_DIR = BASE_DIR / "logs"
LOG_DIR.mkdir(exist_ok=True)

# Use console-only logging in production/Docker for simplicity
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
    },
    "root": {
        "handlers": ["console"],
        "level": os.getenv("LOG_LEVEL", "INFO"),
    },
    "loggers": {
        "django": {
            "handlers": ["console"],
            "level": os.getenv("LOG_LEVEL", "INFO"),
            "propagate": False,
        },
        "application": {
            "handlers": ["console"],
            "level": "DEBUG",
            "propagate": False,
        },
        "infrastructure": {
            "handlers": ["console"],
            "level": "DEBUG",
            "propagate": False,
        },
        "shared.format": {
            "handlers": ["console"],
            "level": "DEBUG",
            "propagate": False,
        },
    },
}

# Duplicated LOGGING config removed - using the one above

# =============================================================================
# FCM CONFIGURATION
# =============================================================================

# Firebase Admin SDK Configuration
FIREBASE_SERVICE_ACCOUNT_PATH = os.path.join(BASE_DIR, "firebase-service-account.json")
FCM_PROJECT_ID = "simplelab-ced4d"  # From your service account JSON

# =============================================================================
# CELERY CONFIGURATION
# =============================================================================

CELERY_BROKER_URL = os.getenv("CELERY_BROKER_URL", "redis://backend-redis-1:6379/0")
CELERY_RESULT_BACKEND = os.getenv(
    "CELERY_RESULT_BACKEND", "redis://backend-redis-1:6379/0"
)
CELERY_ACCEPT_CONTENT = ["json"]
CELERY_TASK_SERIALIZER = "json"
CELERY_RESULT_SERIALIZER = "json"
CELERY_TIMEZONE = "Asia/Jakarta"
CELERY_TASK_TRACK_STARTED = True
CELERY_TASK_TIME_LIMIT = 30 * 60  # 30 minutes
CELERY_TASK_SOFT_TIME_LIMIT = 25 * 60  # 25 minutes

# Celery Beat Schedule for periodic tasks
CELERY_BEAT_SCHEDULE = {
    "send-lab-reminders": {
        "task": "fcm_notifications.tasks.notification_tasks.send_lab_schedule_reminders",
        "schedule": 300.0,  # Every 5 minutes
        "args": (15,),  # Look 15 minutes ahead
    },
    "test-notification-system": {
        "task": "fcm_notifications.tasks.notification_tasks.test_lab_notification_system",
        "schedule": 3600.0,  # Every hour for monitoring
    },
    # Legacy tasks (disabled for now)
    # "send-lab-notifications": {
    #     "task": "fcm_notifications.tasks.send_lab_schedule_notifications",
    #     "schedule": 300.0,  # Every 5 minutes
    #     "args": (15,),  # Look 15 minutes ahead
    # },
    # "cleanup-old-notifications": {
    #     "task": "fcm_notifications.tasks.cleanup_old_notifications",
    #     "schedule": 86400.0,  # Every 24 hours
    #     "args": (30,),  # Remove logs older than 30 days
    # },
}

# =============================================================================
# FACE RECOGNITION SERVICE COMMUNICATION
# =============================================================================

# Point to Face Recognition service via subdomain
FACE_RECOGNITION_WS_URL = os.getenv(
    "FACE_RECOGNITION_WS_URL", "wss://ai.2025wisuda.me/ws/backend-communication/"
)
FACE_RECOGNITION_AUTH_TOKEN = os.getenv(
    "FACE_RECOGNITION_AUTH_TOKEN", "backend-service-token"
)
FACE_RECOGNITION_ENABLED = (
    os.getenv("FACE_RECOGNITION_ENABLED", "True").lower() == "true"
)
FACE_RECOGNITION_TIMEOUT = int(os.getenv("FACE_RECOGNITION_TIMEOUT", "30"))

# Lab Security Settings
LAB_ACCESS_KEY = "LAB_SECRET_2025"  # Change this to your secret key
LAB_SESSION_TIMEOUT = 3600  # 1 hour in seconds
