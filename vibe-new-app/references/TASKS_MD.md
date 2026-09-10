# TASKS_MD.md Template

Used by vibe-new-app Step 7 to generate `vibe/TASKS.md` — the single
human-facing file. Every phase is fully represented. Phase 2 is the complete
ordered feature list derived from PLAN.md Section 6 (Feature Map), with
dependencies visible — not slugs.

**Non-negotiable rules**
- Build order + dependency reason visible for every Phase 2+ feature.
- `feature: [name]` trigger visible on every planned feature.
- Phase gate instruction visible at the end of each phase.
- Plain English everywhere — what the user experiences, not internals.
- A human should never need to open PLAN.md to know what to build next.

---

```markdown
# TASKS — [Project Name]
> [2-3 plain English sentences: what this app does, who it's for, core value.]
> One file to watch. Updated after every task.

## Phase 1 — Foundation
> No user-facing features. Sets up everything Phase 2 depends on.
> Phase 1 exit: run `review: phase 1` when all tasks complete.

[ ] P1-001 · [Task] — [one plain English line]
[ ] P1-002 · [Task] — [one plain English line]
[ ] P1-00N · Populate CODEBASE.md — document everything built in Phase 1

## Phase 1 gate
⬜ review: phase 1 — pending

## Design gate (UI projects)
⬜ design: — pending · UI features need a shared design language first
   (`design-md:` then `design:`, or `design:` alone). Skip only for non-UI projects.

## Phase 2 — Core features
> Build order is deliberate. Features are sequenced by dependency.
> A feature marked [needs: X] cannot start until X is complete.
> Features marked [parallel with: X] can run simultaneously with X.
> Phase 2 exit: run `review: phase 2` when all features complete.

⬜ [Feature 1 name] — [what the user can do when this is done]
   Build order: 1 · No dependencies · Start here after Phase 1 gate passes
   Shared data: creates [Entity] used by Feature 2 and Feature 3
   Estimate: ~[N] hours
   Spec: run `feature: [name]` to plan this feature in detail

⬜ [Feature 2 name] — [what the user can do]
   Build order: 2 · Needs: Feature 1 complete
   Reason: reads [Entity] created by Feature 1
   Parallel with: Feature 3 (no shared writes)
   Estimate: ~[N] hours
   Spec: run `feature: [name]` to plan this feature in detail

## Phase 2 gate
⬜ review: phase 2 — pending

## Phase 3 — Polish and hardening
> Runs after Phase 2 gate passes. No new features.
> Phase 3 exit: run `review: final` — 0 P0 + 0 P1 before deploy.

⬜ Performance audit — profile and fix slow paths
⬜ Error handling pass — all edge cases, empty states, error boundaries
⬜ Accessibility audit — WCAG AA for all screens
⬜ E2E tests — critical user flows automated
⬜ Security review — auth, input validation, secrets, dependencies
⬜ Documentation — README, API docs, deployment guide

## Final gate
⬜ review: final — pending

## Phase 4+ — Future (not in current build)
> Planned so Phase 1-3 architecture doesn't foreclose these.
> Run `brainstorm:` when ready to plan the next version.

⬜ [Future feature] — [one sentence] · planned for v2

---
## What just happened
[Project name] project kit created. Phase 1 ready to begin.

## What's next
⬜ P1-001 · [First Phase 1 task in plain English]
Start Phase 1: read CLAUDE.md then vibe/TASKS.md. Say "next" for each task.
Run `review: phase 1` when all Phase 1 tasks are complete.
```

---

## Update rules (how TASKS.md changes over the build)

- **Status markers:** `[ ]`/`⬜` pending · `[x]` done · `[~]` partial · `[!]` blocked.
- After every task: tick it, then rewrite **What just happened** / **What's next**.
- When `feature:` plans a Phase 2 feature, its line stays but gains a link to
  `vibe/features/[slug]/FEATURE_TASKS.md`.
- Phase gate lines flip `⬜ pending` → `✅ passed [date]` only when `review:`
  reports 0 P0 (0 P0 + 0 P1 for the final gate).
- Never delete completed phases — they are the project's visible history.
