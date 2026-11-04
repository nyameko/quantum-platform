# Workbench and durable research runs

## Default Jupyter workbench

The default workbench is a lightweight JupyterHub **KubeSpawner** user server with a shared research home. One server supports many browser tabs and JupyterLab workspaces. These are not separate GPU allocations. Named server support is a future, bounded design; older BatchSpawner manifests are optional non-default infrastructure templates.

From the authenticated portal, select Workbench/Notebooks and launch only after a research POSIX identity has been provisioned. The backend expects a configured JupyterHub API, signing key and user UID/GID. A missing UID/GID produces a provisioning error rather than an anonymous workspace.

Keep notebooks under `/home/research/<username>`. Verify imports/kernel and use small examples interactively. To stop the workbench, use the portal's stop control; stopping it should not delete persisted home files.

## Durable execution

The portal's Runs surface wraps `ExecutionRecord` and a restricted Slurm gateway. At the time of the reviewed source, executable reference offerings include `cpu-smoke` and `bell-aer` endpoints. Eligibility, current configuration, walltime, image selection and cluster availability must be checked by the server. GPU and QPU hardware execution require separate explicit entitlement and specialized runners.

```text
portal action -> authenticated execution API -> server-side entitlement
 -> restricted SSH Slurm gateway -> job -> Quantum Workflows runner
 -> shared result directory / manifest.json / summary.json
 -> ExecutionRecord and result view
```

A submission response is **not** final completion. Read scheduler state and exit status, verify scientific checks, then inspect reproducibility fields. Avoid running jobs that outlive a workbench kernel through an unmanaged notebook background process.

## Failure distinctions

A workbench launch failure can be JupyterHub configuration, identity or shared storage. A queued Slurm job can be legitimate resource contention. A failed workflow can have successful scheduler dispatch but failed numerical validation. A missing run record is a database/proxy issue; a missing artifact is workflow/permissions/storage.

References: [workbench contract](https://github.com/nyameko/quantum-platform/blob/main/docs/architecture/research-workbench-execution.md), [`workbench_api.py`](https://github.com/nyameko/quantum-platform/blob/main/apps/user-api/portal/workbench_api.py), [`execution_api.py`](https://github.com/nyameko/quantum-platform/blob/main/apps/user-api/portal/execution_api.py).