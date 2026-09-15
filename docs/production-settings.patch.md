# Production settings changes

Apply these changes to `apps/user-api/config/settings.py` before production deployment.

## WhiteNoise

Immediately after Django `SecurityMiddleware`:

```python
MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "whitenoise.middleware.WhiteNoiseMiddleware",
    ...
]
```

Add:

```python
STATICFILES_STORAGE = "whitenoise.storage.CompressedManifestStaticFilesStorage"
```

## Frontend base URL

Replace hard-coded localhost values with:

```python
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
```

## Email backend

Replace the fixed development backend with:

```python
EMAIL_BACKEND = os.getenv(
    "DJANGO_EMAIL_BACKEND",
    "django.core.mail.backends.console.EmailBackend",
)

EMAIL_HOST = os.getenv("DJANGO_EMAIL_HOST", "")
EMAIL_PORT = int(os.getenv("DJANGO_EMAIL_PORT", "587"))
EMAIL_HOST_USER = os.getenv("DJANGO_EMAIL_HOST_USER", "")
EMAIL_HOST_PASSWORD = os.getenv("DJANGO_EMAIL_HOST_PASSWORD", "")
EMAIL_USE_TLS = (
    os.getenv("DJANGO_EMAIL_USE_TLS", "true").lower() == "true"
)
DEFAULT_FROM_EMAIL = os.getenv(
    "DJANGO_DEFAULT_FROM_EMAIL",
    "Quantum Platform <noreply@nyameko.com>",
)
```

Production secret values must be provided by Kubernetes, not committed to this repository.
