# AUTONOMOUS_EXECUTION_BLOCK.md
#
# Read this file when VIBE_MODE=autonomous is detected.
# Inserted into: vibe-add-feature, vibe-fix-bug, vibe-new-app, and `vibe-mode: run`
# at the task execution step (after planning, after "kit ready").
#
# This block replaces the "say next after each task" instruction
# when autonomous mode is active. The full headless contract — settings, approvals,
# run state, resume — is references/HEADLESS.md.

---

## Autonomous execution protocol

**Read the settings** (see HEADLESS.md §1 — never grep CLAUDE.md by hand):
```bash
VS="$HOME/.claude/skills/vibe-mode/scripts/vibe_state.py"
python3 "$VS" mode        # → vibe_mode, approvals, phases
```
Entered from `vibe-mode: run` (directly, or through a skill that `run` invoked)? Use
`python3 "$VS" mode --run` instead. It forces `vibe_mode: autonomous`, because asking to
continue the build is the instruction to run it.

If `vibe_mode` is `manual` → use standard sequential execution.
Tell the user: "Say **next** after each task."
Stop here — do not proceed with autonomous execution.

If `vibe_mode` is `autonomous` → continue below. Record that work has started:
```bash
python3 "$VS" run-state set --status running --phase [N]
```

**How stopping works.** Whenever this block says **STOP**: first write the run state
(`needs_human`, `phase_done`, `failed` or `complete` — HEADLESS.md §4) with the exact
reason and next action, then print the stop message, then end your turn. In an
interactive session that is the same as waiting for the user ("resume" continues). In a
headless session (`claude -p`) there is no one to wait for — the run state is how the
driver or UI learns why you stopped. **Never end a stop without writing the run state.**

---

## Autonomous execution flow

Do not wait for "next". Execute all tasks automatically.

### Phase execution loop

For the current unit of work (a phase's tasks, a feature's tasks, a bug fix's tasks, or
a gate's RFX fix tasks):

**1. Detect independent tasks**

Read the task file (`FEATURE_TASKS.md` / `BUG_TASKS.md` / `TASKS.md`).
Build dependency graph. Identify Wave 1 independent tasks.

If Wave 1 has 2+ independent tasks:
→ Invoke `vibe-parallel` (subagent dispatch, no prompt in autonomous mode). **Always** —
  even when the tasks look small enough to do yourself in one go. vibe-parallel is what
  checks file conflicts, writes `vibe/parallel/wave-N-status.md` (the record anyone
  watching the build reads) and gives each task its own structured report. Doing several
  tasks inline in this session skips all three.

If Wave 1 has 1 task:
→ Execute it directly as a single subagent

**2. Execute each wave**

For each wave (parallel or single):
- **Count every dispatch you make yourself:** `python3 "$VS" attempt [TASK-ID]` right
  before it. The budget is 2 (the first try and one retry) and it is saved in
  `vibe/.run_state.json`, so a new session can't start over. A wave handed to
  vibe-parallel is counted by vibe-parallel, so don't count those tasks here: counting
  twice would spend the retry on the first try. Exit 1 means it is spent: don't dispatch, **STOP** with
  `run-state set --status needs_human --phase [N] --reason "[TASK-ID] failed after retry: [root cause]" --next "[what a person must decide or fix]"`.
- Dispatch subagent(s) with scoped task prompts. Each subagent returns the
  **structured JSON completion report** (see vibe-parallel/references/REPORTING.md) —
  consume that, don't scrape prose.
- Wait for completion; read `status` + `criteria` from each report.
- On `DONE` with all criteria met and tests passing: mark `[x]`, update TASKS.md. The one
  allowed failing test is a declared expected-red regression test: a task with
  `Expect: red` whose report lists it in `tests.expected_failing`
  (vibe-parallel `references/REPORTING.md`). That task must not write the fix.
- On `FAILED` or `PARTIAL` (`[~]`), retry with a **diagnosis-first** pass rather than a
  blind re-run. PARTIAL is treated exactly like a failure: a task with unmet criteria
  never counts as done and never unlocks its dependents.
  1. Re-dispatch the task at higher reasoning effort (e.g. `effort: high`/`xhigh`
     with adaptive thinking), giving the subagent the failing report + error and
     asking it to state the root cause before fixing.
  2. Before declaring success, **self-verify**: re-check the task's acceptance
     criteria against the actual result — don't trust the report's own claim.
  3. If the second attempt is still FAILED or PARTIAL, mark it `[!]` and **STOP** with
     `run-state set --status needs_human --phase [N] --reason "[TASK-ID] failed after retry: [root cause]" --next "[what a person must decide or fix]"`.
- The budget is exactly two dispatches per task (`attempt` enforces it). Only a person
  gives a task more: `vibe-mode: resume` resets the counters.

**Keep the human view current.** After every wave, and before every stop, rewrite the
`## What just happened` / `## What's next` sections at the bottom of `vibe/TASKS.md` to
match the file's actual state — the next unticked task, or the gate that's due. A stale
"What's next" misleads anyone reading the plan mid-build.

**3. Unlock next wave**

When all tasks in Wave N complete successfully:
→ Check Wave N+1 dependencies — all met → proceed automatically
→ Dispatch Wave N+1 subagents

**4. Unit complete — when is the gate run?**

When every task in the unit is `[x]` (a unit with any `[ ]`, `[~]` or `[!]` left is not
complete: keep executing, or STOP as above, but never report it complete):
- **A phase** (Phase N tasks in TASKS.md) → run the **review gate** below for Phase N.
- **A feature** → first make sure vibe-add-feature has run its post-build steps for it
  (graph update, vibe-test on the files it touched, and the reopen check for a passed
  gate), so the review sees the finished feature. Then, if it was the **last unfinished
  feature of its phase**, run the review gate for that phase; otherwise announce "feature complete" and return to the caller
  (the phase loop continues with the next feature).
- **A bug fix** → announce "fix complete" and return. Bug fixes don't trigger a phase
  gate on their own, but if the fix landed after a review gate passed, vibe-fix-bug has
  reopened that gate (`gate reopen`), so the phase loop runs that review again before
  moving on.
- **RFX fix tasks** → re-run the review gate for the same phase (see the fix loop).

Never start the next phase from here — that only happens through the review gate.

---

## Autonomous review gate

```
Running review: [phase name] automatically (VIBE_MODE=autonomous)...
```

Invoke `vibe-review` for this phase. It records the result in `vibe/.gates.json` and
edits the phase's gate line in TASKS.md. The bar is **0 P0 and 0 P1**.

### PASS (0 P0 and 0 P1)

```
✅ Review passed — Phase [N] · 0 P0, 0 P1 · [N] P2/P3 to backlog
```

Then, by caller and setting:
- **Called from a feature or bug flow outside a phase loop** → announce and return.
- **`PHASES=stop`** (default) → **STOP** with
  `run-state set --status phase_done --phase [N] --next "start phase [N+1]"`.
- **`PHASES=continue`** → go to **Phase continuation** below.

### FAIL (any P0 or P1) — the fix loop

A failing gate is cleared the way a person would clear it: fix exactly what the review
found, then review again. **Only the RFX tasks review wrote under the phase's gate line
are in scope** — never add features or unrelated work.

1. **Count the cycle:** `python3 "$VS" cycle [N]` (`final` for the final gate). Exit 1
   means 2 cycles are already spent, possibly by an earlier session: go to step 4.
2. Treat the open `RFX-NNN` tasks under `## Phase [N] gate` as the unit of work and run
   them through the phase execution loop above (waves, retries, `[x]` marks).
3. Re-run the review gate for Phase [N]. When it passes, vibe-review resets the cycle
   counter (`counters reset --phase [N]`).
4. **At most 2 fix cycles.** If the gate still fails after the second cycle,
   **STOP** with
   `run-state set --status needs_human --phase [N] --reason "Phase [N] gate blocked: [X] P0 + [Y] P1 after 2 fix cycles" --next "see vibe/reviews/phase-[N]-review.md"`
   and print:
   ```
   🔴 AUTONOMOUS EXECUTION PAUSED — Phase [N] gate still blocked after 2 fix cycles

   [List each open P0/P1 with file path, line number, and specific fix required]

   Fix these (or decide they are acceptable), then say "resume" / run `vibe-mode: run`.
   ```
   On resume, re-run the review first — never assume a gate is clear.

Run the fix loop in **manual** mode only if the user asks; otherwise manual mode stops at
the first failing review, as before.

---

## Phase continuation (`PHASES=continue`)

After Phase [N]'s gate passes:

1. **Find the next phase** in TASKS.md with unfinished work. If there is none, go to
   **Final gate**.
2. **Design gate first, if needed.** If the next phase contains UI work and the project
   has a `## Design gate` line, run `vibe_state.py gate check design`. If it is not
   cleared, follow HEADLESS.md §5 step 3 (build the design, critique, up to 2
   `design: fix must` passes while MUST-FIX > 0, then approve or stop for a person per
   `APPROVALS`; an agent can never approve with MUST-FIX items open).
3. Write `run-state set --status running --phase [N+1]`.
4. **Run the phase:**
   - **Concrete task lines** (`[ ] P[N+1]-001 · …`) → run this block for them.
   - **Feature lines** (`⬜ [Feature] — …` with `Spec: run feature: …`) → work in
     **batches** in build order (PLAN.md §6 — respect every `Needs:`). A batch is every
     unfinished feature whose `Needs:` are all complete. The `Parallel with:` lines the
     planner wrote say which of them share no writes.
     - **Batch of 1** → run `feature: [name]`. vibe-add-feature plans it with no waits
       (HEADLESS.md §2) and builds it with this block.
     - **Batch of 2+** → the features are built **together**, not one after another:
       1. Plan each one: `feature: [name] plan-only` (vibe-add-feature stops after its
          task review, Trigger 4T, and its derived files: nothing is built, no gate is
          run). If any feature's review stopped the run (`run-state show` says
          needs_human), **STOP** here: build none of the batch.
       2. Run vibe-parallel **Entry point E** on all of the batch's `FEATURE_TASKS.md`
          files at once. Its conflict passes keep two features that touch the same file
          (e.g. a shared `app.js`) in different waves, so this is safe even when the
          `Parallel with:` hint was optimistic.
       3. For every feature in the batch, once its tasks finish: run vibe-add-feature's
          post-build steps (graph update, vibe-test on the files its FEATURE_TASKS.md
          `Touches` lists, the reopen check), then mark it `✅` in TASKS.md. Then take the
          next batch.
     The phase's review gate runs once, after the last feature of the phase is done.
5. Continue until every phase has passed.

### Final gate

When every phase gate has passed, run `review: final`.
- PASS → **STOP** with `run-state set --status complete`, then announce that the build is
  complete and deploy-ready (deploy itself stays manual — `vibe-mode` never deploys).
- FAIL → the same fix loop as a phase gate, with `final` as the phase.

---

## What the user sees in autonomous mode

At the start (after kit is ready):
```
⚡ Autonomous mode active — executing all tasks automatically.
   Independent tasks run as parallel subagents.
   Review runs automatically after each phase; failing reviews get up to 2 fix cycles.
   I'll stop if a gate is still blocked after that, a task fails twice, or an approval is needed.
   To switch to manual at any time: vibe-mode: manual
```

During execution (brief updates, not verbose):
```
⚡ Wave 1: spawning [N] subagents — [TASK-IDs]
✅ Wave 1 complete ([N]m [N]s)
⚡ Wave 2: spawning [N] subagents — [TASK-IDs]
✅ Wave 2 complete ([N]m [N]s)
✅ All tasks complete — running review automatically...
🔧 Gate blocked (1 P0, 2 P1) — fix cycle 1: running RFX-001..003
✅ Phase 1 gate passed — 0 P0, 0 P1
```

---

## Switching back to manual mid-session

User types: `vibe-mode: manual`

The current subagents already dispatched complete their tasks.
After they finish — execution pauses. User must say `next` to continue.
Review must be run manually with `review: phase N`.

The mode change takes effect for the NEXT task, not the current one.
