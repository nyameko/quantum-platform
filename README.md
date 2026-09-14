# Quantum Platform — visual system v0.2.0

This overlay evolves the existing `quantum-platform` workspace from commit `1792fb3` into a consistent visual platform across:

- `blog.nyameko.com`
- `wiki.quantum.nyameko.com`
- `users.quantum.nyameko.com`

It introduces a shared Astro layout, shared design tokens, shared cards/buttons, and polished landing pages without introducing authentication, PostgreSQL, or infrastructure dependencies.

## Apply

From the repository root:

```bash
tar -xzf quantum-platform-visual-v0.2.0.tar.gz
```

The archive paths are relative to the repository root.

Then run:

```bash
npm run check
npm run build
```

This checkpoint intentionally does **not** add the registration/authentication/database work. That remains the next application milestone.
