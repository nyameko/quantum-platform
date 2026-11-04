# Research programmes, membership and resource authorization

## Three stages of eligibility

An authenticated account is a *person*, not an allocation. A profile and verified email establish the applicant; a PI application or programme membership establishes research purpose; a separate trusted approval and infrastructure reconciliation establish access to compute resources. Programme membership is scoped: joining Programme A does not confer rights to Programme B's conversation rooms, project storage, Slurm allocations or QPU credits.

The backend contains `Person`, `PIApplication`, `ResearchProgramme`, `ProgrammeMembership` and `AuditEvent` models. PI approval services run under a database transaction, create/update programme membership, allocate identifiers, and may coordinate POSIX provisioning. Review [programme approval source](https://github.com/nyameko/quantum-platform/blob/main/apps/user-api/portal/programme_services.py) before modifying this path.

## Researcher workflow

1. Sign up, verify email, enable MFA and complete the person profile.
2. Review institution and existing programmes; apply as PI only if proposing and leading a programme.
3. Provide the research scope and justification through the available application controls.
4. Await an explicit decision. An application preview or pending membership is not an entitlement.
5. After approval, confirm assigned system identity, workbench and offered compute profiles through the portal. A failure to launch immediately after approval may mean infrastructure reconciliation is incomplete.
6. Use resources only within the approved programme, time, quota and data-access terms. An agent cannot self-approve membership.

## Administrator workflow

Verify applicant identity and institutional relationship; assess proposal ownership and duplicate programmes; approve/reject with a documented reason and audited actor. Avoid approving an application just to repair a broken UI. Reconcile identity and resource grants separately, checking user UID/GID, NFS ownership, SSH/WireGuard peer state, JupyterHub and Slurm association. Test authorized and unauthorized membership access.

Do not issue duplicate POSIX IDs or recycle retired IDs. Keep the programme identifier stable even if the visible title changes. For users with multiple programmes, maintain distinct entitlements and accounting labels.

## Troubleshooting

If an application isn't visible: confirm the account and programme scope. If approval appears successful but workbench fails: inspect person UID/GID and the reconciliation state. If programme conversation calls return 403/404, confirm *current* membership and ACP schema readiness; copying a room ID is not permission. Preserve a redacted audit trail.

References: [identity/programme specification](https://github.com/nyameko/quantum-platform/blob/main/docs/identity-programmes.md), [service implementation](https://github.com/nyameko/quantum-platform/blob/main/apps/user-api/portal/programme_services.py), [membership APIs](https://github.com/nyameko/quantum-platform/blob/main/apps/user-api/portal/identity_api.py), [programme permissions tutorial](https://github.com/nyameko/quantum-platform/blob/main/docs/tutorials/11-identity-programme-resource-boundaries.md).