# vibe-* skills

> A framework of 27 Claude Code skills that covers the complete software development lifecycle — from first idea to client sign-off.

Built by **Aakash Dhar** at [BetaCraft](https://betacraft.in) for production AI-assisted development workflows.

---

## What this is

vibe-* is a collection of Claude Code CLI skills. Each skill is a structured instruction set that tells Claude Code exactly what to do at a specific moment in a project — how to plan it, build it, review it, test it, deploy it, and hand it off.

Every skill follows the same principles:

- **Grounded in real files** — reads your actual TASKS.md, SPEC.md, DECISIONS.md, git history. Nothing invented.
- **One trigger, complete output** — type `feature: add dark mode` and get a spec, plan, task list, and code.
- **Phase-gated** — skills enforce quality gates. A phase cannot proceed until review passes.
- **Two audiences** — client-facing documents are always plain English. Developer documents are technical and precise.

---

## Installation

```bash
# Clone into your Claude skills folder
git clone https://github.com/aakashdhar/vibe-skill ~/.claude/skills/vibe-skills

# Or copy individual skills you need
cp -r vibe-skills/vibe-deploy ~/.claude/skills/
cp -r vibe-skills/vibe-handoff ~/.claude/skills/
```

Skills live in `~/.claude/skills/`. Claude Code reads them automatically on every session.

---

## The 27 skills

### Planning

| Skill | Trigger | What it does |
|---|---|---|
| vibe-brainstorm | `brainstorm:` | Turns a rough idea into a validated BRIEF.md through guided questions. Two paths: personal project (8 steps) and client/business project (13 steps). |
| vibe-spec-review | *(auto-triggered)* | Audits BRIEF.md and SPEC.md quality before any code is written. Catches vague requirements, missing acceptance criteria, and scope gaps. |
| vibe-architect | `architect:` | Plans code structure, patterns, and principles before writing code. Produces ARCHITECTURE.md which every subsequent session reads. |
| vibe-agent | `agent:` | Designs multi-agent systems — orchestrators, subagents, tool graphs, human-in-the-loop points. Produces AGENT_ARCH.md. |
| vibe-new-app | `new:` | Full greenfield project setup. Generates CLAUDE.md and the complete vibe/ folder from your BRIEF.md. |
| vibe-init | `vibe-init` | Onboards an existing codebase. Reads actual source files, infers architecture, generates the vibe/ folder so all other skills work immediately. |

### Build loop

| Skill | Trigger | What it does |
|---|---|---|
| vibe-add-feature | `feature:` | Full spec-driven feature workflow. Creates FEATURE_SPEC.md, FEATURE_PLAN.md, FEATURE_TASKS.md, then builds. |
| vibe-fix-bug | `bug:` | Severity-triaged bug workflow. Trivial bugs get 3 steps. Significant bugs get full diagnosis, BUG_SPEC.md, regression test before fix. |
| vibe-change-spec | `change:` | Modifies, adds, or removes requirements mid-build. Cascades changes through all affected docs in the correct order. |
| vibe-review | `review:` | Evidence-based code review. Mandatory phase gate — Phase N cannot proceed to N+1 until review passes with zero P0 issues. |
| vibe-test | `test:` | Blast-radius-aware test generation. Traces every file a change touches, maps the full dependency graph, writes coverage across the entire impact zone. |

### Visibility

| Skill | Trigger | What it does |
|---|---|---|
| vibe-progress | `progress:` | Live ASCII dashboard of project state from TASKS.md and git log. Read-only, no files modified. |
| vibe-cost | `cost:` | Tracks token usage and dollar cost per task, session, feature, and phase. Detects 8 waste patterns. Writes summary.json for vibe-ledger. |
| vibe-ledger | `ledger:` | Generates a self-contained HTML cost report from history.json + summary.json. 8-bit terminal aesthetic. Opens automatically in browser. |
| vibe-graph | `graph:` | Builds a dependency and concept graph of the codebase. Detects clusters, circular dependencies, and orphaned files. Incremental updates via git diff. |

### Design

| Skill | Trigger | What it does |
|---|---|---|
| vibe-design-md | `design-md:` | Generates DESIGN_SYSTEM.md — 55+ pattern catalogue. Can fetch from a URL or from the awesome-design-md collection. |
| vibe-design | `design:` | Frontend design workflow for styling components and pages. Reads DESIGN_SYSTEM.md and produces non-generic, editorial-quality UI. |

### Advanced

| Skill | Trigger | What it does |
|---|---|---|
| vibe-parallel | `parallel:` | Wave-based parallel subagent execution. Builds dependency waves, detects file conflicts, coordinates multiple agents. |
| vibe-mode | `mode:` | Switches between Autonomous (runs until done) and Supervised (waits for "next" between tasks) execution modes. |
| vibe-perf | `perf:` | Full-stack performance audit — frontend, backend, agentic pipelines, infrastructure. Risk-ranked fix plan with before/after benchmarks. |
| vibe-doctor | `doctor:` | 10-point environment health check. Finds broken configs, wrong versions, missing setup. Auto-remediates safe fixes. |

### Ship

| Skill | Trigger | What it does |
|---|---|---|
| vibe-deploy | `deploy: [platform]` | Prepares the project for deployment to 7 platforms. Patches source files, generates platform config, inlines env vars per service, generates step-by-step DEPLOY.md. |
| vibe-e2e | `e2e: [url]` | Generates and runs Playwright E2E tests from SPEC.md against a live URL. Auto-installs Playwright. Video on failure. Cleanup script removes test data after every run. |

### Close

| Skill | Trigger | What it does |
|---|---|---|
| vibe-document | `document:` | Generates all documentation in one session — inline code docs, README.md, CHANGELOG.md, API reference, component library docs. |
| vibe-changelog | `changelog:` | Generates two changelogs from git tags — CHANGELOG.md (developer-facing, Keep a Changelog format) and CHANGELOG_CLIENT.md (plain English, product update style). |
| vibe-handoff | `handoff: [mode]` | Generates a complete handoff package for 5 scenarios. Produces both MD files and a single self-contained index.html portal for client sharing. |

---

## The full development cycle

```
PLAN
  brainstorm: → spec-review (auto) → architect: → new: / vibe-init

BUILD
  feature: → review: → test:
  bug: (when needed)
  change: (when needed)

WATCH
  progress: ← always available
  cost: → ledger: ← after sessions
  graph: ← when architecture questions arise

DESIGN
  design-md: → design:

ADVANCED
  parallel: / mode: / perf: / doctor:

SHIP
  doctor: → deploy: railway → e2e: https://your-app.railway.app

CLOSE
  document: → changelog: → handoff: client
```

---

## Examples

### Starting a new project

```
brainstorm: I want to build a SaaS tool for freelancers to track client invoices
```

Claude asks 13 structured questions across product, users, revenue, and tech. Produces `BRIEF.md`.

```
architect:
```

Claude reads BRIEF.md and produces `ARCHITECTURE.md` — tech stack decisions, folder structure, data model, API patterns, auth approach. This file is read at the start of every future session.

```
new:
```

Claude reads BRIEF.md and ARCHITECTURE.md, generates `CLAUDE.md` at the project root and the complete `vibe/` folder — SPEC.md, TASKS.md, CODEBASE.md, DECISIONS.md, DESIGN_SYSTEM.md. Then starts building Phase 1.

---

### Adding a feature

```
feature: add CSV export for invoices
```

Claude produces:

```
vibe/features/2026-04-17-csv-export/
├── FEATURE_SPEC.md    ← acceptance criteria, edge cases, out of scope
├── FEATURE_PLAN.md    ← implementation approach, files to change
└── FEATURE_TASKS.md   ← task breakdown with size (S/M/L) and order
```

Shows the plan. You say `go` and it builds.

---

### Fixing a bug

```
bug: the invoice total shows NaN when tax rate is empty
```

Claude triages severity (Medium — UX impact, has workaround). Diagnoses root cause in the calculation logic. Writes a regression test that fails. Fixes the bug. Regression test now passes.

---

### Reviewing a phase

```
review: phase 2
```

Claude acts as Senior Engineer, Architect, and Code Quality Auditor simultaneously. Every finding is backed by a file path and line number. No vague feedback.

```
PHASE 2 REVIEW — Invoice SaaS
Score: 7.2/10 · Grade: B+

P0 — Must fix before Phase 3
  · backend/app/services/invoice.py:142
    SQL query not parameterised — injection risk

P1 — Fix before deploy
  · web/components/InvoiceForm.tsx:67
    No loading state on submit — UX issue on slow connections

P2 — Address in backlog
  · backend/app/models/client.py:23
    Missing index on email column — will degrade at scale

Phase 3 is BLOCKED until P0 resolved.
```

---

### Tracking costs

```
cost:
```

After each session Claude calculates token usage, estimates dollar cost, tags every task with size (S/M/L) and cost, detects waste patterns. Writes to `vibe/cost/history.json` and `vibe/cost/summary.json`.

```
ledger:
```

Generates a full HTML cost report and opens it in the browser:

```
VIBE-LEDGER · Invoice SaaS
Total spent: $12.40 · 18 sessions · 94 tasks

AVG COST/TASK   $0.13
PEAK SESSION    $1.89 — Phase 2 Backend
CACHE SAVINGS   $0.00 — unlock caching to save ~$0.40

SESSION BURN
  S1 · Phase 1 Foundation      ● ● ○ ○ ○ ○ ○   $0.58
  S2 · Phase 2 Backend   [peak] ● ● ● ● ● ● ●  $1.89
  S3 · Phase 2 Frontend        ● ● ● ○ ○ ○ ○   $0.82
```

---

### Deploying to Railway

```
deploy: railway
```

Claude reads the project. Detects FastAPI backend + Next.js web + PostgreSQL. Asks one question: GitHub Actions yes or no?

Then:
- Patches `main.py` — port binding to `$PORT`
- Adds `GET /health` endpoint if missing
- Locks CORS to `FRONTEND_URL` env var
- Prepends `alembic upgrade head &&` to start command
- Generates `railway.json` with backend + web + worker services, all scoped
- Non-secret env vars inlined per service
- `DATABASE_URL` linked via `${{Postgres.DATABASE_URL}}`
- Generates `ENV_SETUP.md` with exact `railway variables set` commands for secrets
- Generates `DEPLOY.md` — step-by-step human checklist

---

### Running E2E tests

```
e2e: https://invoice-saas.railway.app
```

Claude reads SPEC.md and FEATURES.md. Identifies 14 critical user flows. Installs Playwright into `e2e/` in isolation if needed. Generates test files. Runs the suite.

```
E2E REPORT — Invoice SaaS
URL: https://invoice-saas.railway.app
────────────────────────────────────────
01 auth     · Register → onboarding → dashboard   ✅  3.8s
02 auth     · Login email/password                ✅  1.4s
03 auth     · Google OAuth                        ⚠️   SKIPPED
04 invoices · Create invoice → appears in list    ✅  4.1s
05 invoices · Send invoice → status updates       ✅  6.7s
06 clients  · Add client → invoice autocompletes  ✅  3.2s
07 export   · CSV export → file downloads         ❌  FAILED
────────────────────────────────────────
6 passed · 1 failed · 1 skipped (OAuth)

FAILURE 07 · CSV export
  Expected: file download dialog
  Got: 500 error from /api/export
  Video: e2e/test-results/07-export/video.webm

Cleanup: ✓ 3 test invoices deleted · ✓ 2 test users deleted
```

---

### Generating changelogs

```
changelog:
```

Claude reads git tags, git log, TASKS.md, DECISIONS.md, and all feature specs. Groups 47 completed tasks into 8 meaningful entries. Generates two files simultaneously.

**CHANGELOG.md** (developer-facing):
```markdown
## [2.0.0] — 2026-04-17

### Added
- CSV export for invoices and client lists (EXP-01–EXP-04)
- Recurring invoice scheduler with configurable intervals (REC-01–REC-06)
- Stripe payment link generation from invoice detail (PAY-01–PAY-03)

### Changed
- Invoice numbering moved to server-side sequence (DECISION: 2026-04-10)
- PDF generation upgraded from html2pdf to Puppeteer (DECISION: 2026-04-12)

### Fixed
- NaN total when tax rate is empty (BUG-012)
- Invoice date picker broken on Safari (BUG-014)
```

**CHANGELOG_CLIENT.md** (plain English):
```markdown
## Version 2.0 — April 2026

**Export your data.**
Download any invoice list or client list as a CSV file —
one click from the list view.

**Set invoices to repeat automatically.**
Create a recurring invoice once and it sends itself — weekly,
monthly, or on any schedule you choose.

**Get paid faster with payment links.**
Every invoice now has a "Get paid" button that generates a Stripe
payment link your client can use immediately.
```

---

### Handing off to a client

```
handoff: client
```

Claude reads all project files and generates a complete package:

```
vibe/handoff/client-2026-04-17/
├── DELIVERY.md           ← what was built (plain English, 600-1000 words)
├── FEATURES.md           ← screen-by-screen walkthrough
├── KNOWN_ISSUES.md       ← honest, specific, no hedging
├── CREDENTIALS.md        ← placeholder list — human fills values
├── SUPPORT.md            ← how to get help and escalate
├── ROADMAP.md            ← what was deferred and why
├── SIGN_OFF_CHECKLIST.md ← PM works through this on the sign-off call
└── index.html            ← self-contained portal combining all docs
```

The `index.html` portal is a fully designed, light-mode web page — sidebar navigation, document index, all 7 documents in one shareable file. Send it to the client directly.

---

## Cheat sheet

### The mental model — one line per phase

```
THINK    brainstorm: → architect: → new: / vibe-init
BUILD    feature: → review: → test:
WATCH    progress: / cost: / ledger: / graph:
DESIGN   design-md: → design:
FIX      bug: / change: / doctor:
SHIP     deploy: [platform] → e2e: [url]
CLOSE    document: → changelog: → handoff: [mode]
```

### Every trigger at a glance

```
PLANNING
  brainstorm:               Start a new project from an idea
  architect:                Plan the architecture before coding
  agent:                    Design a multi-agent system
  new:                      Set up a greenfield project
  vibe-init                 Onboard an existing codebase

BUILD
  feature: [description]    Add a feature
  bug: [description]        Fix a bug
  change: [description]     Modify the spec mid-build
  review:                   Review the current phase (phase gate)
  review: phase 2           Review a specific phase
  test: [description]       Write tests for a change

VISIBILITY
  progress:                 Show project dashboard
  cost:                     Track this session's cost
  ledger:                   Generate HTML cost report
  graph:                    Generate dependency graph

DESIGN
  design-md: [url]          Fetch or generate design system
  design: [description]     Design or redesign a component/page

ADVANCED
  parallel:                 Run tasks with parallel subagents
  mode: autonomous          Run until done without prompting
  mode: supervised          Wait for approval between tasks
  perf:                     Performance audit
  doctor:                   Environment health check

SHIP
  deploy: railway           Prepare for Railway deployment
  deploy: render            Prepare for Render deployment
  deploy: fly               Prepare for Fly.io deployment
  deploy: heroku            Prepare for Heroku deployment
  deploy: vercel            Prepare for Vercel deployment
  deploy: netlify           Prepare for Netlify deployment
  deploy: github-pages      Prepare for GitHub Pages deployment
  e2e: https://[url]        Generate and run E2E tests
  e2e: run https://[url]    Run existing tests only
  e2e: regenerate           Rewrite tests from SPEC.md
  e2e: cleanup https://[url] Delete test data only

CLOSE
  document:                 Generate all documentation
  changelog:                Generate dev + client changelogs
  changelog: since v1.0     Generate changelog since a tag
  handoff: client           Full project delivery package
  handoff: milestone        Phase sign-off package
  handoff: dev              Developer onboarding package
  handoff: internal         Internal team handoff
  handoff: maintenance      Client dev team package
```

### Files the framework owns

```
BRIEF.md                    ← brainstorm output — project definition
CLAUDE.md                   ← root instructions read every session
CHANGELOG.md                ← developer changelog (git tag based)
CHANGELOG_CLIENT.md         ← plain English changelog for clients

vibe/
  SPEC.md                   ← features, acceptance criteria, out of scope
  ARCHITECTURE.md           ← tech decisions, patterns, principles
  TASKS.md                  ← single source of truth for all tasks
  DECISIONS.md              ← architectural decisions with reasoning
  CODEBASE.md               ← codebase map, updated every session
  DESIGN_SYSTEM.md          ← design tokens, components, patterns

  features/[date-slug]/
    FEATURE_SPEC.md
    FEATURE_PLAN.md
    FEATURE_TASKS.md

  bugs/[date-slug]/
    BUG_SPEC.md
    BUG_PLAN.md
    BUG_TASKS.md

  cost/
    history.json            ← every session's cost data
    summary.json            ← rich context for vibe-ledger
    ledger/index.html       ← generated HTML cost report

  handoff/[mode]-[date]/
    *.md                    ← handoff documents
    index.html              ← self-contained portal

railway.json / render.yaml / fly.toml / Procfile / vercel.json / netlify.toml
  ← generated by vibe-deploy

e2e/
  playwright.config.ts
  tests/
  cleanup.ts
```

### Task size labels

```
S — Small    Quick fixes, config changes, minor UI tweaks    ~$0.05/task
M — Medium   Features, screens, API endpoints               ~$0.13/task
L — Large    Complex features, real-time, auth, migrations  ~$0.30/task
```

### Phase gate rules

```
Phase N cannot proceed to Phase N+1 until review: passes with zero P0 issues.
Final phase review must pass zero P0 + zero P1 before deploy.
vibe-review is the enforcer. No exceptions.
```

### Severity levels used in review and issues

```
P0   Blocking — must fix before next phase or deploy
P1   Significant — must fix before deploy
P2   Should fix — add to backlog
P3   Nice to fix — cosmetic or edge case
```

### Cost waste patterns vibe-cost detects

```
CP-01    Context window too large — CODEBASE.md needs splitting
CP-02    Repeated re-reads — same files loaded every session
CP-03    Output-heavy session — large files generated from scratch
CP-04    No prompt caching — paying full price every session
CP-05    Review session expensive — too many files in context
CP-06    Small tasks in separate sessions — should be batched
CP-07    Tooling sessions accumulating — batch cost checks
CP-GAP   Tracking gap — sessions run without cost tracking
```

### Handoff modes and audiences

```
handoff: client       →  Non-technical client stakeholder
handoff: milestone    →  Client + PM, end of a phase
handoff: dev          →  Developer taking over the codebase
handoff: internal     →  BetaCraft team member handoff
handoff: maintenance  →  Client's own technical team
```

### Deploy platform quick reference

```
Platform        Config file        Database              Best for
────────────────────────────────────────────────────────────────────
railway         railway.json       PostgreSQL plugin      Full-stack, multi-service
render          render.yaml        PostgreSQL service     Background workers
fly             fly.toml/service   Fly Postgres           Containers, global
heroku          Procfile+app.json  Heroku Postgres add-on Legacy, simple
vercel          vercel.json        External only          Next.js, frontend
netlify         netlify.toml       External only          Static, JAMstack
github-pages    .github/workflow   None                   Static sites only
```

### E2E quick reference

```
First run     e2e: https://url      Generates tests + runs them
Re-run        e2e: run https://url  Runs existing tests only
Update tests  e2e: regenerate       Rewrites from SPEC.md (preserves helpers)
Cleanup only  e2e: cleanup url      Deletes test data, no tests run

OAuth flows   → always test.skip() — cannot be automated
Two users     → browser.newContext() in parallel, always in finally block
Test emails   → qa-[role]-[timestamp]@[project]-test.invalid
Video         → retained on failure only
Playwright    → installed into e2e/ only, never touches app dependencies
```

### Changelog quick reference

```
changelog:              Generate both files for current version
changelog: since v1.0   Generate since a specific git tag

CHANGELOG.md            Keep a Changelog format, task IDs, decisions
CHANGELOG_CLIENT.md     Plain English, product update style, zero tech terms

Version detection order:
  1. git tag --sort=-version:refname  ← primary
  2. package.json version field       ← fallback
  3. pyproject.toml version field     ← fallback
  4. [Unreleased]                     ← if nothing found

Scoping rule: git log [last-tag]..HEAD — never date-based
```

---

## Project structure after `new:`

```
my-project/
├── CLAUDE.md                   ← read every session
├── BRIEF.md                    ← project definition
├── CHANGELOG.md                ← dev changelog
├── CHANGELOG_CLIENT.md         ← client changelog
│
├── vibe/
│   ├── SPEC.md
│   ├── ARCHITECTURE.md
│   ├── TASKS.md
│   ├── DECISIONS.md
│   ├── CODEBASE.md
│   ├── DESIGN_SYSTEM.md
│   ├── features/
│   ├── bugs/
│   ├── reviews/
│   ├── cost/
│   └── handoff/
│
├── backend/                    ← your app code
├── web/
├── mobile/
└── e2e/                        ← generated by vibe-e2e
```

---

## Design principles

**Skills are instruction sets, not scripts.**
They run inside Claude Code's context window. No external processes, no servers, no npm packages required for the framework itself — only for what it builds.

**Everything is grounded.**
Every skill reads actual project files before doing anything. SPEC.md, TASKS.md, DECISIONS.md, git history. Nothing is invented. If a section has no data source, it says so rather than fabricating content.

**Docs are first-class.**
The framework produces documents that serve real audiences — developers, clients, PMs. CHANGELOG_CLIENT.md is readable by a business owner. DELIVERY.md can be sent directly to a client. ONBOARDING.md gets a new dev running in 30 minutes.

**Cost is visible.**
Every session is tracked. Every task has a cost. The ledger shows where money went. Waste patterns are flagged before they compound. summary.json bridges raw cost data and human-readable reports.

**The gate is real.**
vibe-review is not optional. Phase gates are enforced. P0 issues block progress. This is what makes the output shippable rather than just generated.

**Two audiences, always.**
Client documents are plain English — no task IDs, no framework names, no file paths. Developer documents are precise and technical. The framework never conflates the two.

---

## Contributing

Built and maintained by **Aakash Dhar** ([@aakashdhar](https://github.com/aakashdhar)) at [BetaCraft](https://betacraft.in).

Issues, suggestions, and skill contributions welcome — skills are just markdown files with a consistent structure. Open a PR with your skill in its own folder following the existing naming convention.

If this framework has been useful to you, give Aakash a follow — [@aakashdhar](https://github.com/aakashdhar).

---

## License

MIT — use freely, attribution appreciated.
