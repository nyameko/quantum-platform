import os
from pathlib import Path

from dotenv import load_dotenv


BASE_DIR = Path(__file__).resolve().parent.parent

# Load local development configuration.
# In production, Kubernetes should inject these values as environment
# variables / Secrets rather than mounting a .env file.
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
    # Django
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",

    # Authentication
    "allauth",
    "allauth.account",
    "allauth.headless",

    # API
    "rest_framework",

    # Quantum Platform domain
    "portal",
]


# ---------------------------------------------------------------------------
# Middleware
# ---------------------------------------------------------------------------

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",

    # django-allauth
    "allauth.account.middleware.AccountMiddleware",
]


# ---------------------------------------------------------------------------
# URLs
# ---------------------------------------------------------------------------

ROOT_URLCONF = "config.urls"


# ---------------------------------------------------------------------------
# Templates
# ---------------------------------------------------------------------------

# Required by Django Admin and django-allauth browser views.
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


# ---------------------------------------------------------------------------
# Application servers
# ---------------------------------------------------------------------------

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
    # Keep Django's normal backend available for the admin and compatibility.
    "django.contrib.auth.backends.ModelBackend",

    # django-allauth authentication.
    "allauth.account.auth_backends.AuthenticationBackend",
]


# Use email as the primary public authentication identity.
ACCOUNT_LOGIN_METHODS = {
    "email",
}

# Registration currently requires:
#   - email
#   - password
#   - password confirmation
#
# Person / PI / programme information is deliberately NOT collected here.
# That belongs to the later registration workflow.
ACCOUNT_SIGNUP_FIELDS = [
    "email*",
    "password1*",
    "password2*",
]


# ---------------------------------------------------------------------------
# Email verification
# ---------------------------------------------------------------------------

# Users must verify their email before normal authentication.
ACCOUNT_EMAIL_VERIFICATION = "mandatory"

# Do not automatically authenticate a user merely because they clicked
# the email confirmation link.
ACCOUNT_LOGIN_ON_EMAIL_CONFIRMATION = False

# Confirmation links are valid for three days.
ACCOUNT_EMAIL_CONFIRMATION_EXPIRE_DAYS = 3

# Avoid leaking account existence through authentication-related responses.
ACCOUNT_PREVENT_ENUMERATION = True


# ---------------------------------------------------------------------------
# Login / logout / sessions
# ---------------------------------------------------------------------------

# Keep login sessions bounded.
ACCOUNT_LOGIN_TIMEOUT = 900

# Logout should not occur simply by visiting a GET URL.
ACCOUNT_LOGOUT_ON_GET = False

LOGIN_URL = "/accounts/login/"
LOGIN_REDIRECT_URL = "/"
LOGOUT_REDIRECT_URL = "/accounts/login/"


# ---------------------------------------------------------------------------
# Password reset
# ---------------------------------------------------------------------------

# Use the normal email-link password reset workflow for this iteration.
ACCOUNT_PASSWORD_RESET_BY_CODE_ENABLED = False


# ---------------------------------------------------------------------------
# Email backend
# ---------------------------------------------------------------------------

# Local development:
# verification and password-reset emails are printed to the Django terminal.
#
# Production will use a real transactional mail service.
EMAIL_BACKEND = "django.core.mail.backends.console.EmailBackend"

ACCOUNT_EMAIL_SUBJECT_PREFIX = "[Quantum Platform] "


# ---------------------------------------------------------------------------
# django-allauth headless frontend integration
# ---------------------------------------------------------------------------

# These are the future Astro User Portal destinations.
#
# The Django backend owns authentication state; the Astro application will
# consume the allauth headless API once the authentication flows are proven.
HEADLESS_FRONTEND_URLS = {
    "account_confirm_email": (
        "http://127.0.0.1:4323/account/verify-email/{key}"
    ),
    "account_reset_password": (
        "http://127.0.0.1:4323/account/password/reset"
    ),
    "account_reset_password_from_key": (
        "http://127.0.0.1:4323/account/password/reset/key/{key}"
    ),
    "account_signup": (
        "http://127.0.0.1:4323/account/signup"
    ),
}


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

# The production deployment will sit behind HAProxy / Traefik.
# This allows Django to understand the original HTTPS request.
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


# ---------------------------------------------------------------------------
# Django defaults
# ---------------------------------------------------------------------------

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"
