# Tutorial 1 — Building the Astro Platform

## 1. Objective

Build a small public web platform containing three separate sites that share one design language without becoming one tightly coupled application.

The target surfaces are:

```text
blog.nyameko.com
wiki.quantum.nyameko.com
users.quantum.nyameko.com
```

The first two are public information surfaces. The third becomes the authenticated researcher portal.

## 2. Why three applications?

It would be easy to build one large website with routes such as `/blog`, `/wiki`, and `/users`. That is not the goal.

Separate applications give us:

- independent release cycles
- clear trust boundaries
- different future scaling models
- simpler ownership for student teams
- a clean mapping from hostname to Kubernetes Service
- the option to replace one application without rewriting the others

What *is* shared is the design system.

```text
apps/blog ─┐
apps/wiki ─┼──► packages/ui
apps/users ┘
```

This is a useful example of **shared implementation without shared deployment**.

## 3. npm workspaces

The root package describes the workspace:

```json
{
  "workspaces": [
    "apps/*",
    "packages/*"
  ]
}
```

The important root commands are:

```bash
npm run dev:blog
npm run dev:wiki
npm run dev:users

npm run check
npm run build
```

The root `check` and `build` commands run each workspace.

This gives the repository one developer entrypoint while preserving multiple deployable applications.

## 4. Shared UI

`packages/ui` contains components and CSS shared across the three websites.

The current platform uses:

- shared `SiteLayout`
- shared buttons
- shared cards
- global colour/design tokens
- dark/light theme support
- common navigation
- GitHub/project footer links

This avoids copy/pasting CSS into each site.

A key principle:

> Share the design language, not the application state.

Blog does not need to know who is logged into the User Portal. Wiki does not need Django. The shared UI package contains presentation, not identity.

## 5. Static output

All three Astro applications are built as static sites.

Run:

```bash
npm run build
```

Astro creates:

```text
apps/blog/dist/
apps/wiki/dist/
apps/users/dist/
```

Static output is a strong default because it:

- reduces runtime complexity
- needs no Node process in production
- is easy to cache
- has a small attack surface
- is easy to containerize
- makes Blog and Wiki extremely resilient

The User Portal can also remain static because authenticated state is fetched by browser JavaScript from Django.

## 6. Local binding

The applications bind to loopback during development.

That is deliberate.

Use:

```text
127.0.0.1
```

rather than exposing the dev server to every interface by default.

The User Portal is explicitly fixed to port `4323` so it matches the allauth frontend URLs and CSRF configuration.

```text
http://127.0.0.1:4323/
```

## 7. User Portal proxy

The User Portal needs to communicate with Django during development.

Instead of enabling broad CORS, Vite proxies selected paths:

```text
/_allauth  → http://127.0.0.1:8000
/api/v1    → http://127.0.0.1:8000
/accounts  → http://127.0.0.1:8000
```

The browser therefore experiences one origin:

```text
127.0.0.1:4323
```

This matters because normal Django session cookies and CSRF protection can remain intact.

## 8. Build validation

Before every meaningful checkpoint:

```bash
npm run check && npm run build
```

A healthy Phase 2 frontend produces zero Astro errors, warnings, and hints.

This test verifies:

- TypeScript/Astro diagnostics
- import paths
- static route generation
- shared-package integration
- production bundle generation

## 9. Failure encountered: wrong nested import

One useful failure occurred in:

```text
src/pages/account/password/reset/key.astro
```

The authentication utility lived at:

```text
src/lib/auth.ts
```

The nested page needed:

```text
../../../../lib/auth
```

rather than:

```text
../../../lib/auth
```

The important lesson is not the specific path. It is that a successful development page load does not prove the entire static build graph is valid.

`npm run check` and `npm run build` caught the problem immediately.

## 10. Failure encountered: wrong Wiki canonical site

The Wiki configuration must use:

```text
https://wiki.quantum.nyameko.com
```

not the Blog hostname.

Astro's `site` value is used for canonical URL generation and build-time URL behaviour. A copy/paste error here can silently generate incorrect public metadata even when pages render correctly.

## 11. Student exercise

1. Add a new shared card component.
2. Use it in Blog and Wiki.
3. Confirm User Portal is unaffected unless it imports the component.
4. Break an import deliberately.
5. Run `npm run check`.
6. Fix it.
7. Build all three apps.
8. Inspect each `dist/` directory.

## 12. Questions

- Why keep the User Portal static even though it is authenticated?
- What would force us to adopt Astro SSR?
- What belongs in `packages/ui`, and what should remain inside an individual app?
- What security advantage comes from not exposing the development server on all interfaces?
- Why is same-origin proxying preferable to casually enabling CORS?

## 13. Acceptance criteria

```text
✓ npm install succeeds
✓ Blog runs
✓ Wiki runs
✓ User Portal runs on 127.0.0.1:4323
✓ shared layout is visible on all applications
✓ npm run check passes
✓ npm run build passes
✓ three independent dist/ trees exist
```
