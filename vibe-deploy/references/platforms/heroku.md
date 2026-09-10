# vibe-deploy platform: Heroku

Loaded by vibe-deploy Step 3 only when the trigger is `deploy: heroku`.
Contains the platform config generation for Heroku.

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
    "ANTHROPIC_API_KEY": {
      "description": "Anthropic API key — get from console.anthropic.com (example; use whatever external keys the project actually needs)",
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
