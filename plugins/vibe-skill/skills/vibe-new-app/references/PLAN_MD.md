# PLAN_MD.md

The canonical PLAN.md template for vibe-* projects.
Used by vibe-new-app to generate PLAN.md.
The feature map section is the critical addition — it plans every feature
across every phase before a single task runs.

Downstream consumers and what they read:
  vibe-new-app:     generates TASKS.md from the feature map
  vibe-add-feature: reads feature map before drafting spec — checks dependencies
  vibe-change-spec: reads feature map to assess phase impact of scope changes
  vibe-review:      reads phase boundaries to understand scope of each gate

---

## PLAN.md TEMPLATE

```markdown
# PLAN.md — [Project Name]
> Created: [date] · Last updated: [date]
> Source: BRIEF.md + ARCHITECTURE.md + SPEC.md

---

## 1. Project structure

\`\`\`
[Exact folder/file layout — matches ARCHITECTURE.md]
[Every planned file with one-line comment explaining its role]
\`\`\`

---

## 2. Tech stack

| Layer | Choice | Why |
|-------|--------|-----|
| Frontend | [choice] | [reason] |
| Backend | [choice] | [reason] |
| Database | [choice] | [reason] |
| Auth | [choice] | [reason] |
| Hosting | [choice] | [reason] |
| Key libraries | [list] | [reason] |

---

## 3. Architecture overview

\`\`\`
[ASCII diagram showing how the main parts connect]
[Data flow from user action to database and back]
[Agent topology if agentic project]
\`\`\`

---

## 4. Data model

| Entity | Key fields | Relationships |
|--------|-----------|---------------|
| [Entity] | [field: type, field: type] | [belongs to X, has many Y] |

Full schema:
\`\`\`
[Complete schema with types, constraints, indexes]
\`\`\`

**Shared data — used across multiple features:**
| Data | Used by features | Notes |
|------|-----------------|-------|
| [Table/entity] | [Feature A, Feature B] | [e.g. "Feature A writes, Feature B reads"] |

---

## 5. API contract

| Method | Path | Auth | Request | Response | Used by |
|--------|------|------|---------|----------|---------|
| [METHOD] | [/path] | [Yes/No] | [body shape] | [response shape] | [Feature] |

---

## 6. Feature map — all phases planned

> This is the complete build plan. Every feature across every phase.
> Sequencing is deliberate — features listed in the order they should be built.
> Dependencies are explicit — a feature cannot start until its dependencies are complete.
> This map is the source of truth for TASKS.md Phase 2+.

### Phase 1 — Foundation
*No user-facing features. Pure scaffolding, auth, and data layer.*
*All Phase 2 features depend on Phase 1 being complete.*

| Task | What it does | Size |
|------|-------------|------|
| Scaffold project structure | [What gets created] | [S/M/L] |
| Configure database | [Schema, migrations] | [S/M/L] |
| Set up auth | [Auth provider, user model] | [S/M/L] |
| Configure hosting/CI | [Deployment, env vars] | [S/M/L] |
| Populate CODEBASE.md | [Last task — documents everything built] | S |

**Phase 1 exit gate:** `review: phase 1` — 0 P0 findings before Phase 2 begins.

---

### Phase 2 — Core features
*The features that deliver the core value from BRIEF.md.*
*Build order matters — features are sequenced by dependency.*

#### [Feature 1 name] — [one sentence: what it lets the user do]
**Build order:** 1 (no dependencies — start here)
**Depends on:** Phase 1 complete
**Depended on by:** [Feature 2], [Feature 3]
**Shared data:** Creates [Entity] used by [Feature 2] and [Feature 3]
**New data:** [Tables/fields this feature adds]
**New routes:** [Endpoints this feature adds]
**Estimated size:** [S/M/L] — [N] tasks, ~[N] hours

| Sub-task | Type | Size |
|----------|------|------|
| [Data layer task] | data | [S/M/L] |
| [Backend task] | backend | [S/M/L] |
| [Frontend task] | frontend | [S/M/L] |
| [Tests task] | tests | S |

**Done when:** [Plain English — what the user can do when this feature is complete]
**Spec:** `vibe/features/[date-slug-feature-1]/` ← created when `feature: [name]` runs

---

#### [Feature 2 name] — [one sentence]
**Build order:** 2
**Depends on:** Phase 1 + Feature 1 complete
**Reason for dependency:** [Why Feature 1 must be built first — e.g. "reads [Entity] created by Feature 1"]
**Depended on by:** [Feature 4]
**Shared data:** Reads [Entity] from Feature 1, creates [New Entity]
**New data:** [Tables/fields]
**New routes:** [Endpoints]
**Estimated size:** [S/M/L] — [N] tasks, ~[N] hours

| Sub-task | Type | Size |
|----------|------|------|
| [Data layer task] | data | [S/M/L] |
| [Backend task] | backend | [S/M/L] |
| [Frontend task] | frontend | [S/M/L] |
| [Tests task] | tests | S |

**Done when:** [Plain English]
**Spec:** `vibe/features/[date-slug-feature-2]/` ← created when `feature: [name]` runs

---

#### [Feature 3 name] — [one sentence]
**Build order:** 3
**Depends on:** Phase 1 + Feature 1 complete
**Reason for dependency:** [Why]
**Depended on by:** None — can be built in parallel with Feature 2
**Can run in parallel with:** Feature 2 (no shared writes, no data dependency)
**Shared data:** Reads [Entity] from Feature 1 only
**New data:** [Tables/fields]
**New routes:** [Endpoints]
**Estimated size:** [S/M/L] — [N] tasks, ~[N] hours

**Done when:** [Plain English]
**Spec:** `vibe/features/[date-slug-feature-3]/` ← created when `feature: [name]` runs

---

[Repeat for each Phase 2 feature]

**Phase 2 build order summary:**
\`\`\`
Phase 1 complete
    ↓
Feature 1 (no deps — start here)
    ↓           ↓
Feature 2    Feature 3 (parallel — no shared writes)
    ↓           ↓
        Feature 4 (needs Feature 2 + 3)
            ↓
        Feature 5 (needs Feature 4)
\`\`\`

**Phase 2 exit gate:** `review: phase 2` — 0 P0 findings before Phase 3 begins.

---

### Phase 3 — Polish and hardening
*Non-functional improvements. No new features.*
*Run only after Phase 2 review passes.*

| Task | What it does | Size | Depends on |
|------|-------------|------|-----------|
| Performance audit | [What gets profiled] | M | Phase 2 complete |
| Error handling pass | [Edge cases, empty states] | M | Phase 2 complete |
| Accessibility audit | [What gets checked] | S | Phase 2 complete |
| E2E tests | [Critical user flows] | M | Phase 2 complete |
| Security review | [Auth, input validation, secrets] | M | Phase 2 complete |
| Documentation | [README, API docs] | S | Phase 2 complete |

**Phase 3 exit gate:** `review: final` — 0 P0 + 0 P1 findings before deploy.

---

### Phase 4+ — Future phases (if applicable)
*Plan now so architecture decisions in Phase 1–3 don't block these.*
*These are not built yet — they inform what NOT to hard-code in earlier phases.*

#### [Future phase name] — [what it adds]
**When:** After Phase 3 ships and [condition — e.g. "100 users", "client signs off on v2"]
**Why planned now:** [What Phase 1-3 must not hard-code so Phase 4 is possible]
**Rough features:**
- [Feature] — [one sentence]
- [Feature] — [one sentence]
**Architectural implications for earlier phases:**
- [What Phase 1 must leave room for]
- [What Phase 2 features must not assume]

---

## 7. Component/module map

| Component/Module | Responsibility | Used by |
|-----------------|---------------|---------|
| [Name] | [What it does] | [Which features] |

---

## 8. Testing strategy

| Type | What's tested | When |
|------|-------------|------|
| Unit | [Pure functions, utilities] | Every task that adds logic |
| Component | [UI interactions, state] | Every UI task |
| Integration | [API endpoints with real DB] | Every backend task |
| E2E | [Critical user flows] | Phase 3 |

---

## 9. Known risks

| Risk | Phase affected | Implication | Mitigation |
|------|--------------|-------------|------------|
| [Specific risk] | [Phase N] | [Impact] | [Plan] |

---

## 10. Open questions (must resolve before affected phase starts)

- [ ] [Question] — affects [Phase N, Feature X] — must answer before [milestone]
- [ ] [Question] — affects [Phase N, Feature X] — must answer before [milestone]
(Delete when resolved — log resolution in DECISIONS.md)
```

---

## Feature map rules

**Every feature must have:**
- A build order number (1, 2, 3...)
- Dependencies listed explicitly (Phase 1, Feature X, or "None")
- A reason for each dependency ("reads Entity created by Feature X")
- A depended-on-by list (what breaks if this is skipped)
- Shared data callout (what it reads, what it writes, what others will consume)
- A plain English "done when" statement
- A size estimate (S/M/L) with task count and hour estimate

**Parallel features must be explicitly identified:**
If Feature B and Feature C both depend only on Feature A and have no
shared writes to the same tables/files — mark them explicitly as
"Can run in parallel with: Feature C/B"
This feeds directly into vibe-parallel wave planning.

**Future phases must be sketched even if not built:**
Phase 4+ features don't need full detail — they need enough to ensure
Phase 1-3 decisions don't accidentally foreclose them.
The key question: "What must earlier phases NOT hard-code so this stays possible?"

**The feature map is updated by change-spec, not manually:**
If scope changes mid-build — run `change:` which reads this map,
assesses impact, and updates it in the correct order.
Never edit PLAN.md directly.
