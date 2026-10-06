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


## Validated M3 state

The default workbench model is now live:

- JupyterHub authenticates through the Quantum Platform signed-launch flow;
- KubeSpawner creates the lightweight single-user workbench;
- the user's shared research home is mounted at `/home/research/<user>`;
- the execution API submits durable Slurm jobs through a restricted gateway;
- `ExecutionRecord` preserves scheduler/result metadata;
- the reference `cpu-smoke` completed successfully as Slurm job 15.

The workbench is therefore a control/interactive surface, not the lifetime owner of the workload.

## Multiple Jupyter workspaces and future named servers

Today one user receives one Jupyter single-user server. Multiple JupyterLab workspaces such as `/lab/workspaces/auto-*` are logical UI/workspace state inside that one server.

Future named servers may expose bounded additional workbenches, for example:

```text
Workbench
├── Default
└── Experimental
```

but should remain explicitly limited and should not become the mechanism for acquiring scarce HPC/GPU resources.

## Prebuilt environments

The platform should progressively expose prebuilt workbench environments/kernels rather than require every cohort user to build SDK stacks in NFS homes.

Logical offerings can include:

- Intro Qiskit;
- IBM/Qiskit;
- PennyLane;
- CUDA-Q;
- IQM;
- Pasqal/Pulser;
- D-Wave/Ocean;
- Cirq;
- Braket;
- Azure/QDK;
- interoperability/translation.

GPU-specific A100/H200 environments should be represented as environment + execution-provider/resource-profile combinations rather than as ad-hoc notebook Pods permanently holding GPUs.
