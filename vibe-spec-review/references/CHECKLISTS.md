# CHECKLISTS.md

The vibe spec-review checklists. Read by the **rubric** goldfish reviewer
(`vibe-gf-rubric`), together with the example rubrics in this folder
(BRIEF_RUBRIC.md, AGENT_ARCH_RUBRIC.md, SPEC_RUBRIC.md). Each item names its severity.

Apply only the sections for the documents in your task. Section 6 (cross-document
consistency) always applies when two or more documents are in scope.

**Where the six core areas live.** In a vibe project the build, test and git commands
are written to the project `CLAUDE.md` (by vibe-new-app / vibe-init), not to SPEC.md.
For check 3A, an area counts as present when it is in SPEC.md, ARCHITECTURE.md, or a
`CLAUDE.md` that your task lists as a document. Only report it missing when none of them
has it.

---

## 1 — Audit BRIEF.md

**Skip if BRIEF.md does not exist.**

Read the full BRIEF.md. Check against `references/BRIEF_RUBRIC.md`.

### 1A — Problem definition
- [ ] Is the core problem stated in one clear sentence? (vague = P1)
- [ ] Is the problem grounded in a real user pain? (generic = P1)
- [ ] Does it say who has the problem specifically? (missing = P0)

### 1B — User definition
- [ ] Is at least one primary user type defined? (missing = P0)
- [ ] Is the user described with enough specificity to make design decisions?
      ("small business owners" = too vague = P1 / "marketing managers at B2B SaaS companies with 10-50 employees" = good)

### 1C — Success criteria
- [ ] Are success criteria present? (missing = P0)
- [ ] Are they measurable? ("users are happy" = P0 / "user completes onboarding in <5 minutes" = good)
- [ ] Could a developer write a test for each criterion? (untestable = P1)
- [ ] Is there at least one quantitative metric? (none = P1)

### 1D — Constraints and non-goals
- [ ] Are technical constraints stated? (missing = P1)
- [ ] Are non-goals stated? (missing = P1 — without non-goals, scope creep is guaranteed)
- [ ] Is the v1 scope explicitly bounded? (unbounded = P1)

### 1E — Risks
- [ ] Are known risks or open questions listed? (missing = P2)
- [ ] Are dependencies on external systems noted? (missing = P1 if applicable)

---

## 2 — Audit AGENT_ARCH.md

**Skip if AGENT_ARCH.md does not exist.**

Read the full AGENT_ARCH.md. Check against `references/AGENT_ARCH_RUBRIC.md`.

### 2A — Pattern and framework
- [ ] Is a pattern selected with reasoning? (missing = P1)
- [ ] Is pattern selection appropriate for the stated complexity?
      (Orchestrator+Subagents for a 2-step pipeline = P1 over-engineering)
- [ ] Is a framework selected? (missing = P1)
- [ ] Does the framework match the stated stack? (mismatch = P0)

### 2B — Agent roles
- [ ] Does every agent have exactly one stated responsibility? (multiple = P1)
- [ ] Are agent names descriptive of their function? (Agent1, Agent2 = P2)
- [ ] Is there an orchestrator defined if the pattern requires one? (missing = P0)
- [ ] Does any agent's responsibility overlap with another's? (overlap = P1)

### 2C — VerifierAgent coverage
- [ ] Does every sub-agent have a corresponding VerifierAgent? (missing = P0)
- [ ] Does each verifier have a defined rubric (not just "checks quality")? (vague = P1)
- [ ] Is retry logic defined? (retry once → HITL = required, missing = P1)
- [ ] Does each verifier have a PASS/FAIL verdict format? (missing = P1)

### 2D — HITL checkpoints
- [ ] Are HITL checkpoints defined for irreversible actions? (missing = P0 if applicable)
- [ ] Does each checkpoint define what the human sees? (vague = P1)
- [ ] Does each checkpoint define available actions? (missing = P1)
- [ ] Is timeout behaviour defined for each checkpoint? (missing = P2)

### 2E — Tool mapping
- [ ] Does every tool have an assigned owner agent? (unassigned = P1)
- [ ] Are write tools flagged for risk? (unflagged write tool = P1)
- [ ] Are external API dependencies noted? (missing = P1)
- [ ] Do any write tools lack a HITL gate? (missing HITL before irreversible write = P0)

### 2F — State design
- [ ] Is state ownership defined per key? (missing = P1)
- [ ] Are there any multi-writer state keys? (multi-writer = P0 — race condition risk)
- [ ] Is cross-run memory need addressed? (yes/no required, missing = P2)

### 2G — Implementation plan
- [ ] Is an implementation order defined? (missing = P1)
- [ ] Does implementation order respect dependencies? (misordered = P0)

---

## 3 — Audit SPEC.md / vibe/SPEC.md

**Skip if neither exists.**

Read the full SPEC.md. Check against `references/SPEC_RUBRIC.md`.

### 3A — O'Reilly six core areas check
Per the O'Reilly northstar, a complete spec covers six areas.
Score each as present (✅) / partial (⚠️) / missing (❌):

- [ ] **Commands** — build, test, lint, run commands with exact flags (missing = P1)
- [ ] **Testing** — framework, file locations, coverage expectations (missing = P1)
- [ ] **Project structure** — where source, tests, docs live (missing = P1)
- [ ] **Code style** — naming conventions, formatting, real code example (missing = P2)
- [ ] **Git workflow** — branch naming, commit format, PR process (missing = P2)
- [ ] **Boundaries** — three-tier system: always / ask first / never (missing = P1)

Any missing area with P1 severity is a collective finding:
> "Spec is missing [N] of the 6 O'Reilly core areas: [list]. These will cause agent confusion during build."

### 3B — Acceptance criteria quality
For each feature / requirement in SPEC.md:
- [ ] Does it have acceptance criteria? (missing = P0 on any item)
- [ ] Is each criterion testable by a developer? (untestable = P1)
- [ ] Is each criterion specific enough to write a single test for? (vague = P1)
- [ ] Are edge cases and error states covered? (missing on critical paths = P1)

**Testability test:** Can you write `expect([something]).toBe([specific value])`
from this criterion? If no — it's untestable.

Examples:
- "Users should have a good experience" → P0 untestable
- "Users can log in" → P1 incomplete (no error state, no timeout)
- "User submits valid email + password → redirected to /dashboard within 2s" → ✅

### 3C — Scope and non-goals
- [ ] Is v1 scope explicitly defined? (missing = P1)
- [ ] Are non-goals listed? (missing = P1)
- [ ] Does scope align with BRIEF.md? (contradiction = P0)
- [ ] Are deferred features documented? (missing = P2)

### 3D — Tech stack completeness
- [ ] Is the primary language and framework stated with version? (missing = P1)
- [ ] Is the database stated? (missing = P1 if applicable)
- [ ] Are key dependencies listed? (missing = P2)
- [ ] Does the stack match what ARCHITECTURE.md prescribes? (mismatch = P0)

### 3E — Provisional flag check
If SPEC.md contains `⚠️ PROVISIONAL` (set by vibe-init):
> "⚠️ P1: SPEC.md is marked PROVISIONAL — generated from code, not from original requirements. Human must verify it reflects actual intent before this review is considered complete."

---

## 4 — Audit ARCHITECTURE.md / vibe/ARCHITECTURE.md

**Skip if neither exists.**

Read the full ARCHITECTURE.md. Check against the `# ARCHITECTURE_RUBRIC.md` section inside `references/SPEC_RUBRIC.md`.

### 4A — Pattern documentation
- [ ] Is the primary architectural pattern stated? (missing = P1)
- [ ] Is the folder structure defined? (missing = P1)
- [ ] Is state management approach defined? (missing = P1 for frontend projects)
- [ ] Is the API design pattern defined (REST/GraphQL/tRPC)? (missing = P1 if applicable)

### 4B — Convention completeness
- [ ] Are naming conventions defined? (missing = P1)
- [ ] Is TypeScript strictness level stated? (missing = P1 for TS projects)
- [ ] Is error handling pattern defined? (missing = P1)
- [ ] Are testing conventions defined? (missing = P1)

### 4C — Boundary definition (three-tier)
- [ ] Is an Always section present? (missing = P1)
- [ ] Is an Ask First section present? (missing = P1)
- [ ] Is a Never section present? (missing = P1)
- [ ] Does Never include "never commit secrets"? (missing = P0)
- [ ] Are the three tiers specific enough to act on?
      ("write good code" in Always = P1 too vague)

### 4D — SPEC.md alignment
- [ ] Does the tech stack match SPEC.md? (mismatch = P0)
- [ ] Do architectural patterns support the spec's requirements? (gap = P1)
- [ ] Are there requirements in SPEC.md that have no architectural pattern? (gap = P1)

### 4E — Performance and security
- [ ] Are performance expectations defined? (missing = P2)
- [ ] Are security requirements stated? (missing = P1 for any user-facing system)
- [ ] Are authentication/authorisation patterns defined? (missing = P0 if auth required)

---

## 5 — Audit FEATURE_SPEC.md

**Skip if no FEATURE_SPEC.md exists.**

Read the FEATURE_SPEC.md for the current feature.
Check against the `# FEATURE_SPEC_RUBRIC.md` section inside `references/SPEC_RUBRIC.md`.

### 5A — Acceptance criteria
- [ ] Every task has acceptance criteria (missing = P0)
- [ ] Every criterion is testable (untestable = P1)
- [ ] Error states are covered on every user-facing task (missing = P1)
- [ ] Edge cases are covered on critical paths (missing = P1)

### 5B — Scope boundary
- [ ] Does FEATURE_SPEC.md define what is explicitly OUT of scope? (missing = P1)
- [ ] Does it contradict anything in SPEC.md? (contradiction = P0)
- [ ] Does it introduce a new pattern not in ARCHITECTURE.md? (undocumented pattern = P1)

### 5C — Task quality
- [ ] Every task has a Touches field listing specific files (missing = P1)
- [ ] Every task has a Dependencies field (missing = P1)
- [ ] Every task is scoped to a single file or concern (multi-file sprawl = P1)
- [ ] Task sizes are estimated (S/M/L) (missing = P2)

---

## 6 — Cross-document consistency check

Check for contradictions across all documents that exist.

**BRIEF.md ↔ SPEC.md:**
- Does SPEC.md scope match BRIEF.md's v1 definition? (mismatch = P0)
- Do SPEC.md success criteria satisfy BRIEF.md's success criteria? (gap = P1)

**SPEC.md ↔ ARCHITECTURE.md:**
- Does the tech stack match? (mismatch = P0)
- Do architectural constraints allow the spec's requirements? (conflict = P0)

**AGENT_ARCH.md ↔ SPEC.md:**
- Does every agent's output map to a SPEC.md requirement? (orphaned agent = P1)
- Does every SPEC.md requirement that needs an agent have one? (missing agent = P0)

**AGENT_ARCH.md ↔ ARCHITECTURE.md:**
- Does the agent framework match the stated stack? (mismatch = P0)
- Do agent patterns conflict with architectural conventions? (conflict = P1)

---

