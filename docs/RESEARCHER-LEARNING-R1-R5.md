# Researcher learning experience: R1–R5 (proposed, draft)

This roadmap adds researcher-facing **product releases** alongside, not instead of, ACP M4a–M4g. It does not alter production deployment or the identity model. Keep the existing authoritative `ExecutionRecord`, `AgentPrincipal`, approved programme membership, JupyterHub signed handoff and shared research home.

## Product principle

The new researcher sees a **goal**, not a dump of 87 notebooks. Ask what they want to learn, optionally establish prerequisites, recommend an editable path, open a first runnable notebook and persist their actual progress and scientific evidence. Advanced PIs get an opt-in research-profile and course-authoring workflow with human publication approval.

## R1: persistent researcher workbench — immediate acceptance

The README records JupyterHub signed handoff, KubeSpawner, a shared research home, and a successful `cpu-smoke` Slurm run. Treat these as **reported existing functionality**. They do not prove a completed learner journey.

**Acceptance scenario (staging / approved test users; no production changes from this RFC):**

1. Approved programme member signs in via normal portal MFA and opens a JupyterHub/KubeSpawner workbench.
2. The teaching entry point `quantum-workflows/labs/01-intro-quantum-computing/Intro_QC_Demo.ipynb` is available at a pinned revision and can run with *no QPU credential* in the workbench's documented environment.
3. Learner executes a Bell-state or basic optics experiment, edits a cell, and saves a distinct, user-owned copy (do not write into a shared canonical source).
4. Record notebook SHA/revision, environment, observed result and timestamp under the approved shared research home; ensure directory ownership and access restrictions.
5. Stop/cull/delete **only that test user's** KubeSpawner pod through the approved operational workflow; reopen a new workbench.
6. Confirm same approved identity and POSIX/NFS home, edited notebook and result. Compare checksums and inspect saved changes.
7. Re-run and confirm output is reproducible; if Slurm is involved, ensure independent `ExecutionRecord` and `quantum-workflows` manifest references.
8. Confirm another user cannot list or retrieve the private notebook or results.
9. Record redacted evidence: project/experiment ID, image digest, commits, CI, relevant pod lifecycle, before/after checksums, test result and reviewer sign-off.

**R1 fails** if the lesson is not runnable, if files vanish with the pod, if the identity/authorisation boundary fails, or if the only evidence is a successful demo without resume.

Do not replace the existing immutable home identity or create a parallel per-user Cinder home merely for this course. Admin `kubectl`/Argo operations are performed from the control-plane host, not the workstation. The infrastructure repository owns actual GitOps deployment.

## R2–R5 and M4 dependencies

| Release | User experience | Relation to M4 |
| --- | --- | --- |
| R1 | Login -> lesson -> save -> return | Independent of M4a |
| R2 | Research conversation/project survives browser, worker and client loss | Verified M4a; richer M4b/c/f |
| R3 | Goal -> prerequisite-aware pathway -> notebook -> progress -> next lesson | M4b/c/d/f for agentic features; non-agent catalogue could ship earlier |
| R4 | Verified ORCID/publication review -> PI drafts/edits/approves/publishes course | M4c/d/f, optional M4e |
| R5 | Validated CPU/GPU/QPU job -> resource/cost/accuracy -> immutable results | Cross-repository integration, optional M4g terminal client |

ACP owns canonical agent projects/conversations/memory/task state. Platform owns programme/access, enrolment, progress projection and publication controls. Quantum Workflows owns curriculum source, assessment definitions, executable science and result provenance. Slurm/provider owns physical execution.

## Researcher and PI experiences

### Beginner

Ask: “I want to learn QEC.” Offer recommended, skippable prerequisite modules, first runnable notebook, verified references, expected environment/runtime, learning outcomes and one test with an observable result. Save module completion only upon verifiable evidence; separate learner self-report from assessor verification.

### PI / instructor

Verified ORCID and a user-confirmed bibliography; opt-in interpretation of topical expertise; user-controlled private draft curriculum and lecture track; manual module reorder/fork/annotation; peer/instructor review; course versioned release; optional student cohort sharing. No automatic scientific endorsement, faculty ranking or agent self-approval. Publication identifiers, rights, embargoes and licensing remain visible.

### Course structure (proposed contract)

```yaml
pathway:
  id: qec-foundations
  version: 0.1.0
  status: draft
  owner_ref: platform-principal-uuid
  curriculum:
    repository: nyameko/quantum-workflows
    commit_sha: null  # pin on review/publish
  prerequisite_policy: recommended-not-mandatory
  modules:
    - id: qubits-and-measurements
      notebook: labs/01-intro-quantum-computing/Intro_QC_Demo.ipynb
      outcome: prepare-and-measure-a-bell-state
  approval:
    required_for_publication: true
```

The version, SHA, environment digest, assessment version and actual result evidence are never silently overwritten. Optional adaptive recommendations form branches of a learning graph, not a forced lockstep syllabus. A published class is an immutable snapshot; a PI may release a new revision.

## UI slices (not implemented by this RFC)

1. R1: a signed-in course entry/link that opens an existing pinned notebook in Jupyter, with documented test evidence.
2. R3: course cards, module DAG/prerequisites, “Start lesson”, run/status, progress and “Continue”.
3. R4: identity-confirmed PI “Research studio” to map publications, draft/edit/review/approve a track, assign cohorts, and manage course revisions.
4. R5: execution plan, environment/provider capabilities, estimated/actual resource use and scientific provenance.

Prefer accessible, responsive, low-bandwidth experiences with exportable curriculum/achievement records. Do not assert that EOSC/AOSP/GOSC interoperability is already present. Public research objects should support FAIR metadata; federated login and compute entitlements must remain separate.

## Tests and immediate prioritisation

- **First**: ACP M4a destructive PostgreSQL continuity test and evidence, as specified in its own repo; do not conflate with R1.
- **Alongside**: one R1 login/workbench/notebook/persistent-home end-to-end user journey, with two-user authorisation check.
- **Later**: one approved four-week QEC pathway, then PI studio and federated interoperability.

This PR is documentation/acceptance design only: it does not claim R1 has been observed or create production routes/migrations.
