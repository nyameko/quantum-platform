# Quantum Platform User API

Django/DRF + PostgreSQL backend for the portal's account, authentication, research programme and resource orchestration contracts.

**Current source status (4 November 2026):** the original Phase 2 scaffold has progressed. The source tree includes account verification and MFA flows, identity/PI/programme administration, SSH/WireGuard public key registration, POSIX allocation, JupyterHub launch, Slurm execution records, and signed personal-agent proxy methods. These capabilities still require the correct deployed image, settings, migrations, accounts, providers and live acceptance tests. This README describes source features, **not** blanket production readiness.

## Local setup

```sh
cd apps/user-api
python -m venv .venv
. .venv/bin/activate
python -m pip install -e .
cp .env.example .env
# Configure a disposable development PostgreSQL database in .env.
python manage.py check
python manage.py migrate
python manage.py test portal --settings=config.test_settings
python manage.py runserver 127.0.0.1:8000
```

Never commit `.env`, tokens, private keys or production settings. Do not run `makemigrations` as part of routine environment setup; generate migrations only for reviewed model changes. Development health endpoint: `http://127.0.0.1:8000/api/v1/health/`; local admin: `http://127.0.0.1:8000/admin/` when appropriately configured.

See [wiki API map](../../docs/wiki/API-and-integration.md), [developer guide](../../docs/wiki/Developer-guide.md), [root quick start](../../docs/QUICK_START.md) and [route declarations](portal/api_urls.py).