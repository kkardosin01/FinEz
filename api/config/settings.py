"""
Django settings for FinEz.

Segredos e config específica de ambiente vêm de variáveis de ambiente
(django-environ), nunca hardcoded. Ver `.env.example` na raiz do projeto.
"""
from pathlib import Path

import environ

BASE_DIR = Path(__file__).resolve().parent.parent

env = environ.Env(
    DEBUG=(bool, False),
)
environ.Env.read_env(BASE_DIR / ".env")

SECRET_KEY = env("DJANGO_SECRET_KEY", default="insecure-dev-key-change-me")
DEBUG = env("DEBUG")

ALLOWED_HOSTS = env.list("ALLOWED_HOSTS", default=["localhost", "127.0.0.1"])
CSRF_TRUSTED_ORIGINS = env.list("CSRF_TRUSTED_ORIGINS", default=[])

INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "rest_framework",
    "drf_spectacular",
    "corsheaders",
    "django_ratelimit",
    "common",
    "accounts",
    "connections",
    "transactions",
    "budgets",
    "goals",
    "subscriptions",
    "engagement",
    "whatsapp",
    "exports",
    "investments",
    "insights",
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "corsheaders.middleware.CorsMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

ROOT_URLCONF = "config.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [],
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

WSGI_APPLICATION = "config.wsgi.application"

DATABASES = {
    "default": env.db(
        "DATABASE_URL", default="postgres://finez:finez@localhost:5432/finez"
    )
}

AUTH_USER_MODEL = "accounts.User"

AUTH_PASSWORD_VALIDATORS = [
    {"NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"},
    {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator", "OPTIONS": {"min_length": 8}},
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
]

LANGUAGE_CODE = "pt-br"
TIME_ZONE = "America/Sao_Paulo"
USE_I18N = True
USE_TZ = True

STATIC_URL = "static/"
STATIC_ROOT = BASE_DIR / "staticfiles"

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

# --- REST Framework ---------------------------------------------------
REST_FRAMEWORK = {
    "DEFAULT_AUTHENTICATION_CLASSES": (
        "rest_framework.authentication.SessionAuthentication",
    ),
    "DEFAULT_PERMISSION_CLASSES": ("rest_framework.permissions.IsAuthenticated",),
    "DEFAULT_SCHEMA_CLASS": "drf_spectacular.openapi.AutoSchema",
    "DEFAULT_PAGINATION_CLASS": "rest_framework.pagination.LimitOffsetPagination",
    "PAGE_SIZE": 50,
    "EXCEPTION_HANDLER": "common.exceptions.finez_exception_handler",
}

SPECTACULAR_SETTINGS = {
    "TITLE": "FinEz API",
    "DESCRIPTION": "API do FinEz — gestão financeira pessoal com Open Finance e bot de WhatsApp.",
    "VERSION": "1.0.0",
    "SERVE_INCLUDE_SCHEMA": False,
}

# --- Sessão / CSRF (cookie httpOnly, sem JWT em localStorage) ---------
SESSION_COOKIE_HTTPONLY = True
SESSION_COOKIE_SAMESITE = "Lax"
SESSION_COOKIE_SECURE = env.bool("SESSION_COOKIE_SECURE", default=not DEBUG)
CSRF_COOKIE_SAMESITE = "Lax"
CSRF_COOKIE_SECURE = env.bool("CSRF_COOKIE_SECURE", default=not DEBUG)

CORS_ALLOWED_ORIGINS = env.list("CORS_ALLOWED_ORIGINS", default=["http://localhost:5173"])
CORS_ALLOW_CREDENTIALS = True

# --- Cache (compartilhado — django_ratelimit exige um backend não-local) --
CACHES = {
    "default": {
        "BACKEND": "django.core.cache.backends.redis.RedisCache",
        "LOCATION": env("REDIS_URL", default="redis://localhost:6379/0"),
    }
}

# --- Celery -------------------------------------------------------------
from celery.schedules import crontab  # noqa: E402

CELERY_BROKER_URL = env("REDIS_URL", default="redis://localhost:6379/0")
CELERY_RESULT_BACKEND = env("REDIS_URL", default="redis://localhost:6379/0")
CELERY_TASK_SERIALIZER = "json"
CELERY_ACCEPT_CONTENT = ["json"]
CELERY_TIMEZONE = TIME_ZONE
CELERY_BEAT_SCHEDULE = {
    "weekly-whatsapp-summary": {
        "task": "whatsapp.tasks.send_weekly_summaries",
        # Domingo às 20h (horário de São Paulo)
        "schedule": crontab(hour=20, minute=0, day_of_week=0),
    },
    "weekly-lgpd-orphan-check": {
        "task": "accounts.tasks.check_orphan_records",
        "schedule": crontab(hour=4, minute=0, day_of_week=1),
    },
    "daily-subscription-charge-reminders": {
        "task": "subscriptions.tasks.remind_upcoming_charges",
        "schedule": crontab(hour=9, minute=0),
    },
    "monthly-budget-completion-badges": {
        "task": "budgets.tasks.check_budget_completions",
        "schedule": crontab(hour=9, minute=0, day_of_month=1),
    },
}

# --- Segredos / criptografia --------------------------------------------
FERNET_KEY = env("FERNET_KEY", default="")  # obrigatório em produção

# --- Integrações ---------------------------------------------------------
PLUGGY_CLIENT_ID = env("PLUGGY_CLIENT_ID", default="")
PLUGGY_CLIENT_SECRET = env("PLUGGY_CLIENT_SECRET", default="")
PLUGGY_BASE_URL = env("PLUGGY_BASE_URL", default="https://api.pluggy.ai")
PLUGGY_WEBHOOK_SECRET = env("PLUGGY_WEBHOOK_SECRET", default="")

BRAPI_TOKEN = env("BRAPI_TOKEN", default="")  # https://brapi.dev/dashboard — plano gratuito

WHATSAPP_ADAPTER_URL = env("WHATSAPP_ADAPTER_URL", default="http://whatsapp:3333")
WHATSAPP_ADAPTER_TOKEN = env("WHATSAPP_ADAPTER_TOKEN", default="")
WHATSAPP_WEBHOOK_SECRET = env("WHATSAPP_WEBHOOK_SECRET", default="")

LLM_PROVIDER = env("LLM_PROVIDER", default="")  # hoje só "anthropic" é suportado
LLM_API_KEY = env("LLM_API_KEY", default="")
LLM_MODEL = env("LLM_MODEL", default="claude-haiku-4-5-20251001")

FRONTEND_URL = env("FRONTEND_URL", default="http://localhost:5173")

# --- Sentry ----------------------------------------------------------------
SENTRY_DSN = env("SENTRY_DSN", default="")
if SENTRY_DSN:
    import sentry_sdk

    sentry_sdk.init(dsn=SENTRY_DSN, traces_sample_rate=0.1, send_default_pii=False)

# --- Logs estruturados -----------------------------------------------------
# Nunca logar amount_cents + description juntos, nem payloads completos de webhook.
LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "json": {
            "format": '{"level":"%(levelname)s","time":"%(asctime)s","logger":"%(name)s","message":"%(message)s"}'
        }
    },
    "handlers": {"console": {"class": "logging.StreamHandler", "formatter": "json"}},
    "root": {"handlers": ["console"], "level": env("LOG_LEVEL", default="INFO")},
}
