# Tutorial 11 — Identity, MFA and programme-scoped authorization

## Goals

Trace one researcher from registration to an authorization object future
SSH/Slurm/QPU provisioning can consume, without weakening the existing Agent
Control Plane boundary.

## Registration

Provide given name(s), family name, primary institution, email and password.
Do not choose a username.

Confirm server allocation:

```text
Nyameko Lisa -> nlisa
Nelly Lisa   -> nlisa1
Nigel Lisa   -> nlisa2
```

## Email verification and MFA

Confirm the Brevo email has a clickable HTML verification button and plaintext
fallback. The verification URL must use the canonical trailing-slash Astro
route and never leak nginx's internal `:8080`.

Verify login works with email and username, then enable TOTP and recovery
codes.

## PI programme

Submit:

```text
Institution: CSIR
Programme: Hybrid Quantum Centric Supercomputing Workflows
```

Expected preview/server identifier:

```text
csir-nlisa-qcsc
```

Django remains authoritative.

## Approval

Use **Approve selected PI applications** or the approval API. Do not directly
edit the status field.

Approval creates atomically:

```text
PIApplication(status=approved)
ResearchProgramme(status=active)
ProgrammeMembership(role=pi,status=approved)
AuditEvent(PI_APPLICATION_APPROVED)
```

For an old manually-approved application:

```bash
python manage.py reconcile_programmes
python manage.py reconcile_programmes --apply
```

## Agent-control-plane regression check

Confirm the existing administrator diagnostics page and task history still
work. Identity/programme approval does not grant ACP scope or execute a
quantum workflow.
