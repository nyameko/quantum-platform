# Publishing and maintaining the GitHub Wiki

`docs/wiki/` is the reviewable source; the [native GitHub Wiki](https://github.com/nyameko/quantum-platform/wiki) lives in a separate `.wiki.git` repository and is **not** published by a docs PR. After merging, initialize the wiki with a first page if necessary. From a clean authenticated checkout, run `bash scripts/publish-github-wiki.sh --dry-run` and inspect changes, then `bash scripts/publish-github-wiki.sh` to publish. Do not place access tokens in command lines, logs or URLs. Verify Home, sidebar and all links.

Guides follow ArchWiki-style task navigation: context/prerequisites, clear commands and scopes, warnings near side effects, troubleshooting by symptom, references to exact owned source. **Status** is per capability, not inferred from a merged PR or dashboard color. Production source/image/schema/entitlement may differ from current main. Public docs never contain private topologies, credentials or user records.

For Guide/ACP retrieval, capture title, repo, page slug, source commit, audience, capability status and cited source path. An agent can advise from public docs but must not infer permission to change accounts, secrets, hardware allocations or production resources. If information conflicts, escalate with links to conflicting evidence.

## Automatic publishing from `dev`

The `.github/workflows/publish-github-wiki.yml` workflow publishes reviewed `docs/wiki/*.md` pages on changes merged into `dev` (and supports a manual dispatch from `dev` when available). It first validates the Guide index and local links, sets up a secure short-lived `GITHUB_TOKEN` Git credential helper, runs the existing publisher in dry-run mode, then publishes. No ChatGPT, OpenAI, Anthropic, QPU or inference API key is required.

**Before the first run**, enable repository Wiki in Settings → General → Features and create/save one `Home` page from the Wiki tab. The underlying `.wiki.git` remote does not exist until that initial save. Repository Actions must permit `contents: write` for the job. Do not add a PAT unless the repository/organization policy requires an alternative and it has been security-reviewed.

After each reviewed `dev` wiki edit is merged, inspect Actions → Publish GitHub Wiki and then check the actual Wiki Home/sidebar. It publishes from **`dev`**, so articles must distinguish source/development behavior from live deployment. To republish manually, authenticate Git via `gh auth login` and `gh auth setup-git`, check out `dev`, and run `bash scripts/publish-github-wiki.sh --dry-run` followed by `bash scripts/publish-github-wiki.sh`. A manual `workflow_dispatch` may not appear in the Actions UI until the workflow also exists on the default branch; automatic `push: dev` is sufficient.

This job does not erase unrelated Wiki pages. Reviewers should verify source SHA/version links, redact private material and use Wiki Git history for recovery. Publication does not enable a live RAG backend or grant permission to run documented commands.

## Rendered Wiki links (publisher fix)

In the Git repository, relative Markdown links such as `[Getting started](Getting-started.md)` navigate between `docs/wiki/` files. In the **native GitHub Wiki**, that same `.md` link can open raw source instead of an HTML-rendered page. The canonical page URL omits the extension: `https://github.com/nyameko/quantum-platform/wiki/Getting-started` (when such a page exists).

The publish script now invokes `scripts/prepare_github_wiki.py` to rewrite local Wiki page links **only in the copied publication**, preserving readable source Markdown. The transform converts recognized local Wiki pages into full rendered Wiki URLs and non-Wiki local files, including `guide-index.json`, into `blob/dev` source links. External links, Markdown code examples and original checked-in files remain unchanged. Missing local links abort publication. PR validation runs offline regression tests and generates a full preview without publishing; the real Wiki push occurs only after the reviewed change is merged into `dev`.
