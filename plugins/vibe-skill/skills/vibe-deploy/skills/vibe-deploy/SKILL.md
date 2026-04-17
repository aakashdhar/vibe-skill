---
name: vibe-deploy
description: >
  Prepares a vibe-* project for deployment to 7 platforms: Railway, Render,
  Fly.io, Heroku, Vercel, Netlify, GitHub Pages. Detects stack automatically
  (FastAPI, Express, Next.js, Django, React, Vue, static). Patches source
  files (port binding to $PORT, adds /health endpoint, production CORS).
  Generates platform config files scoped per service — backend, web, worker.
  Inlines non-secret env vars directly in config files per service. Links
  database connections using platform-native syntax. Generates ENV_SETUP.md
  with per-service CLI commands for secrets only. Handles background workers
  and cron services if the project requires them. Optionally generates GitHub
  Actions CI/CD workflow. Produces DEPLOY.md step-by-step checklist.
  Triggers: deploy: railway, deploy: render, deploy: fly, deploy: heroku,
  deploy: vercel, deploy: netlify, deploy: github-pages.
---

# Vibe Deploy Skill

Prepares your project for deployment — config files, source patches, env vars,
database provisioning, worker services, and a human checklist.
Deployment itself is manual. Everything before that is automated.

---

## Supported platforms

| Trigger | Platform | Best for | Database |
|---|---|---|---|
| `deploy: railway` | Railway | Full-stack, multi-service, APIs | PostgreSQL plugin |
| `deploy: render` | Render | Full-stack, background workers | PostgreSQL service |
| `deploy: fly` | Fly.io | Containers, globally distributed | Fly Postgres |
| `deploy: heroku` | Heroku | Full-stack, legacy projects | Heroku Postgres add-on |
| `deploy: vercel` | Vercel | Next.js, frontend, serverless | External only |
| `deploy: netlify` | Netlify | Static, JAMstack, serverless functions | External only |
| `deploy: github-pages` | GitHub Pages | Static sites only | None |

---

## Step 0 — Detect stack and services

Read the project to understand what is being deployed:

```bash
# Detect package managers and frameworks
cat package.json 2>/dev/null
cat requirements.txt 2>/dev/null
cat pyproject.toml 2>/dev/null
cat Dockerfile 2>/dev/null

# Detect framework-specific files
ls next.config.js next.config.ts 2>/dev/null
ls manage.py 2>/dev/null
ls main.py app.py 2>/dev/null
ls vite.config.js vite.config.ts 2>/dev/null

# Detect service directories
ls -la 2>/dev/null

# Read vibe context if available
cat vibe/ARCHITECTURE.md 2>/dev/null
cat CLAUDE.md 2>/dev/null

# Check for existing deploy configs
ls railway.json render.yaml fly.toml Procfile vercel.json netlify.toml 2>/dev/null
ls .github/workflows/ 2>/dev/null
```

**Identify:**

- **Services present** — backend API, frontend web, background worker, cron job, static site
- **Stack per service:**
  - Python: FastAPI, Django, Flask — check for `uvicorn`, `gunicorn`, `manage.py`
  - Node: Express, Next.js, Fastify — check `package.json` scripts and dependencies
  - Frontend: Next.js (SSR), React/Vite (static), Vue, plain HTML
  - Worker: Celery, Bull, custom scripts — check for worker entry points
- **Database in use** — PostgreSQL, MySQL, SQLite, Redis
- **Port usage** — is the app already binding to `$PORT` or hardcoded?
- **Health endpoint** — does `GET /health` exist?
- **CORS config** — is it set to `*` or localhost?
- **Existing migration system** — Alembic, Prisma, Knex, Django migrations

---

## Step 1 — Ask one question

Ask the user once before proceeding:

> "Do you want a GitHub Actions workflow for automatic deployment to [platform] on push to main?
> · **Yes** — generates `.github/workflows/deploy-[platform].yml`
> · **No** — manual deployment only"

Wait for answer. Then proceed with full generation.

---

## Step 2 — Patch source files

Patch existing source files to be production-ready.
Do not rewrite files — surgical edits only.
Report every file changed and what was changed.

### 2a — Port binding

**FastAPI / Python:**
Find `uvicorn.run(...)` or the startup command and ensure it uses `$PORT`:
```python
# Before
uvicorn.run("main:app", host="0.0.0.0", port=8000)

# After
import os
port = int(os.environ.get("PORT", 8000))
uvicorn.run("main:app", host="0.0.0.0", port=port)
```

If using a Procfile or start command (not uvicorn.run in code), patch the command instead:
```
web: uvicorn main:app --host 0.0.0.0 --port $PORT
```

**Express / Node:**
```javascript
// Before
app.listen(3000)

// After
const PORT = process.env.PORT || 3000
app.listen(PORT)
```

**Next.js:** Next.js reads PORT automatically — no patch needed.

**Django:**
```
# Procfile / start command
web: gunicorn myapp.wsgi --bind 0.0.0.0:$PORT
```

### 2b — Health endpoint

If `GET /health` does not exist, add it to the main app file.

**FastAPI:**
```python
@app.get("/health")
async def health():
    return {"status": "ok"}
```

**Express:**
```javascript
app.get('/health', (req, res) => res.json({ status: 'ok' }))
```

**Django:** Add to `urls.py`:
```python
from django.http import JsonResponse
path('health/', lambda r: JsonResponse({'status': 'ok'})),
```

**Next.js:** Create `app/api/health/route.ts`:
```typescript
export async function GET() {
  return Response.json({ status: 'ok' })
}
```

### 2c — Production CORS

Replace hardcoded `*` or `localhost` with `FRONTEND_URL` env var.

**FastAPI:**
```python
# Before
origins = ["*"]
# or
origins = ["http://localhost:3000"]

# After
import os
origins = [os.environ.get("FRONTEND_URL", "http://localhost:3000")]
```

**Express:**
```javascript
// Before
app.use(cors({ origin: '*' }))

// After
app.use(cors({ origin: process.env.FRONTEND_URL || 'http://localhost:3000' }))
```

**Django:** Update `CORS_ALLOWED_ORIGINS` in settings:
```python
CORS_ALLOWED_ORIGINS = [os.environ.get("FRONTEND_URL", "http://localhost:3000")]
```

### 2d — Database migration at startup

Append migration to the start command so it runs automatically on each deploy.

**Alembic (FastAPI/Python):**
```
web: alembic upgrade head && uvicorn main:app --host 0.0.0.0 --port $PORT
```

**Django:**
```
web: python manage.py migrate && gunicorn myapp.wsgi --bind 0.0.0.0:$PORT
```

**Prisma (Node):**
```
web: npx prisma migrate deploy && node server.js
```

**Knex (Node):**
```
web: npx knex migrate:latest && node server.js
```

### 2e — Worker / cron service

If a worker or cron service is detected, identify the entry point and add it as a separate service in the platform config. Do not patch the worker source — just configure it correctly in the deployment files.

---

## Step 3 — Generate platform config

### Railway — `railway.json`

Single file at repo root. Covers all services.
Non-secret env vars inlined per service.
Secrets get placeholder comments.
DATABASE_URL linked via Railway's internal reference syntax.

```json
{
  "$schema": "https://railway.app/railway.schema.json",
  "build": {
    "builder": "NIXPACKS"
  },
  "services": {
    "backend": {
      "source": {
        "repo": ".",
        "rootDirectory": "backend"
      },
      "build": {
        "buildCommand": "pip install -r requirements.txt"
      },
      "deploy": {
        "startCommand": "alembic upgrade head && uvicorn main:app --host 0.0.0.0 --port $PORT",
        "healthcheckPath": "/health",
        "healthcheckTimeout": 30,
        "restartPolicyType": "ON_FAILURE",
        "restartPolicyMaxRetries": 3
      },
      "variables": {
        "ENVIRONMENT": "production",
        "FRONTEND_URL": "${{web.RAILWAY_PUBLIC_DOMAIN}}",
        "DATABASE_URL": "${{Postgres.DATABASE_URL}}",
        "PORT": "8000"
      }
    },
    "web": {
      "source": {
        "repo": ".",
        "rootDirectory": "web"
      },
      "build": {
        "buildCommand": "npm install && npm run build"
      },
      "deploy": {
        "startCommand": "npm run start",
        "healthcheckPath": "/api/health",
        "healthcheckTimeout": 30
      },
      "variables": {
        "NODE_ENV": "production",
        "NEXT_PUBLIC_API_URL": "${{backend.RAILWAY_PUBLIC_DOMAIN}}"
      }
    }
  }
}
```

**Worker service** (add if detected):
```json
"worker": {
  "source": { "repo": ".", "rootDirectory": "backend" },
  "deploy": {
    "startCommand": "celery -A app.celery worker --loglevel=info"
  },
  "variables": {
    "DATABASE_URL": "${{Postgres.DATABASE_URL}}"
  }
}
```

**Cron service** (add if detected):
```json
"cron": {
  "source": { "repo": ".", "rootDirectory": "backend" },
  "deploy": {
    "startCommand": "python -m app.cron",
    "cronSchedule": "0 * * * *"
  },
  "variables": {
    "DATABASE_URL": "${{Postgres.DATABASE_URL}}",
    "CRON_SECRET": "set-in-dashboard"
  }
}
```

---

### Render — `render.yaml`

Single file at repo root. Multi-service blueprint.
`fromDatabase` links DATABASE_URL automatically.
`generateValue: true` for auto-generated secrets.

```yaml
databases:
  - name: [project]-db
    databaseName: [project]
    user: [project]
    plan: free

services:
  - type: web
    name: [project]-backend
    runtime: python
    rootDir: backend
    buildCommand: pip install -r requirements.txt
    startCommand: alembic upgrade head && uvicorn main:app --host 0.0.0.0 --port $PORT
    healthCheckPath: /health
    envVars:
      - key: ENVIRONMENT
        value: production
      - key: DATABASE_URL
        fromDatabase:
          name: [project]-db
          property: connectionString
      - key: JWT_SECRET
        generateValue: true
      - key: CRON_SECRET
        generateValue: true
      - key: FRONTEND_URL
        sync: false   # set in dashboard — Railway web URL not known at config time
      - key: GEMINI_API_KEY
        sync: false   # set in dashboard
      - key: OPENWEATHER_API_KEY
        sync: false   # set in dashboard

  - type: web
    name: [project]-web
    runtime: node
    rootDir: web
    buildCommand: npm install && npm run build
    startCommand: npm run start
    healthCheckPath: /api/health
    envVars:
      - key: NODE_ENV
        value: production
      - key: NEXT_PUBLIC_API_URL
        sync: false   # set to backend URL after first deploy

  - type: worker
    name: [project]-worker
    runtime: python
    rootDir: backend
    buildCommand: pip install -r requirements.txt
    startCommand: celery -A app.celery worker --loglevel=info
    envVars:
      - key: DATABASE_URL
        fromDatabase:
          name: [project]-db
          property: connectionString
```

---

### Fly.io — `fly.toml` per service

Fly deploys one app per toml. Generate one per service directory.

**`backend/fly.toml`:**
```toml
app = "[project]-backend"
primary_region = "bom"  # Mumbai — closest to India

[build]

[env]
  ENVIRONMENT = "production"
  PORT = "8080"

[http_service]
  internal_port = 8080
  force_https = true
  auto_stop_machines = true
  auto_start_machines = true
  min_machines_running = 0

  [[http_service.checks]]
    grace_period = "10s"
    interval = "30s"
    method = "GET"
    path = "/health"
    timeout = "5s"

[[vm]]
  cpu_kind = "shared"
  cpus = 1
  memory_mb = 512

[deploy]
  release_command = "alembic upgrade head"
```

**`web/fly.toml`:**
```toml
app = "[project]-web"
primary_region = "bom"

[build]

[env]
  NODE_ENV = "production"

[http_service]
  internal_port = 3000
  force_https = true
  auto_stop_machines = true
  auto_start_machines = true
  min_machines_running = 0

  [[http_service.checks]]
    grace_period = "10s"
    interval = "30s"
    method = "GET"
    path = "/api/health"
    timeout = "5s"

[[vm]]
  cpu_kind = "shared"
  cpus = 1
  memory_mb = 512
```

**Dockerfile** — generate if not present. Detect stack and generate minimal production Dockerfile:

FastAPI example:
```dockerfile
FROM python:3.12-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .
EXPOSE 8080
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8080"]
```

---

### Heroku — `Procfile` + `app.json`

**`Procfile`** (root):
```
web: alembic upgrade head && uvicorn main:app --host 0.0.0.0 --port $PORT
worker: celery -A app.celery worker --loglevel=info
```

**`app.json`** (root):
```json
{
  "name": "[project]",
  "description": "[project description from BRIEF.md]",
  "repository": "",
  "addons": [
    {
      "plan": "heroku-postgresql:mini"
    }
  ],
  "env": {
    "ENVIRONMENT": {
      "value": "production"
    },
    "JWT_SECRET": {
      "description": "Secret key for JWT signing",
      "generator": "secret"
    },
    "FRONTEND_URL": {
      "description": "URL of the frontend web app",
      "required": true
    },
    "GEMINI_API_KEY": {
      "description": "Google Gemini API key — get from aistudio.google.com",
      "required": false
    }
  },
  "formation": {
    "web": { "quantity": 1, "size": "eco" },
    "worker": { "quantity": 1, "size": "eco" }
  },
  "buildpacks": [
    { "url": "heroku/python" }
  ]
}
```

---

### Vercel — `vercel.json`

Frontend only. Generated at web service root or repo root.

```json
{
  "framework": "nextjs",
  "buildCommand": "npm run build",
  "outputDirectory": ".next",
  "installCommand": "npm install",
  "rewrites": [
    {
      "source": "/api/:path*",
      "destination": "https://[backend-url]/api/:path*"
    }
  ],
  "headers": [
    {
      "source": "/(.*)",
      "headers": [
        { "key": "X-Content-Type-Options", "value": "nosniff" },
        { "key": "X-Frame-Options", "value": "DENY" },
        { "key": "X-XSS-Protection", "value": "1; mode=block" }
      ]
    }
  ],
  "env": {
    "NEXT_PUBLIC_API_URL": "@next_public_api_url"
  }
}
```

For static React/Vite (no SSR):
```json
{
  "buildCommand": "npm run build",
  "outputDirectory": "dist",
  "rewrites": [{ "source": "/(.*)", "destination": "/index.html" }]
}
```

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

---

### GitHub Pages — `.github/workflows/deploy.yml`

Static export only. Generates the workflow even if user said no to GitHub Actions
(GitHub Pages requires a workflow — it's how it deploys).

```yaml
name: Deploy to GitHub Pages

on:
  push:
    branches: [main]
  workflow_dispatch:

permissions:
  contents: read
  pages: write
  id-token: write

concurrency:
  group: pages
  cancel-in-progress: false

jobs:
  build:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-node@v4
        with:
          node-version: 20
          cache: npm
      - run: npm install
      - run: npm run build
        env:
          NEXT_PUBLIC_API_URL: ${{ secrets.NEXT_PUBLIC_API_URL }}
      - uses: actions/upload-pages-artifact@v3
        with:
          path: ./out   # or dist for Vite

  deploy:
    environment:
      name: github-pages
      url: ${{ steps.deployment.outputs.page_url }}
    runs-on: ubuntu-latest
    needs: build
    steps:
      - uses: actions/deploy-pages@v4
        id: deployment
```

---

## Step 4 — GitHub Actions CI/CD (if user said yes)

Generate `.github/workflows/deploy-[platform].yml`.
Skip for Vercel and Netlify (they handle CI/CD natively — a workflow is unnecessary).
For GitHub Pages, the workflow is always generated regardless of this answer (it's required).

### Railway
```yaml
name: Deploy to Railway

on:
  push:
    branches: [main]

jobs:
  deploy:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-node@v4
        with:
          node-version: 20
      - run: npm install -g @railway/cli
      - run: railway up --service backend
        env:
          RAILWAY_TOKEN: ${{ secrets.RAILWAY_TOKEN }}
      - run: railway up --service web
        env:
          RAILWAY_TOKEN: ${{ secrets.RAILWAY_TOKEN }}
```

### Render
```yaml
name: Deploy to Render

on:
  push:
    branches: [main]

jobs:
  deploy:
    runs-on: ubuntu-latest
    steps:
      - name: Trigger Render Deploy — backend
        run: |
          curl -X POST "${{ secrets.RENDER_BACKEND_DEPLOY_HOOK }}"
      - name: Trigger Render Deploy — web
        run: |
          curl -X POST "${{ secrets.RENDER_WEB_DEPLOY_HOOK }}"
```

### Fly.io
```yaml
name: Deploy to Fly.io

on:
  push:
    branches: [main]

jobs:
  deploy-backend:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: superfly/flyctl-actions/setup-flyctl@master
      - run: flyctl deploy --config backend/fly.toml --remote-only
        env:
          FLY_API_TOKEN: ${{ secrets.FLY_API_TOKEN }}

  deploy-web:
    runs-on: ubuntu-latest
    needs: deploy-backend
    steps:
      - uses: actions/checkout@v4
      - uses: superfly/flyctl-actions/setup-flyctl@master
      - run: flyctl deploy --config web/fly.toml --remote-only
        env:
          FLY_API_TOKEN: ${{ secrets.FLY_API_TOKEN }}
```

### Heroku
```yaml
name: Deploy to Heroku

on:
  push:
    branches: [main]

jobs:
  deploy:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
        with:
          fetch-depth: 0
      - uses: akhileshns/heroku-deploy@v3.13.15
        with:
          heroku_api_key: ${{ secrets.HEROKU_API_KEY }}
          heroku_app_name: ${{ secrets.HEROKU_APP_NAME }}
          heroku_email: ${{ secrets.HEROKU_EMAIL }}
```

---

## Step 5 — Generate ENV_SETUP.md

Secrets only — values that cannot be inlined in config files.
Group by service. Include exact CLI commands per platform.

**Railway example:**
```markdown
# [Project] — Railway Secrets Setup

Run these after `railway link` connects your local project to Railway.
Non-secret env vars are already set in railway.json.

## Backend service secrets

railway variables set JWT_SECRET="$(openssl rand -hex 32)" --service backend
railway variables set GEMINI_API_KEY="get from aistudio.google.com/app/apikey" --service backend
railway variables set OPENWEATHER_API_KEY="get from openweathermap.org/api_keys" --service backend
railway variables set CRON_SECRET="$(openssl rand -hex 32)" --service backend

## Web service secrets

railway variables set NEXTAUTH_SECRET="$(openssl rand -hex 32)" --service web

## After first deploy — update with real URLs

railway variables set FRONTEND_URL="https://[your-web-url].up.railway.app" --service backend
railway variables set NEXT_PUBLIC_API_URL="https://[your-backend-url].up.railway.app" --service web
railway variables set NEXT_PUBLIC_WS_URL="wss://[your-backend-url].up.railway.app" --service web
```

**Render** — fewer secrets because `generateValue: true` handles JWT_SECRET and CRON_SECRET automatically. Only external API keys need manual setting.

**Fly.io:**
```bash
# Backend secrets
fly secrets set JWT_SECRET="$(openssl rand -hex 32)" --app [project]-backend
fly secrets set GEMINI_API_KEY="your-key" --app [project]-backend
fly secrets set DATABASE_URL="your-fly-postgres-url" --app [project]-backend

# Web secrets
fly secrets set NEXT_PUBLIC_API_URL="https://[project]-backend.fly.dev" --app [project]-web
```

---

## Step 6 — Generate DEPLOY.md

Step-by-step human checklist, platform-specific.
Every step is binary — done or not done.
Nothing assumed. Links to official docs where helpful.

### Railway DEPLOY.md structure:
```markdown
# [Project] — Deploy to Railway

## Prerequisites
- [ ] Railway account — railway.app
- [ ] Railway CLI installed — `npm install -g @railway/cli`
- [ ] GitHub repository connected to Railway

## Step 1 — Create Railway project
1. Go to railway.app → New Project → Deploy from GitHub repo
2. Select your repository
3. Railway will detect the services from railway.json automatically

## Step 2 — Provision PostgreSQL
1. In Railway dashboard → Add Service → Database → PostgreSQL
2. The DATABASE_URL is already wired in railway.json — no manual linking needed

## Step 3 — Set secrets
Run the commands in ENV_SETUP.md exactly as written.
Do not skip any — missing secrets will cause the deploy to fail silently.

## Step 4 — Deploy
Railway auto-deploys on push to main.
Or: railway up --service backend && railway up --service web

## Step 5 — Verify
- [ ] Backend health: https://[backend-url].up.railway.app/health → {"status":"ok"}
- [ ] Web loads: https://[web-url].up.railway.app
- [ ] Database migrations ran: check Railway logs for "alembic upgrade head" success
- [ ] Login flow works end to end

## Step 6 — Update cross-service URLs
After first deploy, real URLs are known. Update:
railway variables set FRONTEND_URL="https://[web-url].up.railway.app" --service backend
railway variables set NEXT_PUBLIC_API_URL="https://[backend-url].up.railway.app" --service web
Then redeploy: railway up --service backend && railway up --service web

## Step 7 — Set admin user (if applicable)
[Any platform-specific admin setup from the project]
```

---

## Step 7 — Confirm to user

Present a complete summary:

```
DEPLOY PACKAGE — [Project Name]
Platform: [platform]
Services detected: [backend / web / worker / cron]
GitHub Actions: [yes / no]

Files generated:
  ✅ [config file] — [description]
  ✅ ENV_SETUP.md — secrets setup commands per service
  ✅ DEPLOY.md — step-by-step checklist

Source files patched:
  ✅ [file] — [what was changed]
  ✅ [file] — [what was changed]

⚠️ Action required before deploying:
  · Run ENV_SETUP.md commands to set secrets
  · [any platform-specific manual steps]
  [· CREDENTIALS.md — fill values if handoff package also present]

After first deploy — update cross-service URLs:
  · [exact commands]
```

---

## Absolute rules

**Never write actual secret values.**
ENV_SETUP.md contains placeholder instructions only.
Commands use `$(openssl rand -hex 32)` generators where possible.
External API keys always say "get from [source]" — never invent values.

**Surgical source patches only.**
Never rewrite a file — only add or modify the specific lines needed.
Always report what was changed and why.

**Stack detection before generation.**
Never assume the stack — always read the files first.
If the stack cannot be determined, ask before generating.

**Worker/cron services only if present.**
Detect them from the codebase — don't add them if they don't exist.
A non-existent worker service in a config file will fail the deploy.

**Platform compatibility warnings.**
If the user runs `deploy: github-pages` on a server-side app, warn:
"GitHub Pages only supports static sites. This project has a backend service
that cannot be deployed to GitHub Pages. Consider Railway, Render, or Fly.io
for this project."

**Cross-service URL note always included.**
After first deploy, cross-service URLs (FRONTEND_URL, NEXT_PUBLIC_API_URL)
must be updated with real values. Always include this as a step in DEPLOY.md
and in the confirmation summary.

**Regenerate portal if vibe-handoff was run.**
If `vibe/handoff/` exists, remind the user to regenerate the handoff portal
after updating DEPLOY.md with real URLs post-deploy.
