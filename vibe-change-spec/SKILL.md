---
name: vibe-change-spec
description: >
  Scope change workflow for modifying, adding, or removing requirements at any point during a build.
  Triggers on "change:" prefix, "I forgot to add", "actually I also want", "can we add",
  "remove X from scope", "I changed my mind about", "before we continue add",
  "one more thing", "I want to change the spec", "revert the X change".
  Handles new additions, removals, renames, backlog operations, and reverting previous changes.
  Assesses impact before touching any file. Updates all affected docs upstream first
  (BRIEF, ARCHITECTURE, SPEC, PLAN feature map, affected feature folders), then re-runs the
  independent review on every reviewed document it changed and asks for approval of the
  reviewed text. A change to an approved spec sets the spec gate back to pending.
  If BRIEF.md doesn't exist, updates SPEC.md and DECISIONS.md only.
---

# Vibe Change Spec Skill

Handles scope changes at any point during the build: safely, in the right order.
Always assesses impact first. Always waits for confirmation. Never edits files speculatively.
Every reviewed document it changes is reviewed again, independently, before anything is
built from it.

**No application code. The only files this skill writes are:** `BRIEF.md`,
`ARCHITECTURE.md` (root or `vibe/`), `vibe/SPEC.md`, `vibe/SPEC_INDEX.md`, `vibe/PLAN.md`,
`vibe/TASKS.md`, `vibe/DECISIONS.md`, `vibe/CODEBASE.md`, `vibe/backlog/*.md`, the
FEATURE_SPEC.md / FEATURE_PLAN.md / FEATURE_TASKS.md of the feature folders the change
touches, and the spec and design gates (`vibe/.gates.json`, through `vibe_state.py`). The
review it runs (vibe-spec-review → vibe-goldfish) writes its own records under
`vibe/goldfish/` and `vibe/spec-reviews/`.

> **Autonomous / headless mode.** At startup resolve the settings with
> `python3 ~/.claude/skills/vibe-mode/scripts/vibe_state.py mode` (`mode --run` when the
> caller says this skill was entered from `vibe-mode: run`, which forces autonomous). If
> `vibe_mode` is `autonomous`, every "wait", "ask", "confirm" and approval step in this skill follows
> vibe-mode's `references/HEADLESS.md` §2 instead: take the recommended option, accept a
> changed document only as §2.2 allows (after its independent goldfish review, Step 11),
> record the spec and design gates per §3 (Steps 13 and 14), log each choice to
> `vibe/DECISIONS.md`, never ask the user, and stop (writing `vibe/.run_state.json`) only
> when a person is genuinely required.

---

## The O'Reilly principle this enforces

**Drift prevention** — scope changes must be logged explicitly. An informal "just quickly add X"
mid-task produces a codebase that doesn't match its documentation. When review: runs,
it finds violations with no logged context. change: prevents this by stopping work,
assessing impact, and updating all affected documents before building continues.

---

## When this skill runs

Any time the user signals a scope change:
- `change: add dark mode before we build screens`
- `change: remove social login — email only`
- `change: add push notifications to backlog`
- `change: promote push notifications to active`
- `change: rename "ideas" to "posts" throughout`
- `change: revert the PDF attachment change we made last week`
- Natural language: "actually I also want X", "I forgot Y", "can we cut Z"

---

## Step 1 — Understand the change

**First, look for an unfinished change.** An autonomous stop in the middle of a change
(Step 11, Step 13, or the promote flow in Step 15) leaves a line
`- **Resume D-[ID]**: at [step] · ...` in `vibe/DECISIONS.md`. A change is unfinished when
the last line about its D-[ID] is such a Resume line, not a `- **D-[ID] completed**` line.
If one is unfinished (or the person says `change: resume D-[ID]`):
- Manual mode, and the person asked for a new change: tell them in one line and offer to
  finish the open one first (recommended). Autonomous: finish it first.
- To finish it, read the current state (Step 2). Steps 3 to 10B are already done: the
  change was confirmed, the gates were reset and the documents were edited and committed.
  Don't redo them. Continue at the step the Resume line names:
  - **Step 11:** targets whose `goldfish.py status <target>` already exits 0 are done;
    review the rest, then Step 12 onward.
  - **Step 13:** the approval, then Step 14 onward.
  - **promote item 6:** `python3 "$VS" gate check spec` first. Not cleared: stop again
    with the same reason and next action. Cleared: item 6 onward.
- If the reason for the stop still stands (the review still needs a person, the helper
  still refuses), stop again the same way. Append a new Resume line only when the change
  stops at a later point than the last one.

Otherwise, extract:
- What is being added, removed, modified, renamed, or reverted
- Whether it's a new feature, requirement tweak, removal, rename, backlog op, or revert
- Whether it's urgent (insert now) or deferred (backlog)

If ambiguous, ask the clarifying questions you actually need — batched together,
not one at a time.

Confirm:
> "Got it — you want to [add/remove/modify/revert] [X]. Let me check what this affects."

---

## Step 2 — Read current state

Read in order. Skip files that don't exist — note their absence:

1. `BRIEF.md` *(if exists)* — original problem, core value, v1 feature set
2. `vibe/ARCHITECTURE.md` *(if exists)* — established patterns and principles
3. `vibe/SPEC.md` — what is currently in scope
4. `vibe/SPEC_INDEX.md` — feature list and state
5. `vibe/TASKS.md` — active work, done vs pending
6. `vibe/PLAN.md` — current architecture
7. `vibe/CODEBASE.md` — what has actually been built

If active feature or bug folder exists (from TASKS.md active block):
8. Active `FEATURE_SPEC.md`, `FEATURE_PLAN.md` and `FEATURE_TASKS.md`, or `BUG_TASKS.md`

Then read the gates:
```bash
VS="$HOME/.claude/skills/vibe-mode/scripts/vibe_state.py"
python3 "$VS" gate show     # spec and design: approved | pending | skipped | na | unset
```

---

## Step 3 — Assess impact

### Build stage

**Before any code** — doc updates only. Zero retrofit.
**Between tasks** — last task done, next not started. New tasks slot cleanly.
**Mid-phase** — some tasks done. May need to pause and insert new tasks.
**Cross-phase** — change affects already-built architecture or data layer. Retrofit needed.
**Post-completion** — fully built and conformance-checked. Full retrofit + regression strategy.

### Impact checklist

- [ ] Adds/removes feature from SPEC.md?
- [ ] Changes data model (table, field, relationship)?
- [ ] Changes any API endpoints already built?
- [ ] Affects screens or components (already built, or in the SPEC's UI Specification)? → design gate (Step 14)
- [ ] Changes architecture in PLAN.md?
- [ ] Changes patterns or conventions in ARCHITECTURE.md?
- [ ] Changes core value or feature set in BRIEF.md?
- [ ] Do tasks already marked [x] need retrofitting?
- [ ] Affects active feature/bug folder?
- [ ] Is this additive (now) or deferred (backlog)?

### Feature map cascade check

If vibe/PLAN.md exists and has a Section 6 feature map — run this check:

Find the affected feature in the feature map.

Read these lines of its entry:
- `Depended on by:` — features that cannot start until this one is done
- `Shared data:` — entities this feature creates that others consume
- `Can run in parallel with:` — features planned to run alongside this one

For each feature in `Depended on by:`:
- Is it already built? → retrofit risk, flag as cross-phase
- Is it planned but not built? → update its feature-map entry (Step 9), and its
  FEATURE_SPEC/FEATURE_PLAN if it already has a feature folder (Step 10), before it starts
- Is it in progress? → pause it, assess data model impact first; its FEATURE_SPEC/FEATURE_PLAN
  are updated in Step 10

For each `Shared data:` entity this change affects:
- Which downstream features read this entity?
- Does the change alter the entity schema? → all consumers need review
- Does the change remove the entity? → all consumers are now broken

For each feature in `Can run in parallel with:`: does the change add a shared write or a
data dependency between them? → they can no longer run in parallel; correct both entries
in Step 9.

Surface cascade clearly in Step 4:
```
Feature map cascade:
  ⚠️  [Feature X] depends on [changed feature] — [built/in progress/planned]
      Impact: [what breaks or needs updating]
  ⚠️  [Feature Y] reads [affected entity] — [built/in progress/planned]
      Impact: [schema change affects Y's data layer]
  ✅  [Feature Z] — no dependency on changed feature
```

If no feature map in PLAN.md — skip this check, note its absence.

### Revert detection

If the change is reverting a previous scope change (e.g. "remove the PDF feature we added"):
- Find the original D-ID in DECISIONS.md
- Identify all tasks that were added or retrofitted at that time
- Assess which tasks have been completed since (those need retrofit to undo)
- Treat as a new scope change entry (not a deletion of the original D-ID)
- Run the feature map cascade check for the reverted feature too

---

## Step 4 — Tell the user impact before touching anything

> **Change requested:** [one sentence plain English]
>
> **Build stage:** [Before code / Between tasks / Mid-phase / Cross-phase / Post-completion]
>
> **What this affects:**
> - Spec: [what changes in plain English]
> - Tasks: [N new / M retrofit / K removed — plain English]
> - Code already built: [affected — what needs revisiting / not affected]
> - Architecture: [patterns affected / not affected]
>
> **Feature map cascade:** [None / see cascade findings above]
> - [Feature X] — [built/planned] — [impact]
> - [Feature Y] — [built/planned] — [impact]
>
> **Documents to update and review again:** [BRIEF / ARCHITECTURE / SPEC and PLAN / feature folders]
>
> **Gates:** [the approved spec goes back to pending until you approve the reviewed changes /
> the design goes back through a design critique / not affected]
>
> **Effort:** [Small — doc only / Medium — new tasks / Large — retrofit needed]
>
> **Recommendation:** [Add to backlog / Insert before next task / Address now with retrofit]
>
> Ready to proceed? (or "add to backlog instead")

Wait for confirmation. Never touch files before confirmation.

This confirms what to change. It is not the approval of the new text: the person approves
the changed documents after their independent review (Step 13).

- "add to backlog" → jump to Step 15 (Backlog)
- "proceed" → continue to Step 5

---

## Step 5 — Reopen the gates this change affects

An approved gate covers the documents as they were reviewed. Once the change edits them,
the approval no longer describes what will be built, so it goes back to pending before
any document is touched:

- **Spec gate `approved`, and the change edits `vibe/SPEC.md`, `vibe/PLAN.md` or
  `vibe/ARCHITECTURE.md`:**
  `python3 "$VS" gate set spec --status pending --report vibe/goldfish/spec`.
  Nothing is built from the changed spec until Step 13 records the approval of the
  reviewed text (`vibe-mode: run` stops at a pending spec gate).
- **Design gate `approved`, and the change adds, changes or removes screens or
  components:** `python3 "$VS" gate set design --status pending --report vibe/design/critique.md`.
  The design goes back through `design: critique` in Step 14.
- **Any other status** (`skipped`, `na`, unset, already `pending`): leave it. One
  exception: a design gate of `na` when the change adds a UI to the project. The project
  now needs a design sign-off, so set it pending too
  (`python3 "$VS" gate set design --status pending --report vibe/design/critique.md`);
  Step 12 adds the design gate section to TASKS.md and Step 14 runs the design gate.

Say in one line which gates were reset. Then pick the next `D-[ID]` (the highest in
DECISIONS.md plus one) and use it in every document below; the entry itself is written in
Step 13.

---

**Documents are updated upstream first** (Steps 6 to 10B): BRIEF → ARCHITECTURE → SPEC →
PLAN and its feature map → feature folders, so each one is written against the decisions
above it. If writing a later document shows that an earlier one has to change, go back and
change it there before you continue. Files that copy these documents (SPEC_INDEX.md,
TASKS.md, FEATURE_TASKS.md) wait until the review (Steps 11 and 12).

## Step 6 — Update BRIEF.md *(if exists)*

If BRIEF.md doesn't exist — skip this step, note it in the user's summary.

BRIEF.md must reflect current reality — not the original idea.

**Feature added/removed:** Update v1 feature set table.
**Core value changed:** Update core value section with change and reason.
**Stack changed:** Update tech stack table.
**Always append:**
```
- Scope change [date]: [what changed and why — one line]
```

Save updated `BRIEF.md`.

---

## Step 7 — Update vibe/ARCHITECTURE.md *(if affected)*

(`ARCHITECTURE.md` at the project root if vibe-new-app has not moved it into `vibe/` yet.)

Only if change affects: patterns, conventions, folder structure, state management,
API design, testing philosophy, or tech decisions.

Add new pattern or update changed decision. Always add changelog line if updated:
```
> 📝 [date] · Scope change D-[ID] — [what changed architecturally]
```

Skip and state explicitly if no architecture impact.

---

## Step 8 — Update vibe/SPEC.md

**Adding a feature:** Add section with acceptance criteria. Add update note at top:
```
> ⚠️ Last updated: [date] · Scope addition: [what] · Build stage: [stage]
```

**Removing a feature:** Strikethrough, never delete:
```
~~## Feature: [Name]~~
> ⚠️ Removed: [date] · Reason: [why] · See DECISIONS.md D-[ID]
```

**Modifying:** Edit in-place, mark what changed:
```
> ~~Original: [old]~~
> Changed [date]: [new] — [reason]
```

Save. SPEC.md and SPEC_INDEX.md still always change together, but the index is updated
from the reviewed SPEC in Step 12, so it never copies text the review then changes.

---

## Step 9 — Update vibe/PLAN.md

**Feature map (Section 6), whenever it exists** and the change adds, removes, renames or
reverts a feature, or the cascade (Step 3) named affected features:
- **Added feature:** add its entry in the `← UNPLANNED ADDITION` form that vibe-add-feature's
  feature-map step uses (Added date with D-[ID], Build order, Depends on, Shared data).
- **Removed feature:** strike its entry (`~~#### [Feature]~~`) and add
  `> Removed: [date] · See DECISIONS.md D-[ID]` under it. Never delete it.
- **Renamed concept:** rename the entry and every mention of it in other entries.
- **Every feature the cascade named:** correct its `Build order:`, `Depends on:`,
  `Depended on by:`, `Shared data:` and `Can run in parallel with:` lines so they match
  the change (a removed dependency, a new shared write, a changed entity).

**Other sections**, only if the change affects data model, API shape, architecture layers,
or phase structure: add changelog line at top and update the relevant sections in-place.

Skip and state explicitly if there is no impact on the feature map or the other sections.

---

## Step 10 — Update the feature folders the change touches

- **In-progress feature** (the active one, or one the cascade paused) whose scope, data or
  API the change touches: update its `FEATURE_SPEC.md` and `FEATURE_PLAN.md` in place, with
  the same markers as Step 8 (strikethrough for removals, `Changed [date]` for edits).
- **Planned dependents the cascade named that already have a feature folder** (planned,
  build not started): update their FEATURE_SPEC/FEATURE_PLAN for the changed dependency or
  entity the same way.
- **Planned dependents without a folder:** their feature-map entry (Step 9) is all there
  is. vibe-add-feature reads it when the feature starts.
- **Built features:** no document edit here. Their retrofit tasks go into TASKS.md (Step 12).

Their `FEATURE_TASKS.md` is derived from these two files, so it is updated after their
review (Step 11). Skip and state explicitly if no feature folder is affected.

## Step 10B — Update vibe/CODEBASE.md *(only if change affects built structure)*

Update only if: the change removes/renames something built, or establishes a new pattern.
Skip and state explicitly if no update needed.

**Before any review runs, record the change in progress** (both modes). The documents are
edited now and the reviews may stop the session, so the change must be findable:
write the D-[ID] entry (format in Step 13) with `**Approved by**: pending (change in
progress, see Resume)`, and append `- **Resume D-[ID]**: at Step 11 · [date] · reviews not
run yet`. Step 1 then picks the change up whatever the mode, and Step 13 completes the
same entry.

---

## Step 11 — Independent review of every changed document

Announce:
> "Scope changed. Re-running the independent review on the changed documents..."

Invoke **vibe-spec-review** with trigger 6 (`change-spec`), once for each reviewed document
this change edited, each with that document's preset, **upstream first**:

| Changed in Steps 6 to 10B | Preset | Goldfish target |
|---|---|---|
| `BRIEF.md` | `brief` | `brief` |
| `ARCHITECTURE.md` at the root (before vibe-new-app moved it) | `architecture` | `architecture` |
| `vibe/SPEC.md`, `vibe/PLAN.md` or `vibe/ARCHITECTURE.md` | `init` when vibe/CODEBASE.md carries the vibe-init header (`📥 Generated by vibe-init`), otherwise `spec` | `spec` |
| `vibe/CODEBASE.md`, in a project vibe-init set up (its review covers CODEBASE.md) | `init` | `spec` |
| a feature's `FEATURE_SPEC.md` / `FEATURE_PLAN.md` | `feature`, with the feature folder | `feature-<folder>` |

**A vibe-init project's PLAN.md is derived, not reviewed** (vibe-init generates it after
its review, from the reviewed SPEC.md). So in such a project, don't edit PLAN.md in Step 9:
make the change in SPEC.md, and regenerate the feature map in Step 12 from the reviewed
SPEC.md, following vibe-init's `references/PLAN_RETROFIT.md` rules (keep every
`### Planned features` entry).

A target is reviewed once even when several of its documents changed. Each review reuses
its target, so findings settled before stay settled and the reviewers judge the changed
text. Don't run the checklists yourself (spec-review Step 1).

A fix that a review makes to an upstream document can change what a downstream one must
say. Carry it down before that downstream review runs, and if the downstream review has
already run, run it again on the corrected text.

**After each review:** if spec-review stopped the run (`python3 "$VS" run-state show` says
needs_human from spec review), **stop here too**: don't run the next review or Step 12.
Follow *Stopping before the change is finished* below, with the Resume point `Step 11`,
the review's reason, and its next action (`see vibe/goldfish/<target>/resolution.md`).
Manual mode: a 🔴 SPEC NOT READY verdict means follow spec-review's Step 3 (more rounds,
rework, or "continue anyway"), then come back here. If the person accepts a document as it
is ("continue anyway", or goldfish's "accept the document as it is"), note it for Step 13:
its `goldfish.py status` stays 3, and that acceptance stands.

**Then the feature tasks.** For each feature folder changed in Step 10, and an in-progress
feature that gets new or retrofit tasks, update its `FEATURE_TASKS.md` from the reviewed
FEATURE_SPEC/FEATURE_PLAN (new tasks, retrofit tasks, strikethrough removals, in its
existing task format). Then run vibe-spec-review with the `feature-tasks` preset for that
folder (target `feature-<folder>-tasks`), with the same stop rule.

### Stopping before the change is finished

In both modes, a session that stops between here and the end of the change (a review that
needs a person, a 🔴 the person chose to rework, the session simply ending) must leave a
way back to it.
`vibe-mode: run` on its own goes to the spec gate and the build, and would never return to
the steps this change has left. At every such stop:
1. **DECISIONS.md:** if the D-[ID] entry isn't written yet, write it now (format in
   Step 13) with what is known so far and `**Approved by**: pending (change stopped, see Resume)`.
   Then append, unless the last Resume line for D-[ID] already names this point:
   `- **Resume D-[ID]**: at [Step 11 | Step 13 | promote item 6] · [date] · [what a person has to do first]`
2. **Commit** the documents changed so far (Step 16, only the files that changed).
3. **Run state:** overwrite the next action so the resume comes back here:
   `python3 "$VS" run-state set --status needs_human --reason "[the same reason]" --next "[what a person has to do], then run change: resume D-[ID] (continues at [step])"`.
4. End the session. Don't report the change as complete.

---

## Step 12 — Regenerate the derived files from the reviewed text

Only now, from the documents as the review left them:

**`vibe/SPEC_INDEX.md`:** update the relevant entry and the sync date.

**`vibe/PLAN.md` in a vibe-init project:** regenerate the feature map from the reviewed
SPEC.md (see Step 11).

**`vibe/TASKS.md`:** all updates in plain English. Task IDs stay for agent sequencing.

**Adding new tasks** — expand inline feature block, insert in correct sequence.
**Adding retrofit tasks** — add HM-001-R style entries inline with plain English.
**Removing tasks** — strikethrough inline with plain English reason.
**Reverting** — add retrofit tasks for any completed work that needs undoing.
**A feature folder's tasks** mirror its reviewed `FEATURE_TASKS.md`.
**A UI added to a project whose design gate was `na`** (Step 5): add the
`## Design gate (UI projects)` section from vibe-new-app's `references/TASKS_MD.md` before
`## Phase 2`, so the gate line exists for `gate set design` to flip and for
`vibe-mode: run` to find.

Always update "What just happened" and "What's next":
```
## What just happened
🔄 Scope change: [plain English — what changed and why]
   [N new tasks / M retrofits / K removed]

## What's next
⬜ [TASK-ID] · [plain English next task]
Say "next" to continue.
```

If a person edits a reviewed document after this (at approval or later), its review
re-opens by itself: run Step 11 for it again and regenerate these files from the new text.

---

## Step 13 — Approval of the reviewed text, then the decision log

Before any approval, every target reviewed in Step 11 must be converged on the current
text: `python3 ~/.claude/skills/vibe-goldfish/scripts/goldfish.py status <target>` exits 0.
If one doesn't:
- **The person accepted that document as it is in Step 11** (manual: spec-review Step 3
  "continue anyway", or goldfish's "accept the document as it is"; its status stays 3):
  that acceptance stands. Say so in the approval question and in the DECISIONS
  **Reviewed** line, and continue.
- **Otherwise** (someone edited the document since), run its review again first.

**Manual mode:** show what the review changed, one line per fix (from each
`vibe/goldfish/<target>/resolution.md`), and ask:
> "The independent review is done. It changed: [one line per fix]. Do you approve the
>  updated [documents] as they are now?"

Wait for a clear yes. If the person edits a document instead, run Step 11 for it again and
Step 12, then ask again on the new reviewed text. On yes:
- if Step 5 set the spec gate pending:
  `python3 "$VS" gate set spec --status approved --by human --report vibe/goldfish/spec`;
- write the DECISIONS.md entry below with `**Approved by**: human`.

**Autonomous mode:** the converged reviews are the acceptance (HEADLESS.md §2.2). If Step 5
set the spec gate pending, `APPROVALS` decides, as in vibe-new-app's spec sign-off step:
- **`APPROVALS=auto`:** `gate set spec --status approved --by agent-autonomous --report vibe/goldfish/spec`.
  The helper refuses unless the spec review converged on the current text. If it refuses,
  don't retry with other flags: STOP, following *Stopping before the change is finished*
  (Step 11) with the Resume point `Step 13`, the reason `spec gate: [the helper's error]`
  and the next action `see vibe/goldfish/spec`.
- **`APPROVALS=human`:** leave the gate pending. Write the DECISIONS.md entry, commit the
  docs (Step 16), then STOP with
  `run-state set --status needs_human --reason spec_approval --next "approve the changed spec, then run vibe-mode: run"`
  and end the session.

Write the entry with `**Approved by**: agent-autonomous`, or, when the spec gate stays
pending under `APPROVALS=human`, `pending (spec gate waiting for a person)`.

`vibe/DECISIONS.md` is append-only: add to the end. If the entry for D-[ID] was already
written at a stop (it has a Resume line), don't write a second one. Once the change is
finished, append instead:
`- **D-[ID] completed**: [date] · Reviewed: [goldfish targets], fixes made by the review: [n] · Gates: [as below] · Approved by: [as below]`
(for a promoted backlog item, after Step 15 item 7).

```
---
### D-[ID] — [Short title]
- **Date**: [date] · **Type**: scope-change
- **Trigger**: change: command — user-initiated
- **Build stage**: [stage]
- **What changed**: [exact description]
- **Why**: [user's stated reason]
- **Before**: [original scope]
- **After**: [new scope]
- **Tasks affected**: New: [IDs] · Retrofit: [IDs] · Removed: [IDs]
- **Folders affected**: [feature/bug folders or "none"]
- **Architecture impact**: [Yes — what / None]
- **BRIEF.md updated**: [Yes / No — didn't exist]
- **Reviewed**: [goldfish targets] · fixes made by the review: [n]
- **Gates**: spec [reset and approved again / pending / not affected] · design [back through critique / not affected]
- **Approved by**: [human | agent-autonomous | pending (spec gate waiting for a person) | pending (change stopped, see Resume)]
---
```

---

## Step 14 — Design gate *(only when screens or components changed)*

Run this when Step 5 set the design gate pending. If the design gate was `na` and the change
adds a UI to the project, run vibe-new-app's design gate step (the UI project branch)
instead. Otherwise skip, and say so.

1. If the design contract doesn't cover the new or changed screens and components yet, run
   `design:` for them, up to its Step 3.5 checkpoint (contract, tokens, preview; no
   production UI files).
2. Run the **critique loop** from vibe-new-app's design gate step: `design: critique`, read
   the count from the `## MUST-FIX (N)` heading in `vibe/design/critique.md`, and while
   N > 0 run `design: fix must`, at most 2 passes.
3. Record the gate:
   - **Manual:** show the person the critique; when they approve,
     `gate set design --status approved --by human --report vibe/design/critique.md`. The
     helper refuses while MUST-FIX > 0: show the open items; the person can ask for more
     fixes or approve anyway with `--by human --accept-open "[their reason]"`.
   - **Autonomous:** MUST-FIX still > 0 after 2 passes → commit the docs (Step 16) and STOP with
     `run-state set --status needs_human --reason design_must_fix --next "resolve the open MUST-FIX items in vibe/design/critique.md, then run vibe-mode: run"`.
     Otherwise `APPROVALS=auto` → `gate set design --status approved --by agent-autonomous --report vibe/design/critique.md`;
     `APPROVALS=human` → leave it pending, commit the docs (Step 16), and STOP with
     `run-state set --status needs_human --reason design_approval --next "approve the design, then run vibe-mode: run"`.

---

## Step 15 — Backlog (add now, build later)

### Adding to the backlog

Run Step 5 first (the SPEC text changes, so an approved spec gate goes back to pending).
Then, upstream first:
1. **BRIEF.md**, if its v1 feature set lists the item: update it as in Step 6 (the item
   leaves v1).
2. **vibe/SPEC.md:** add the item to the Backlog section. If it had an active section,
   strike it as Step 8 does for a removal.
3. **vibe/PLAN.md:** if the feature map has an entry for it, strike it as Step 9 does.
4. Write `vibe/backlog/[YYYY-MM-DD]-[feature-slug].md`:

```
# [Feature Name]
> Added: [date] | Status: deferred

## What
[Description]

## Why deferred
[Reason]

## Effort estimate
[Small / Medium / Large]

## Dependencies
[What must be done before this]

## Promote when
[Condition]

## Promote with
change: promote [feature-name] to active
```

5. **Step 11:** review the changed documents (`spec`, and `brief` if BRIEF changed).
6. **Step 12:** update SPEC_INDEX.md and the TASKS.md backlog section.
7. **Step 13:** approval of the reviewed text and the DECISIONS.md entry
   (**Type**: scope-change (backlog)).
8. Steps 16 and 17.

### Promoting a backlog item

When user says `change: promote [item] to active`:
1. Read vibe/backlog/[date-slug].md.
2. Run Step 5 (the spec gate goes back to pending if it was approved). Set the backlog
   file's status to `Status: promoting (D-[ID])`.
3. **Update the documents upstream first, as Steps 6 to 9 do:** BRIEF.md if the v1 feature
   set changes (Step 6), ARCHITECTURE.md if the feature affects its patterns (Step 7),
   SPEC.md (move the item from the Backlog section to the active features, with acceptance
   criteria, as Step 8 does for an added feature), then the PLAN.md feature map (Step 9).
   SPEC.md is always updated before vibe-add-feature runs (item 6).
4. **Step 11:** review the changed documents. **Step 12:** update SPEC_INDEX.md and remove
   the item from the TASKS.md backlog section.
5. **Step 13:** approval of the reviewed SPEC/PLAN and the DECISIONS.md entry. Under
   autonomous `APPROVALS=human` the run stops here: follow *Stopping before the change is
   finished* (Step 11) with the Resume point `promote item 6`, the reason `spec_approval`
   and what a person has to do `approve the changed spec`.
6. Only then run vibe-add-feature to generate the full feature kit
   (tell user: "Running feature: to build the full spec and task list for this").
   It now finds the feature in the reviewed SPEC and in the feature map, runs its own
   independent review of the feature kit, and updates TASKS.md. If it stops for a person,
   stop here too: follow *Stopping before the change is finished* with the Resume point
   `promote item 6`, keeping vibe-add-feature's reason and its next action. On resume it
   runs again and picks up the feature folder it already made.
7. Mark the backlog file `Status: promoted (D-[ID]) [date]` (or delete it). If the
   D-[ID] entry has a Resume line, append its completed line (Step 13).
8. Steps 16 and 17. vibe-add-feature's feature-map update (its Step 12D) edits
   `vibe/PLAN.md` after the spec review converged, so `goldfish.py status spec` is 2 again.
   Step 17 then runs the `spec` review again (trigger 6, preset as in Step 11) instead of
   reporting the change as unfinished. That edit only records that the feature is planned,
   so the approval from Step 13 stands, unless the review makes a fix: then ask for
   approval of that fix as Step 13 does.

---

## Step 16 — Commit docs

```bash
# SPEC always — always paired:
git add vibe/SPEC.md vibe/SPEC_INDEX.md
git commit -m "docs(SPEC): [add/remove/modify] [what] — D-[ID]"

# TASKS + DECISIONS always:
git add vibe/TASKS.md vibe/DECISIONS.md
git commit -m "docs(TASKS+DECISIONS): scope change D-[ID] — [N new, M retrofit, K removed]"

# BRIEF.md if exists and changed:
git add BRIEF.md
git commit -m "docs(BRIEF): scope change D-[ID] — [what changed]"

# ARCHITECTURE.md if changed:
git add vibe/ARCHITECTURE.md
git commit -m "docs(ARCHITECTURE): [what changed] — D-[ID]"

# PLAN.md if changed:
git add vibe/PLAN.md
git commit -m "docs(PLAN): [what changed] — D-[ID]"

# Each feature folder the change touched (Step 10, Step 11):
git add vibe/features/[date-slug]/FEATURE_SPEC.md vibe/features/[date-slug]/FEATURE_PLAN.md vibe/features/[date-slug]/FEATURE_TASKS.md
git commit -m "docs(FEATURE): scope change D-[ID] — [feature]"

# CODEBASE.md if changed:
git add vibe/CODEBASE.md
git commit -m "docs(CODEBASE): [what changed] — D-[ID]"

# Backlog if created:
git add vibe/backlog/[date-slug].md
git commit -m "docs(BACKLOG): add [feature-name] — deferred [date]"
```

---

## Step 17 — Hand off to user

Hand off only when every target reviewed in Step 11 is converged on the current text
(`goldfish.py status <target>` exits 0), or the person accepted it as it is in Step 11
(Step 13), and the gates Step 5 reset are cleared again. A target that went stale after its
review (status 2, for example after the promote flow's feature-map edit in Step 15 item 8)
gets its review run again now (trigger 6) before you hand off. If one still isn't
converged, say so in plain words instead and offer to finish it (run the review again, or
approve the gate).

```
✅ Scope change complete.

**What changed:** [plain English — one or two sentences]
**Reviewed:** [the documents] were checked again by an independent review [and approved by you].
**Your task list is updated** — open vibe/TASKS.md to see the new sequence.
**Next task:** [plain English]

Say "next" to continue building.
```

No session phrases. No file paths. Human readable only.

---

## Quick reference — change types and files touched

| Change type | BRIEF | ARCH | SPEC | PLAN | TASKS | CODEBASE | DECISIONS |
|-------------|-------|------|------|------|-------|----------|-----------|
| Add feature (pre-build) | ✅ if exists | maybe | ✅ | ✅ map | ✅ new | ⏭ | ✅ |
| Add feature (mid-build) | ✅ if exists | maybe | ✅ | ✅ map | ✅ +retrofit | ⏭ | ✅ |
| Remove feature (unbuilt) | ✅ if exists | maybe | ✅ strike | ✅ map | ✅ remove | ⏭ | ✅ |
| Remove feature (built) | ✅ if exists | maybe | ✅ strike | ✅ map | ✅ retrofit | ✅ | ✅ |
| Revert scope change | ✅ if exists | maybe | ✅ | ✅ map | ✅ +retrofit | maybe | ✅ |
| Add to backlog | ✅ if v1 lists it | ⏭ | ✅ backlog | maybe | ✅ backlog | ⏭ | ✅ |
| Promote backlog item | ✅ if exists | maybe | ✅ | ✅ map | ✅ schedule | ⏭ | ✅ |
| Rename concept | ✅ if exists | maybe | ✅ | ✅ map | ✅ refs | ✅ if built | ✅ |
| Change tech/pattern | ✅ if exists | ✅ | maybe | ✅ | maybe | ✅ if built | ✅ |

`✅ map` = the PLAN.md feature map, when one exists (Step 9).

On every row: an in-progress or planned feature folder the change touches is updated too
(Step 10). Every reviewed document that changed is reviewed again with its preset (Step 11),
and the person approves the reviewed text before the build continues (Step 13). A change to
SPEC, PLAN or ARCHITECTURE after the spec gate was approved sets it back to pending (Step 5),
and a change to screens or components sends the design gate back through
`design: critique` (Step 14).
