# Quantum Platform

Public web, identity, and research-access platform for quantum-centric computing.

`quantum-platform` is the application layer of a larger hybrid HPC / Kubernetes / quantum-computing research environment. It provides the public-facing web applications, researcher identity workflows, and the user portal that will progressively connect people to infrastructure services such as JupyterHub, Slurm, GPU systems, and quantum-computing resources.

The repository is intentionally public. **Secrets, production credentials, private keys, persistent production data, and infrastructure state do not belong here.** Production deployment and cluster lifecycle are owned by [`infra-hpc-qc-k8s`](https://github.com/nyameko/infra-hpc-qc-k8s).

---

## Current status — Phase 2 MVP

Phase 2 establishes the first complete vertical slice from a public web interface to authenticated research identity and programme approval.

Working today:

- Astro monorepo with a shared design system
- public Blog
- ~public Wiki~ (removed)
- authenticated User Portal
- Django backend API
- PostgreSQL-backed application state
- registration and email verification
- password login, logout, password change, and password reset
- Django session authentication
- TOTP MFA
- recovery codes
- WebAuthn/passkey foundation
- researcher profiles
- Principal Investigator applications
- research programme creation through approval
- research programme membership requests
- PI-controlled membership approval/rejection
- audit events for approval-sensitive workflows
- static Astro production builds
- health API suitable for Kubernetes probes
- development proxy keeping Astro and Django on one browser origin

The Phase 2 MVP is intentionally small enough to stress-test with students before deeper automation is added.

---

## Platform surfaces

| Surface | Purpose | Technology | Target hostname |
| --- | --- | --- | --- |
| Blog | Research writing, public technical documentation & announcements, project notes | Astro | `blog.nyameko.com` |
| User Portal | Research identity, security, programmes, access workflow | Astro | `users.quantum.nyameko.com` |
| User API | Authentication and platform business logic | Django + DRF + allauth | same origin as User Portal |
| Database | Identity and application state | PostgreSQL | internal Kubernetes service only |

The User Portal is deliberately split into a static presentation layer and a stateful backend. Astro owns the experience; Django owns identity, authorization, business rules, and durable state.

---

## Architecture

```text
                              Internet / private DNS
                                      │
                 ┌────────────────────┼────────────────────┐
                 │                    │                    │
                 ▼                    ▼                    ▼
        blog.nyameko.com   wiki.quantum.nyameko.com  users.quantum.nyameko.com
                 │                    │                    │
                 ▼                    ▼            ┌───────┴─────────┐
              Astro                Astro           │                 │
             static               static           ▼                 ▼
                                                   Astro          Django
                                                   static        User API
                                                                  │
                                                     ┌────────────┼────────────┐
                                                     │            │            │
                                                     ▼            ▼            ▼
                                                  allauth       DRF API     Django Admin
                                                     │            │
                                                     └──────┬─────┘
                                                            ▼
                                                        PostgreSQL
```

In local development, the User Portal runs on `127.0.0.1:4323` and Vite proxies:

```text
/_allauth/*  ──► 127.0.0.1:8000
/api/v1/*    ──► 127.0.0.1:8000
/accounts/*  ──► 127.0.0.1:8000
```

In Kubernetes, Traefik provides the same split at `users.quantum.nyameko.com`. This preserves normal Django session cookies and CSRF protection without adding browser-stored JWTs or cross-origin complexity.

---

## Repository layout

```text
quantum-platform/
├── .github/
│   └── workflows/
│       ├── ci.yml
│       └── images.yml
│
├── apps/
│   ├── blog/
│   │   ├── src/
│   │   ├── astro.config.mjs
│   │   └── Dockerfile
│   │
│   ├── users/
│   │   ├── src/
│   │   │   ├── lib/auth.ts
│   │   │   └── pages/
│   │   ├── astro.config.mjs
│   │   └── Dockerfile
│   │
│   └── user-api/
│       ├── config/
│       ├── portal/
│       ├── templates/
│       ├── manage.py
│       ├── pyproject.toml
│       └── Dockerfile
│
├── packages/
│   ├── content/
│   └── ui/
│
├── docs/
│   ├── architecture/
│   └── tutorials/
│       ├── README.md
│       ├── 01-ASTRO-PLATFORM.md
│       ├── 02-DJANGO-POSTGRES-AUTH.md
│       ├── 03-MFA-RESEARCH-WORKFLOWS.md
│       └── 04-CONTAINERS-GITOPS-KUBERNETES.md
│
├── package.json
└── README.md
```

---

## Separation of concerns

The project deliberately keeps responsibilities narrow.

```text
Astro
  └── presentation, navigation, static content, browser interaction

Django
  └── identity, authentication, authorization, workflow rules, APIs

django-allauth
  └── account lifecycle, email verification, MFA, WebAuthn/passkeys

PostgreSQL
  └── durable application and identity state

Kubernetes
  └── workload scheduling, service discovery, persistence attachment

Argo CD
  └── desired deployment state

Traefik
  └── HTTP routing and same-origin application ingress

infra-hpc-qc-k8s
  └── production manifests, secrets integration, DNS/ingress, storage, operations
```

This separation is central to the teaching value of the project. Students can work on UI, identity, APIs, Kubernetes, security, HPC, or research applications without every contributor owning every layer.

---

## Identity and research model

The Django backend uses the standard Django `User` as the authentication identity and adds research-domain objects around it.

```text
User
 │
 └── Person
      ├── SSHKey
      ├── WireGuardKey
      │
      ├── PIApplication
      │      │
      │      └── approved ──► ResearchProgramme
      │                           │
      │                           └── PI membership
      │
      └── ProgrammeMembership
             ├── PI
             ├── researcher
             └── programme admin
```

Core models:

- `Person`
- `ResearchProgramme`
- `ProgrammeMembership`
- `PIApplication`
- `AuditEvent`
- `SSHKey`
- `WireGuardKey`

SSH and WireGuard models intentionally store **public keys only**. Private credentials belong to the user and must never be stored by this application.

---

## Authentication and security

The current account lifecycle is:

```text
registration
    ↓
mandatory email verification
    ↓
password authentication
    ↓
session
    ↓
optional / policy-driven MFA
    ├── TOTP
    ├── WebAuthn / passkeys
    └── recovery codes
```

Important principles:

1. Django sessions remain the browser authentication mechanism.
2. CSRF protection remains enabled.
3. MFA implementation is delegated to `django-allauth`; the project does not invent its own cryptography.
4. Authorization decisions happen server-side.
5. Browser input never decides whether a user is a PI, administrator, or approver.
6. Audit-sensitive domain operations create immutable `AuditEvent` records.
7. Production cookies must be secure and HTTPS-only.

The student-facing Astro UI is not a security boundary. A hidden button or route guard improves UX, but Django remains authoritative.

---

## Research programme workflow

### New PI

```text
verified user
    ↓
complete Person profile
    ↓
submit PIApplication
    ↓
status = pending
    ↓
platform administrator review
    ↓
approved
    ├── ResearchProgramme(status=active)
    └── ProgrammeMembership(role=pi, status=approved)
```

### Existing programme

```text
verified user
    ↓
complete Person profile
    ↓
select active ResearchProgramme
    ↓
ProgrammeMembership(status=pending)
    ↓
programme PI reviews request
    ↓
approved / rejected
```

The current MVP uses Django Admin for platform-level PI approval. This is intentional: administrative workflow can remain plain while the researcher-facing portal is refined.

---

## API surface

Current domain endpoints include:

```text
GET  /api/v1/health/
GET  /api/v1/csrf/
GET  /api/v1/me/

PUT  /api/v1/profile/

GET  /api/v1/programmes/

GET  /api/v1/pi-applications/
POST /api/v1/pi-applications/submit/
POST /api/v1/pi-applications/<id>/approve/
POST /api/v1/pi-applications/<id>/reject/

GET  /api/v1/memberships/
POST /api/v1/programmes/<id>/membership/
GET  /api/v1/programmes/<id>/membership-requests/
POST /api/v1/memberships/<id>/approve/
POST /api/v1/memberships/<id>/reject/
```

Authentication endpoints are provided through django-allauth headless under:

```text
/_allauth/browser/v1/*
```

---

## Local development

### Requirements

- Node.js 22+
- npm
- Python 3.12+ (the current development environment uses Python 3.14)
- Docker
- Docker Compose

Clone and install frontend dependencies:

```bash
git clone https://github.com/nyameko/quantum-platform.git
cd quantum-platform
npm install
```

Validate all Astro workspaces:

```bash
npm run check
npm run build
```

Run individual applications:

```bash
npm run dev:blog
npm run dev:users
```

The User Portal is fixed to:

```text
http://127.0.0.1:4323/
```

### User API

Create the Python environment:

```bash
cd apps/user-api

python -m venv .venv
source .venv/bin/activate

pip install -e .
```

Create a development environment file from `.env.example`, then start PostgreSQL:

```bash
docker compose up -d
```

Run migrations:

```bash
python manage.py check
python manage.py migrate
```

Run Django:

```bash
python manage.py runserver 127.0.0.1:8000
```

For local allauth static assets and WebAuthn development:

```dotenv
DJANGO_DEBUG=true
```

Do not use the Django development server in production.

---

## Local acceptance test

A useful Phase 2 smoke test is:

```text
1. Create account
2. Receive console verification email
3. Verify email through Astro
4. Sign in
5. Complete MFA challenge
6. Open dashboard
7. Edit profile
8. Submit PI application
9. Approve PI application as platform admin
10. Confirm active ResearchProgramme and approved PI membership
11. Sign out
12. Confirm browser Back cannot restore authenticated access
```

Backend checks:

```bash
python manage.py check
python manage.py makemigrations --check
python manage.py migrate
```

Frontend checks:

```bash
npm run check
npm run build
```

---

## Production deployment model

The public application repository builds container images. The infrastructure repository decides where and how those images run.

```text
quantum-platform
     │
     ├── CI tests Astro
     ├── builds container images
     └── publishes images to GHCR
               │
               ▼
         ghcr.io/nyameko/*
               │
               ▼
infra-hpc-qc-k8s
     │
     ├── pins image versions
     ├── defines PostgreSQL PVC/stateful workload
     ├── defines Deployments + Services
     ├── defines Traefik ingress
     └── Argo CD reconciles Kubernetes
               │
               ▼
          Kubernetes cluster
```

The initial production namespace is:

```text
quantum-platform
```

The expected Kubernetes services are:

```text
quantum-platform-blog
quantum-platform-users
quantum-platform-user-api
quantum-platform-postgres
```

PostgreSQL must use persistent Cinder-backed storage. The database is never exposed through ingress.

---

## Production routing

Traefik should route:

```text
blog.nyameko.com
  /                   → quantum-platform-blog

users.quantum.nyameko.com
  /_allauth/*          → quantum-platform-user-api
  /api/v1/*            → quantum-platform-user-api
  /accounts/*          → quantum-platform-user-api
  /admin/*             → quantum-platform-user-api
  /static/*            → quantum-platform-user-api
  everything else      → quantum-platform-users
```

This same-origin split is deliberate and should be preserved.

---

## Production configuration

At minimum the Django deployment needs:

```text
DJANGO_DEBUG=false
DJANGO_SECRET_KEY=<secret>
DJANGO_ALLOWED_HOSTS=users.quantum.nyameko.com
DJANGO_CSRF_TRUSTED_ORIGINS=https://users.quantum.nyameko.com
DJANGO_SESSION_COOKIE_SECURE=true
DJANGO_CSRF_COOKIE_SECURE=true

PORTAL_BASE_URL=https://users.quantum.nyameko.com

POSTGRES_DB=quantum_platform
POSTGRES_USER=quantum_platform
POSTGRES_PASSWORD=<secret>
POSTGRES_HOST=quantum-platform-postgres
POSTGRES_PORT=5432
```

SMTP can be enabled through environment variables when real user email delivery is required. Until then, the console backend remains useful for controlled integration testing.

---

## CI/CD contract

The intended split is:

```text
application CI
  quantum-platform
      ↓
  check + build + container image
      ↓
  immutable image tag

deployment CD
  infra-hpc-qc-k8s
      ↓
  image tag in Git
      ↓
  Argo CD
      ↓
  Kubernetes
```

Argo CD does **not** build application images. It reconciles deployment state from Git.

For serious environments, prefer immutable `sha-*` image tags in the infrastructure repository rather than mutable `latest` tags.

---

## Documentation

Start here:

- [`docs/tutorials/README.md`](docs/tutorials/README.md) — teaching path and learning objectives
- [`docs/tutorials/01-ASTRO-PLATFORM.md`](docs/tutorials/01-ASTRO-PLATFORM.md) — Astro monorepo and design system
- [`docs/tutorials/02-DJANGO-POSTGRES-AUTH.md`](docs/tutorials/02-DJANGO-POSTGRES-AUTH.md) — Django, PostgreSQL, sessions, email and passwords
- [`docs/tutorials/03-MFA-RESEARCH-WORKFLOWS.md`](docs/tutorials/03-MFA-RESEARCH-WORKFLOWS.md) — MFA, research identity, PI/membership workflows and auditing
- [`docs/tutorials/04-CONTAINERS-GITOPS-KUBERNETES.md`](docs/tutorials/04-CONTAINERS-GITOPS-KUBERNETES.md) — container images and the handoff to Argo CD/Kubernetes

---

## Roadmap

Phase 1 — public web platform:

- [x] Astro workspace
- [x] shared visual system
- [x] Blog
- [x] User Portal shell

Phase 2 — identity and research workflow:

- [x] Django backend
- [x] PostgreSQL
- [x] registration / verification / sessions
- [x] password lifecycle
- [x] MFA and recovery
- [x] WebAuthn/passkey foundation
- [x] researcher profile
- [x] PI applications
- [x] programme membership approval
- [x] audit trail
- [x] Astro integration
- [x] production container/GitOps handoff

Later platform phases live primarily in `infra-hpc-qc-k8s`:

- security telemetry
- Slurm integration
- JupyterHub
- Hermes / Heretic
- resource allocation and accounting
- researcher access provisioning
- hybrid HPC–QC applications

---

## Design principles

1. **Public source, private secrets.**
2. **Static where possible, stateful only where necessary.**
3. **Django is authoritative for identity and authorization.**
4. **PostgreSQL is durable state, not a browser concern.**
5. **GitOps owns production desired state.**
6. **Infrastructure deployment belongs in `infra-hpc-qc-k8s`.**
7. **Private credentials are never collected by the portal.**
8. **Real failures and acceptance tests are teaching material.**
9. **The MVP should be stress-tested before it is over-engineered.**
10. **Research infrastructure must remain auditable and least-privileged.**

---

## License

MIT.

<!-- identity-programme-doc -->
## Identity and programme authorization

Quantum Platform allocates immutable infrastructure usernames at registration
and uses approved programme membership as the future resource-authorization
boundary. This is intentionally separate from the Agent Control Plane
principal/task identity and from scientific workflow provenance.

See [Identity and programme authorization](docs/identity-programmes.md).
