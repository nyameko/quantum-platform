# Quantum Platform Quick Start

This guide is the shortest path to understanding and validating the current Quantum Platform.

## What this repository owns

`quantum-platform` owns the user-facing application and research-access control plane:

- registration, authentication and MFA;
- Person/profile and programme workflows;
- SSH/WireGuard public-key registration;
- POSIX identity metadata and allocator;
- Jupyter workbench lifecycle;
- execution offerings and `ExecutionRecord`;
- the browser experience for research users.

Infrastructure deployment remains in `infra-hpc-qc-k8s`.
Scientific runners remain in `quantum-workflows`.
Persistent agent state/orchestration belongs in `agent-control-plane`.

## Current M3 vertical slice

The deployed path is:

```text
User
 ↓
Quantum Platform
 ↓
JupyterHub / KubeSpawner
 ↓
shared /home/research/<user>
 ↓
Execution API
 ↓
restricted Slurm gateway
 ↓
Slurm
 ↓
quantum-workflows
 ↓
durable run + provenance
```

The reference cpu-smoke completed successfully as Slurm job 15 with exit code `0:0`.

## Local development

Frontend:

```bash
npm install
npm run check
npm run build
```

User API:

```bash
cd apps/user-api
python -m venv .venv
source .venv/bin/activate
python -m pip install -e .
python manage.py check
python manage.py migrate
python manage.py test portal --settings=config.test_settings
```

## Production validation

On the Kubernetes control-plane host:

```bash
kubectl -n quantum-platform get deploy,pods,svc
kubectl -n quantum-platform exec   deploy/quantum-platform-user-api --   python manage.py showmigrations portal
```

Current portal migrations should include:

```text
[X] 0005_person_posix_identity
[X] 0006_executionrecord
[X] 0007_posix_identity_allocator
```

Inspect the allocator:

```bash
kubectl -n quantum-platform exec   deploy/quantum-platform-user-api --   python manage.py shell -c '
from portal.models import PosixIdentitySequence
print(list(PosixIdentitySequence.objects.values()))
'
```

The current managed sequence begins at `21000`.

## Important identity rule

Public account creation does **not** allocate compute identity.

The intended sequence is:

```text
account
 ↓
verified research profile
 ↓
trusted programme/administrative approval
 ↓
POSIX UID/GID allocation
 ↓
infrastructure reconciliation
 ↓
SSH / NFS / Jupyter / Slurm
```

This prevents unauthenticated/public signup from consuming permanent UID/GID space.

## Workbench behavior

The normal user gets one Jupyter single-user server, but may open multiple JupyterLab workspaces and browser tabs inside it.

Named Jupyter servers are intentionally deferred.

The default workbench should remain lightweight; substantial CPU/GPU/QPU work should be submitted through the durable execution path.

## Runs

The user-facing execution path is available under the research-runs UI.

A successful run should expose:

- scheduler job ID;
- scheduler state;
- result path;
- durable workflow artifacts;
- provenance produced by `quantum-workflows`.

## Next milestone — M4

M4 moves the platform from “research portal with durable execution” to “persistent research environment”.

The same user should be able to continue one project/conversation through:

- Quantum Platform web;
- Jupyter;
- SSH/TUI;
- gptel/Spacemacs;

while Agent Control Plane preserves canonical conversations, projects, memories, skills and task/run history.

See `agent-control-plane` for the canonical M4 architecture.
