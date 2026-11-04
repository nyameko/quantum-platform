# Backend development and API testing

## Runtime and local installation

The backend is Django 6.1/DRF, PostgreSQL and Python **3.14** (`>=3.14,<3.15`); the frontend requires Node 24.x. Use isolated dependencies and disposable development credentials, not copied production environment files.

```sh
cd apps/user-api
python3.14 -m venv .venv
. .venv/bin/activate
python -m pip install -e .
python manage.py check
python manage.py test portal --settings=config.test_settings
```

To exercise migrations and full API behavior, configure local PostgreSQL in a private `.env`, review `config/settings.py`, and migrate only this disposable DB. A test runner passing mocks is not proof of the live Quantum Platform/ACP network, migration or Slurm gateway.

## API layout

`portal/api_urls.py` registers the available route suffixes; `config/urls.py` owns the root API prefixes. `identity_api.py` owns person, PI and programme operations; `access_keys_api.py` SSH/WireGuard public keys; `workbench_api.py` Jupyter launch; `execution_api.py` scheduler jobs; `agent_api.py` signed ACP proxy. Do not present proposed ACP terminal-pairing routes as implemented.

## API change checklist

1. Identify the authoritative owner/repository and model.
2. Add or change typed request/response validation and authorization; don't trust an email/UID/tenant field in a client body as identity.
3. Define method, HTTP codes, session/CSRF rules, scope, idempotency, concurrency and effects.
4. Cover happy path and negative cases: anonymous user, suspended account, foreign ownership UUID, wrong programme membership, replay, expired token, duplicate requests, unavailable backend.
5. Add migrations only when changing persisted schema; never edit existing released migration contents.
6. Update UI states for pending/denied/success, record audit and regression evidence.
7. Verify GitOps image promotion and live response separately from code CI.

## Source checks

Root frontend uses `npm ci`, `npm run check`, `npm run build`; Python tests use `python manage.py test portal --settings=config.test_settings`. Before reporting success check installed Python version, source branch, test database state and pipeline logs.

References: [API routes](https://github.com/nyameko/quantum-platform/blob/main/apps/user-api/portal/api_urls.py), [Python dependencies](https://github.com/nyameko/quantum-platform/blob/main/apps/user-api/pyproject.toml), [root Node scripts](https://github.com/nyameko/quantum-platform/blob/main/package.json), [workspace proxy authorization tests](https://github.com/nyameko/quantum-platform/blob/main/apps/user-api/portal/test_agent_workspace.py).