# API and integration contracts

This page is **a route map, not a guarantee of deployed endpoints**. Review [Django `portal/api_urls.py`](https://github.com/nyameko/quantum-platform/blob/main/apps/user-api/portal/api_urls.py) and [top-level URL config](https://github.com/nyameko/quantum-platform/blob/main/apps/user-api/config/urls.py) for exact prefixes and HTTP method permissions; use a signed-in browser session and CSRF protections where required.

| Domain | Representative route suffix | Authority |
|---|---|---|
| Identity | `me/`, `profile/`, `programmes/`, `memberships/` | Quantum Platform |
| Credential registration | `ssh-keys/`, `wireguard-keys/` | Quantum Platform; infrastructure reconciles |
| Workbench | `workbench/`, `workbench/launch/`, `workbench/stop/` | Platform API + JupyterHub |
| Durable jobs | `executions/`, `executions/cpu-smoke/`, `executions/bell-aer/` | ExecutionRecord + Slurm gateway |
| Agent | `agent/projects/`, `agent/conversations/`, `agent/runs/<id>/` | Signed proxy to ACP |
| Agent memory | `agent/memories/`, per-memory approve/revoke | ACP canonical state |
| Programme rooms | `agent/programmes/<id>/conversations/` | Membership check + ACP |
| Agent profile | `agent/profile/` | ACP portable preferences |

Never forward the user's browser cookie as an ACP assertion or derive trust from a client-supplied `tenant` or `user_id`. Server-side Quantum Platform signs short-lived scoped assertions; ACP validates subject, tenant, audience, signature and permissions. A scientific Slurm job ID, platform ExecutionRecord UUID and ACP task/run UUID must remain separate identifiers.

### Error handling for clients

Handle 401/403 distinctly from 404, 409 (not yet provisioned/conflict), 422 (invalid request) and 5xx (service unavailable). Avoid retry loops that duplicate expensive jobs; honor idempotency where supported. Do not scrape HTML or guess undocumented API actions from UI labels. Prefer audited official endpoints and stable versioned contracts.