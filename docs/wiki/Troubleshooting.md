# Troubleshooting

## Login and account

Check email verification, correct login surface, session expiry, MFA status and CSRF origin. Do not diagnose failed login by collecting a user's password or session cookie. A verified account without a programme/UID is an **authorization/provisioning** issue, not a broken password.

## Workbench

Check the portal workbench status API, entitlement/UID, JupyterHub connectivity and signing configuration, KubeSpawner Pod events, image pulls, NFS mount and home ownership. Log redacted timestamps; do not display signing-key environment variables.

## Slurm runs

Separate rejected entitlement, missing gateway config, SSH host-key validation, scheduler pending, task failure and result ingestion. Inspect the ExecutionRecord and job ID using approved support tools. A failed reference `bell-aer` may also be caused by scheduler-provided job-name and walltime restrictions; do not assume a science-code bug.

## Agent issues

If a chat is missing, compare the authenticated AgentPrincipal, ACP migration versions, project/conversation UUIDs and status of the ACP service. A missing memory button or feature may indicate a staged UI but unavailable backend migration. Check [ACP acceptance gates](https://github.com/nyameko/agent-control-plane/blob/main/docs/conformance/m4c-m4g-live-release-gates.md) before marking live. A cross-user room appearing is a **security incident**, not a normal troubleshooting issue.

## Escalate with evidence

Report user role, environment, exact time/timezone, source revision, UI route, expected versus actual, HTTP status, job/run correlation ID and non-sensitive reproduction. Select [issues](https://github.com/nyameko/quantum-platform/issues) for ordinary bugs; report sensitive access failures privately.

See [quick start](https://github.com/nyameko/quantum-platform/blob/main/docs/QUICK_START.md) and [infrastructure diagnostics](https://github.com/nyameko/infra-hpc-qc-k8s/blob/main/docs/QUICK_GUIDE.md).