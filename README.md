# Quantum Platform

Public web and research platform for quantum-centric computing.

This repository contains the public-facing Astro applications and shared content/UI packages for:

- `blog.nyameko.com` — public research and project writing
- `wiki.quantum.nyameko.com` — platform documentation
- `users.quantum.nyameko.com` — authenticated quantum/HPC user portal

The repository is intentionally public. Secrets, production credentials, persistent infrastructure,
and database data do not belong here.

## Architecture

```text
quantum-platform
├── apps/
│   ├── blog/     -> blog.nyameko.com
│   ├── wiki/     -> wiki.quantum.nyameko.com
│   └── users/    -> users.quantum.nyameko.com
├── packages/
│   ├── content/  shared content definitions and helpers
│   └── ui/       shared Astro components and styles
└── content/      public Markdown/MDX source
```

Application infrastructure is deployed through `infra-hpc-qc-k8s` and Argo CD.

The users portal will eventually consume a private PostgreSQL database backed by persistent storage in the
infrastructure repository. Database credentials and other secrets are never committed here.

## Local development

Requirements:

- Node.js 22+
- npm 10+

Install dependencies:

```bash
npm install
```

Run an application:

```bash
npm run dev:blog
npm run dev:wiki
npm run dev:users
```

Build all applications:

```bash
npm run build
```

## License

MIT
