# vibe-deploy platform: Netlify

Loaded by vibe-deploy Step 3 only when the trigger is `deploy: netlify`.
Contains the platform config generation for Netlify.

---

### Netlify — `netlify.toml`

```toml
[build]
  command = "npm run build"
  publish = "dist"         # or "out" for Next.js static export
  functions = "netlify/functions"

[build.environment]
  NODE_VERSION = "20"
  NODE_ENV = "production"

[[redirects]]
  from = "/*"
  to = "/index.html"
  status = 200

[[headers]]
  for = "/*"
  [headers.values]
    X-Frame-Options = "DENY"
    X-XSS-Protection = "1; mode=block"
    X-Content-Type-Options = "nosniff"
    Cache-Control = "public, max-age=0, must-revalidate"

[[headers]]
  for = "/assets/*"
  [headers.values]
    Cache-Control = "public, max-age=31536000, immutable"
```
