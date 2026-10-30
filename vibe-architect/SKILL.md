---
name: vibe-architect
description: >
  Architecture planning workflow for establishing code structure, patterns, and principles
  before any code is written. Runs after brainstorm: and before new: on every project.
  Triggers on "architect:" prefix, "plan the architecture", "architect this",
  "how should we structure this", "what patterns should we use".
  Runs on every project — architecture is never skipped (it can proceed without
  BRIEF.md by asking the stack questions directly, but the architecture step itself
  is not optional).
  Reads BRIEF.md stack decisions and confirms them explicitly before asking any questions —
  prevents scaffolding with wrong framework (e.g. Next.js when React+Vite is specified).
  Produces ARCHITECTURE.md from canonical template — structurally consistent so
  review:, fix-bug:, and add-feature: can parse it reliably every session.
  review: uses ARCHITECTURE.md as its primary reference for drift detection.
  Handles gracefully if BRIEF.md is missing. Detects existing ARCHITECTURE.md before overwriting.
---

# Vibe Architect Skill

Establishes the architectural foundation before a single line of spec or code is written.
Every pattern, convention, and structural decision made here becomes the law for the entire build.

**No application code. The only files this skill writes are:** `ARCHITECTURE.md` at the
project root, what vibe-spec-review writes when it runs (its records under
`vibe/goldfish/` and `vibe/spec-reviews/`, accepted fixes to the documents it reviews
(ARCHITECTURE.md, and BRIEF.md / AGENT_ARCH.md when Step 0 reviews them),
`vibe/DECISIONS.md`), the approval entry in `vibe/DECISIONS.md`, and
`vibe/.run_state.json` on a stop. It never edits BRIEF.md or AGENT_ARCH.md itself. They
are reviewed documents: BRIEF.md changes through `change:`, AGENT_ARCH.md through `agent:`.

**The order:** read the reviewed inputs and settle choices (Steps 0–5) → write
ARCHITECTURE.md (Step 6) → independent review (Step 7) → the person approves the reviewed
architecture (Step 8) → new:. Nothing is approved before the review.

> **Autonomous / headless mode.** At startup resolve the settings with
> `python3 ~/.claude/skills/vibe-mode/scripts/vibe_state.py mode` (`mode --run` when the
> caller says this skill was entered from `vibe-mode: run`). If `vibe_mode` is
> `autonomous`, every "wait", "ask", "confirm" and approval step in this skill follows
> vibe-mode's `references/HEADLESS.md` §2 instead: take the recommended option, accept a draft
> only as §2.2 allows (after its independent goldfish review where one runs), log each choice to `vibe/DECISIONS.md`, never ask the
> user, and stop — writing `vibe/.run_state.json` — only when a person is genuinely required.

---

## The O'Reilly principle this enforces

Spec before code — and architecture before spec. Without deliberate architecture decisions,
agents make reasonable but unconsidered defaults. Folder structure, naming conventions,
state management, error handling — these just happen, inconsistently.

ARCHITECTURE.md is the agent's constitution for the project.
Not what gets built (SPEC.md does that) — how everything gets built.
Every task from Phase 1 through Phase 3 is measured against it.
`review:` detects drift from it at every phase gate.

Good architecture on a small project costs 20 minutes.
Bad architecture on a small project costs days of refactoring.

---

## Step 0 — Read BRIEF.md, confirm stack, classify project type

**Check for existing ARCHITECTURE.md first:**
If ARCHITECTURE.md already exists at the project root:
> "An ARCHITECTURE.md already exists for this project.
> Do you want to update it (add new decisions) or start fresh (replace it entirely)?"
Wait for answer before proceeding. On "start fresh", the old review is archived in Step 6,
right before the new document is written.

**Check for BRIEF.md:**
If BRIEF.md does not exist:
> "BRIEF.md not found. Ideally run `brainstorm:` first — it captures the problem,
> user, stack preferences, and constraints that make architecture decisions meaningful.
>
> I can proceed without it by asking those questions now, or you can run brainstorm: first.
> Which do you prefer?"
- If proceeding without: ask for app name, core purpose, platform, and rough stack preference before Step 1.
- If running brainstorm first: stop here and tell user to run `brainstorm:` then return.

**Check the upstream reviews.** For each of BRIEF.md and AGENT_ARCH.md that exists:
```bash
python3 ~/.claude/skills/vibe-goldfish/scripts/goldfish.py status brief        # BRIEF.md
python3 ~/.claude/skills/vibe-goldfish/scripts/goldfish.py status agent-arch   # AGENT_ARCH.md
```
Exit 0 means that document's review converged on its current text. Anything else (2, 3,
or a "no goldfish review" error) means it was never reviewed, or changed since. Manual:
say so in one line and offer to run `spec-review:` on it now *(recommended)* or continue.
Autonomous: run vibe-spec-review on it first (preset `brief` or `agent-arch`), and stop
with it if it stops. A missing document is fine: both are optional.

**If BRIEF.md exists:** read it fully. Extract:
- Core problem and user
- Platform (mobile-first, desktop, both)
- v1 feature set and complexity
- Tech stack preferences or mandates ← CRITICAL
- Compliance requirements (affects architecture choices)
- Known risks
- Agentic flag (the `## Agentic flag` section and the `Agentic / AI` signal)

**Agentic projects: read AGENT_ARCH.md.**
- **AGENT_ARCH.md exists:** read it fully. Take the framework and language, the pattern,
  the agent roster, the state ownership table, the tools (with write and irreversible
  tools flagged), the HITL checkpoints and the boilerplate folder structure. They go into
  ARCHITECTURE.md's Agent topology section and folder structure (Step 6) as decided
  there, not decided again here. Say so out loud with the stack confirmation below.
- **Agentic flag is Yes and there is no AGENT_ARCH.md:** the agent design hasn't been done.
  Manual: stop and route the person to it:
  > "BRIEF.md flags this as an agentic project, but there's no AGENT_ARCH.md yet. Run
  > `agent:` first: it decides the framework, agents, state and HITL checkpoints that this
  > architecture has to hold. Then come back to `architect:`."
  Autonomous: record it in `vibe/DECISIONS.md` (autonomous-assumption: agentic flag set,
  no AGENT_ARCH.md, architecture written without an agent topology) and continue.

**Stack confirmation — mandatory before asking any questions:**

After reading BRIEF.md, immediately confirm the stack out loud:

> "Stack from BRIEF.md:
>   Frontend: [exact value from brief]
>   Backend:  [exact value from brief]
>   Database: [exact value from brief]
>   Auth:     [exact value from brief]
>   Agents:   [framework] ([language]) from AGENT_ARCH.md  *(agentic projects only)*
>
> Proceeding with this stack. I will NOT suggest alternatives unless
> a technical constraint discovered during this session requires it."

This one explicit confirmation step prevents the most common architect: failure:
silently defaulting to a popular framework (Next.js, Create React App) instead of
the stack already decided in brainstorm:.

If the stack seems mismatched for the requirements (e.g. brief says
"mobile app" but stack says "Next.js") — flag it now:
> "I notice the brief specifies [requirement] but the stack is [choice].
> This may cause [issue]. Recommend [alternative]. Proceed with brief's choice or switch?"

**Agent framework check (when AGENT_ARCH.md exists):** compare the framework and
Language rows of AGENT_ARCH.md's System overview table with the brief's backend stack. Many
frameworks ship in more than one language, so go by the Language row, not the framework
name. If they don't fit (e.g. a Python agent under a Node-only backend), flag it the same
way: name both, recommend one (often a separate agent service in the
agent's language), and ask. If the answer means a reviewed document must change, a
BRIEF.md change goes through `change:` and an AGENT_ARCH.md change through `agent:`
(update). Both re-run that document's review. Never edit them from here.

Wait for answer before continuing.

**Classify project type:**
- **Web app** — frontend (React/Vue/Svelte/Next.js etc) + optional backend
- **Mobile app** — React Native / Expo / Flutter
- **API service** — backend only, no UI
- **CLI tool** — command line
- **Static site** — HTML/CSS/JS, minimal interactivity
- **Library / package** — reusable code

Tell the user: "This is a [type] project. I'll ask about [relevant areas]."

Branch questions:
- Web app / Mobile app → Steps 1, 2 (if backend), 3, 4, 5
- API service → Steps 2, 3, 4, 5
- CLI / Library → Steps 3, 4, 5
- Static site → Step 1 (light), 4, 5

---

## Step 1 — Frontend architecture (web/mobile only)

Present as recommendations. User says "sounds good" or overrides.

> **Frontend structure — my recommendations:**
>
> 1. **Folder approach:** [Feature-based / Type-based] — I recommend [choice]
>    because [one sentence reason based on BRIEF.md size and complexity].
>    Sound good, or do you have a preference?
>
> 2. **State management:** For [app name], data is [describe from brief].
>    I recommend [Context+localStorage / Zustand / Redux / other]
>    because [one sentence reason]. Sound good?
>
> 3. **TypeScript:** Strict mode, no `any` — the O'Reilly framework requires this.
>    Any reason to deviate?
>
> 4. **Component library:** [Recommend based on design direction —
>    Tailwind only / shadcn/ui / Radix / none / existing if mandated].
>    Does this fit?

Lock in recommendations if user agrees. Note any overrides. The component library is
chosen before any `design:` run, from the brief's design direction. If `design:` later
needs a different library or token rule, that change goes through `change:`, which
re-runs this document's review.

---

## Step 2 — Backend architecture (if project has backend)

Skip entirely if client-only with no API.

> **Backend structure — my recommendations:**
>
> 1. **API style:** REST with clear resource naming.
>    Reason to use tRPC or GraphQL instead?
>
> 2. **Business logic:** [Route handlers / Service layer] —
>    I recommend [choice] because [reason based on complexity].
>
> 3. **Input validation:** [Zod / Joi / yup] at route entry before any logic.
>    For this stack, [Zod] is the best fit. Agree?
>
> 4. **Error responses:** Consistent envelope —
>    `{ success: false, error: { code, message } }`.
>    This is what review: checks for. Agree?

---

## Step 3 — Testing philosophy

> **Testing approach:**
>
> My recommended approach for [app name]:
> - Unit: pure functions, utilities, calculations — always
> - Component: user interactions, state changes, conditional rendering — always
> - Integration: [if backend] API endpoints with real DB — always
> - E2E: skip for v1 unless a flow is genuinely high-risk
>
> The O'Reilly framework requires tests for every task —
> what gets tested matters more than coverage numbers.
> Stricter or lighter than this?

Lock the testing philosophy.

---

## Step 4 — Code quality and git conventions

> **Code quality:**
>
> 1. **Linter:** ESLint strict — `no-any`, `no-unused-vars`, `react-hooks/exhaustive-deps`.
>    Existing config to follow?
>
> 2. **Formatter:** Prettier — single quotes, semicolons, 2-space indent,
>    100 char line length. Standard?
>
> 3. **Dependencies:** Pin exact versions, `npm audit` before every commit,
>    prefer packages >1M weekly downloads. Sound reasonable?
>
> 4. **Git commits:** Conventional format — `feat(scope)`, `fix(scope)`,
>    `docs(scope)`, `design(scope)`. Doc commits always separate from code.
>    This is what the framework uses throughout. Agree?
>
> 5. **Pre-commit hooks:** Linter + tests before every commit?

---

## Step 5 — Synthesise and check

> 🧠 **Effort:** architecture trade-offs are one-shot and load-bearing — `review:`
> enforces this document every phase. Reason at high/xhigh effort with adaptive
> thinking; weigh the alternatives explicitly before committing to patterns.

> **Architecture summary for [App Name]:**
>
> **Project type:** [type]
> **Frontend:** [structure] · [state] · TypeScript strict · [component library]
> **Backend:** [API style] · [logic layer] · [validation] · [error format]  *(if applicable)*
> **Testing:** [philosophy summary]
> **Quality:** ESLint strict + Prettier + conventional commits + pre-commit hooks
> **Dependencies:** pinned, npm audit before commit
>
> Did I get anything wrong? Any changes before I write ARCHITECTURE.md? (This is a check
> of the facts, not the sign-off: you approve the architecture after the independent
> review.)

Wait for the answer. Note every change: Step 6 writes them in.

---

## Step 6 — Generate ARCHITECTURE.md

**Start fresh only** (the person chose it in Step 0): set the old review aside first, so
findings settled on the old document can't settle findings on the new one:
```bash
python3 ~/.claude/skills/vibe-goldfish/scripts/goldfish.py archive architecture
```

Read `references/ARCHITECTURE_MD.md` for the full canonical template.

Generate ARCHITECTURE.md by filling every section of the template:
- **Project type section:** Copy stack from BRIEF.md verbatim. Include the
  "Do NOT scaffold with alternatives" warning with the specific stack chosen.
- **Folder structure:** Generate the actual project tree, not a generic example.
  This tree is the source: `new:` writes PLAN.md from it later. On an agentic project,
  include AGENT_ARCH.md's boilerplate structure where the agent code lives.
- **Agent topology:** filled from AGENT_ARCH.md when it exists (framework, pattern,
  agents, state ownership, tools, HITL). Delete the section when there is none.
- **Boundaries (Always / Ask First / Never):** fill all three tiers. Never keeps both
  universal items (one is the literal "Never commit secrets" rule), every conditional
  item whose layer the project has, and 2 project-specific ones derived from the
  conversation (e.g. "no direct Supabase calls outside repositories").
- **Testing table:** Adjust for project complexity (S/M/L from BRIEF.md).
- **Architecture decisions log:** Fill with the decisions made in Steps 1-5, with every
  change the person asked for in Step 5.
- **Delete inapplicable sections:** Backend section for client-only projects,
  database section if no DB, etc.

If updating existing ARCHITECTURE.md: add changelog entry and update
affected sections only. Never overwrite the Never list or decisions log.
If it has no Always or Ask First tier, or its Never list lacks the literal "Never commit
secrets" rule, add them from the template's Boundaries section (adding, not overwriting:
keep every existing Never item).

Save as `ARCHITECTURE.md` at project root.
*(Moved to `vibe/ARCHITECTURE.md` when `new:` runs.)*

---

## Step 7 — Spec review gate

ARCHITECTURE.md is a load-bearing document — `review:` audits every phase against
it. Audit it now, the same way `brainstorm:` audits BRIEF.md and `vibe-agent`
audits AGENT_ARCH.md, rather than leaving it to be checked indirectly later when
`new:` runs.

> "Architecture drafted. Running an independent review before you scaffold..."

Invoke `vibe-spec-review` with:
- Trigger source: `architect` (Trigger 2.5, preset `architecture`)
- Scope: ARCHITECTURE.md (BRIEF.md and AGENT_ARCH.md, when they exist, are read as
  related files)

Present the verdict.

**If spec-review stopped the run** (`python3 ~/.claude/skills/vibe-mode/scripts/vibe_state.py run-state show`
says needs_human from spec review), **stop here too**: end the session, don't continue,
don't report the step as done. In manual mode, a 🔴 verdict means follow spec-review
Step 3 (more rounds, rework, or the person accepts). Never fix findings outside vibe-goldfish.

Otherwise continue to Step 8.

---

## Step 8 — Approve the reviewed architecture and tell the user

**Check the review is current:**
```bash
python3 ~/.claude/skills/vibe-goldfish/scripts/goldfish.py status architecture
```
Exit 0 means the review converged on ARCHITECTURE.md as it is now. Anything else: manual,
tell the person plainly and offer to run `spec-review:` on ARCHITECTURE.md now;
autonomous, go back to Step 7. Never hand off a document whose status is not 0. (`new:`
checks this status too before it builds on ARCHITECTURE.md.) The only exceptions are the person's own choices in spec-review: continuing without a
review (⚠️ SPEC NOT REVIEWED) or continuing anyway on a 🔴 (status stays 3). Then ask for
approval as below, name that choice in the DECISIONS entry and on the card, and hand off.

**Manual mode: the person approves the reviewed text.** Show what the review changed, one
line per fix (from `vibe/goldfish/architecture/resolution.md`), then ask:
> "This is ARCHITECTURE.md after the independent review. Do you approve it as it is now?"

- **Approved:** append to `vibe/DECISIONS.md` (append-only: create it with its canonical
  header only if it doesn't exist, continue the `D-NNN` numbering):
  ```
  ### D-[ID]: ARCHITECTURE.md approved
  - **Type**: approval
  - **Skill / step**: vibe-architect · Step 8 (after the independent review)
  - **Approved**: ARCHITECTURE.md as reviewed · record: vibe/goldfish/architecture/resolution.md
  - **Approved by**: human
  ```
- **The person wants changes:** make them in ARCHITECTURE.md. The edit re-opens the
  review by itself, so go back to Step 7, then ask again here. Never hand off an edited
  document without that review.

**Autonomous mode:** the converged review is the acceptance (HEADLESS §2.2). Don't ask,
and don't add a self-approval.

Then tell the user:

---
> ✅ **Architecture locked** (independently reviewed, approved by [human / review converged (autonomous)]).
>
> **Decisions made:** [N]
> **O'Reilly principles:** enforced in every session via ARCHITECTURE.md
>
> Every task Phase 1 through Phase 3 follows these patterns.
> No agent defaults. No inconsistent conventions. No architectural drift.
> `review:` uses ARCHITECTURE.md as primary reference — drift caught at every gate.
>
> **To generate your project kit:**
> ```
> new: [your app description]
> ```
---

---

## How the agent uses ARCHITECTURE.md every session

Session startup order:
1. Read CLAUDE.md
2. Read vibe/CODEBASE.md
3. Read vibe/ARCHITECTURE.md — check patterns for today's task
4. Read vibe/SPEC_INDEX.md
5. Read vibe/TASKS.md

Before writing code: does this follow ARCHITECTURE.md patterns?
After writing code: did I introduce a new pattern not in ARCHITECTURE.md?
→ Yes: update ARCHITECTURE.md before marking task done.
→ Yes, and it was a necessary deviation: log in DECISIONS.md, update ARCHITECTURE.md.

## Document update rules

| Document | Updated when |
|----------|-------------|
| ARCHITECTURE.md | New pattern, library added, tech decision changed |
| BRIEF.md | Scope changes, core value refined, stack changed |
| SPEC.md + SPEC_INDEX.md | Always together — any scope change |
| PLAN.md | Architecture changes, phase structure changes |
| TASKS.md | After every single task — no exceptions |
| CODEBASE.md | New file, route, schema, or pattern added |
| DECISIONS.md | Every drift, scope change, tech choice mid-build |
| FEATURE_TASKS.md | Task done, decisions filled, checklist ticked |
| CLAUDE.md | Conventions change, active feature changes |

**The rule:** if something changed in the codebase, something changed in the docs.
If the docs aren't updated, the task isn't done.
