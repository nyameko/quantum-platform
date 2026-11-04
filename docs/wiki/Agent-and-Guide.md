# Projects, conversations, memory and Quantum Guide

## What Guide is

The [agent page](https://quantum.nyameko.com/agent/) is a researcher-facing interface backed by Quantum Platform and the Agent Control Plane (ACP). Quantum Platform handles browser authentication, approval boundaries and signed server-to-server assertions; ACP owns canonical project/conversation IDs, messages, runs, profiles and memory. The model or harness is replaceable; canonical state should survive it.

The current source includes browser API proxies for private projects, conversations, turns, runs, memories, profile preferences and programme conversations. **Deployment readiness varies by ACP schema, image and access gates.** Before relying on a particular operation, check the live release status; do not interpret a hidden/disabled control as a guaranteed permission.

## Practical use

Organize related experiments in a project; start distinct conversations for questions, notebooks or bugs. Refer to exact code paths, workflow IDs and source revisions when asking for technical help. When a memory control is available, confirm the content and provenance; do not treat a model's suggestion as automatically approved memory. A reviewed skill link can open a scientific notebook but must not execute privileged commands merely by being clicked.

The Guide may display a **passive reasoning/processing status** reflecting observed work, without exposing a manual provider/model selector. Such status must reflect real broker/model/harness telemetry, not simulated colors or guessed effort. A green availability indicator alone does not prove an agent run finished successfully.

## Programme rooms and terminal clients

Programme conversations require current membership authorization on every relevant call, distinct from private agent projects. The secure terminal pairing/broker contract in ACP ADR 0012 remains a proposed integration until separately implemented and live-accepted; a POSIX SSH login must not be promoted to ACP identity proof.

See [ACP documentation](https://github.com/nyameko/agent-control-plane/blob/main/docs/M4-PERSISTENT-AGENTS.md), [M4 conformance](https://github.com/nyameko/agent-control-plane/blob/main/docs/conformance/m4c-m4g-live-release-gates.md) and [portal agent proxy](https://github.com/nyameko/quantum-platform/blob/main/apps/user-api/portal/agent_api.py).
## M4g browser-approved terminal pairing — source candidate, not live-validated

The browser approval page `/agent/pair/` now has a reviewed source candidate
for **one short-lived SSH/terminal-to-ACP pairing** (default five-minute
lifetime). The terminal generates a high-entropy proof held **only in process
memory** and shows a 12-character code. The real researcher, already logged in,
enters the matching code and explicitly confirms the device pairing. The
server records the hashed code/proof, not raw credentials.

Each `/api/v1/agent/terminal-gateway/*` read/turn request rechecks that
pairing is active and unexpired, then **Quantum Platform**—not the SSH
host—signs a fresh owner-scoped ACP assertion and forwards an allowlisted API
operation. The user can revoke the pairing in the portal; the next gateway
request is rejected. **POSIX UID, SSH username, browser cookies and shell
environment names do not confer ACP rights.**

The baseline client issues **one requested ACP operation per pairing**,
without writing auth secrets to disk; interactive long-running session
ergonomics can follow once actual authorization and revocation are verified.
No login-node sshd/PAM changes, shell replacement, database dump, browser
cookie transfer, or model/tool access are introduced.

This requires reviewed portal database migration `0008_terminal_pairing.py`,
an approved Quantum Platform backend/frontend release and the corresponding
updated thin terminal client in ACP. Source/CI tests are synthetic. **The
human operator performs all real `nlisa` browser/SSH tests**, including a
wrong-user attempt, expired proof and immediate subsequent-request denial
after revocation. No deployment or human acceptance is claimed here.
## M4c shared programme conversation baseline (source candidate)

The Guide programme folder can now offer **Create shared room** to a current
programme PI/delegate, with a distinct programme transcript and a **Post
message** form for approved members. This uses the existing signed Quantum
Platform → ACP C2 endpoints; it does **not** turn a personal chat into a shared
room, automatically expose private research memory, or invoke an agent model.

- The server rechecks current programme approval/status before every list,
  create, read and post; a browser role label is never authorization.
- Refreshing a room re-reads the shared canonical transcript. A denied/revoked
  response clears the previously displayed content and disables further posts.
- This is a **source implementation**, not observed live `nlisa` acceptance.
  A human PI and separately approved researcher must prove create, post,
  outsider denial and revocation in the deployed interface.


## M4d reviewed notebook references (source candidate)

Research Assistant includes **Reviewed research resources** below its approved
memory section. The source of trust is the **ACP immutable Git allow-list**,
not unreviewed notebook files, model messages or a portal-configured URL.

- Catalog and personal bindings are fetched using authenticated Quantum Platform
  proxies; ACP verifies the signed identity and database owner/tenant RLS.
- A researcher can inspect the exact reviewed `quantum-workflows` notebook at
  its immutable Git SHA, explicitly **Enable** a version, or **Revoke** it using
  an optimistic `If-Match` revision. Stale revisions are rejected.
- The ACP catalog is deliberately **empty until a human reviewer approves a
  real source manifest in a separate PR**. An empty panel is a truthful
  "no reviewed resources" status, not a failure of the UI.
- Enabling a notebook reference only attaches a reviewed resource to the
  researcher's ACP profile. **It does not install packages, create a skill
  executor, allocate resources, submit Slurm jobs, access a QPU, or grant
  model tools.** Workbench runs are separate explicit actions.
- Requires ACP schema v8 and paired M4d ACP API. Source CI is not proof of
  live migration or human `nlisa` acceptance.
