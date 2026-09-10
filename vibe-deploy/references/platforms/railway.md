# vibe-deploy platform: Railway

Loaded by vibe-deploy Step 3 only when the trigger is `deploy: railway`.
Contains the platform config generation for Railway.

---

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
