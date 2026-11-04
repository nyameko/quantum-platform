# Quantum Platform wiki

Quantum Platform provides the web experience, human identity, research programmes, access, notebooks, durable runs and a doorway to persistent research agents. This wiki is for **researchers, educators, programme administrators, developers and support agents**.

**Source basis:** `main` as of 4 November 2026; the deployed site can differ. A source route, planned contract or green CI check is **not** proof of production availability.

## Find the right guide

| Task | Article |
|---|---|
| Create an account, join a programme, get resources | [Account and access](Account-and-access.md) |
| Organize work and learn in the portal | [Researcher guide](Researcher-guide.md) |
| Launch notebooks, submit work, retrieve results | [Workbench and runs](Workbench-and-runs.md) |
| Use projects, conversations, memories and Guide | [Agent and Guide](Agent-and-Guide.md) |
| Review/reconcile programme access | [Administrator guide](Administrator-guide.md) |
| Develop the portal and Python API | [Developer guide](Developer-guide.md) |
| Understand API boundaries and contracts | [API and integration](API-and-integration.md) |
| Debug a failed login, spawn, run or agent turn | [Troubleshooting](Troubleshooting.md) |
| Secure data and contribute safely | [Security](Security.md) and [Contributing](Contributing.md) |

## Relationship to the ecosystem

Infrastructure deploys the environment; Quantum Platform owns user and programme policy; Quantum Workflows owns scientific runners, notebooks and provenance; ACP owns durable agent conversations, profiles and memory; PhotonicsLab owns optics/quantum photonics teaching models. Keep unique identifiers for the person, programme, ACP AgentPrincipal, POSIX account, Slurm job and scientific run.

Begin with [root README](https://github.com/nyameko/quantum-platform/blob/main/README.md), [quick start](https://github.com/nyameko/quantum-platform/blob/main/docs/QUICK_START.md), [identity/programmes](https://github.com/nyameko/quantum-platform/blob/main/docs/identity-programmes.md) and [researcher learning path](https://github.com/nyameko/quantum-platform/blob/main/docs/RESEARCHER-LEARNING-R1-R5.md).

## Guide and automated help

See [Guide integration and ticket routing](Guide-assistance.md) and the [machine-readable discovery index](guide-index.json). Public documentation is not an execution authorization.


## Detailed researcher and operator topics

- [Programme approval and resource entitlements](Programme-approval-and-resource-entitlements.md)
- [Authentication MFA and key management](Authentication-MFA-and-key-management.md)
- [JupyterHub and SSH identity](JupyterHub-and-SSH-identity.md)
- [API development and tests](API-development-and-tests.md)
- [Research programme administration](Research-programme-administration.md)
