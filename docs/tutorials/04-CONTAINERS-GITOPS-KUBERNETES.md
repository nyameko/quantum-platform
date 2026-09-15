# Tutorial 4 — Containers, GitOps and Kubernetes Deployment

## 1. Objective

Move the working Phase 2 application from a developer workstation onto the real Kubernetes platform without moving infrastructure ownership into the application repository.

The production chain is:

```text
quantum-platform
    ↓
CI
    ↓
container images
    ↓
GHCR
    ↓
infra-hpc-qc-k8s
    ↓
Argo CD
    ↓
Kubernetes
    ↓
Traefik
    ↓
users
```

## 2. Two repositories, two responsibilities

### `quantum-platform`

Owns:

- application source
- unit/static checks
- application builds
- Dockerfiles
- image publication

Does not own:

- cluster credentials
- production passwords
- Cinder volumes
- ingress infrastructure
- Kubernetes lifecycle

### `infra-hpc-qc-k8s`

Owns:

- Kubernetes desired state
- Argo CD Applications
- persistent volumes
- production configuration
- secret delivery
- Traefik routes
- operations and monitoring

This boundary is intentional.

## 3. Argo CD is not a build system

Argo CD should not compile Astro or pip-install Django from Git on every sync.

Instead:

```text
source commit
   ↓
CI creates image
   ↓
registry stores immutable artifact
   ↓
infra repo references image
   ↓
Argo deploys it
```

This means a rollback is a Git change to a previous image tag.

## 4. Static Astro containers

Astro produces static files.

A multi-stage image can:

1. use Node.js to build;
2. copy `dist/`;
3. serve it from unprivileged Nginx.

Runtime does not require Node.js.

This keeps the production image small and simple.

## 5. Django container

Django needs a real production WSGI process.

The production image uses Gunicorn.

It must also provide static files used by:

- Django Admin
- django-allauth
- MFA/WebAuthn management screens

The deployment checkpoint uses WhiteNoise so `/static/` can be served directly by Django without introducing another shared static volume.

## 6. PostgreSQL

The Kubernetes database is:

```text
StatefulSet
   ↓
PersistentVolumeClaim
   ↓
default OpenStack Cinder StorageClass
   ↓
Cinder volume
```

The PVC must survive:

- pod deletion
- StatefulSet restart
- node rescheduling

Deleting the PVC is a destructive operation and should not be part of normal Argo reconciliation.

## 7. Database migrations

Schema migrations must run before a new API version expects the schema.

The GitOps deployment uses a migration Job in an earlier Argo sync wave than the API Deployment.

Conceptually:

```text
wave 0: PostgreSQL
wave 1: migration job
wave 2: applications
wave 3: ingress
```

This is safer than having every API replica race to run migrations.

## 8. Same-origin production routing

The development proxy must become ingress routing.

For:

```text
users.quantum.nyameko.com
```

Traefik routes backend paths to Django:

```text
/_allauth/*
/api/v1/*
/accounts/*
/admin/*
/static/*
```

All other paths go to the static User Portal.

The browser still sees one origin.

This preserves:

- session cookies
- CSRF
- verification links
- password reset links

## 9. Blog and Wiki

Blog and Wiki are straightforward:

```text
blog.nyameko.com
    ↓
Traefik
    ↓
blog Service
    ↓
static pod

wiki.quantum.nyameko.com
    ↓
Traefik
    ↓
wiki Service
    ↓
static pod
```

Neither requires PostgreSQL.

## 10. Secrets

Do not put plaintext secrets in either public repository.

Required secrets include:

```text
DJANGO_SECRET_KEY
POSTGRES_PASSWORD
```

A first integration can bootstrap a Kubernetes Secret out-of-band.

Longer-term secret management can use the platform's chosen SOPS/KSOPS or external secret mechanism.

The key rule is stable regardless of tool:

> Git may contain encrypted or referential secret material, never production plaintext.

## 11. Production Django values

Use:

```text
DJANGO_DEBUG=false
DJANGO_ALLOWED_HOSTS=users.quantum.nyameko.com
DJANGO_CSRF_TRUSTED_ORIGINS=https://users.quantum.nyameko.com
DJANGO_SESSION_COOKIE_SECURE=true
DJANGO_CSRF_COOKIE_SECURE=true
PORTAL_BASE_URL=https://users.quantum.nyameko.com
```

Django already understands the reverse-proxy HTTPS signal through:

```text
X-Forwarded-Proto
```

## 12. Health and readiness

Kubernetes should probe:

```text
/api/v1/health/
```

A pod should not receive user traffic until:

- Django can run;
- PostgreSQL is reachable.

Static sites can use `/`.

## 13. GHCR

The application repository publishes:

```text
ghcr.io/nyameko/quantum-platform-blog
ghcr.io/nyameko/quantum-platform-wiki
ghcr.io/nyameko/quantum-platform-users
ghcr.io/nyameko/quantum-platform-user-api
```

For production, prefer immutable tags:

```text
sha-abc1234
```

instead of:

```text
latest
```

A public repository can also expose its application images publicly so the cluster does not need a registry credential for these non-secret artifacts.

## 14. Argo CD Application

The infrastructure repository contains an Argo CD `Application` pointing at the Quantum Platform Kubernetes manifests.

Argo then provides:

- automated sync
- self-heal
- prune
- visible health state
- diff between Git and cluster

The desired workflow is:

```text
edit infra Git
    ↓
commit
    ↓
Argo notices
    ↓
Kubernetes reconciles
```

not:

```text
kubectl edit deployment
```

## 15. Deployment acceptance test

After Argo sync:

```bash
kubectl -n quantum-platform get pods
kubectl -n quantum-platform get svc
kubectl -n quantum-platform get pvc
kubectl -n quantum-platform get ingress
```

Verify PostgreSQL:

```text
pod Ready
PVC Bound
```

Verify API internally:

```bash
kubectl -n quantum-platform run curl-test \
  --rm -it \
  --restart=Never \
  --image=curlimages/curl \
  -- curl -fsS http://quantum-platform-user-api:8000/api/v1/health/
```

Then verify each hostname through the actual ingress path.

## 16. Persistence test

1. create a test user;
2. verify the user exists;
3. delete the PostgreSQL pod;
4. wait for StatefulSet recreation;
5. log in again.

If the account disappears, storage is not persistent and the deployment fails acceptance.

## 17. Rollback test

1. deploy image `sha-A`;
2. deploy `sha-B`;
3. verify behaviour;
4. change Git back to `sha-A`;
5. sync Argo;
6. verify workload rolled back.

This is the operational value of immutable artifacts plus GitOps.

## 18. Failure injection

Students should deliberately test:

- bad API image tag
- PostgreSQL unavailable
- wrong database password
- invalid hostname
- missing TLS secret
- failed migration
- broken readiness endpoint

The goal is to learn to answer:

```text
Is this a DNS problem?
Ingress problem?
Service problem?
Pod problem?
Application problem?
Database problem?
Secret problem?
```

## 19. Phase 2 production definition of done

```text
✓ CI builds four images
✓ images exist in registry
✓ Argo Application is Healthy/Synced
✓ all workloads Ready
✓ PostgreSQL PVC Bound
✓ Blog reachable
✓ Wiki reachable
✓ User Portal reachable
✓ same-origin Django paths work
✓ registration works
✓ email link points to production portal
✓ login + MFA works
✓ PI workflow persists
✓ PostgreSQL pod restart preserves state
✓ no production plaintext secret exists in Git
```
