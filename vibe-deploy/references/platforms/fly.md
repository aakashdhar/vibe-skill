# vibe-deploy platform: Fly.io

Loaded by vibe-deploy Step 3 only when the trigger is `deploy: fly`.
Contains the platform config generation for Fly.io.

---

### Fly.io — `fly.toml` per service

Fly deploys one app per toml. Generate one per service directory.

**`backend/fly.toml`:**
```toml
app = "[project]-backend"
primary_region = "[region]"  # pick the region closest to your users — `fly platform regions`

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
primary_region = "[region]"  # match the backend's region

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
