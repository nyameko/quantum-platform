# Researcher guide to the portal

## Main surfaces

The Astro user application includes account/profile/security pages, programmes and applications, access keys, notebooks/workbench, runs, and the agent page. Direct route source is [`apps/users/src/pages/`](https://github.com/nyameko/quantum-platform/tree/main/apps/users/src/pages). Authentication, entitlement and deployed routing may restrict which pages work for a given user.

### Recommended first day

Sign in → verify account and research profile → request/join a programme → register public access keys if instructed → open the workbench → run a credential-free notebook → submit a small approved CPU run → inspect durable results → open a project/conversation in Guide when supported.

The platform is a **research environment**, not merely a chatbot. Use the guide for explanations, documentation, research navigation and safe suggestions. Run scientific code in the specified notebook/workflow execution environment; don't mistake a plausible generated result for a completed computation.

## Learning progression

Start with mathematical/scientific foundations, a local classical reference and a short Qiskit/Aer notebook. Continue to Slurm/CPU scale, GPU simulation and optionally provider-authorized QPU runs. When GPU/QPU capacity is not available, use credential-free simulator tracks. Keep run specifications, versions, seeds, input datasets and results reproducible.

## Collaboration and responsibility

Programme membership grants access only to authorized programme resources. Shared research folders, results and agent rooms require explicit server-side authorization. Never assume a URL, a copied UUID or a notebook link grants access to another student's work. Report wrong-access bugs through private security channels.

See [curriculum progression](https://github.com/nyameko/quantum-platform/blob/main/docs/RESEARCHER-LEARNING-R1-R5.md) and [scientific academy](https://github.com/nyameko/quantum-workflows/blob/main/docs/MASTER-ACADEMY-AND-RESEARCH-TRACKS.md).