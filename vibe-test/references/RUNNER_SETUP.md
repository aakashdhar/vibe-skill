# RUNNER_SETUP.md

Used by vibe-test Step 0 when no test runner or E2E runner is detected.
Present the relevant section to the user based on their stack.

---

## Unit / Integration runners

### Jest (Node.js / React / Next.js)
```bash
npm install --save-dev jest @types/jest ts-jest
```

`jest.config.ts`:
```typescript
import type { Config } from 'jest'
const config: Config = {
  preset: 'ts-jest',
  testEnvironment: 'node',
  testMatch: ['**/*.test.ts', '**/*.test.tsx'],
  moduleNameMapper: {
    '^@/(.*)$': '<rootDir>/src/$1',
  },
}
export default config
```

Add to `package.json`:
```json
"scripts": {
  "test": "jest",
  "test:watch": "jest --watch",
  "test:coverage": "jest --coverage"
}
```

---

### Vitest (Vite / SvelteKit / Vue)
```bash
npm install --save-dev vitest @vitest/coverage-v8
```

`vitest.config.ts`:
```typescript
import { defineConfig } from 'vitest/config'
export default defineConfig({
  test: {
    environment: 'jsdom',
    globals: true,
    coverage: { provider: 'v8' }
  }
})
```

Add to `package.json`:
```json
"scripts": {
  "test": "vitest run",
  "test:watch": "vitest",
  "test:coverage": "vitest run --coverage"
}
```

---

### pytest (Python / FastAPI / Django)
```bash
pip install pytest pytest-asyncio httpx --break-system-packages
```

`pytest.ini` or `pyproject.toml [tool.pytest.ini_options]`:
```ini
[pytest]
asyncio_mode = auto
testpaths = tests
python_files = test_*.py
python_functions = test_*
```

---

### React Testing Library (component tests — add alongside Jest or Vitest)
```bash
npm install --save-dev @testing-library/react @testing-library/user-event @testing-library/jest-dom
```

Add to test setup file:
```typescript
import '@testing-library/jest-dom'
```

---

## E2E runners

### Playwright (recommended)
```bash
npm install --save-dev @playwright/test
npx playwright install
```

`playwright.config.ts`:
```typescript
import { defineConfig, devices } from '@playwright/test'
export default defineConfig({
  testDir: './tests/e2e',
  fullyParallel: true,
  retries: process.env.CI ? 2 : 0,
  use: {
    baseURL: 'http://localhost:3000',
    trace: 'on-first-retry',
  },
  projects: [
    { name: 'chromium', use: { ...devices['Desktop Chrome'] } },
  ],
  webServer: {
    command: 'npm run dev',
    url: 'http://localhost:3000',
    reuseExistingServer: !process.env.CI,
  },
})
```

Add to `package.json`:
```json
"scripts": {
  "test:e2e": "playwright test",
  "test:e2e:ui": "playwright test --ui"
}
```

---

### Cypress
```bash
npm install --save-dev cypress
```

`cypress.config.ts`:
```typescript
import { defineConfig } from 'cypress'
export default defineConfig({
  e2e: {
    baseUrl: 'http://localhost:3000',
    specPattern: 'tests/e2e/**/*.cy.{ts,tsx}',
    supportFile: false,
  },
})
```

Add to `package.json`:
```json
"scripts": {
  "test:e2e": "cypress run",
  "test:e2e:open": "cypress open"
}
```

---

## Folder conventions (establish if not present)

```
[project-root]/
├── src/
│   └── [source files]
└── tests/
    ├── unit/           ← pure function tests
    ├── integration/    ← API + DB tests
    ├── components/     ← component tests (or co-located as *.test.tsx)
    └── e2e/            ← Playwright or Cypress specs
```

Co-location (common in React/Next.js projects):
```
src/
├── components/
│   ├── Button.tsx
│   └── Button.test.tsx   ← co-located
└── api/
    ├── auth.ts
    └── auth.test.ts      ← co-located
```

Use whichever pattern is already established in the project.
If starting fresh: co-location for unit/component, `tests/` folder for integration and E2E.
