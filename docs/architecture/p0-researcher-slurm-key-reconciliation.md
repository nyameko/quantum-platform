# P0 — Reconcile research SSH public keys with native Slurm logins

**Source-only, pilot operator procedure.** This does not install keys, enable
Slurm jobs, modify Kubernetes Secrets, or replace Quantum Platform's existing
legacy `execution_api._gateway`. Do not retire the legacy gateway while Runs
still depends on it. See [P0 blocker #162](https://github.com/nyameko/quantum-platform/issues/162)
and [infra PR #290](https://github.com/nyameko/infra-hpc-qc-k8s/pull/290).

For an explicitly identified and authorized **pilot** researcher, an
administrator of the existing Django User API may run:

```bash
python manage.py export_slurm_researcher_public_keys nlisa
```

The read-only command queries Quantum Platform's **existing** Person,
ProgrammeMembership and SSHKey models. It refuses disabled accounts,
unprovisioned/mismatched UID/GID, inactive/archived programme membership,
invalid usernames, and missing or malformed active public keys.
Revoked SSHKey records are never included. The result is JSON with the
username, provisioned UID/GID, active **public** SSH keys and an explicit
`site_execution_approval_required=true` marker. It intentionally does
NOT emit `execution_enabled: true`, passwords or private keys.

An operator must cross-check the exported values against the approved
private `research_users` inventory, add the independent site-scoped
`execution_enabled` approval and explicitly apply the
`researcher_slurm_ssh` role from infra PR #290. **A registered portal
public key is not yet a deployed SSH key.** A revoked key also does not
cease to work on a live site until the authorized-key allowlist is
reconciled and confirmed. That delay must be covered by operational
revocation policy before production onboarding. Do not export all users
or mass-provision access based on generic programme membership.

Then from the *researcher's actual SSH session*, run the native
`sbatch/squeue/sacct/scancel` acceptance checklist in the infrastructure
P0 document. Login/node MUNGE/UID/GID/Slurm association must match.
Users maintain their own private SSH keys; the central Django API never
receives any of them.

## Remaining P0 release gate

Even with this safe admission and key-export mechanism, the current Runs
API still uses `SLURM_GATEWAY_PRIVATE_KEY` to operate on behalf of users.
It must be migrated to a verified **user-bound** authority or retired
coherently before the installed root/sudo helper and SealedSecret are
removed. This change alone does not close P0, nor does it claim a real
cross-user denial test.
