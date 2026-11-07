# First-user publication and short-video plan (review queue)

**Status:** editorial plan only. Blog drafts in `apps/blog/src/content/posts/`
remain `draft: true` until routes and human onboarding are verified.
No video was produced or published. Public videos must use a disposable
account, blur resource identifiers and never show credentials or real user data.

## Publication order and research workflow

| Priority | Article / news item | Audience | Video storyboard (suggested length) | Evidence before publishing |
| --- | --- | --- | --- | --- |
| 1 | Create an account, verify email and enable MFA | Everyone | 45–60s: signup → verification → authenticator setup → backup-code handling offscreen | Tested sign-up, login, MFA recovery |
| 2 | Generate and register SSH and WireGuard **public** keys | Everyone needing SSH | 75–90s: generate locally → copy public key → upload → check provisioning → private path test | Verified no private-key exposure and correct WG routing |
| 3 | Join a research programme as a student | Students | 60s: programme browse → membership request → status → entitlement | PI approval and wrong-user denial |
| 4 | Apply as a principal investigator | PIs | 60s: research profile → programme application → review status | Actual approval/rejection outcome |
| 5 | Check and request resource access | Everyone | 45s: access panel → eligible versus pending resources → operator support | Honest live allocation status |
| 6 | Launch Jupyter and run your first local notebook | Students/researchers | 60–90s: Workbench → notebook → run → save → stop server | Verified non-GPU default and stable home path |
| 7 | Submit your first Slurm job from Workbench | Researchers | 90s: open terminal → submit approved CPU job → squeue → sacct → manifest | Real job ID and artifact evidence |
| 8 | Submit Slurm from an SSH shell | Advanced researchers | 60s: WG/SSH → `sbatch` → `squeue` → `sacct`; no new scheduler | Role/UID, accounting, walltime and command verification |
| 9 | Continue work with Guide, projects and Herdr | Researchers | 75s: create C1 → resume same UUID in browser/Jupyter/terminal → model answer | M4a/M4g live continuity passed |
| 10 | What research agents can do — and cannot do | Researchers/engineers | 60s: view status, approve action in web UI, inspect bounded run and deny unauthorized mutation | Isolated pilot and audit/permission evidence |
| 11 | CPU-to-H200 quantum simulation: our first benchmark | Researchers | 90s: CPU reference → approved GPU queue → numerical comparison | M5a–M5c live artifacts, no performance exaggeration |

## Suggested production format

Each video: 5–8 second opening goal; 3–4 short labeled actions using
actual captured UI; a clear 'how to verify success'; a final failure/help
cue and direct route link. Accessible captions in English first, then
optional isiXhosa/isiZulu versions. Target 720p or 1080p horizontal desktop
and legible text; no generative imitation of an actual platform run.

Each article has: prerequisites, explicit action, expected result, common
failure, security caution, verified status and source/docs link.
Blog posts are for orientation; detailed and evolving instructions are
canonical `docs/wiki/` documents. Do not imply pending features are live.

News articles (publish only on evidence):
- 'Introducing the revised Quantum Platform onboarding journey' after QP
  home and signup acceptance.
- 'Persistent Guide and terminal continuity: M4 acceptance report' only
  after cross-client ID and security tests.
- 'First H200 simulation reference results' only with hardware, numerical
  and reproducibility evidence.
- 'PhotonicsLab tabletop teaching experiments' only with benchmark notebook.
