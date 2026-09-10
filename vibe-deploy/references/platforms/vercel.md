# vibe-deploy platform: Vercel

Loaded by vibe-deploy Step 3 only when the trigger is `deploy: vercel`.
Contains the platform config generation for Vercel.

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
