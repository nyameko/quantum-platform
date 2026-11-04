# Research administration, support and audit

## Responsibilities

Programme administrators review research affiliations and use cases, approve/deny membership requests, maintain entitlement boundaries, help users interpret account and workbench status, and track requests without becoming the owner of user scientific results or ACP memories. Infrastructure operators reconcile POSIX, WireGuard, NFS, Slurm and Kubernetes resources; scientific maintainers own workflows. A support bot can explain status but cannot approve itself as an administrator.

## A support incident in five steps

**Identify:** Does the request concern registration, verification, programme decision, POSIX provisioning, Jupyter, Slurm execution, ACP conversation or scientific method? **Confirm:** Inspect current account/application status using authorized admin UI; validate with non-sensitive audit and timestamps. **Isolate:** Avoid switching users, exporting private data, or granting temporary broad rights. **Resolve:** Change only the owning subsystem through a reviewed, logged path. **Verify:** Reproduce the full user journey and a negative unauthorized request before closing.

## Programme changes

Maintain stable project/programme identifiers and immutable system username rules. Membership revocation should prevent new resource access and new programme-room operations; it should not erase the researcher's lawful personal work or corrupt historical accounting. Some resources require background reconciliation; document pending versus materialized status explicitly. Never manually recycle a previously allocated UID.

## Audit and privacy

Approvals, credential registration/revocation, job submissions/cancellations, role changes, and agent authorizations should produce bounded records with a trusted actor and request ID. Avoid logging secrets, browser cookies, raw JWTs, protected source files or science data. Build support documentation that distinguishes administrative decisions from automated provisioning outcomes.

## Reporting

When users need assistance, include public environment and package version, UI route, time and timezone, redacted status/trace, programme context via private authorized support, and expected versus actual; route to the [Portal issues](https://github.com/nyameko/quantum-platform/issues) if non-sensitive. A security access-control bug should follow private disclosure, not a normal public issue.

Sources: [staff approval service](https://github.com/nyameko/quantum-platform/blob/main/apps/user-api/portal/programme_services.py), [identity code](https://github.com/nyameko/quantum-platform/blob/main/apps/user-api/portal/identity_api.py), [agent admin design](https://github.com/nyameko/quantum-platform/blob/main/docs/agent-administrator-phase1.md) and [programme boundaries](https://github.com/nyameko/quantum-platform/blob/main/docs/identity-programmes.md).