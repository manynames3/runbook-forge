# Runbook Forge Sales Page

This directory is a static Cloudflare Pages Direct Upload target.

Deploy with:

```bash
npx wrangler pages deploy sales-page --project-name runbook-forge
```

This is a static site with no Workers, storage, databases, scheduled jobs, or paid bindings. Idle cost
should remain within Cloudflare Pages free-tier behavior.

The page links to the working product repository at:

```text
https://github.com/manynames3/runbook-forge
```
