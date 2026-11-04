# JupyterHub, system identity and Slurm submission

## One identity, multiple execution surfaces

An approved research account can be associated with a stable lowercase ASCII system username, permanent POSIX UID/GID, authorized SSH public keys and membership-based Slurm accounting. The browser identity remains in Quantum Platform; JupyterHub/Slurm consume the authorized identity and must not create a rival account registry. ACP's AgentPrincipal UUID is another separate identity for conversation ownership.

## Workbench session

The user-facing workbench is a lightweight Kubernetes KubeSpawner single-user server. The backend requests a signed, short-lived Jupyter launch token carrying selected identity metadata and submits to the hub API. The user can open multiple JupyterLab workspaces within one server; that is **not** multiple GPU/CPU reservations. Notebook files go into the shared research home mounted by UID/GID. A mismatched `HOME`, numeric username or permission failure usually signals a provisioning/NSS/NFS issue rather than something the user can fix by `chmod 777`.

## Durable HPC run

The Portal execution service checks approved research access and submits through a restricted SSH gateway. A Slurm job has a real scheduler job ID and resource/walltime policy; Quantum Platform tracks an `ExecutionRecord` and Quantum Workflows writes the immutable scientific result/provenance directory. Workbench process lifetime should not own the job's lifetime. Reject unsanctioned command arguments; the gateway only supports configured, allowlisted actions.

## Read-only debugging

On the authorized admin machine, inspect `kubectl -n quantum-platform get deployment,pods,services`, hub/workbench namespace events, Slurm job state and redacted logs. Check corresponding source and image digests, not only `Healthy`. The user's own `id`, `pwd`, `echo "$HOME"` and `findmnt "$HOME"` can reveal identity or mount anomalies without privileged secrets.

## Security invariants

A signed launch token is not a substitute for current programme authorization. Reject expired/replayed tokens and unauthorized UID/GID claims; no automatic root home mounts. Do not place gateway keys or Jupyter API tokens in browser or notebooks. Any named-server/BatchSpawner expansion requires an explicit engineering/release contract.

See [workbench backend](https://github.com/nyameko/quantum-platform/blob/main/apps/user-api/portal/workbench_api.py), [Slurm execution backend](https://github.com/nyameko/quantum-platform/blob/main/apps/user-api/portal/execution_api.py), [workbench architecture](https://github.com/nyameko/quantum-platform/blob/main/docs/architecture/research-workbench-execution.md) and [Infra M3 guide](https://github.com/nyameko/infra-hpc-qc-k8s/blob/main/docs/tutorials/m3-account-workbench-slurm-sprint.md).