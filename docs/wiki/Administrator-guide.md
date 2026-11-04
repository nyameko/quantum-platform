# Administrator guide

## Review and approval

Use the supported staff/admin flows for PI applications and programme memberships. Verify institution, PI authority, intended research use, scope and time window. Approval and resource provisioning are distinct audited actions. A human account can have more than one programme membership without cross-granting resources.

The server allocates stable system usernames and, at an authorized boundary, POSIX UID/GID with a permanent ledger. Reconciliation across WireGuard, SSH, NFS, Jupyter and Slurm is owned by the infrastructure layer. Do not create alternative identities manually in JupyterHub or Slurm to bypass a missing approval.

## Read-only operational checks

On the Kubernetes administration host, with appropriate authorization:

```sh
kubectl -n quantum-platform get deploy,pods,svc
kubectl -n argocd get application quantum-platform
kubectl -n quantum-platform exec deployment/quantum-platform-user-api -- python manage.py check
kubectl -n quantum-platform exec deployment/quantum-platform-user-api -- python manage.py showmigrations portal
```

Do not assume the deployment name is unchanged across environments; discover it with the first command. Verify the source revision, image digest, database migration state and logs before changing anything. Direct DB edits, applying migrations, public image promotions or `rollout restart` require an approved change plan.

## Evidence and incident response

Keep membership decision audit trails, administrator identity, timestamps, minimal redacted error details, migration version and exact task/run IDs. Separate application health from successful Jupyter, Slurm and ACP acceptance. Do not paste encrypted-secret working values or personally identifying research content into public tickets.

See [administrator phase 1](https://github.com/nyameko/quantum-platform/blob/main/docs/agent-administrator-phase1.md), [programme identity](https://github.com/nyameko/quantum-platform/blob/main/docs/identity-programmes.md) and [infrastructure release guide](https://github.com/nyameko/infra-hpc-qc-k8s/blob/main/docs/INSTALLATION.md).