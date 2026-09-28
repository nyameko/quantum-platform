# Research workbench, catalog and allocation ownership

Status: accepted architecture direction.

Quantum Platform owns what a researcher is **allowed and invited to use**. Infrastructure owns how the resource is physically deployed and scheduled.

## Default interaction model

The primary notebook session is a cheap KubeSpawner workbench. Users should not need to reserve 64 CPU cores, an H200 or a QPU while they are reading, editing, debugging small code or talking to agents.

```text
User -> Quantum Platform -> JupyterHub/KubeSpawner workbench
                              |
                              +-> execution API -> Slurm CPU/GPU
                              +-> quantum-workflows -> QPU/provider
```

## Product data model

Model these separately rather than encoding scheduler details into UI choices:

1. `WorkbenchEnvironment` — software UX/container family.
2. `ExecutionOffering` — logical execution target shown to users.
3. `ResourceEntitlement` — user/programme eligibility and expiry.
4. `AllocationBudget` — concurrency, credits, GPU-hours, shots or provider units.
5. `ExecutionRecord` — logical job plus scheduler/provider identifiers and provenance.

The infrastructure repository may bootstrap an equivalent static catalog during M2, but Quantum Platform becomes authoritative once M3 provisioning/entitlement is implemented.

## Usage

Classical CPU/RAM/GPU consumption should reconcile against Slurm accounting/TRES. QPU/provider concepts such as shots, provider credits and hardware sessions need a provider-aware ledger. Do not fake them as CPU hours merely to keep one accounting model.

## Agent experience

The same user conversation identity should be available in portal, Jupyter and terminal clients. Canonical chat/research memory belongs to platform user data; Agent Control Plane runs and harness-native PVC state reference those stable IDs rather than becoming competing memory databases.

## Persistent home

The user's platform-assigned POSIX UID/GID and `/home/research/<user>` remain authoritative across SSH, Kubernetes workbench and Slurm execution. Kubernetes service PVCs are not substitutes for the user's research home.
