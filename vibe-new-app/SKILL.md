---
name: vibe-new-app
description: >
  Full spec-driven setup workflow for building a brand new app from scratch with an AI coding agent.
  Triggers on "new:" prefix, "I want to build a new app", "starting a new project",
  "help me spec out a new app", "new project". Always use when the user is starting a
  greenfield project, even without the exact prefix and however small the project: a
  small project gets a short spec, never a skipped one. Reads BRIEF.md, ARCHITECTURE.md
  and AGENT_ARCH.md if they exist and skips questions already answered. Drafts SPEC.md,
  a multi-phase PLAN.md feature map (sequence, dependencies, parallel opportunities) and
  ARCHITECTURE.md (a minimal one if architect: was skipped); these are independently
  reviewed (spec-review) and signed off before CLAUDE.md, TASKS.md and the rest of the
  vibe/ folder are generated. TASKS.md is the single human-facing file. Requires the
  frontend-design skill for the Step 3 wireframe.
---

# Vibe New App Skill

Generates the complete project kit from brief and architecture.
Produces CLAUDE.md at project root and the full vibe/ folder the AI coding agent uses.

**No application code.** The only files this skill writes are: `CLAUDE.md`,
`vibe/SPEC.md`, `vibe/SPEC_INDEX.md`, `vibe/PLAN.md`, `vibe/ARCHITECTURE.md` (moved or
generated), `vibe/TASKS.md`, `vibe/CODEBASE.md`, `vibe/DECISIONS.md`,
`vibe/IMPLEMENTATION_LOG.md`, `vibe/reviews/backlog.md`, the empty `vibe/features/`,
`vibe/bugs/` and `vibe/backlog/` folders, `vibe/.gates.json` and `vibe/.run_state.json`
(through `vibe_state.py`), and the git pre-push hook (Step 10D). The skills it hands off
to (spec-review, vibe-graph, design:) write their own files.

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

**Step order: draft, review, sign off, then generate.**

```
1 capture → 2 SPEC.md → 3 UI Specification → 4 PLAN.md → 5 vibe/ARCHITECTURE.md
  → 6 spec review → 10S spec gate → 10F derived files → 10G graph
  → 10C design gate → 10D pre-push hook → 11 tell the user
```

The person can react to every draft (Steps 2 to 4), but nothing is approved before the
independent review in Step 6. The sign-off (Step 10S) is on the documents as the review
left them. The files generated from them (SPEC_INDEX.md, CLAUDE.md, TASKS.md,
CODEBASE.md) are written only after that, in Step 10F, so a review fix never has to chase
a copy. The labels 10S, 10C and 10D are kept because other skills refer to them.

---

## The O'Reilly principles this enforces

**Spec before code** — SPEC.md with acceptance criteria exists before any task runs.
**Context preservation** — CLAUDE.md, CODEBASE.md, ARCHITECTURE.md, SPEC_INDEX.md, TASKS.md
read every session so the agent never re-discovers what's been built.
**Incremental verifiable progress** — TASKS.md breaks the build into single verifiable tasks.
**Drift prevention** — DECISIONS.md created or preserved (never overwritten), ready to log from the first task forward.

---

## Two audiences. Two file types.

**Human-facing — open this:**
- `vibe/TASKS.md` — your single progress view. Plain English. Updated after every task.

**Agent-facing — agent reads these, you never need to open them:**
- `CLAUDE.md` · `vibe/ARCHITECTURE.md` · `vibe/CODEBASE.md`
- `vibe/SPEC.md` · `vibe/SPEC_INDEX.md` · `vibe/PLAN.md` · `vibe/DECISIONS.md`
- `vibe/IMPLEMENTATION_LOG.md` — agent: append-only implementation-decision log (why-this-approach / why-this-library)
- `vibe/DESIGN_SYSTEM.md` *(created by design: — agent reads for design context)*
- `vibe/reviews/` · `vibe/features/` · `vibe/bugs/` · `vibe/backlog/`

---

## Folder structure this skill creates

```
your-project/
├── BRIEF.md                   ← brainstorm output (if exists)
├── CLAUDE.md                  ← agent rules — auto-read by Claude Code
└── vibe/
    ├── TASKS.md               ← YOUR progress view — only file you open
    ├── ARCHITECTURE.md        ← agent: patterns, read every session
    ├── CODEBASE.md            ← agent: live codebase snapshot
    ├── SPEC.md                ← agent: full requirements
    ├── SPEC_INDEX.md          ← agent: compressed spec map
    ├── PLAN.md                ← agent: phases and architecture
    ├── DECISIONS.md           ← agent: spec/scope drift and change log (append-only)
    ├── IMPLEMENTATION_LOG.md  ← agent: implementation-decision log — why-this-approach (append-only)
    ├── DESIGN_SYSTEM.md       ← agent: design tokens (created by design:)
    ├── reviews/
    │   └── backlog.md
    ├── features/
    ├── bugs/
    └── backlog/
```

Note: `vibe/DESIGN_SYSTEM.md` is not created here — it is generated the first time
`design:` runs. The agent checks for it at session startup and reads it if it exists.

---

## Step 1 — Capture the idea and check for existing files

**Run the parity check first.** Read `references/PIPELINE.md` and follow its parity
check: classify UI vs non-UI, detect the pipeline stage, and route to any missing
upstream step. In particular:
- If `BRIEF.md` is **missing, empty, or in a foreign shape** (an idea pasted or
  dropped from elsewhere, e.g. the Claude desktop app): route to `brainstorm:`
  first — its Step 0 ingests and normalizes external input into a canonical
  BRIEF.md. This is what brings an externally-produced idea to parity. Don't
  scaffold from a hollow or non-canonical brief.
- Note whether this is a **UI project** — it determines the design gate in Step 10C.

**Check for an existing `vibe/` folder.** Upstream skills may have created it already:
spec-review writes to `vibe/DECISIONS.md` and `vibe/spec-reviews/` after `brainstorm:`,
`architect:` and `agent:`, and in autonomous mode every skill logs its choices to
`vibe/DECISIONS.md`. If `vibe/DECISIONS.md` exists, read it and note its entries and the
highest `D-NNN` ID: Step 10F keeps every one of them. Never treat an existing `vibe/` folder
as empty, and never delete what is in it.

**A setup that already started.** If `vibe/SPEC.md` or `vibe/PLAN.md` exists, an earlier
`new:` run got part of the way: it stopped for a person, or the session ended. Never
redraft over it silently. Offer:
> "Found an earlier setup ([files]). (a) Resume where it stopped *(recommended)* ·
>  (b) Start fresh: the drafts are rewritten and their review starts over."

- **(a) Resume** (always, in autonomous mode): keep the drafts, read the inputs below as
  usual (skipping the questions they answer), then continue at the first step that isn't
  done, checking in this order:
  ```bash
  GF="$HOME/.claude/skills/vibe-goldfish/scripts/goldfish.py"
  python3 "$GF" status spec     # exit 0 = the review converged on the current text
  python3 "$VS" gate show       # the spec / design gates recorded so far
  ```
  1. `vibe/SPEC.md` has no `## UI Specification` on a UI project → Step 3. No
     `vibe/PLAN.md` → Step 4. No `vibe/ARCHITECTURE.md` → Step 5.
  2. `goldfish.py status spec` does not exit 0 → Step 6. spec-review picks up the same
     review, so settled findings stay settled. Skip this check when the person already
     decided: the spec gate was approved with no review at all (its `gate show` entry has
     no `report`), or approved with `reviewed: false` while status is 3 and
     `docs_changed_since_last_round` is false (they chose "continue anyway" on a 🔴).
  3. `python3 "$VS" gate check spec` fails → Step 10S.
  4. No `vibe/TASKS.md` → Step 10F (TASKS.md is its last file). Keep `vibe/DECISIONS.md`
     and `vibe/IMPLEMENTATION_LOG.md` as they are if they exist, and generate the rest.
  5. `vibe/TASKS.md` exists, so the kit was generated. If its `## Spec gate` line is still
     ⬜ while `gate check spec` passes, or a human spec approval has no DECISIONS.md entry,
     the session ended just after TASKS.md was saved: finish the spec gate part at the end
     of Step 10F first. Then: no `vibe/graph/` → Step 10G; the
     design gate is not cleared (`gate check design`) → Step 10C; no pre-push hook and no
     DECISIONS.md note that it was declined → Step 10D; then Step 11. If every step is
     done, the kit already exists: say so and point to `feature:` or `change:`.

  If the spec gate is cleared but `goldfish.py status spec` no longer exits 0 (and the
  gate has a `report`), a reviewed document was edited after the review converged. Run
  Step 6 again before anything else.
  If that review changes the documents, the sign-off no longer covers them: run
  `python3 "$VS" gate set spec --status pending --report vibe/goldfish/spec` and go
  through Step 10S again.
- **(b) Start fresh:** first archive the old review, so findings settled on the old
  drafts are not carried over to the new ones:
  ```bash
  GF="$HOME/.claude/skills/vibe-goldfish/scripts/goldfish.py"
  python3 "$GF" archive spec
  python3 "$VS" gate set spec --status pending     # an old sign-off never covers new drafts
  ```
  Then draft from Step 2. `vibe/DECISIONS.md` stays as it is (append-only).

**Then check for BRIEF.md and ARCHITECTURE.md at project root.**

**Both exist** (ran brainstorm: and architect: — recommended path):
- Read both fully before doing anything else
- Confirm: "Found brief and architecture. [App name] — [core value]. [N] decisions locked. Building from these — no repeated questions."
- Pre-populate Steps 2–4 from BRIEF.md. Use ARCHITECTURE.md for PLAN.md folder structure and CLAUDE.md conventions.
- Skip all answered questions. Surface open questions from the brief.

**Only BRIEF.md exists** (ran brainstorm: but not architect:):
- Read BRIEF.md fully
- Confirm: "Found brief. [App name] — [core value]. [N] decisions locked."
- Pre-populate Steps 2–4. Skip answered questions.
- Note: architect: was skipped — minimal ARCHITECTURE.md will be generated from PLAN.md decisions in Step 5.

**Neither exists** (starting fresh — not recommended but supported):
- Extract: what the app does, who uses it, the core value.
- If unclear, ask the few genuinely-needed clarifying questions together (batched,
  not one at a time) — but only what you actually need to proceed.
- Confirm: "Got it — building [X] for [who], core value: [Y]. Starting spec."
- Note: both BRIEF.md and ARCHITECTURE.md will be absent — minimal versions generated.

**AGENT_ARCH.md exists** (ran `agent:`): read it fully too. Its framework, agent roles,
state design, tool mapping and human-in-the-loop checkpoints are already decided. Carry
them into SPEC.md (tech stack) and PLAN.md (the agent topology in Section 3) instead of
designing them again, and check that the stack agrees with its framework.

**Check the upstream reviews.** Every upstream document that exists should have converged
in its own independent review before you build on it:

```bash
GF="$HOME/.claude/skills/vibe-goldfish/scripts/goldfish.py"
python3 "$GF" status brief          # if BRIEF.md exists
python3 "$GF" status agent-arch     # if AGENT_ARCH.md exists
python3 "$GF" status architecture   # if ARCHITECTURE.md exists (before Step 5 moves it)
```

Exit 0 means converged on the current text. Anything else (2 in progress or stale, 3
needs a person, or a "no goldfish review" error) means the document isn't reviewed as it
stands now.
- **Manual:** say so in one line per document and offer to run `spec-review:` on it now
  *(recommended)*, or to continue with it as it is.
- **Autonomous:** run `vibe-spec-review` on it first (preset `brief`, `agent-arch` or
  `architecture`). If that review stops for a person, stop here too.

A missing upstream document is fine: they are optional.

---

## Step 2 — Draft vibe/SPEC.md

Draft SPEC.md covering:
1. **Overview** — What this app does and why (2-3 sentences)
2. **Target users** — Who uses this and what they need
3. **Core features** — Each feature with acceptance criteria
4. **Out of scope** — Explicitly NOT in v1
5. **Tech stack** — Confirmed choices with reasoning
6. **Data model** — Key entities and relationships
7. **API shape** — Core endpoints (if applicable)
8. **Non-functional requirements** — Performance, security, responsiveness
9. **Conformance checklist** — What must be true for v1 to be done

Present the draft and ask for corrections: "Here's the draft spec. Anything to add,
change, or cut?" Fold in what the person says and save as `vibe/SPEC.md`. This is a
draft, not the sign-off: the person approves SPEC.md and PLAN.md together after the
independent review, at Step 10S. Don't grade the draft against the rubric yourself
either; that is the review's job. (Autonomous: save the draft without waiting.)

**Living document rules:**
- Edit in-place on scope changes (via `change:` only — never informally). Until the spec
  gate (Step 10S) it is still a draft: edit it directly, and through the review's fixes.
- ~~Strikethrough~~ for removed items — never delete
- Update note at top: `> ⚠️ Last updated: [date] · [reason]`
- SPEC.md and SPEC_INDEX.md always updated as a pair — never one without the other
  (SPEC_INDEX.md is first written in Step 10F, after the review's fixes are in)

---

## Step 3 — UI Design

**Requires: frontend-design skill.** If not installed, proceed with prose wireframe description.

**If `DESIGN.md` (project root) or `vibe/design/CONTRACT.md` already exists**
(the user ran `design-md:` / `design:` first), read it and treat its tokens as
authoritative — the wireframe must use those colours/type/spacing rather than
inventing a new aesthetic. `DESIGN.md` wins where it and `DESIGN_SYSTEM.md` conflict.

Tell the user: "Before planning the build phases, let's sketch the UI."

Ask all at once:
1. **Screens** — How many screens/views? List briefly.
2. **Primary screen** — Where do users spend most time?
3. **Layout & nav** — Preferences? (sidebar, bottom nav, top nav — or no preference)
4. **Device** — Desktop only, mobile first, or both?
5. **Interactions** — Anything complex? (drag-drop, real-time, multi-step)
6. **References** — Any apps whose UI you like?
7. **Constraints** — Component library already chosen? Anything must show above fold?

Wait for answers. Generate wireframe using **frontend-design skill** principles:
- Commit to a bold, intentional aesthetic based on the app's purpose
- Complete HTML wireframe artifact covering all screens
- Realistic placeholder content — not Lorem ipsum
- Show navigation between screens

Present the wireframe and iterate on the person's reactions until the screens and
navigation are right. Then append the UI Specification to vibe/SPEC.md. The UI
Specification is what gets reviewed and what `design:` builds from; the wireframe is a
sketch for this conversation and is not updated afterwards.

```
## UI Specification
### Design direction
[One sentence: aesthetic direction and why]
### Component library
[What's being used, or "none specified"]
### Navigation structure
[Top-level destinations and flow — locked here, expensive to change mid-build]
### Screens
#### [Screen name]
- **Purpose**: [What the user does here]
- **Layout**: [Describe]
- **Key components**: [List]
- **User interactions**: [What the user can do]
- **States**: [Empty, loading, error states]
### Responsive behaviour
[Desktop/mobile approach]
```

Tell the user: "UI spec drafted. Moving to planning."

---

## Step 4 — Draft vibe/PLAN.md

Read `references/PLAN_MD.md` for the full template.
Read vibe/SPEC.md in full. Read ARCHITECTURE.md if it exists (still at the project root
until Step 5 moves it), and AGENT_ARCH.md if it exists.
Read BRIEF.md — specifically: feature list, non-goals, complexity estimate.

The critical section is the **Feature Map** (Section 6).
This is the complete build plan — every feature, every phase, fully sequenced.
It is not a list of slugs. It is not deferred to later.
It is planned now, before Phase 1 begins.

**Step 4A — Draft Sections 1–5 (structure, stack, architecture, data model, API):**

These are standard — fill from SPEC.md and ARCHITECTURE.md (and the agent topology from
AGENT_ARCH.md, if it exists).
Identify shared data now: which tables/entities will be read or written by
multiple features. List them explicitly in Section 4 "Shared data" table.
This is the most common source of inter-feature conflicts caught too late.

**Step 4B — Build the Feature Map (Section 6) — the most important step:**

> 🧠 **Effort:** sequencing features by dependency is the reasoning that every
> later build wave and parallel dispatch relies on. Run it at high/xhigh effort
> with adaptive thinking — get the dependency ordering and shared-data analysis
> right here, because errors propagate through the whole build.

Read vibe/SPEC.md features section. Read BRIEF.md feature list and non-goals.

For every v1 feature, determine:

1. **Build order** — which features have no dependencies (start here),
   which need another feature's data model first, which can run in parallel.

   Ask yourself for each feature:
   - Does this feature READ data created by another feature?
     → It depends on that feature. Build that one first.
   - Does this feature WRITE data that another feature reads?
     → It must come before that feature.
   - Do two features share NO data writes and have the same dependencies?
     → They can run in parallel. Mark both explicitly.

2. **Shared data** — which entities/tables are created by one feature
   and consumed by another. These are the inter-feature dependency points
   that cause mid-build surprises if not planned now.

3. **Future phase sketch** — for Phase 4+ features from BRIEF.md backlog:
   note what Phase 1-3 must NOT hard-code to keep them possible.
   This prevents architectural decisions that feel fine now but block v2.

Build the dependency diagram:
```
Phase 1 complete
    ↓
[Feature with no deps — can start immediately after Phase 1]
    ↓              ↓
[Next feature]  [Parallel feature — no shared writes]
    ↓
[Feature that needs both above]
```

If the dependency order is unclear — ask the user ONE focused question:
> "Does [Feature B] need [Feature A]'s [entity] to exist first, or can they be built independently?"

**Step 4C — Show the feature map:**

> "Here's the complete build plan — all phases mapped out before we start.
>
> [Present the feature map — Phase 1, Phase 2 ordered features with deps,
> Phase 3 tasks, Phase 4+ sketch if applicable]
>
> Build order for Phase 2:
> [ASCII dependency diagram]
>
> Parallel opportunities: [list features that can run simultaneously]
> Shared data points: [list entities that cross feature boundaries]
>
> Does this sequencing look right? Any features that should move earlier or later?
> You'll sign off the reviewed plan after the independent review."

Take the person's corrections. If one moves, splits or cuts a feature, change SPEC.md to
match now, while both are still drafts, so the two never disagree. This is not the
sign-off (that is Step 10S). (Autonomous: no wait.)

**Step 4D — Save as `vibe/PLAN.md`.**

The feature map in PLAN.md is the source of truth for:
- TASKS.md Phase 2+ section (generated from it in Step 10F)
- vibe-add-feature (reads it before drafting each feature spec)
- vibe-change-spec (reads it to assess phase impact of scope changes)
- vibe-parallel (reads dependency diagram for wave planning)

---

## Step 5 — Move or create vibe/ARCHITECTURE.md

The spec review in Step 6 reviews `vibe/ARCHITECTURE.md` together with SPEC.md and
PLAN.md, and CLAUDE.md (Step 10F) takes its conventions from it, so it must be in place
first.

**If ARCHITECTURE.md exists at project root:** Move to `vibe/ARCHITECTURE.md`.

**If ARCHITECTURE.md does not exist** (architect: was skipped):
Generate a minimal `vibe/ARCHITECTURE.md` from PLAN.md decisions, using
`references/ARCHITECTURE_MD.md`:
- Extract the folder structure, naming conventions, and tech choices from PLAN.md
- Apply the O'Reilly Principles section verbatim from `references/ARCHITECTURE_MD.md`
- Mark it clearly: `> ⚠️ Auto-generated from PLAN.md — architect: was not run.`
- `> Consider running architect: to make these decisions explicit and add missing sections.`
This ensures review: has an ARCHITECTURE.md to check against from Phase 1.

---

## Step 6 — Spec review

Announce and hand off to spec-review:

> "SPEC.md, PLAN.md and ARCHITECTURE.md drafted. Running an independent spec review before you sign off..."

Invoke `vibe-spec-review` with:
- Trigger source: `new-app` (Trigger 3, goldfish preset `spec`)
- Scope, as the `spec` preset defines it: `vibe/SPEC.md` (with its UI Specification),
  `vibe/ARCHITECTURE.md` and `vibe/PLAN.md` are reviewed. `BRIEF.md` and `AGENT_ARCH.md`
  (when they exist) are read as related files, to check the three against them.

When you answer a finding with a fix (inside vibe-goldfish), make it in every reviewed
document that says the same thing: a feature cut from SPEC.md also leaves PLAN.md's
feature map, and a stack change reaches ARCHITECTURE.md. The derived files don't exist
yet, so there is nothing else to update.

**If spec-review stopped the run** (`python3 "$VS" run-state show` says needs_human from
spec review), **stop here too**: end the session, don't continue, don't report the step as
done. That means: do not record the spec gate in Step 10S, and start nothing after it.
`vibe-mode: run` resumes once a person has resolved it (Step 1 then resumes the setup).
In manual mode, a 🔴 verdict means follow spec-review Step 3 (more rounds, rework, or the
person accepts). Never fix findings outside vibe-goldfish.

After spec-review completes without stopping:

## Step 10S — Spec gate: sign-off on the reviewed plan

The spec gate is the person's sign-off on the plan the build will follow: SPEC.md (with
its UI Specification), PLAN.md and ARCHITECTURE.md as the review left them, fixes
included. Nothing the person said about the drafts in Steps 2 to 4 counts as this
sign-off. It is recorded in `vibe/.gates.json` with the helper, with the goldfish review
that Step 6 ran, `vibe/goldfish/spec`, as `--report`:

```bash
VS="$HOME/.claude/skills/vibe-mode/scripts/vibe_state.py"
python3 "$VS" mode        # → vibe_mode, approvals (add --run when entered from vibe-mode: run)
```

- **Manual mode:** show the spec-review verdict and what the review changed, one line per
  fix (and say when a fix changed screens or navigation, since the Step 3 wireframe
  predates it). Ask: "Do you approve SPEC.md, PLAN.md and ARCHITECTURE.md as they are
  now?" and wait for a clear yes.
  - Changes requested: make them, then run Step 6 again (an edit re-opens the review by
    itself), and ask again on the result.
  - Yes: `python3 "$VS" gate set spec --status approved --by human --report vibe/goldfish/spec`,
    and append a DECISIONS.md entry for the approval (`Approved by: human`, after the
    review).
  - The review never ran (⚠️ SPEC NOT REVIEWED, the person chose to continue without it):
    record `gate set spec --status approved --by human` without `--report`, and say in the
    DECISIONS.md entry that no independent review ran.
- **Autonomous, `APPROVALS=auto`:** `gate set spec --status approved --by agent-autonomous --report vibe/goldfish/spec`,
  log it to DECISIONS.md (HEADLESS.md §2.4), and continue. Never run this when spec-review
  stopped with `needs_human` (Step 6). The
  helper refuses unless that goldfish review converged. If it refuses, do not retry with
  other flags (`--backfill` is only for HEADLESS.md §5 projects that predate the gate):
  STOP with `run-state set --status needs_human --reason "spec gate: [the helper's error]" --next "see vibe/goldfish/spec"`
  and end the session.
- **Autonomous, `APPROVALS=human`:** `gate set spec --status pending --report vibe/goldfish/spec`,
  then STOP — `python3 "$VS" run-state set --status needs_human --reason spec_approval --next "approve vibe/SPEC.md, vibe/PLAN.md and vibe/ARCHITECTURE.md (python3 $VS gate set spec --status approved --by human --report vibe/goldfish/spec), then run vibe-mode: run"`
  — and end the session. Generate nothing more and start no task. `vibe-mode: run` re-runs
  `new:` (there is no TASKS.md yet), and Step 1 resumes the setup at Step 10F once the
  spec is approved.

`vibe/TASKS.md` doesn't exist yet, so the helper only writes `vibe/.gates.json` here.
Step 10F writes the `## Spec gate` line and records the decision on it.

## Step 10F — Generate the files derived from the approved plan

Everything below is derived from the reviewed, approved SPEC.md, PLAN.md and
ARCHITECTURE.md. Generate it from them as they are now; don't re-plan anything here. If
something in them looks wrong, that is a change to a reviewed document: run `change:`,
which re-runs the review.

### vibe/SPEC_INDEX.md

Read vibe/SPEC.md in full. Generate SPEC_INDEX.md — compressed map under 40 lines:

```
# SPEC_INDEX — [Project Name]
> Compressed map of SPEC.md. Read each session. Fetch only the section you need.
> Last synced: [date]
## Overview — [one sentence] → SPEC.md#overview
## Features — [Feature]: [one sentence] (N criteria) → SPEC.md#feature-name
## UI — [N screens, direction summary] → SPEC.md#ui-specification
## Boundaries — Out of scope: [N items] → SPEC.md#out-of-scope
## Technical — Stack: [key choices] · Data: [N entities] · API: [N endpoints]
## Done condition — Conformance: [N items] → SPEC.md#conformance-checklist
## Backlog — [N items deferred] → vibe/backlog/
```

Save as `vibe/SPEC_INDEX.md`.
Rule: SPEC.md and SPEC_INDEX.md always committed together. Never one without the other.

### CLAUDE.md (project root)

Read vibe/SPEC.md, vibe/PLAN.md and vibe/ARCHITECTURE.md (Step 5 put it there).
Read `references/CLAUDE_MD.md` for the full template.

Generate CLAUDE.md at **project root** substituting all [placeholders]:
- Project overview from SPEC.md
- Tech stack from PLAN.md
- Commands from chosen stack
- Code style and naming from vibe/ARCHITECTURE.md
- Architecture rules: the Always / Ask First / Never boundaries from vibe/ARCHITECTURE.md
- Phase gates section — mandatory review gates baked in from day one
- Execution mode section — the three settings **as resolved now** by
  `python3 ~/.claude/skills/vibe-mode/scripts/vibe_state.py mode` (never hardcode
  `manual`: a driver may have set `VIBE_MODE=autonomous` in the environment)
- The "Per-task sequence", "Investigation discipline" and "Session completion checklist"
  blocks, copied **verbatim** from the template. They are the contract every other
  vibe-* skill relies on, so don't reword, shorten or renumber them.
- CLAUDE.md active feature sections — cleanup rule included

Save as `CLAUDE.md` at project root.

### vibe/CODEBASE.md (placeholder)

Read `references/CODEBASE_MD.md` for the full template.

For a new app, CODEBASE.md starts as a placeholder.
The last task in Phase 1 populates it fully from the scaffolded project.

Generate the placeholder version. Save as `vibe/CODEBASE.md`.

### vibe/DECISIONS.md

DECISIONS.md is append-only. Never write it from this template when it already exists
(Step 1 checked, and spec-review creates it with this header when it was absent):
- **Absent:** create it with the template below.
- **Exists:** keep every existing entry exactly as it is, including entries other skills
  wrote in other formats (for example `## [date] — Spec review`). If the header (the title
  through the `## Format` block) is missing, add it above the existing entries. Do not add
  the `(No entries yet)` line. New entries continue the `D-NNN` numbering from the highest
  existing ID.

```
# DECISIONS — [Project Name]
> Append-only. Every drift, scope change, tech choice — logged with full context.

## Decision types
- drift — deviated from PLAN.md or ARCHITECTURE.md
- blocker-resolution — impossible; workaround found
- tech-choice — chose between valid approaches not in plan
- scope-change — added/removed via change: command
- discovery — unexpected finding affecting future tasks

## Format
### D-[ID] — [Short title]
- **Date**: · **Task**: [TASK-ID] · **Type**: [type]
- **What was planned**: · **What was done**: · **Why**: 
- **Alternatives considered**: · **Impact on other tasks**:
- **Approved by**: human | agent-autonomous

(No entries yet)
```

### vibe/IMPLEMENTATION_LOG.md

Write this file from the canonical template in
`references/IMPLEMENTATION_LOG_MD.md` (use the **FILE TEMPLATE** block there verbatim).
It is the append-only **implementation-decision** log — code-altitude "why this approach,
why this library" — the companion to DECISIONS.md (which stays at spec/scope altitude).
It starts empty; the build skills append to it as meaningful decisions are made, and
`Touches:` lines link each decision to vibe-graph nodes. Do not duplicate the schema here —
the file's own header carries it.

### vibe/reviews/ folder

Create `vibe/reviews/backlog.md`:
```
# Review Backlog
> P1/P2/P3 issues tracked across all phase reviews.
> P1 must resolve before deploy. Updated after every review.
## Outstanding P1 Issues
(none yet)
## Outstanding P2 Issues
(none yet)
## Resolved Issues
(none yet)
```

Create the empty `vibe/features/`, `vibe/bugs/` and `vibe/backlog/` folders.

### vibe/TASKS.md

Read `references/TASKS_MD.md` for the template and update rules, and copy its skeleton
exactly: header, `## Spec gate`, Phase 1 (with each task's metadata line), `## Phase 1
gate`, `## Design gate (UI projects)`, Phase 2, Phase 3, `## Final gate`, Phase 4+ and the
footer. Read vibe/SPEC.md, vibe/SPEC_INDEX.md, vibe/PLAN.md — especially Section 6
(Feature Map).

Phase 2 is not slugs — it is the complete ordered feature list with dependencies
visible, derived from PLAN.md Section 6: build order, needs, reason, parallel-with,
estimate and the `feature: [name]` trigger for every feature. Leave out the Design gate
section only for a non-UI project.

**Non-negotiable rules:**
- Build order and dependency reasons visible for every Phase 2+ feature
- `feature: [name]` trigger visible on every planned feature — user knows exactly what to run
- Phase gate instruction visible at end of each phase
- Plain English everywhere — what the user sees/experiences, not technical details
- Human should never need to open PLAN.md to know what to build next or in what order

Save as `vibe/TASKS.md`. Then record the Step 10S decision on its `## Spec gate` line:
read it with `python3 "$VS" gate show` and run the same `gate set spec` call again (same
`--status`, `--by` and `--report`). The helper rewrites the line from that decision;
never edit a gate line by hand.

If `gate show` says the spec was approved `by: human` and DECISIONS.md has no entry for
that approval (in autonomous mode with `APPROVALS=human` the person approves outside the
session, with the helper), append one now: `Approved by: human`, after the review, with
the report `vibe/goldfish/spec`.

TASKS.md is written last on purpose: `vibe-mode: run` and Step 1 both treat an existing
TASKS.md as "Step 10F is done", so a session that ends partway through this step has no
TASKS.md and comes back here.

## Step 10G — Initialise dependency graph

Invoke `vibe-graph: init`.

This builds the spec graph from SPEC.md and ARCHITECTURE.md —
all planned nodes created before any code is written.
Nodes will transition from `planned` to `built` as features are implemented.
It runs after the spec gate, so the planned nodes come from the signed-off plan.

After graph init completes:

## Step 10C — Design gate (UI projects)

Design is a required pipeline step for UI projects, not an afterthought (see
`references/PIPELINE.md`). Do not let the build start UI features with no design
language — that is the "it skipped design" failure.

The order is the same in manual and autonomous mode: `design:` up to its Step 3.5
checkpoint (contract, tokens, `vibe/design/preview.html`, no production UI files), then
the **critique loop** below, and only then the approval. The production UI is built
afterwards by the phase's UI tasks from the approved contract, never before the critique.
When you invoke `design:`, tell it that it is running as the design gate, so it stops at
Step 3.5.

- **Non-UI project** (API / CLI / library / pure backend): skip this step; note
  "design gate N/A — no UI", record it with `vibe_state.py gate set design --status na`,
  and continue.
- **UI project, no design system yet** (`DESIGN.md` / `vibe/DESIGN_SYSTEM.md` /
  `vibe/design/CONTRACT.md` all absent):
  - **Manual:** announce and hand off —
    > "This is a UI project. Before building screens, let's lock the design so they
    >  share one derived design language. Optionally run `design-md:` first to
    >  capture brand tokens, then `design:` to produce the design contract.
    >  Recommended. Reply 'skip design' to build without a design pass."
    On a clear yes, run `design:` up to Step 3.5, then the critique loop. Then show the
    person `vibe/design/preview.html`, the MUST-FIX / CONSIDER / NIT counts and what the
    fixes changed, and ask them to approve the design as it is now. On approval, record
    `gate set design --status approved --by human --report vibe/design/critique.md`.
    The helper refuses while MUST-FIX > 0: show the user the open items; they can ask for
    more fixes, or approve anyway with
    `--by human --accept-open "[their reason]"`. If the user says skip, log it in
    `vibe/DECISIONS.md` ("design gate skipped by user") so it's a visible decision, and
    record `gate set design --status skipped`.
  - **Autonomous:** never skip. Run `design:` up to Step 3.5, then the critique loop. Only
    when MUST-FIX = 0, record per `APPROVALS`:
    `auto` → `gate set design --status approved --by agent-autonomous --report vibe/design/critique.md`
    and continue; `human` → `gate set design --status pending --report vibe/design/critique.md`,
    STOP with `run-state set --status needs_human --reason design_approval --next "approve the design, then run vibe-mode: run"`,
    and end the session.
- **Design system already exists** (user ran `design-md:`/`design:` before `new:`, or an
  earlier session of this setup stopped at the design gate): a design made before `new:`
  has never been checked against the reviewed UI Specification. Run the **critique loop**
  on it first, even when `gate check design` already passes. If the critique comes back with MUST-FIX 0 and the gate already passes,
  continue. If the gate already passes but the critique finds MUST-FIX > 0, the old
  approval no longer holds: first run
  `python3 "$VS" gate set design --status pending --report vibe/design/critique.md`, so a
  stop in the critique loop leaves no cleared gate behind for a resumed build to trust.
  Then, or when the gate was never cleared, go through the critique loop and record the
  gate as the branches above say (manual: the person approves after the critique;
  autonomous: per `APPROVALS`).

**Critique loop** (every branch that approves a design): run `design: critique`, then read
the count from the `## MUST-FIX (N)` heading in `vibe/design/critique.md`. While N > 0,
run `design: fix must` (it re-critiques and rewrites the count), **at most 2 passes**. If
MUST-FIX is still > 0 after 2 passes, an agent cannot approve the gate (the helper refuses).
In autonomous mode STOP with
`run-state set --status needs_human --reason design_must_fix --next "resolve the open MUST-FIX items in vibe/design/critique.md, then run vibe-mode: run"`
and end the session. In manual mode, show the open items and let the user decide.

**Before ending the session at either autonomous stop** (`design_approval` or
`design_must_fix`), run Step 10D first. The hook doesn't depend on the design, and a
resumed session goes straight to the design gate and the build (HEADLESS.md §5), so it
would never come back to Step 10D.

The generated TASKS.md carries a matching **Design gate** line before Phase 2 so
this is visible in the human-facing plan.

After the design gate resolves:

## Step 10D — Install the gate hard-lock (git pre-push hook)

The phase/deploy gates are enforced by flow + `vibe/.gates.json` (see
`vibe-review/references/GATES.md`), but the only true machine-level lock is a git
hook. Offer to install it:

> "Install the gate hard-lock? It blocks `git push` while any review gate is open
>  (P0 or P1 outstanding) — so quality gates hold even if a step is skipped. Override
>  anytime with `git push --no-verify`. (y/n)"

If yes, write `.git/hooks/pre-push` (chmod +x) with the check from GATES.md
(reads `vibe/.gates.json`; any `open` gate → exit 1). If the project uses husky,
add it as a husky `pre-push` instead. If declined, note it in DECISIONS.md — gates then
rely on flow + state only. In autonomous mode, install it (the recommended option) and note it
in DECISIONS.md. If the hook is already installed (Step 10C ran this step before
stopping), skip it.

## Step 11 — Tell the user

---
> 🎉 **Your project kit is ready.**
>
> **One file to watch:** `vibe/TASKS.md`
>
> **Structure created:**
> ```
> CLAUDE.md
> vibe/TASKS.md        ← open this
> vibe/ARCHITECTURE.md ← [locked from architect: / auto-generated from plan]
> vibe/CODEBASE.md     ← placeholder until Phase 1 done
> vibe/SPEC.md + SPEC_INDEX.md + PLAN.md + DECISIONS.md
> vibe/IMPLEMENTATION_LOG.md  ← implementation decisions logged as you build
> vibe/reviews/backlog.md
> vibe/spec-reviews/   ← spec review history
> vibe/graph/          ← dependency graph (spec graph initialised)
> ```
> **Spec review:** [✅ SPEC READY / ⚠️ SPEC READY WITH ACCEPTED RISKS ([N]) / ⚠️ SPEC NOT REVIEWED]
> **Spec gate:** [approved by human / approved by agent-autonomous]
> **Graph:** [N] planned nodes · [N] concepts mapped · updates automatically
>
> **Read execution mode:**
> ```bash
> python3 ~/.claude/skills/vibe-mode/scripts/vibe_state.py mode   # add --run when entered from vibe-mode: run
> ```
>
> If `autonomous` → read the vibe-mode skill's `references/AUTONOMOUS_EXECUTION_BLOCK.md`
> (resolve the vibe-mode install dir — commonly `~/.claude/skills/vibe-mode/`, or
> `~/.claude/plugins/marketplaces/*/skills/vibe-mode/` under a plugin install)
> and follow the autonomous execution protocol for Phase 1 tasks. Begin immediately.
> (If Step 6, 10S or 10C stopped for a person, the session has already ended. A stop at
> Step 6 or 10S resumes through `new:` (Step 1); a stop at 10C resumes at the design gate
> (HEADLESS.md §5), and the build starts from there.)
>
> If `manual` or not set → tell the user:
> ```
> Read CLAUDE.md, then vibe/CODEBASE.md, then vibe/ARCHITECTURE.md,
> then vibe/SPEC_INDEX.md, then vibe/TASKS.md.
> Confirm the first task before writing any code.
> ```
> Say **"next"** after each task.
> Run **"review: phase 1"** when Phase 1 completes — mandatory gate.
---
