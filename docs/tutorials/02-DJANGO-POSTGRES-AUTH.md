# Tutorial 2 — Django, PostgreSQL and Authentication

## 1. Objective

Add durable identity and application state without turning Astro into an application server.

The target architecture is:

```text
Astro browser UI
      │
      ▼
Django
      │
      ├── django-allauth
      ├── DRF
      └── domain logic
      │
      ▼
PostgreSQL
```

## 2. Why Django?

Django gives the project mature implementations of:

- users
- password hashing
- sessions
- CSRF protection
- administration
- forms
- migrations
- ORM
- security defaults

The project should not rebuild these primitives.

Django REST Framework provides the application-facing JSON API.

django-allauth provides the account lifecycle and later MFA/WebAuthn.

## 3. Why PostgreSQL?

Identity and research access are durable data.

They must survive:

- application restarts
- pod restarts
- frontend rebuilds
- browser changes
- future scaling of the API

PostgreSQL becomes the authoritative store for application state.

The browser is never the authoritative state store.

## 4. Local PostgreSQL

For development, PostgreSQL runs in Docker Compose and is bound only to loopback.

From:

```text
apps/user-api/
```

run:

```bash
docker compose up -d
```

The database is disposable development infrastructure. Production PostgreSQL belongs in Kubernetes with persistent Cinder-backed storage.

## 5. Python application

Create the environment:

```bash
cd apps/user-api
python -m venv .venv
source .venv/bin/activate
pip install -e .
```

Core dependencies are:

- Django 6.1
- django-allauth with `headless` and `mfa`
- Django REST Framework
- psycopg
- python-dotenv

Run:

```bash
python manage.py check
python manage.py migrate
```

## 6. Environment configuration

Development settings belong in `.env`, not Git.

Typical local values:

```dotenv
DJANGO_DEBUG=true
DJANGO_SECRET_KEY=development-only-secret
DJANGO_ALLOWED_HOSTS=localhost,127.0.0.1
DJANGO_CSRF_TRUSTED_ORIGINS=http://127.0.0.1:8000,http://127.0.0.1:4323
DJANGO_SESSION_COOKIE_SECURE=false
DJANGO_CSRF_COOKIE_SECURE=false

POSTGRES_DB=quantum_platform
POSTGRES_USER=quantum_platform
POSTGRES_PASSWORD=development-only-change-me
POSTGRES_HOST=127.0.0.1
POSTGRES_PORT=5432
```

Never commit the real production secret key or database password.

## 7. Database-backed health check

The backend exposes:

```text
GET /api/v1/health/
```

A useful health endpoint should prove more than "the Python process exists".

The current health endpoint checks the database with a simple query before returning success.

This becomes useful later for:

- Kubernetes readiness
- smoke tests
- monitoring
- deployment validation

## 8. Registration

The account lifecycle starts with registration.

django-allauth owns the credential workflow.

The project uses mandatory email verification:

```text
registration
    ↓
verification email
    ↓
email confirmed
    ↓
login permitted
```

Email verification is stored in allauth's email model. It is not equivalent to Django's `User.is_active`.

## 9. Email verification

In development the email backend prints messages to the console.

The verification URL is deliberately directed to Astro:

```text
http://127.0.0.1:4323/account/verify-email?key=...
```

Astro consumes the key and calls the allauth headless endpoint.

The query-string approach matters because the Astro User Portal remains a static build. We do not need a dynamic server route just to accept an arbitrary emailed token.

## 10. Login and sessions

The browser uses normal Django session cookies.

This was chosen instead of browser-stored JWTs.

Advantages:

- mature Django session behaviour
- server-side session invalidation
- no access token in localStorage
- normal CSRF protection
- simpler same-origin architecture

The browser flow is:

```text
POST /_allauth/browser/v1/auth/login
        ↓
Django validates credentials
        ↓
session cookie
        ↓
authenticated browser
```

## 11. CSRF

State-changing browser requests require CSRF protection.

The project exposes:

```text
GET /api/v1/csrf/
```

to establish a CSRF cookie, then sends the token back using:

```text
X-CSRFToken
```

The User Portal helper in:

```text
apps/users/src/lib/auth.ts
```

centralizes this behaviour.

## 12. Logout failure and why response checking matters

During development the portal temporarily ran on the wrong port.

The UI redirected after calling logout even when Django returned:

```text
403
```

The user *appeared* signed out, but the Django session still existed.

The fix was twofold:

1. make the User Portal own its expected port (`4323`);
2. check the logout response before redirecting.

This is an important security lesson:

> A client-side navigation event is not proof that a server-side security operation succeeded.

## 13. Browser Back / Forward cache

After logout, browsers may restore a cached page when the user presses Back.

The dashboard therefore revalidates the session on the `pageshow` event.

If the session is gone, it performs:

```text
window.location.replace('/login/')
```

The browser history is not a security boundary, but stale authenticated UI should still be corrected.

## 14. Password lifecycle

The project has tested:

- password change
- old password rejection
- new password login
- password reset flow

Password reset links are routed to the static Astro application, which then uses the allauth browser API.

## 15. Django Admin

Django Admin is intentionally not the polished user-facing interface.

It is an operator surface for:

- inspecting users
- approving platform-level workflows
- debugging state
- viewing audit events

This separation saves development time.

## 16. Student exercise

1. Start PostgreSQL.
2. Run migrations.
3. Start Django.
4. Create a user through signup.
5. copy the verification URL from the console.
6. verify the account.
7. log in through Astro.
8. inspect the Django session.
9. change the password.
10. log out.
11. prove the old password fails.

## 17. Acceptance criteria

```text
✓ PostgreSQL is reachable only where intended
✓ migrations apply
✓ /api/v1/health/ returns database=ok
✓ registration succeeds
✓ unverified account cannot complete normal login
✓ verification succeeds
✓ session login succeeds
✓ logout invalidates server session
✓ password change succeeds
✓ old password is rejected
✓ password reset succeeds
```
