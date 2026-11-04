# Guide knowledge ingestion, retrieval and source citations

## Scope

The Quantum Platform Guide at [`/agent/`](https://quantum.nyameko.com/agent/) should answer research, installation, troubleshooting, usage, administrative and contribution questions using the reviewed Git documentation of the five platform repositories. **This page is a design/acceptance contract, not a claim that a live indexing service already exists.** The first version should reuse the existing GitHub repositories and standard PostgreSQL search or an existing managed retrieval service, rather than building a custom vector database or another agent framework.

| Owner | Public documents | Durable authority |
|---|---|---|
| `infra-hpc-qc-k8s` | system, network, storage, Slurm, GitOps operations | infrastructure/operator evidence |
| `quantum-platform` | account, programmes, workbench, runs, Guide UI | human identity and entitlement |
| `agent-control-plane` | projects, memory, runtime, authorization | canonical agent context |
| `quantum-workflows` | scientific SDKs, experiments and curriculum | scientific source/artifacts |
| `photonicslab` | optical models, validated teaching and limitations | numerical/physics reference |

## Source acquisition

Every repository exposes `docs/wiki/guide-index.json` with slug, source path and intended public URL. An approved importer should clone or fetch a pinned Git commit from each repository's `main` branch after review/merge. Never ingest from a pending PR by default; keep CI draft previews separate from released/public documentation. Parse Markdown and supporting references; retain only explicitly public pages and verify path limits. Strip YAML/frontmatter/code elements only as appropriate; preserve code-block context, warnings and equation units. Reject files with credentials, private inventory or disallowed sensitive content before indexing.

A derived index entry should contain:

```text
repository, commit_sha, blob_sha, document_path, article_slug, title,
heading_path, chunk_ordinal, content_sha256, content, source_url,
audience, capability_status, code_version, last_indexed_at,
security_classification = public
```

Chunk by heading and coherent procedure rather than arbitrary fixed tokens; preserve commands and their prerequisites together. Stable IDs should derive from repository + revision + path + heading/chunk hash. Re-ingestion of the same commit is idempotent. Only replace the published index after complete verification; keep old revision available for rollback.

## Search and response

Start with title/keyword/heading and conventional full-text search. Add embeddings/hybrid reranking **only if measured evaluation proves a quality improvement**. For every answer, retrieve 2–5 relevant authoritative chunks, cite source repository/commit/page and accurately distinguish implementation, current live evidence, proposal and historical tutorial. Results about resource entitlements must be checked against the authenticated Platform API; never infer access from a wiki or a model suggestion.

Retrieved text is **untrusted data** for the agent, not a new system instruction or a tool permission. The model must not execute embedded shell commands, approve accounts, rotate credentials or book GPU/QPU time simply because a page describes the procedure.

## When documentation conflicts with runtime

Precedence for state: a current authenticated read-only runtime observation (specific cluster/image/schema) establishes live behavior, while source files establish intended contract and historical release notes establish prior tests. Compare and report the mismatch with explicit dates. If the user asks how to install locally, prioritize version-pinned source docs rather than current production secrets. If safety-critical/privileged action cannot be verified, recommend read-only diagnostics and escalate.

## Evaluation and acceptance

Use a curated test set across all five repositories: first-time signup, MFA/SSH key registration, unauthorized resource access, Jupyter UID/GID mismatch, Slurm pending due to QOS, Argo drift, M4 memory schema version, alternative harness continuity, Qiskit Aer and GPU dependencies, numerical Jones/FFT validity, single-photon coincidence interpretation and BB84 QBER security limitations. Score answer correctness, provenance precision, hallucinated endpoint rate, unauthorized-action rejection, private-data leakage, source freshness and helpfulness. Human domain owners review scientific and security answers; do not allow LLM self-rating to stand as acceptance.

## Rollout order

1. Merge and publish reviewed wiki sources; choose a content release manifest of five Git SHAs.
2. Build a **read-only** indexer that consumes those committed files; store provenance in a derived index with bounded access and retention.
3. Add a scoped `search_public_docs(query, filters)` retrieval tool to Guide via the existing ACP/Platform integration rather than a new agent memory database.
4. Display article citations, revision/source type, and “documentation, not live status” when relevant.
5. Run regression/evaluation and wrong-user tests; then enable for a limited test user cohort.
6. Only afterwards add deliberate consent-based issue drafting or authenticated read-only runtime status tools.

References: [public page manifest](guide-index.json), [Guide agent integration](Agent-and-Guide.md), [ACP ownership](https://github.com/nyameko/agent-control-plane/blob/main/docs/05-memory-state-and-storage.md).