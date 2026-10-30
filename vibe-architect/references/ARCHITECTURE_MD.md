# ARCHITECTURE_MD.md

The canonical ARCHITECTURE.md template for vibe-* projects.
Used by vibe-architect Step 6 to generate ARCHITECTURE.md.
Every field must be filled. No placeholders left blank.
This file ensures every project's ARCHITECTURE.md has the same
structure so vibe-review, vibe-fix-bug, and vibe-add-feature
can parse it reliably.

---

## ARCHITECTURE.md TEMPLATE

```markdown
# ARCHITECTURE.md — [Project Name]
> Created: [date] via architect: | Last updated: [date]
> Source: BRIEF.md + AGENT_ARCH.md (agentic projects) + architect: conversation decisions
> ⚠️ This is the agent's constitution. Every code decision is measured against it.

---

## Project type

**Type:** [Web app / Mobile app / API service / CLI tool / Static site / Library]
**Platform:** [Mobile-first / Desktop-first / Both / Server-only]
**Stack (locked):**
  Frontend: [exact choice — e.g. React + Vite, NOT "React"]
  Backend:  [exact choice — e.g. Node + Express, or "none — client-only"]
  Database: [exact choice — e.g. Supabase PostgreSQL, or "none"]
  Auth:     [exact choice — e.g. Supabase Auth, or "none"]
  Hosting:  [exact choice — e.g. Railway + Vercel]

> This stack is locked. Do NOT scaffold with alternatives (e.g. Next.js
> if React+Vite is specified). Any deviation requires a change: command
> and a DECISIONS.md entry.

---

## Folder structure

\`\`\`
[Exact folder layout — every top-level directory and its purpose]
[Every file naming convention — e.g. components are PascalCase.tsx]
\`\`\`

**Rules:**
- [Rule 1 — e.g. "Feature-based folders: all files for a feature live together"]
- [Rule 2 — e.g. "No barrel exports (index.ts) — import directly from file"]
- [Rule 3 — e.g. "Components in components/, screens in screens/, hooks in hooks/"]

---

## Naming conventions

| Type | Convention | Example |
|------|-----------|---------|
| Components | PascalCase.tsx | `UserCard.tsx` |
| Hooks | camelCase with use prefix | `useAuthState.ts` |
| Utilities | camelCase | `formatDate.ts` |
| Types/Interfaces | PascalCase with Type/Interface suffix | `UserType.ts` |
| Constants | SCREAMING_SNAKE_CASE | `MAX_RETRY_COUNT` |
| API routes | kebab-case | `/api/user-profile` |
| DB tables | snake_case | `user_sessions` |
| CSS classes | [Tailwind utility / BEM / CSS Modules — pick one] | |

---

## State management

**Approach:** [React Context + hooks / Zustand / Redux / Jotai / none]

**Rules:**
- [Where state lives — e.g. "All server state via React Query. No local caching of API data."]
- [What goes in global state vs local — e.g. "Auth state global. UI state local to component."]
- [Storage rules — e.g. "All localStorage access through src/lib/storage.ts — never directly"]
- [Forbidden patterns — e.g. "No prop drilling beyond 2 levels — extract to context"]

---

## Frontend patterns

**Component rules:**
- [Composition rule — e.g. "Prefer composition over props. Max 5 props per component."]
- [Size rule — e.g. "Components over 150 lines get split. No exceptions."]
- [Logic rule — e.g. "No business logic in components — extract to hooks"]
- [TypeScript — Strict mode. No `any`. No type assertions without comment explaining why.]

**Styling:**
- [Approach — e.g. "Tailwind utility classes only. No inline styles. No CSS Modules."]
- [Version — e.g. "Tailwind v3 syntax. Do NOT use v4 @import syntax."]
- [Design tokens — e.g. "All colours from DESIGN_SYSTEM.md tokens. No hardcoded hex values."]

**Imports:**
- [Order — e.g. "1. React 2. Third-party 3. Internal absolute 4. Internal relative"]
- [Aliases — e.g. "@/ maps to src/ — use for all internal imports"]

---

## Backend patterns (if applicable)

**API style:** [REST with resource naming / tRPC / GraphQL]

**Layer structure:**
\`\`\`
Routes       → validate input (Zod) → call Service
Services     → business logic → call Repository
Repositories → database queries only, no logic
\`\`\`

**Rules:**
- [Validation — e.g. "All input validated with Zod at route entry. Never trust req.body directly."]
- [Error format — e.g. "{ success: false, error: { code, message } } — consistent everywhere"]
- [Auth — e.g. "Auth middleware on all routes except /health and /auth/*"]
- [Logging — e.g. "Winston for structured logs. Never console.log in production code."]

---

## Database patterns (if applicable)

**ORM/Client:** [Prisma / Supabase client / Drizzle / raw SQL]

**Rules:**
- [Migration — e.g. "All schema changes via Prisma migrations. Never alter tables manually."]
- [Query location — e.g. "All queries in repositories/. No DB calls in routes or services."]
- [Relations — e.g. "Always use foreign keys. No denormalisation without DECISIONS.md entry."]
- [Soft deletes — e.g. "Soft delete with deleted_at on all user-facing entities."]

---

## Testing philosophy

**What gets tested:**

| Type | Scope | Tool | When |
|------|-------|------|------|
| Unit | Pure functions, utilities, calculations | Vitest | Every task with logic |
| Component | User interactions, state changes, conditional rendering | Vitest + RTL | Every UI task |
| Integration | API endpoints with real DB | Vitest + Supertest | Every backend task |
| E2E | Critical user flows | Playwright | Phase 3 |

**Rules:**
- [Coverage — e.g. "Tests for every exported function and every component interaction."]
- [Test naming — e.g. "describe('[Component]') → it('should [behaviour] when [condition]')"]
- [Forbidden — e.g. "No snapshot tests. No testing implementation details."]
- [Database — e.g. "Integration tests use a test database. Never run against production."]

---

## Code quality

**Linter:** ESLint strict
- `no-any` — TypeScript any is a P0 review finding
- `no-unused-vars` — no dead code
- `react-hooks/exhaustive-deps` — all hook dependencies declared

**Formatter:** Prettier
- Single quotes, semicolons, 2-space indent, 100 char line length

**Git conventions:**
- Conventional commits: `feat(scope)`, `fix(scope)`, `docs(scope)`, `design(scope)`
- Doc commits always separate from code commits
- Pre-commit: lint + typecheck must pass before commit

**Dependencies:**
- Pin exact versions in package.json
- `npm audit` before every commit — high/critical = block commit
- Prefer packages with >1M weekly downloads and active maintenance

---

## Agent topology (agentic projects: delete when there is no AGENT_ARCH.md)

> Source: AGENT_ARCH.md (reviewed). This section carries its decisions into the
> code structure; it does not decide them again. Full detail stays in AGENT_ARCH.md.

**Framework:** [from AGENT_ARCH.md, e.g. LangGraph (Python)]
**Pattern:** [from AGENT_ARCH.md, e.g. Orchestrator + Sub-agents]

| Agent | Responsibility | Lives in | Verifier |
|-------|---------------|----------|----------|
| [AgentName] | [one line, from the roster] | [path in the folder structure] | [AgentNameVerifier] |

**State ownership:** [each state key and the one agent that writes it]
**Write tools:** [each write tool, its one owning agent, and whether it is irreversible]
**HITL checkpoints:** [where the system pauses for a person, from AGENT_ARCH.md]

---

## The O'Reilly principles (enforced by review:)

**Spec before code** — no task starts without acceptance criteria in FEATURE_TASKS.md.
**Context preservation** — CLAUDE.md, CODEBASE.md, ARCHITECTURE.md, TASKS.md read every session.
**Incremental progress** — one task at a time. Confirm → build → verify → commit.
**Drift prevention** — every deviation from this document logged in DECISIONS.md.

---

## Boundaries

Three tiers. Each item is specific enough to act on ("write good code" is not).

### ✅ Always

- [ ] Run lint, typecheck and tests before every commit
- [ ] Pin exact dependency versions and run the dependency audit before every commit
- [ ] Log every deviation from this document in DECISIONS.md and update this document
- [ ] [Project-specific always, added during architect:]

### ⚠️ Ask First

Stop and ask a person before:

- [ ] Changing the database schema
- [ ] Adding a new external dependency
- [ ] Modifying a public API response shape
- [ ] Changing CI/CD or deployment configuration
- [ ] Adding a new environment variable
- [ ] Changing the locked stack (needs a change: command and a DECISIONS.md entry)
- [ ] [Project-specific ask-first, added during architect:]

### 🚫 Never list

The following are P0 review findings — they block phase gates.

**Universal (every project):**
- [ ] Never commit secrets: no credentials, API keys, tokens or .env files in code or git
- [ ] Skipping input validation on any user-facing route or input

**When the project has that layer (delete the ones that don't apply):**
- [ ] Using `any` type in TypeScript (TypeScript projects)
- [ ] Business logic in route handlers, which belongs in services (backend projects)
- [ ] Direct database queries outside repositories (projects with a database)
- [ ] Frontend component importing directly from backend module (frontend + backend)
- [ ] Agent calling another agent directly, bypassing the orchestrator (agentic projects
      with an orchestrator)
- [ ] Inline styles overriding design tokens (projects with a UI)

**Project-specific:**
- [ ] [Project-specific never — add during architect:]
- [ ] [Project-specific never — add during architect:]

---

## Architecture decisions log

> Decisions made during architect: session.
> Full history of changes in DECISIONS.md.

| Decision | Choice | Reason | Date |
|----------|--------|--------|------|
| State management | [choice] | [reason] | [date] |
| Component library | [choice] | [reason] | [date] |
| [Decision] | [choice] | [reason] | [date] |

---

## Changelog

> Updated by architect: when decisions change.
> ⚠️ [date] — [what changed and why]
```

---

## Filling the template — rules for vibe-architect

**Stack section:** Copy from BRIEF.md tech stack table verbatim.
Include the explicit "Do NOT scaffold with alternatives" warning.
This is the line that prevents Next.js being scaffolded when React+Vite is specified.

**Folder structure:** Generate the actual tree, not a generic example.
For a React+Vite project with auth and DB, it should show the actual
src/components/, src/hooks/, src/screens/, src/lib/, src/api/ structure.
This tree is the source for PLAN.md, which `new:` writes later. On an agentic
project, include where AGENT_ARCH.md's boilerplate (agents/, tools/, state/, hitl/)
lives.

**Agent topology:** Fill it from AGENT_ARCH.md when it exists. Don't decide the
framework, roster, state or HITL again here. Delete the section when there is no
AGENT_ARCH.md.

**Boundaries:** Fill all three tiers. Always and Ask First keep their listed items
that apply and gain any project-specific ones from the conversation.
Never keeps both universal items (the literal "Never commit secrets" rule is one of
them), every conditional item whose layer the project has, and 2 project-specific
nevers based on the conversation.

**Testing table:** Adjust based on project complexity from BRIEF.md.
No E2E for S/M projects unless explicitly requested.
Always include Unit and Component for frontend projects.

**The template is a floor, not a ceiling.**
Add sections for project-specific patterns (e.g. real-time patterns,
offline-first patterns) when relevant.
Delete sections that don't apply (backend for client-only projects).
