import os
from pathlib import Path

from dotenv import load_dotenv


BASE_DIR = Path(__file__).resolve().parent.parent
load_dotenv(BASE_DIR / ".env")


# ---------------------------------------------------------------------------
# Core Django configuration
# ---------------------------------------------------------------------------

SECRET_KEY = os.getenv(
    "DJANGO_SECRET_KEY",
    "development-only-change-me",
)

DEBUG = os.getenv(
    "DJANGO_DEBUG",
    "false",
).lower() == "true"

ALLOWED_HOSTS = [
    host.strip()
    for host in os.getenv(
        "DJANGO_ALLOWED_HOSTS",
        "localhost,127.0.0.1",
    ).split(",")
    if host.strip()
]

CSRF_TRUSTED_ORIGINS = [
    origin.strip()
    for origin in os.getenv(
        "DJANGO_CSRF_TRUSTED_ORIGINS",
        "",
    ).split(",")
    if origin.strip()
]


# ---------------------------------------------------------------------------
# Applications
# ---------------------------------------------------------------------------

INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.humanize",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",

    "allauth",
    "allauth.account",
    "allauth.headless",
    "allauth.mfa",

    "rest_framework",

    "portal",
]


# ---------------------------------------------------------------------------
# Middleware
# ---------------------------------------------------------------------------

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "whitenoise.middleware.WhiteNoiseMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
    "allauth.account.middleware.AccountMiddleware",
]


ROOT_URLCONF = "config.urls"


# ---------------------------------------------------------------------------
# Templates
# ---------------------------------------------------------------------------

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [
            BASE_DIR / "templates",
        ],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    },
]


WSGI_APPLICATION = "config.wsgi.application"
ASGI_APPLICATION = "config.asgi.application"


# ---------------------------------------------------------------------------
# Database
# ---------------------------------------------------------------------------

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.postgresql",
        "NAME": os.getenv(
            "POSTGRES_DB",
            "quantum_platform",
        ),
        "USER": os.getenv(
            "POSTGRES_USER",
            "quantum_platform",
        ),
        "PASSWORD": os.getenv(
            "POSTGRES_PASSWORD",
            "",
        ),
        "HOST": os.getenv(
            "POSTGRES_HOST",
            "127.0.0.1",
        ),
        "PORT": os.getenv(
            "POSTGRES_PORT",
            "5432",
        ),
        "CONN_MAX_AGE": int(
            os.getenv(
                "POSTGRES_CONN_MAX_AGE",
                "60",
            )
        ),
    }
}


# ---------------------------------------------------------------------------
# Authentication
# ---------------------------------------------------------------------------

AUTHENTICATION_BACKENDS = [
    "django.contrib.auth.backends.ModelBackend",
    "allauth.account.auth_backends.AuthenticationBackend",
]

ACCOUNT_LOGIN_METHODS = {
    "email",
}

ACCOUNT_SIGNUP_FIELDS = [
    "email*",
    "password1*",
    "password2*",
]

ACCOUNT_EMAIL_VERIFICATION = "mandatory"
ACCOUNT_LOGIN_ON_EMAIL_CONFIRMATION = False
ACCOUNT_EMAIL_CONFIRMATION_EXPIRE_DAYS = 3
ACCOUNT_PREVENT_ENUMERATION = True

ACCOUNT_LOGIN_TIMEOUT = 900
ACCOUNT_LOGOUT_ON_GET = False

LOGIN_URL = "/accounts/login/"
LOGIN_REDIRECT_URL = "/"
LOGOUT_REDIRECT_URL = "/accounts/login/"

ACCOUNT_PASSWORD_RESET_BY_CODE_ENABLED = False


# ---------------------------------------------------------------------------
# Email
# ---------------------------------------------------------------------------

EMAIL_BACKEND = os.getenv(
    "DJANGO_EMAIL_BACKEND",
    "django.core.mail.backends.console.EmailBackend",
)

EMAIL_HOST = os.getenv("DJANGO_EMAIL_HOST", "")
EMAIL_PORT = int(os.getenv("DJANGO_EMAIL_PORT", "587"))
EMAIL_HOST_USER = os.getenv("DJANGO_EMAIL_HOST_USER", "")
EMAIL_HOST_PASSWORD = os.getenv("DJANGO_EMAIL_HOST_PASSWORD", "")
EMAIL_USE_TLS = (
    os.getenv(
        "DJANGO_EMAIL_USE_TLS",
        "true",
    ).lower() == "true"
)

DEFAULT_FROM_EMAIL = os.getenv(
    "DJANGO_DEFAULT_FROM_EMAIL",
    "Quantum Platform <noreply@nyameko.com>",
)

ACCOUNT_EMAIL_SUBJECT_PREFIX = "[Quantum Platform] "


# ---------------------------------------------------------------------------
# django-allauth headless frontend integration
# ---------------------------------------------------------------------------

PORTAL_BASE_URL = os.getenv(
    "PORTAL_BASE_URL",
    "http://127.0.0.1:4323",
).rstrip("/")

HEADLESS_FRONTEND_URLS = {
    "account_confirm_email": (
        f"{PORTAL_BASE_URL}/account/verify-email?key={{key}}"
    ),
    "account_reset_password": (
        f"{PORTAL_BASE_URL}/account/password/reset"
    ),
    "account_reset_password_from_key": (
        f"{PORTAL_BASE_URL}/account/password/reset/key?key={{key}}"
    ),
    "account_signup": (
        f"{PORTAL_BASE_URL}/account/signup"
    ),
}


# ---------------------------------------------------------------------------
# Multi-factor authentication
# ---------------------------------------------------------------------------

MFA_SUPPORTED_TYPES = [
    "totp",
    "webauthn",
    "recovery_codes",
]

MFA_PASSKEY_LOGIN_ENABLED = True

# Development only. Must be False in production.
MFA_WEBAUTHN_ALLOW_INSECURE_ORIGIN = DEBUG

MFA_TOTP_ISSUER = "Quantum Platform"
MFA_TOTP_PERIOD = 30
MFA_TOTP_DIGITS = 6
MFA_TOTP_TOLERANCE = 0

MFA_RECOVERY_CODE_COUNT = 10
MFA_RECOVERY_CODE_DIGITS = 8
MFA_RECOVERY_CODES_SHOW_ONCE = True

MFA_TRUST_ENABLED = False


# ---------------------------------------------------------------------------
# Django REST Framework
# ---------------------------------------------------------------------------

REST_FRAMEWORK = {
    "DEFAULT_RENDERER_CLASSES": [
        "rest_framework.renderers.JSONRenderer",
    ],
    "DEFAULT_PERMISSION_CLASSES": [
        "rest_framework.permissions.AllowAny",
    ],
}


# ---------------------------------------------------------------------------
# Security / reverse proxy
# ---------------------------------------------------------------------------

SECURE_PROXY_SSL_HEADER = (
    "HTTP_X_FORWARDED_PROTO",
    "https",
)

SESSION_COOKIE_SECURE = (
    os.getenv(
        "DJANGO_SESSION_COOKIE_SECURE",
        "false",
    ).lower() == "true"
)

CSRF_COOKIE_SECURE = (
    os.getenv(
        "DJANGO_CSRF_COOKIE_SECURE",
        "false",
    ).lower() == "true"
)


# ---------------------------------------------------------------------------
# Internationalisation
# ---------------------------------------------------------------------------

LANGUAGE_CODE = "en-us"
TIME_ZONE = "Africa/Johannesburg"
USE_I18N = True
USE_TZ = True


# ---------------------------------------------------------------------------
# Static files
# ---------------------------------------------------------------------------

STATIC_URL = "/static/"
STATIC_ROOT = BASE_DIR / "staticfiles"

STORAGES = {
    "default": {
        "BACKEND": "django.core.files.storage.FileSystemStorage",
    },
    "staticfiles": {
        "BACKEND": "whitenoise.storage.CompressedManifestStaticFilesStorage",
    },
}


DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

# Internal administrative agent service. Empty URL keeps the integration disabled.
AGENT_CONTROL_PLANE_URL = os.getenv("AGENT_CONTROL_PLANE_URL", "").rstrip("/")
AGENT_CONTROL_PLANE_SIGNING_KEY_FILE = os.getenv("AGENT_CONTROL_PLANE_SIGNING_KEY_FILE", "")
AGENT_CONTROL_PLANE_TENANT = os.getenv("AGENT_CONTROL_PLANE_TENANT", "nyameko")
AGENT_ADMIN_HOST = os.getenv("AGENT_ADMIN_HOST", "admin.quantum.nyameko.com")
