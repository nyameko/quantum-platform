# Developer guide

## Stack and directories

`apps/users` and `apps/blog` are Astro/TypeScript user-facing applications; `apps/user-api` is Django/DRF/PostgreSQL; `packages/` holds shared code; `docs/` holds architecture and lessons. Node requirement is **24.x** per root `package.json`; use the Python requirement in `apps/user-api/pyproject.toml`, not an arbitrary system Python.

## Local application checks

```sh
npm ci
npm run check
npm run build
cd apps/user-api
python -m venv .venv
. .venv/bin/activate
python -m pip install -e .
python manage.py check
python manage.py test portal --settings=config.test_settings
```

Start a local PostgreSQL instance configured with **development-only** credentials before migration-based integration testing; the basic commands above do not substitute for database tests. For onboarding follow [`docs/QUICK_START.md`](https://github.com/nyameko/quantum-platform/blob/main/docs/QUICK_START.md). Never run `makemigrations` against production or commit sample secrets.

## Implementing a feature

Identify the authoritative repository and domain object first. UI code should not recreate ACP's memory store or Slurm scheduling logic. Add server-side permission tests, ownership-negative tests and browser behavior tests. Use migrations for schema changes and ensure forwards/rollback compatibility. API changes require documented methods, allowed roles, CSRF/session requirements, error responses and version behavior.

Before PR submission, inspect formatting checks, tests, frontend build, status of affected cross-repo manifests, and any necessary pinned image-digest promotion. A feature merged into source may not yet be deployed.

References: [contribution policy](https://github.com/nyameko/quantum-platform/blob/main/CONTRIBUTING.md), [Django test config](https://github.com/nyameko/quantum-platform/blob/main/apps/user-api/config/test_settings.py), [API route map](https://github.com/nyameko/quantum-platform/blob/main/apps/user-api/portal/api_urls.py).