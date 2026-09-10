# vibe-deploy platform: GitHub Pages

Loaded by vibe-deploy Step 3 only when the trigger is `deploy: github-pages`.
Contains the platform config generation for GitHub Pages.

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
