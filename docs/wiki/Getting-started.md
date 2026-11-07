# Getting started — PI, student and researcher first day

The first-time user landing page is now described in the portal source at
[`/getting-started/`](https://quantum.nyameko.com/getting-started/).
The release may not yet be deployed; source/CI and live access are separate.

## Before you request a machine

1. [Create an account](https://quantum.nyameko.com/account/signup/) and verify your email.
2. [Complete research identity](https://quantum.nyameko.com/profile/) and
   [enable MFA](https://quantum.nyameko.com/account/mfa/settings/).
3. [Register only public SSH and WireGuard keys](https://quantum.nyameko.com/account/access-keys/).
   Never paste a private key or recovery code into the portal or Guide.
   Registration is distinct from actual provisioning.
4. A **student** requests membership in an [existing research programme](https://quantum.nyameko.com/programmes/);
   a **PI** applies via [the PI application page](https://quantum.nyameko.com/programmes/apply/).
   Approval is not automatic.
5. [Check resource entitlements](https://quantum.nyameko.com/access/) before
   trying CPU/GPU/QPU workloads.
6. Launch [Workbench](https://quantum.nyameko.com/workbench/) and run a small
   approved CPU notebook. Use [Runs](https://quantum.nyameko.com/runs/)
   for scheduler-managed execution; record the Slurm job ID and artifact manifest.

## What a student should expect

A verified account plus programme membership request does **not** imply
automatic POSIX/SSH/VPN provisioning or GPU access. Once the PI and operator
approve resources, the portal can expose its Workbench and scheduler paths.
Only use an approved scheduler allocation; do not share another user's account.

## What a PI should expect

A programme application creates a **review request**, not a live resource
pool. Programme owners/members, quotas and research permissions remain separate
from account signup. Confirm the membership and capacity allocation before
telling students that hardware is available.

## Shell, Herdr and Guide

Login nodes preserve their existing login shell. `zsh` is installed only as
an **optional** interactive shell; run `zsh` to opt in for that session
and `exit` to return. This never changes a Slurm script's `#!/bin/bash`
shebang or its scheduler authorization.

Herdr reconnects per-user terminal panes; ACP PostgreSQL remains the source
for persistent researcher chats, not saved terminal output. The current
`acp --browser-pair` path is an authentication conformance fallback,
not the planned repeated daily UX. This feature is tracked in
[ACP #88](https://github.com/nyameko/agent-control-plane/issues/88).

## Quick lessons and videos

The reviewed [editorial plan](https://github.com/nyameko/quantum-platform/blob/dev/docs/editorial/onboarding-publishing-and-short-videos.md)
proposes short signup, MFA, SSH/WireGuard, PI, student, Workbench, Slurm and
agent status videos. No videos have yet been released. Never record private keys,
JWTs, live user names, allocations or private workspaces for a tutorial.

More: [Account and access](Account-and-access.md), [Researcher guide](Researcher-guide.md)
and [Workbench and runs](Workbench-and-runs.md).
