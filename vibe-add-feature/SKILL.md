---
name: vibe-add-feature
description: >
  Full spec-driven workflow for adding a feature to an existing codebase with an AI coding agent.
  Triggers on "feature:" prefix, "I want to add a feature", "add X to my project",
  "new feature", "build a feature for".
  Always use when adding functionality to an existing project — even without the exact prefix.
  Reads PLAN.md feature map before drafting (when the project has one): checks build order,
  dependencies, shared data. Stops and surfaces clearly if dependencies are not yet met.
  Marks unplanned features explicitly. Updates PLAN.md feature map after the reviews so it
  stays the live source of truth.
  Creates vibe/features/[date-slug]/ with FEATURE_SPEC.md, FEATURE_PLAN.md, FEATURE_TASKS.md.
  Spec and plan are reviewed independently and approved before tasks are written; tasks
  are reviewed before the build. Checks for an incomplete feature with the same name first.
  Reads SPEC.md before drafting to align with existing acceptance criteria.
  Updates TASKS.md (human progress view) and agent files.
---

# Vibe Add Feature Skill

Spec-driven feature planning for an existing project.
Creates a dated feature folder and updates the human progress view.
CODEBASE.md verified or generated first — future sessions never re-read from scratch.

**No application code while planning.** The only files this skill writes before the
build are: `vibe/CODEBASE.md`; the feature folder (`FEATURE_SPEC.md`, `FEATURE_PLAN.md`,
`FEATURE_TASKS.md`); the review records vibe-spec-review writes (`vibe/goldfish/`,
`vibe/spec-reviews/`); `vibe/design/` (the design pass, only when the feature adds UI);
`vibe/DECISIONS.md`; and, after the reviews, `CLAUDE.md`, `vibe/TASKS.md` and
`vibe/PLAN.md`; plus `vibe/.gates.json` and `vibe/.run_state.json` through vibe_state.py.
Code is written only when the tasks run.

**Order.** Draft, independent review, approval, then the files copied from the drafts.
The person approves FEATURE_SPEC.md and FEATURE_PLAN.md after their review (Step 8),
never before. Nothing is copied out of the feature documents into CLAUDE.md, TASKS.md,
DECISIONS.md or PLAN.md until FEATURE_TASKS.md has passed its own review (Step 11); the
copies are written in Step 12, so a review fix never has to chase a copy.

> **Autonomous / headless mode.** At startup resolve the settings once:
> ```bash
> VS="$HOME/.claude/skills/vibe-mode/scripts/vibe_state.py"
> python3 "$VS" mode        # JSON: vibe_mode, approvals, phases, source
> ```
> When the caller says this skill was entered from `vibe-mode: run`, use
> `python3 "$VS" mode --run` instead (it forces `vibe_mode: autonomous`). Never grep
> CLAUDE.md for the mode: every later step that branches on the mode reuses this
> `vibe_mode` value. If `vibe_mode` is
> `autonomous`, every "wait", "ask", "confirm" and approval step in this skill follows
> vibe-mode's `references/HEADLESS.md` §2 instead: take the recommended option, accept a draft
> only as §2.2 allows (after its independent goldfish review where one runs), log each choice to `vibe/DECISIONS.md`, never ask the
> user, and stop — writing `vibe/.run_state.json` — only when a person is genuinely required.

---

## The O'Reilly principles this enforces

**Spec before code** — FEATURE_SPEC.md with acceptance criteria exists before any task.
**Context preservation** — CODEBASE.md read first, ARCHITECTURE.md conventions followed.
**Incremental verifiable progress** — task breakdown with S/M/L estimates.
**Drift prevention** — DECISIONS.md updated, CLAUDE.md active feature section appended.

---

## Two audiences. Two file types.

**Human-facing:**
- `vibe/TASKS.md` — single progress view, plain English, updated after every task

**Agent-facing (human never opens these):**
- `vibe/features/[date-slug]/FEATURE_SPEC.md`
- `vibe/features/[date-slug]/FEATURE_PLAN.md`
- `vibe/features/[date-slug]/FEATURE_TASKS.md`
- `vibe/CODEBASE.md` · `vibe/ARCHITECTURE.md` · `vibe/DECISIONS.md` · `CLAUDE.md`

---

## Folder structure this skill creates

```
vibe/
├── TASKS.md                            ← human progress view — updated here
├── CODEBASE.md                         ← generated/updated here
├── DECISIONS.md                        ← updated (spec/scope)
├── PLAN.md                             ← feature map updated (when the project has one)
├── IMPLEMENTATION_LOG.md               ← appended (implementation decisions)
├── goldfish/feature-[date-slug]/       ← review record (written by vibe-spec-review)
└── features/
    └── [YYYY-MM-DD]-[feature-slug]/
        ├── FEATURE_SPEC.md
        ├── FEATURE_PLAN.md
        └── FEATURE_TASKS.md
CLAUDE.md                               ← project root, updated
```

**Slug rule:** kebab-case, first 4-5 meaningful words, stop words removed. Date = today.
Examples: `2026-03-20-reading-sessions` · `2026-03-20-dark-mode` · `2026-03-20-push-notifications`

---

## Step 1 — Check for existing feature and read codebase

**Check for existing feature with same or similar name:**
Scan `vibe/features/` for folders matching the requested feature.
If an incomplete feature folder exists:
> "Found an existing [feature] folder: vibe/features/[date-slug]/
> Resume that feature (recommended) or start fresh with a new folder?"
Wait for answer before proceeding.

Resuming picks up at the first step not done. Keep the drafts that exist. **Before the
build has started** (no task in FEATURE_TASKS.md is `[x]`, `[~]` or `[!]`), check the
reviews with `goldfish.py status feature-[date-slug]` (Step 7) and
`goldfish.py status feature-[date-slug]-tasks` (Step 11): a review that has not
converged is run again before anything after it. **Once the build has started**, the
build itself rewrites FEATURE_TASKS.md (status, criteria, decisions), so don't re-check
the reviews: go on with the next unfinished task, or with Steps 14-16 when every task is
`[x]`.

**Check the project's spec review** before this skill changes anything. The spec,
architecture and feature map this feature builds on should have been reviewed as they
are now:
```bash
python3 ~/.claude/skills/vibe-goldfish/scripts/goldfish.py status spec --json
```
(`spec` is the target of both vibe-new-app's and vibe-init's review.) Read the result:
- **Exit 0:** continue.
- **Exit 2, exit 3 (needs a person), or "no goldfish review" (never reviewed):** the
  review doesn't cover the documents as they are now. Feature bookkeeping (the PLAN.md
  `**Status:**`/`**Spec:**` lines, the CLAUDE.md Active Feature section, CODEBASE.md
  "Verified during" lines) never causes this, because the review ignores it. So exit 2
  means a reviewed document really changed: an unplanned addition to the feature map, an
  edit to SPEC or ARCHITECTURE, or a review that never finished.
  - Manual: say so in one line and offer to run `spec-review:` on the project spec now
    (recommended) or continue without it.
  - Autonomous: run `vibe-spec-review` on it first (Trigger 5, preset `init` when
    vibe/CODEBASE.md carries the vibe-init header (`📥 Generated by vibe-init`), otherwise `spec`). If it stops the run, stop here too.
No `vibe/SPEC.md` at all: there is nothing to check; continue.

**If that review changed an approved spec, the spec gate goes back to pending.** Before
running it, note `python3 "$VS" gate check spec` (exit 0 = cleared) and
`shasum vibe/SPEC.md vibe/ARCHITECTURE.md vibe/PLAN.md` (the ones that exist). After it,
compare the hashes. If the gate was `approved` and any of those files changed (a goldfish
fix), the approval no longer describes the spec, so before this skill writes anything:
`python3 "$VS" gate set spec --status pending --report vibe/goldfish/spec`. Then:
- Manual: show what the review changed, one line per fix (from
  `vibe/goldfish/spec/resolution.md`), and ask the person to approve the spec as it is
  now. On yes: `python3 "$VS" gate set spec --status approved --by human --report vibe/goldfish/spec`
  and a DECISIONS.md entry with `**Approved by**: human`, after the review. Don't draft
  the feature until it is approved.
- Autonomous, `approvals: auto`:
  `python3 "$VS" gate set spec --status approved --by agent-autonomous --report vibe/goldfish/spec`.
  If the helper refuses, STOP with
  `python3 "$VS" run-state set --status needs_human --reason "spec gate: [the helper's error]" --next "see vibe/goldfish/spec"`
  and end the session.
- Autonomous, `approvals: human`: leave it pending and STOP with
  `python3 "$VS" run-state set --status needs_human --reason spec_approval --next "approve the changed spec (gate set spec --status approved --by human --report vibe/goldfish/spec), then run vibe-mode: run"`
  and end the session.

**Read vibe/CODEBASE.md (or generate it):**

If vibe/CODEBASE.md exists:
Read it fully. Verify accuracy. If significantly out of date, refresh relevant sections.
Add changelog line: `> 📝 [date] · Verified during [feature-name] planning`

If vibe/CODEBASE.md does not exist:
- **If there is NO `vibe/` folder at all** (an existing repo never onboarded):
  recommend `vibe-init` first — it generates the full vibe/ set (ARCHITECTURE.md,
  SPEC.md, DECISIONS.md, TASKS.md, CLAUDE.md, …) so this feature builds on real parity, not
  a lone improvised CODEBASE.md. Offer: "This repo isn't set up for vibe yet — run
  `vibe-init` first (recommended), or I can generate just CODEBASE.md and proceed?"
- If the user declines init (or only CODEBASE.md is missing): read
  `references/CODEBASE_MD.md` for the generation template, explore the codebase
  (folder structure, package.json, patterns, DB schema, routes), and generate
  `vibe/CODEBASE.md`.

**Read vibe/ARCHITECTURE.md** if it exists — conventions must be followed throughout.

Confirm:
> "Codebase read. [Generated fresh / Verified existing] CODEBASE.md.
>  [Stack] project. Feature to add: [feature].
>  Proposed folder: vibe/features/[date-slug]/
>  Any questions before I draft the spec?"

---

## Step 2 — Read feature map and check dependencies

Before drafting FEATURE_SPEC.md, read:
- `vibe/SPEC.md` — existing features, acceptance criteria, out-of-scope items, data model
- `vibe/SPEC_INDEX.md` (if it exists) — for quick orientation to feature relationships
- `vibe/PLAN.md` Section 6 (Feature Map) — sequencing, dependencies, shared data

**If `vibe/PLAN.md` carries the vibe-init header** (`📥 Generated by vibe-init`), its
feature map lists only what existed at onboarding, so a new feature missing from it is
the normal case. Don't flag it as unplanned and don't send the person to `change:`. Take
dependencies from its Existing features entries, vibe/SPEC.md and vibe/CODEBASE.md, and
let Step 12D add the feature under `### Planned features` (not as an UNPLANNED ADDITION).

**If `vibe/PLAN.md` does not exist** (a project onboarded by vibe-init before v2.8.0 has
no feature map), say: "This project has no feature map (vibe/PLAN.md), so there is no planned build
order to check." Skip the feature map check below. Take dependencies and shared data
from vibe/SPEC.md and vibe/CODEBASE.md instead, and surface an unmet dependency the same
way. Don't call the feature unplanned and don't send the person to `change:`: there was
never a plan for it to be missing from. Continue to Step 3. (Step 12D skips the PLAN.md
update.)

**Feature map check — run before drafting:**

Find this feature in PLAN.md Section 6 and extract:

```python
feature_entry = plan_md.find_feature(requested_feature_name)

checks = {
    "dependencies_met":    all deps marked ✅ in TASKS.md,
    "shared_data_reads":   entities this feature reads from other features,
    "shared_data_writes":  entities this feature creates for other features,
    "parallel_candidates": features that can run simultaneously with this one,
    "depended_on_by":      features that cannot start until this one is done,
    "build_order":         expected position in the Phase 2 sequence
}
```

**If dependencies are NOT met — stop and surface clearly:**
> "⚠️ [Feature name] depends on [Feature X] which is not yet complete.
>
> [Feature X] must be built first because: [reason from PLAN.md]
> [Feature X] current status: [⬜ not started / 🔄 in progress]
>
> Options:
> (a) Build [Feature X] first — run `feature: [Feature X name]`
> (b) Proceed anyway — I'll flag all the missing data model pieces
>
> Which do you prefer?"
>
> Wait for answer. If (b) — note all missing dependencies in FEATURE_SPEC.md
> under a "Missing dependencies" section so the agent knows what to stub.

**If this feature creates data used by others — note it explicitly:**
> "This feature creates [Entity] which [Feature Y] and [Feature Z] will later consume.
> I'll make the schema decisions in this spec. Those features will reference back to it."

**If this feature can run in parallel with another — note it:**
> "[Feature N] can run in parallel with this one — no shared writes.
> If you want to build both simultaneously, say `parallel:` after both feature kits are ready."

**If PLAN.md exists but this feature is NOT in it — flag it:**
> "This feature wasn't in the original plan. This is fine — run `change:` first
> to assess impact on the data model and phase sequencing before I draft the spec.
> Or I can proceed and we treat it as an unplanned addition."

This ensures every feature spec:
- Is aware of what data already exists from earlier features
- Doesn't redefine entities that should come from a dependency
- Doesn't assume data model fields that haven't been built yet
- Integration points reference the correct existing spec sections
- Conformance checklist complements rather than duplicates the main conformance checklist

---

## Step 3 — Draft FEATURE_SPEC.md

Draft FEATURE_SPEC.md covering:
1. **Feature overview** — What it does and why (2-3 sentences)
2. **User stories** — Who does what, outcome
3. **Acceptance criteria** — Concrete, testable conditions for done
4. **Scope boundaries** — Included and explicitly deferred
5. **Integration points** — Exact files, routes, DB tables (use CODEBASE.md section 9)
   Reference relevant SPEC.md sections by anchor (e.g. SPEC.md#data-model)
6. **New data model changes** — Tables, fields, relationships
7. **New API endpoints** — Method, path, request/response (if applicable)
8. **Edge cases and error states** — What can go wrong
9. **Non-functional requirements** — Performance, security, mobile
10. **Conformance checklist** — What must be true for this feature to be shippable

Steps 4 and 5 add its UI part. Save as `vibe/features/[date-slug]/FEATURE_SPEC.md`.

Ask the person anything you need to know while drafting. Don't ask them to approve the
spec yet, and don't grade it against the rubric yourself: the independent review does
that (Step 7), and the person approves the reviewed text (Step 8).

---

## Step 4 — UI check (graduated — not binary)

Ask:
> "How much UI work does this feature involve?
> (a) New screens or significant new components → full wireframe
> (b) Minor additions to existing screens → brief UI note in spec
> (c) No UI — purely logic, data, or backend → skip"

**(c)** → skip to Step 6.
**(b)** → add a brief UI note to FEATURE_SPEC.md, skip to Step 6.
**(a)** → Step 5. The design pass (design system, contract, critique and the design gate)
runs later, in Step 9, from the reviewed and approved spec.

---

## Step 5 — UI Design (only for significant UI work)

**Requires: frontend-design skill.** Reference existing design system from
(in precedence order — `DESIGN.md` wins where they conflict):
- `DESIGN.md` (project root) if it exists — the brand token contract from
  `design-md:`. **Authoritative** for colours/type/spacing.
- `vibe/design/CONTRACT.md` if it exists — the per-project design contract from
  `design:`. New UI must obey it.
- `vibe/DESIGN_SYSTEM.md` if it exists (existing tokens — must be consistent).
- CODEBASE.md sections 2 and 6 (stack, patterns).

If none of these exist yet, draft from the existing screens. Step 9 offers to establish a
design language from the reviewed spec.

Ask all at once:
1. New screens or views being added? Existing screens being modified?
2. Main user interaction?
3. Layout preference? (modal, drawer, full page, inline)
4. Device? (mobile, desktop, both)
5. Anything complex? (multi-step, real-time, drag-drop)
6. UI references for inspiration?
7. Existing patterns to match? (from CODEBASE.md section 6 and DESIGN_SYSTEM.md)

Generate wireframe — must feel like it belongs in the existing product.
Present it and take the person's changes while drafting. This is not the sign-off: that
is Step 8, after the review. Append the UI Specification to FEATURE_SPEC.md, so the
review in Step 7 covers its screens' behaviour and states (flows, empty, loading and error
states, data each screen needs). That review does not judge the look; see Step 9.

---

## Step 6 — Draft FEATURE_PLAN.md

Read FEATURE_SPEC.md, CODEBASE.md, ARCHITECTURE.md, vibe/SPEC.md (integration sections).
Read integration point files directly before drafting.

Draft FEATURE_PLAN.md:
1. **Impact map** — Files to modify vs new files (exact paths from CODEBASE.md section 9)
2. **Files explicitly out of scope** — Must not be touched
3. **DB migration plan** — Exact schema changes
4. **Backend changes** — Routes, controllers, services with file paths
5. **Frontend changes** — Components, pages, hooks with file paths
6. **Conventions to follow** — Paste relevant patterns from CODEBASE.md section 6
7. **Task breakdown**: Data layer → Backend → Frontend (skip if no UI) → Tests
8. **Rollback plan** — How to undo this feature
9. **Testing strategy** — New tests, existing tests needing updates
10. **CODEBASE.md sections to update** — Which sections change as tasks complete

Save as `vibe/features/[date-slug]/FEATURE_PLAN.md`. Questions while drafting are fine;
approval comes after the review (Step 8).

---

## Step 7 — Design review (spec-review Trigger 4)

Announce to the user:
> "Feature designed. Running an independent review before the tasks are written..."

Invoke `vibe-spec-review` with:
- Trigger source: `add-feature`, Trigger 4
- Preset: `feature` (target `feature-[date-slug]`)
- Feature folder: `vibe/features/[date-slug]/` (FEATURE_SPEC.md, with its UI
  Specification, and FEATURE_PLAN.md are reviewed together, checked against vibe/SPEC.md)
- If this skill was entered from `vibe-mode: run`, say so.

**If spec-review stopped the run** (`python3 "$VS" run-state show` says needs_human from
spec review), **stop here too**: end the session, don't continue, don't report the step as
done. Nothing derived has been written, and nothing is written now: no CLAUDE.md section,
no TASKS.md mirror, no DECISIONS.md Feature Start entry, no PLAN.md change. Do not report
the feature as planned (not even under plan-only), do not show "Feature kit ready", and do
not build. `vibe-mode: run` resumes once a person has resolved it.

Manual mode: a 🔴 SPEC NOT READY verdict means follow spec-review's Step 3 (more rounds,
rework, or "continue anyway", which records the person accepting the documents as they
are in DECISIONS.md and the report). Never fix findings outside vibe-goldfish. Go on only
once the verdict is ✅, ⚠️ READY WITH ACCEPTED RISKS, or ⚠️ NOT REVIEWED, or the person
chose "continue anyway". That choice is the person's, in manual mode only; an agent never
makes it.

---

## Step 8 — Approve the reviewed design

**Manual mode.** Show what the review changed, one line per fix (from
`vibe/goldfish/feature-[date-slug]/resolution.md`), and any accepted risks. Then ask:
> "Review: [verdict]. It changed: [one line per fix, or 'nothing'].
>  Approve FEATURE_SPEC.md and FEATURE_PLAN.md as they are now? Anything to change?"

Wait for approval. If the person asks for changes, make them. An edit re-opens the review
by itself (the documents' hash changes), so run Step 7 again and ask again. Never go on
while `goldfish.py status feature-[date-slug]` is not 0, unless the verdict was ⚠️ NOT
REVIEWED (the person chose to continue without a review) or the person chose "continue
anyway" in Step 7 (recorded in DECISIONS.md). In both cases the approval below names it.

Record the approval in `vibe/DECISIONS.md` (append-only, continue the `D-NNN` numbering):
```
### D-[ID]: Feature design approved: [Feature Name]
- **Documents**: vibe/features/[date-slug]/FEATURE_SPEC.md · FEATURE_PLAN.md
- **Review**: [verdict] · vibe/goldfish/feature-[date-slug]/resolution.md
- **Approved by**: human, [date], after the review
```

**Autonomous mode.** The converged review is the acceptance (HEADLESS §2.2). Log it as an
`autonomous-approval` entry in DECISIONS.md (HEADLESS §2.4) and continue.

---

## Step 9 — Design pass (only for significant UI work, path (a))

Paths (b) and (c): skip to Step 10.

The design pass works from the reviewed and approved FEATURE_SPEC.md (its UI
Specification). It does not edit FEATURE_SPEC.md or FEATURE_PLAN.md. If it shows the UI
Specification must change, edit it, then run Steps 7 and 8 again before going on.

**Design-gate check:** if the project has **no** design system yet
(`DESIGN.md` / `vibe/DESIGN_SYSTEM.md` / `vibe/design/CONTRACT.md` all absent),
this feature would invent a look from scratch — the "skipped design" failure.
Offer to establish it before building:
> "No design language exists yet. Run `design:` first (optionally `design-md:` to
>  lock brand tokens) so this and future screens are consistent? Recommended.
>  Reply 'skip design' to build this feature's UI ad hoc."
In autonomous mode take the recommended option (run the design pass). On yes, run the
design gate flow (`VS` as in the startup header):
1. `design:` up to its Step 3.5 checkpoint (contract, tokens, preview; no production UI
   files before sign-off).
2. `design: critique` → writes `vibe/design/critique.md`.
3. While its `## MUST-FIX (N)` count is above 0, run `design: fix must` (it re-critiques
   and rewrites the counts). At most **2** passes.
4. MUST-FIX still above 0 after 2 passes → do not approve.
   - Autonomous: STOP with
     `python3 "$VS" run-state set --status needs_human --reason design_must_fix --next "resolve the open MUST-FIX items in vibe/design/critique.md, then run vibe-mode: run"`
     and end the session.
   - Manual: show the open MUST-FIX items. The user decides: more fixes, or approve
     anyway, recorded as `python3 "$VS" gate set design --status approved --by human --accept-open "<their reason>" --report vibe/design/critique.md`.
5. MUST-FIX is 0 → record the gate:
   - Manual: when the user approves in chat,
     `python3 "$VS" gate set design --status approved --by human --report vibe/design/critique.md`.
   - Autonomous, `approvals: auto`:
     `python3 "$VS" gate set design --status approved --by agent-autonomous --report vibe/design/critique.md`, then continue.
   - Autonomous, `approvals: human`:
     `python3 "$VS" gate set design --status pending --report vibe/design/critique.md`, then STOP with
     `python3 "$VS" run-state set --status needs_human --reason design_approval --next "approve the design, then run vibe-mode: run"`
     and end the session.

If declined: log the skip in DECISIONS.md and record `python3 "$VS" gate set design --status skipped`.
Then continue to Step 10.

If a design system already exists: run `python3 "$VS" gate check design`. Exit 0 → go
straight to Step 10. Otherwise the gate was never recorded: run steps 2 to 5 above
(critique first, never approve without one), then go to Step 10.

**What this does not cover.** `design: critique` judges the project's design system and
`vibe/design/preview.html`, not one feature's wireframe. So when the project already has
an approved design system, this feature's new screens get no visual critique here: the
Step 7 review covers their behaviour and states, and the build's UI tasks must follow
`vibe/design/CONTRACT.md` (and `DESIGN.md`). Say so in one line when it applies:
"Design gate already approved; this feature's screens follow the existing contract and
get no separate visual critique."

---

## Step 10 — Draft FEATURE_TASKS.md

Read the reviewed FEATURE_SPEC.md and FEATURE_PLAN.md, CODEBASE.md, ARCHITECTURE.md (and
`vibe/design/CONTRACT.md` if Step 9 ran).

Add effort estimate at the top:
```
> **Estimated effort:** [N tasks — S: X (<2hrs), M: Y (2-4hrs), L: Z (4+hrs) — approx. [N] hours total]
```

**Task IDs.** Pick a task-ID prefix for this feature: a short uppercase tag (3-5
letters) derived from the feature slug, e.g. `csv-export` → `CSVX`, `reading-sessions`
→ `RDSN`. Check `vibe/TASKS.md` (and any other `vibe/features/*/FEATURE_TASKS.md`): no
other feature may use it, and it must not clash with the reserved schemes `P<N>`, `RFX`
or `BUG`. If it is taken, change a letter. Number the tasks `<PREFIX>-001`,
`<PREFIX>-002`, and so on. Dependencies use the same full IDs. Unique IDs let
vibe-parallel pool several features' task files without one task overwriting another.

Every task uses this structure:

```
---
### [PREFIX]-[NNN] · [Task title]
- **Status**: `[ ]`
- **Size**: [S / M / L]
- **Spec ref**: FEATURE_SPEC.md#[section]
- **Dependencies**: [full task IDs, e.g. CSVX-001, or "None"]
- **Touches**: [exact file paths from CODEBASE.md section 9]

**What to do**: [Specific instructions — precise enough for fresh context to execute]

**Acceptance criteria**:
- [ ] [Checkable condition from FEATURE_SPEC.md]

**Self-verify**: Re-read FEATURE_SPEC.md#[section]. Tick every criterion.
**Test requirement**: [What test must exist and what it verifies]
**⚠️ Boundaries**: [Relevant Ask first / Never rules for this specific task]
**CODEBASE.md update?**: [Yes — describe / No — logic only]
**Architecture compliance**: [Which ARCHITECTURE.md patterns apply to this task]

**Decisions**:
> Filled in by agent after completing.
- None yet.
---
```

Phases: Data layer → Backend → Frontend (skip if no UI) → Tests

End with Feature Conformance Checklist:
```
---
#### Conformance: [Feature Name]
> Tick after every task. All items ✅ before feature is shippable.
- [ ] [Acceptance criterion verbatim from FEATURE_SPEC.md]
- [ ] All new tests pass
- [ ] All existing tests still pass
- [ ] Linter clean
- [ ] No regressions in related features
- [ ] CODEBASE.md updated for structural changes this feature introduced
- [ ] ARCHITECTURE.md updated if new patterns were established
- [ ] DESIGN_SYSTEM.md updated if design: added new tokens for this feature
---
```

Save as `vibe/features/[date-slug]/FEATURE_TASKS.md`. No approval is asked here: Step 11
reviews it.

---

## Step 11 — Task review (spec-review Trigger 4T)

Announce to the user:
> "Tasks written. Running an independent readiness review before the build..."

Invoke `vibe-spec-review` with:
- Trigger source: `add-feature`, Trigger 4T
- Preset: `feature-tasks` (target `feature-[date-slug]-tasks`)
- Feature folder: `vibe/features/[date-slug]/` (FEATURE_TASKS.md, checked against the
  reviewed FEATURE_SPEC.md and FEATURE_PLAN.md)
- If this skill was entered from `vibe-mode: run`, say so.

**If spec-review stopped the run**, stop here too, exactly as in Step 7: nothing derived
is written, the feature is not reported as planned (not even under plan-only), and
nothing is built.

Manual mode: a 🔴 verdict means follow spec-review's Step 3, as in Step 7.

If a fix here needs FEATURE_SPEC.md or FEATURE_PLAN.md to change, that edit re-opens the
design review: run Steps 7 and 8 again, then this step.

Go on to Step 12 only when both `goldfish.py status feature-[date-slug]` and
`goldfish.py status feature-[date-slug]-tasks` exit 0, or, in manual mode, the person
chose to continue without a review (⚠️ NOT REVIEWED) or chose "continue anyway" on that
review (recorded in DECISIONS.md).

---

## Step 12 — Write the derived files

Only now, from the reviewed text. A feature whose review stopped the run never reaches
this step, so it writes none of these.

### 12A. Update CLAUDE.md (project root)

Read existing CLAUDE.md. Append feature section — do NOT overwrite:

```
---
### Active Feature: [Feature Name]
> Folder: vibe/features/[date-slug]/ | Added: [date]

**Feature summary**: [1-line]
**Files in scope**: [exact list from FEATURE_PLAN.md]
**Files out of scope**: [explicit list]
**Design system**: [Check vibe/DESIGN_SYSTEM.md for existing tokens before any styling]

**Conventions** (from vibe/CODEBASE.md section 6 + vibe/ARCHITECTURE.md):
[Reproduce directly relevant patterns]

**Scope changes**: If user says "change:" — stop and run vibe-change-spec immediately.

**Boundaries:**
Always: follow ARCHITECTURE.md patterns · run existing tests after every change ·
        keep changes additive · update CODEBASE.md for new files/routes/schema ·
        update TASKS.md after every task in plain English ·
        check DESIGN_SYSTEM.md before any styling work

Ask first: modifying existing API response shapes · touching auth ·
           changing shared components · any non-additive DB schema change
Never: change behaviour of existing features · remove/rename DB fields ·
       modify existing passing tests · touch files not in FEATURE_PLAN.md

**Session startup:**
1. Read CLAUDE.md · 2. Read vibe/CODEBASE.md · 3. Read vibe/ARCHITECTURE.md
4. Read vibe/DESIGN_SYSTEM.md if exists · 5. Read vibe/SPEC_INDEX.md
6. Read vibe/TASKS.md · 7. Read FEATURE_TASKS.md
8. Confirm task before writing any code

**Between tasks:** "next" triggers this exact sequence — no deviations:
1. Run tests: `npm test 2>&1 | tail -20` (or project test command)
2. Run lint: `npm run lint --silent 2>&1 | tail -10`
3. Stage and commit code changes:
   ```
   git add -A
   git commit -m "feat([feature-slug]): [PREFIX]-[NNN] — [one line plain English]"
   ```
4. If this task made a MEANINGFUL implementation decision (hard to reverse · picked among
   real alternatives — library/pattern/data-model/API shape · would surprise a future
   reader · deviates from ARCHITECTURE.md), append an entry to vibe/IMPLEMENTATION_LOG.md
   per that file's header schema (newest last; `Touches:` = files/functions changed). This
   promotes the task's `Decisions:` note into the durable, graph-linked project log. Skip
   routine work — no noise.
5. Stage and commit doc updates separately:
   ```
   git add vibe/features/[date-slug]/FEATURE_TASKS.md vibe/TASKS.md vibe/DECISIONS.md vibe/IMPLEMENTATION_LOG.md vibe/CODEBASE.md
   git commit -m "docs(FEATURE_TASKS+TASKS): mark [PREFIX]-[NNN] done — [feature]"
   ```
6. Re-read TASKS.md silently → state next task in plain English → confirm.

Do NOT request new session unless 10+ tasks this session.
Do NOT skip the commit step — uncommitted work is invisible to vibe-graph and vibe-review.

**Session completion:** Follow main checklist in CLAUDE.md.
All tasks committed individually during the session — no large end-of-session commit needed.
---
```

**CLAUDE.md cleanup rule:**
When this feature is complete and its phase review passes, archive or remove this section.
If all its rules are now in ARCHITECTURE.md, remove the section entirely.
CLAUDE.md must stay under ~150 lines excluding archived sections.

Save updated `CLAUDE.md`.

### 12B. Update vibe/TASKS.md

Read current TASKS.md. Two changes:

**1. Expand feature inline in Phase 2:**

Replace flat slug line `⬜ [Feature Name] — [description]` with:
```
🔄 [Feature Name] — [what this lets users do] (0/N)
   Estimated: approx. [N] hours (S: X, M: Y, L: Z)
   [ ] [PREFIX]-[NNN] · [task name] — [one plain English line]
   [ ] [PREFIX]-[NNN] · [task name] — [one plain English line]
   ...
   → Full specs: vibe/features/[date-slug]/FEATURE_TASKS.md (agent use)
```

**2. Update "What just happened" and "What's next" after each task:**
```
## What just happened
✅ [PREFIX]-[NNN] · [Task name in plain English] — complete
   Est. cost: ~$[X.XX] · Session running total: ~$[X.XX]
   Committed: feat([feature-slug]): [PREFIX]-[NNN] — [description]

## What's next
⬜ [PREFIX]-[NNN] · [Plain English next task]
   [One sentence: what the user will see when done]
Say "next" to begin.
```

**Cost estimate per task (Mode A — automatic):**
Read task size from FEATURE_TASKS.md (S / M / L). Rough estimate at
`claude-sonnet-5` pricing (source of truth: vibe-cost/references/PRICING.md —
scale for other tiers, and expect lower with prompt caching):
- S task: ~$0.03-0.07
- M task: ~$0.08-0.15
- L task: ~$0.18-0.35

Running session total = sum of all tasks completed this session.
These are estimates. User can run `cost:` for precise numbers from `/cost` output.

After each task: mark [x], update count, update What just happened + What's next.
Feature complete: collapse to `✅ [Feature Name] — [summary] (N/N ✅)`

### 12C. Update vibe/DECISIONS.md

```
---
## — Feature Start: [Feature Name] — [date]
> Folder: vibe/features/[date-slug]/
> [One line description]
> Tasks: [list all IDs, e.g. CSVX-001 to CSVX-006] | Estimated: [N hours]
> Drift logged below.
---
```

### 12D. Update PLAN.md feature map

If `vibe/PLAN.md` does not exist (Step 2 found no feature map), skip this. Don't create
the file.

Mark this feature as planned in PLAN.md Section 6:

Find the feature entry and rewrite its two bookkeeping lines (the independent review
ignores exactly these, so starting a feature never makes the spec review look stale):
```
**Status:** ⬜ not started   →   **Status:** 🔄 in progress
**Spec:** `vibe/features/[date-slug]/` ← created when `feature: [name]` runs   →   **Spec:** `vibe/features/[date-slug]/`
```
An older PLAN.md without a `**Status:**` line: add one under the feature's heading.
Change nothing else in the entry here. A dependency, order or scope change is a change
to a reviewed document and goes through `change:`.

If the feature was NOT in PLAN.md, add it (under `### Planned features` in a vibe-init
PLAN.md, with no UNPLANNED ADDITION label). This adds real content to a reviewed
document, so the next spec check sees it and the review runs again. Otherwise add it
with a note:
```
#### [Feature name] — [one sentence] ← UNPLANNED ADDITION
> Added: [date] · See DECISIONS.md D-[ID] for context
> Build order: [N] · Depends on: [what was determined in Step 2]
> Shared data: [what it reads, what it creates]
```

This keeps PLAN.md as the live source of truth for what's been planned
vs what's been built, across all phases.

---

## Step 13 — Feature kit ready and hand-off

Tell the user:

---
> ✅ **Feature kit ready.**
>
> **Created:** vibe/features/[date-slug]/
>   FEATURE_SPEC.md · FEATURE_PLAN.md · FEATURE_TASKS.md
> **Updated:** vibe/TASKS.md · CLAUDE.md · vibe/CODEBASE.md · vibe/DECISIONS.md · vibe/PLAN.md (if it exists)
> **Estimated:** [N tasks — approx. [N] hours]
> **Design review (Trigger 4):** [✅ SPEC READY / ⚠️ SPEC READY WITH ACCEPTED RISKS ([N]) / ⚠️ SPEC NOT REVIEWED (no subagent tool, you chose to continue) / ⚠️ NOT CONVERGED, accepted as it is by you (DECISIONS.md D-[ID])] · approved by [human / agent-autonomous]
> **Task review (Trigger 4T):** [same verdict line]
> **Review fixes:** [one line per fix from both reviews, or "none"]

**Plan-only (`feature: [name] plan-only`).** The autonomous phase loop plans a batch of
independent features first and then builds them together through vibe-parallel (Entry
point E). When called with `plan-only`, stop here, after the Step 11 review and the
Step 12 derived files: report the feature as planned and return to the caller. Do not
build, and skip Steps 14 to 16. Those steps are still owed: once the batch is built, the
caller must run, for every feature in it and before the phase gate, the graph update
(Step 14), the blast-radius tests on the touched files (Step 15) and the gate-reopen check
of Step 16. Say so when you return: "Planned [feature] (plan-only). After the batch build,
Steps 14, 15 and the Step 16 reopen check are still owed for it."

**Execution mode:** reuse the `vibe_mode` resolved at startup (see the header). If you
need it again, run the same command; never grep CLAUDE.md:
```bash
VS="$HOME/.claude/skills/vibe-mode/scripts/vibe_state.py"
python3 "$VS" mode        # add --run when entered from vibe-mode: run
```

If `vibe_mode` is `autonomous` → read the vibe-mode skill's `references/AUTONOMOUS_EXECUTION_BLOCK.md`
(resolve the vibe-mode install dir — commonly `~/.claude/skills/vibe-mode/`, or
`~/.claude/plugins/marketplaces/*/skills/vibe-mode/` under a plugin install)
and follow the autonomous execution protocol. Begin immediately. Run its phase execution
loop (its steps 1 to 3) for this feature's tasks. When every task is `[x]`, run Steps 14,
15 and 16 here **before** the block's step 4 ("Unit complete"), which runs the phase
review gate when this was the last unfinished feature of its phase. That way the review
covers the graph update and the new tests.

If `vibe_mode` is `manual` → tell the user:
> Tell your coding agent:
> ```
> Read CLAUDE.md, vibe/CODEBASE.md, vibe/ARCHITECTURE.md,
> vibe/SPEC_INDEX.md, vibe/TASKS.md, then FEATURE_TASKS.md.
> Confirm the first task before writing any code.
> ```
> Say **"next"** after each task. When the last task is done, the graph update and
> blast-radius tests (Steps 14 and 15) run before the phase review (Step 16).
---

## Step 14 — Update dependency graph

After the feature is built and tasks are complete, invoke `vibe-graph: update`.

The graph reads `git diff --name-only HEAD` to detect exactly which files
changed this session. Only those nodes are re-indexed. Planned nodes for
this feature transition to `built`. Concept completion percentage updates.

This step runs automatically — no user input needed.
Takes 1-2 minutes on a typical feature. Updates DEPENDENCY_GRAPH.json,
CONCEPT_GRAPH.json, and graph.html for the affected subgraph only.

---

## Step 15 — Blast-radius test coverage

Invoke `vibe-test` (the `test:` skill) on the files this feature touched. The
inline `npm test` in Step 12A only *runs* the existing suite. This step
*generates or extends* coverage across the feature's blast radius (the changed
files plus their dependents / contract consumers), which is what vibe-test
advertises as its auto-handoff from vibe-add-feature.

- `vibe_mode` `autonomous` (from startup): run it automatically after the graph update.
- `vibe_mode` `manual`: offer it —
  > "Feature built. Generate blast-radius tests for the [N] files it touched? (y/n)"

vibe-test reads the `Touches` sections of this feature's `FEATURE_TASKS.md`
(and the graph, if present) to scope coverage. Skip only if the user declines.

---

## Step 16 — Phase gate check

Runs after Steps 14 and 15, so any review that follows covers the new tests too.

**Built after a review passed? Reopen it.** A passed review covers the code as it was
reviewed, and this feature changed it. After the feature's tasks and tests are committed:
```bash
python3 "$VS" gate show     # final.review and phases["N"].review passed?
```
N is the phase this feature belongs to in TASKS.md.
- If `final.review` is `passed`, run
  `python3 "$VS" gate reopen final --reason "vibe-add-feature built [feature]: [files]" --by vibe-add-feature`.
- Otherwise, if `phases["N"].review` is `passed`, run
  `python3 "$VS" gate reopen N --reason "vibe-add-feature built [feature]: [files]" --by vibe-add-feature`.
  (The same rule as vibe-fix-bug: the latest passed gate is the one that no longer covers
  the code.)

For the gate you reopened, tell the user: "This feature changed source after the
[phase N | final] review passed. review: must run again (`review: [phase N | final]`);
the next phase and deploy stay blocked until it passes." If neither had passed, skip this
paragraph.

If this feature was the **last unfinished feature of its phase**, the phase review gate runs now: manual, announce and run `review: phase N`; autonomous,
go back to the execution block's step 4, which runs it. Do not
drift into the next phase's features first. The gate is enforced by the CLAUDE.md
advancement rule + `vibe/.gates.json` (see `vibe-review/references/GATES.md`): the
next phase cannot start until `phases["N"].review` is `passed`. If the feature is
mid-phase, just continue.
