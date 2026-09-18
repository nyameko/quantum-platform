# Identity and programme authorization

This document defines the identity/authorization contract that sits beside the
Phase 1 Agent Control Plane integration.

## Three distinct identities

1. **Human identity** — name, verified email, institution, ORCID.
2. **System identity** — immutable username for SSH/Slurm/Jupyter/HPC/QPU
   provisioning.
3. **Agent identity** — `AgentPrincipal` UUID used by server-to-server ACP
   assertions.

These identifiers must not be collapsed into one another.

## System username

The server allocates:

```text
<first initial><surname>[collision number]

Nyameko Lisa -> nlisa
Nelly Lisa   -> nlisa1
Nigel Lisa   -> nlisa2
```

The username is lowercase ASCII, server-generated, immutable and never
recycled. The account header remains human-facing and displays the
first/preferred name.

## Programme identity

The server generates:

```text
<institution>-<pi_username>-<2..6-char programme code>
```

Example:

```text
CSIR + nlisa + Hybrid Quantum Centric Supercomputing Workflows
-> csir-nlisa-qcsc
```

The browser only previews this value.

## Authorization

An approved `ProgrammeMembership` is the future resource-authorization
boundary. Approval for Programme A does not grant Programme B resources.

Future adapters can map a programme identifier to Slurm account/QOS/quota,
project storage, JupyterHub profiles, QPU metadata, accounting labels and
other resource scopes.

## Agent boundary

Phase 1 ACP remains unchanged. Agent admin assertions use `AgentPrincipal`;
programme membership neither grants ACP administrator scope nor constitutes
scientific provenance.

A future scientific submission may authorize a user plus programme and invoke
a typed adapter. Platform scientific job ID, ACP task/run UUID,
scheduler/provider job ID and workflow experiment ID stay distinct.
