# Quantum Guide help, escalation and ticket creation

## Supported intent types

The Guide should first determine whether the researcher wants learning guidance, account instructions, notebook help, scientific interpretation, local development, operator diagnosis, or a feature request. An agent should answer simple documentation questions without forcing a ticket or collecting unnecessary personal details. For ambiguous production incidents, ask for a single non-sensitive diagnostic, not a private key, browser cookie or entire environment dump.

## Consistent support flow

1. Search released, revision-pinned documentation and cite the exact articles.
2. Explain current source documentation versus live site guarantees. If a feature is design-only, say so plainly.
3. Give safe read-only checks first, showing where to run them and what the result distinguishes.
4. Verify the subsystem owner; recommend the correct GitHub issue tracker. If the user wants to create a ticket, preview a sanitized proposed issue before posting it.
5. Where a change requires privileges, hardware spending, secret access or destructive action, route to an authorized administrator and explicit approval workflow rather than a generic agent command.

## Ticket routing

| User problem | Owner |
|---|---|
| VPN, private DNS, NFS, Kubernetes, Slurm, GPU deployment | Infrastructure |
| Account, MFA, programmes, access keys, Jupyter portal, runs UI | Quantum Platform |
| Project/chat continuity, private memories, harness and model routing | ACP |
| Qiskit/PennyLane notebooks, algorithms, scientific runner output | Quantum Workflows |
| Optical models, experiments, detector statistics and BB84 lesson | PhotonicsLab |

## Draft quality contract

An issue should include a descriptive title, user-visible symptom, expected/actual result, component/role, non-secret environment (Python/Node/sdk version and public Git commit), relevant run or incident timestamp/timezone, sanitized reproduction and error trace, prior safe diagnostics, observed effect and proposed acceptance criteria. Remove raw identities, IP maps, private research content, cloud tokens, certificates, database credentials and signing material. Report vulnerabilities privately.

## Agent authorization boundaries

Opening an issue is a **GitHub write action**, not a mere document search. The browser user must explicitly request it, review the final body and authorize the issue creation through a connected identity with permission. Agents must not impersonate user accounts or copy another user's records into tickets. Ticket comment/reaction/closure must similarly be authorized and auditable. A request to “help” is not an unlimited approval to restart, migrate or deploy services.

## Measurement

Record whether the answer resolved the problem without a ticket, whether the issue was routed to the correct repository, and whether reproduction/source references were useful. Collect only the minimum telemetry and honor retention/security policies. Periodically turn verified resolutions into source-controlled troubleshooting documentation, not undocumented agent-only memory.

See [Guide retrieval design](Guide-knowledge-and-source-ingestion.md), [support routing](Guide-assistance.md), [existing issue tracker](https://github.com/nyameko/quantum-platform/issues) and [repository contribution guide](https://github.com/nyameko/quantum-platform/blob/main/CONTRIBUTING.md).