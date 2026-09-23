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
- Dispatch subagent(s) with scoped task prompts. Each subagent returns the
  **structured JSON completion report** (see vibe-parallel/references/REPORTING.md) —
  consume that, don't scrape prose.
- Wait for completion; read `status` + `criteria` from each report.
- On `DONE` with all criteria met and tests passing: mark `[x]`, update TASKS.md.
- On failure or `PARTIAL`, retry with a **diagnosis-first** pass rather than a
  blind re-run:
  1. Re-dispatch the task at higher reasoning effort (e.g. `effort: high`/`xhigh`
     with adaptive thinking), giving the subagent the failing report + error and
     asking it to state the root cause before fixing.
  2. Before declaring success, **self-verify**: re-check the task's acceptance
     criteria against the actual result — don't trust the report's own claim.
  3. If the second attempt still fails, **STOP** with
     `run-state set --status needs_human --phase [N] --reason "[TASK-ID] failed after retry: [root cause]" --next "[what a person must decide or fix]"`.
- Retry budget is per task; a task that converges (fewer unmet criteria on the
  retry) may warrant one more attempt — use judgment, don't hard-stop at exactly
  two if it's clearly closing in and cheap. Never loop indefinitely.

**Keep the human view current.** After every wave, and before every stop, rewrite the
`## What just happened` / `## What's next` sections at the bottom of `vibe/TASKS.md` to
match the file's actual state — the next unticked task, or the gate that's due. A stale
"What's next" misleads anyone reading the plan mid-build.

**3. Unlock next wave**

When all tasks in Wave N complete successfully:
→ Check Wave N+1 dependencies — all met → proceed automatically
→ Dispatch Wave N+1 subagents

**4. Unit complete — when is the gate run?**

When every task in the unit is `[x]`:
- **A phase** (Phase N tasks in TASKS.md) → run the **review gate** below for Phase N.
- **A feature** → if it was the **last unfinished feature of its phase**, run the review
  gate for that phase; otherwise announce "feature complete" and return to the caller
  (the phase loop continues with the next feature).
- **A bug fix** → announce "fix complete" and return. Bug fixes don't trigger a phase
  gate on their own.
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

1. Treat the open `RFX-NNN` tasks under `## Phase [N] gate` as the unit of work and run
   them through the phase execution loop above (waves, retries, `[x]` marks).
2. Re-run the review gate for Phase [N].
3. Repeat **at most 2 fix cycles.** If the gate still fails after the second cycle,
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
   cleared, follow HEADLESS.md §5 step 3 (build the design, critique, fix once, then
   approve or stop for a person per `APPROVALS`).
3. Write `run-state set --status running --phase [N+1]`.
4. **Run the phase:**
   - **Concrete task lines** (`[ ] P[N+1]-001 · …`) → run this block for them.
   - **Feature lines** (`⬜ [Feature] — …` with `Spec: run feature: …`) → in build order
     (PLAN.md §6 — respect every `Needs:`), run `feature: [name]` for each. vibe-add-feature
     plans it with no waits (HEADLESS.md §2) and builds it with this block; the phase's
     review gate runs when the last feature is done.
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
