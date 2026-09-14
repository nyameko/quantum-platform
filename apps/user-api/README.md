# Quantum Platform User API

Phase 2, iteration 1 establishes the Django/PostgreSQL backend boundary,
core research domain models, Django Admin, and a database-backed health API.

Authentication, registration, email verification, MFA/WebAuthn, PI approval
workflow, and credential provisioning are intentionally deferred.

## Local setup

```bash
cd apps/user-api
python3 -m venv .venv
source .venv/bin/activate
pip install -e .
cp .env.example .env
python manage.py makemigrations
python manage.py migrate
python manage.py createsuperuser
python manage.py runserver 127.0.0.1:8000
```

Health:
`curl http://127.0.0.1:8000/api/v1/health/`

Admin:
`http://127.0.0.1:8000/admin/`

Do not commit `.env` or production credentials.
