# Quantum Platform Tutorials

These tutorials reconstruct the Quantum Platform from first principles and explain the architectural choices that matter.

They are intended for:

- undergraduate and postgraduate students
- infrastructure students
- web/application students
- cybersecurity students
- HPC and quantum-computing students
- mentors and lecturers who need a common reference architecture

The goal is not just to reproduce a running website. The goal is to understand **why each layer exists, which layer owns which responsibility, and how the layers fit together without collapsing into one monolith**.

## Reading order

### Tutorial 1 — Astro platform and design system

[`01-ASTRO-PLATFORM.md`](01-ASTRO-PLATFORM.md)

Build the public web layer:

- npm workspaces
- Astro applications
- Blog / Wiki / User Portal
- shared UI package
- static output
- local development
- build validation

### Tutorial 2 — Django, PostgreSQL and account lifecycle

[`02-DJANGO-POSTGRES-AUTH.md`](02-DJANGO-POSTGRES-AUTH.md)

Build the stateful identity backend:

- Django
- PostgreSQL
- DRF
- django-allauth
- registration
- mandatory email verification
- sessions
- password change/reset
- headless browser API
- CSRF and same-origin design

### Tutorial 3 — MFA and research programme workflow

[`03-MFA-RESEARCH-WORKFLOWS.md`](03-MFA-RESEARCH-WORKFLOWS.md)

Extend authentication into research authorization:

- TOTP
- recovery codes
- WebAuthn/passkeys
- Person profile
- PI application
- ResearchProgramme
- ProgrammeMembership
- approval authorization
- AuditEvent
- SSH/WireGuard public-key model

### Tutorial 4 — Containers, GitOps and Kubernetes

[`04-CONTAINERS-GITOPS-KUBERNETES.md`](04-CONTAINERS-GITOPS-KUBERNETES.md)

Move from laptop development to the real cluster:

- immutable container images
- GHCR
- PostgreSQL persistence
- Kubernetes Services
- Traefik routing
- Argo CD
- health checks
- secrets boundary
- acceptance testing
- rollback model

---

## Teaching model

Each tutorial follows the same structure:

```text
concept
  ↓
architecture
  ↓
implementation
  ↓
validation
  ↓
failure modes
  ↓
discussion / extension
```

Students should not skip validation.

A service is not considered “deployed” merely because a manifest applied successfully. A complete exercise proves:

1. the intended path works;
2. an invalid path fails safely;
3. state survives where it is supposed to survive;
4. secrets do not appear in Git;
5. the application remains observable and debuggable.

## Suggested week-long activation

A strong five-day delivery is:

| Day | Focus |
| --- | --- |
| 1 | Astro, repository structure, UI packages, static builds |
| 2 | Django, PostgreSQL, API boundaries, sessions |
| 3 | MFA, WebAuthn, research identity and authorization |
| 4 | containers, registry, Kubernetes, Services and ingress |
| 5 | Argo CD deployment, failure injection, student demos and review |

Students can work in specialist teams while still sharing the same end-to-end platform.

## Definition of done for Phase 2

A student should be able to explain and demonstrate:

```text
Browser
  ↓
Astro
  ↓
Django session / CSRF
  ↓
allauth + domain API
  ↓
PostgreSQL
```

and then:

```text
Git push
  ↓
CI
  ↓
container registry
  ↓
infra-hpc-qc-k8s
  ↓
Argo CD
  ↓
Kubernetes
  ↓
Traefik
  ↓
working platform
```

That is the conceptual bridge between software development and research infrastructure engineering.
