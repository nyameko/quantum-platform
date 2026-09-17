# Administrative agent integration

The private administrator interface gains `/admin/agent-runs/` and a task detail
view. It reuses the existing Django/allauth staff login, checks the private host,
enforces CSRF for submission, and renders model output as escaped text. No public
portal/Jupyter chat widget is added in this phase.

Apply migration `portal.0003_agentprincipal` before deploying the new portal code.
It adds an immutable UUID for cross-service identity without changing names,
registration or programme approval. If another migration has taken this number,
rebase the migration dependency/name before applying. The separately discussed
identity/programme patch can coexist; do not replace its account changes with an
older full repository snapshot.

Settings are disabled by default with an empty `AGENT_CONTROL_PLANE_URL`. The
optional infra Kustomize component sets that internal URL, tenant and signing key
file. The browser never receives the key. The backend signs short-lived Ed25519
assertions from the currently authenticated staff user. Operational task data
remains in the control-plane PostgreSQL database, read through its API.

The user sees task/run status, evidence, a Hermes explanation, model/revision,
timestamps and failure history. A repeat submission after a transport failure
uses the same hidden idempotency UUID. Refresh retrieves history; it does not run
the diagnostic again. The service limits one active diagnostic per actor.

Run the isolated administrator tests with:

```sh
python manage.py test portal.test_agent_admin --settings=config.test_settings
python manage.py makemigrations --check --dry-run --settings=config.test_settings
```

These auth/template tests use SQLite only in explicit test settings. Production
settings remain PostgreSQL. The control-plane CI separately requires native
PostgreSQL for its data/locking suite.

For deployment and recovery see the infra Phase 1 runbook. Later user-facing chat,
research memory, searches, notebook assistance and conversations belong in
user/programme-scoped platform PostgreSQL tables, referenced by ACP runs. Do not
use the shared administrative Hermes profile as every researcher's personal agent.
