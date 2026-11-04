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
