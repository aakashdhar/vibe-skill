# SPEC_RUBRIC.md

Reference rubric for auditing SPEC.md in Step 3 of vibe-spec-review.

---

## The O'Reilly six core areas — what good looks like

### Commands ✅
```
## Commands
Build:  npm run build           (compiles TypeScript, outputs to dist/)
Test:   npm test                (Jest, must pass before commits)
Lint:   npm run lint --fix      (ESLint auto-fix)
Dev:    npm run dev             (starts on port 3000 with hot reload)
DB:     npx prisma migrate dev  (runs pending migrations)
```

Bad: "Use npm to run things" (not actionable)
Bad: "Run tests before committing" (no command specified)

### Testing ✅
```
## Testing
Framework: Jest + React Testing Library (frontend), Jest + Supertest (API)
Files: co-located with source — ComponentName.test.tsx next to ComponentName.tsx
Coverage: 80% minimum on business logic (src/services/, src/api/)
Command: npm test -- --coverage
E2E: Playwright, tests in e2e/, run with npm run test:e2e
```

Bad: "Write tests for important features" (which features? what framework?)

### Project structure ✅
```
## Project Structure
src/
  api/          ← FastAPI route handlers (one file per resource)
  services/     ← business logic (no direct DB access)
  models/       ← Pydantic schemas and DB models
  agents/       ← LangGraph agent definitions
tests/
  unit/         ← pytest unit tests
  integration/  ← pytest integration tests (require DB)
docs/           ← generated docs only, no manual edits
```

Bad: "Standard React project structure" (not specific enough for agent)

### Code style ✅
Include a real example. One example beats three paragraphs.

```typescript
// ✅ Good — this pattern everywhere
export const createBrandDNA = async (url: string): Promise<BrandDNA> => {
  const result = await guardianAgent.extract(url)
  if (!result.success) throw new BrandExtractionError(result.error)
  return result.data
}

// ❌ Never — no error handling, any type
export async function createBrandDNA(url: any) {
  return await guardianAgent.extract(url)
}
```

### Git workflow ✅
```
## Git Workflow
Branches: feat/[ticket-id]-[short-description], fix/[ticket-id]-[description]
Commits:  conventional commits — feat:, fix:, chore:, docs:, test:
PR:       must have passing tests + review from one other dev
Merge:    squash merge, delete branch after merge
Never:    force push to main
```

### Boundaries ✅
```
## Boundaries
✅ Always:
  - Run npm test before committing
  - Use TypeScript strict mode (no any)
  - Follow naming conventions above

⚠️ Ask first:
  - Adding new npm dependencies
  - Changing database schema
  - Modifying API response shapes
  - Changing CI/CD configuration

🚫 Never:
  - Commit secrets, API keys, or .env files
  - Edit node_modules/ or vendor/
  - Remove a failing test without explicit approval
  - Deploy to production without passing all gates
```

---

## Acceptance criteria testability test

For each requirement, apply this test:
Can you write `expect([something]).toBe([specific value])` from this criterion?

**Fails testability:**
- "Users should be able to log in" → to what? from where? what happens on failure?
- "The dashboard should load quickly" → how quickly? on what device?
- "Errors should be handled gracefully" → what error? what does graceful mean?
- "The form should validate input" → which fields? what rules? what error messages?

**Passes testability:**
- "POST /auth/login with valid credentials returns 200 and JWT token"
- "POST /auth/login with invalid credentials returns 401 with error.code='INVALID_CREDENTIALS'"
- "GET /dashboard renders within 2s (measured by Lighthouse TTI)"
- "Email field: invalid format shows 'Please enter a valid email' inline, no form submission"
- "Empty required field on submit highlights field in red, shows 'Required' below"

**Edge case coverage:**
Every user-facing feature needs at minimum:
1. Happy path (correct input → expected output)
2. Invalid input (wrong format, missing required, out of range)
3. Error state (API down, timeout, network failure)
4. Empty state (no data yet — what does the user see?)

---

# ARCHITECTURE_RUBRIC.md

Reference for auditing ARCHITECTURE.md in Step 4.

---

## Three-tier boundary system — what complete looks like

**P0 — "never commit secrets" missing from Never tier:**
This was the single most important constraint in GitHub's analysis of 2,500+ agent files.
If it's not in Never, add it. Every project. No exceptions.

**P1 — Boundaries too vague to act on:**
Bad: "✅ Always: Write good code"
(What does "good" mean? The agent can't act on this.)

Good: "✅ Always:
  - Run tests before any commit
  - Export only public interfaces from modules
  - Use Result<T, Error> for all functions that can fail
  - Every new file gets a corresponding .test.ts file"

**P1 — Ask First tier not defined:**
Most agents will skip ahead on ambiguous decisions.
The Ask First tier forces them to pause on high-impact changes.

Minimum Ask First items for any project:
- Changing database schema
- Adding new external dependencies
- Modifying public API response shapes
- Changing CI/CD or deployment configuration
- Adding new environment variables

---

## Convention completeness by stack

### TypeScript projects — minimum required:
- [ ] Strict mode: true/false stated
- [ ] `any` usage: explicitly disallowed with no exceptions / allowed in [cases]
- [ ] Null handling: undefined vs null preference stated
- [ ] Import style: named vs default exports convention
- [ ] File naming: PascalCase for components, camelCase for utilities, etc.

### Python projects — minimum required:
- [ ] Type hints: required/optional stated
- [ ] Formatter: black/ruff/autopep8 with config
- [ ] Async pattern: asyncio/sync stated
- [ ] Import style: absolute vs relative
- [ ] Module structure: one class per file / multiple allowed

### API projects — minimum required:
- [ ] Response format: {data, error, meta} structure defined
- [ ] Error codes: standard set defined
- [ ] Auth: JWT/session/API key pattern defined
- [ ] Pagination: cursor/offset approach stated
- [ ] Versioning: /v1/ prefix or header approach stated

---

## Spec ↔ Architecture alignment

Every SPEC.md requirement that has implementation implications
should have a corresponding ARCHITECTURE.md section.

Example alignment:
SPEC: "Real-time competitor analysis updates"
→ ARCHITECTURE must define: WebSocket vs polling approach, connection management pattern

SPEC: "User authentication with social login"
→ ARCHITECTURE must define: auth provider, token strategy, session management

SPEC: "Brand DNA stored across sessions"
→ ARCHITECTURE must define: which DB, schema ownership, migration strategy

If a spec requirement has no architectural answer → P1 gap.

---

# FEATURE_SPEC_RUBRIC.md

Reference for auditing FEATURE_SPEC.md in Step 5.

---

## Task quality — what good looks like

**Good task (specific, bounded, verifiable):**
```
### F-003 · Implement GuardianVerifier

**Description:** Write the VerifierAgent for GuardianAgent output.
Check contract, spec compliance, quality score, and confidence.

**Acceptance criteria:**
- [ ] Verifier checks output contains all required Brand DNA fields
- [ ] Verifier checks clarityScore is between 0-100
- [ ] Verifier checks voiceAttributes has ≥2 items
- [ ] Verifier returns structured PASS/FAIL verdict with fix instructions
- [ ] Verifier fails correctly on missing fields (test: remove one field)
- [ ] Verifier passes correctly on valid output (test: use fixture data)
- [ ] All verifier tests pass

**Touches:** agents/verifiers/guardian_verifier.py, tests/test_guardian_verifier.py
**Dependencies:** F-001 (GuardianAgent must exist first)
**Size:** M
```

**Bad task (vague, unbounded, untestable):**
```
### Task 3 · Add validation
**Description:** Add some validation to the guardian output
**Acceptance criteria:** It should validate correctly
**Touches:** TBD
**Dependencies:** TBD
```

---

## Scope boundary examples

**P0 — Contradicts SPEC.md:**
SPEC.md: "v1 does not include social media posting"
FEATURE_SPEC.md: "Task 7: Publish article to LinkedIn automatically"
→ P0 contradiction: this feature is explicitly out of scope.

**P1 — Missing out-of-scope definition:**
Every FEATURE_SPEC.md must say what it explicitly does NOT include.

Good:
```
## Out of scope for this feature
- Batch article generation (multiple articles in one run)
- Article translation to other languages
- Direct CMS publishing (copy to clipboard only)
- SEO scoring (separate feature)
```

**P1 — New pattern not in ARCHITECTURE.md:**
If a feature introduces a pattern not documented in ARCHITECTURE.md
(new state management approach, new API pattern, new DB access pattern)
→ P1: run `architect:` or `change:` to document it before building.
