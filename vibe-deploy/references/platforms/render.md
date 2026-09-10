# vibe-deploy platform: Render

Loaded by vibe-deploy Step 3 only when the trigger is `deploy: render`.
Contains the platform config generation for Render.

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
      # External API keys the project actually uses — detect from .env.example
      # or ask; a Claude-powered app typically needs ANTHROPIC_API_KEY.
      - key: ANTHROPIC_API_KEY
        sync: false   # set in dashboard
      - key: [OTHER_API_KEY]
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
