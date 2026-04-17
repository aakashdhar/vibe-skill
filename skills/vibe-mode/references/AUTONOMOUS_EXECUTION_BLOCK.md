# AUTONOMOUS_EXECUTION_BLOCK.md
#
# Read this file when VIBE_MODE=autonomous is detected.
# Inserted into: vibe-add-feature, vibe-fix-bug, vibe-new-app
# at the task execution step (after planning, after "kit ready").
#
# This block replaces the "say next after each task" instruction
# when autonomous mode is active.

---

## Autonomous execution protocol

**Read mode:**
```bash
MODE=$(grep "VIBE_MODE" CLAUDE.md 2>/dev/null | cut -d= -f2 | tr -d ' ')
```

If `MODE` is empty or `manual` → use standard sequential execution.
Tell the user: "Say **next** after each task."
Stop here — do not proceed with autonomous execution.

If `MODE` is `autonomous` → continue below.

---

## Autonomous execution flow

Do not wait for "next". Execute all tasks automatically.

### Phase execution loop

For the current phase (Phase 1, Phase 2 feature, bug fix tasks):

**1. Detect independent tasks in this phase**

Read the task file (`FEATURE_TASKS.md` / `BUG_TASKS.md` / `TASKS.md`).
Build dependency graph. Identify Wave 1 independent tasks.

If Wave 1 has 2+ independent tasks:
→ Invoke `vibe-parallel` (subagent dispatch, no prompt in autonomous mode)

If Wave 1 has 1 task:
→ Execute it directly as a single subagent

**2. Execute each wave**

For each wave (parallel or single):
- Dispatch subagent(s) with scoped task prompts
- Wait for completion
- On success: mark tasks `[x]`, update TASKS.md
- On first failure: retry once with failure context
- On second failure: STOP — surface the failure, wait for human

**3. Unlock next wave**

When all tasks in Wave N complete successfully:
→ Check Wave N+1 dependencies — all met → proceed automatically
→ Dispatch Wave N+1 subagents

**4. Phase complete**

When all tasks in this phase are marked `[x]`:
→ Do NOT start the next phase
→ Automatically invoke `vibe-review` for this phase

---

## Autonomous review gate

After phase tasks complete, run review automatically:

```
Running review: [phase name] automatically (VIBE_MODE=autonomous)...
```

Invoke `vibe-review` for this phase.

**Review result handling:**

If review returns 0 P0 findings:
```
✅ Review passed — 0 P0 findings
   [N] P1 findings logged to backlog
   [N] P2 findings logged to backlog

[In autonomous mode: signal to calling skill that phase is complete]
[vibe-new-app: announce Phase 1 done, Phase 2 ready to begin]
[vibe-add-feature: announce feature complete, ready for merge]
[vibe-fix-bug: announce fix complete, ready for merge]
```

If review returns any P0 findings:
```
🔴 AUTONOMOUS EXECUTION PAUSED

Review found [N] P0 issue(s) that must be resolved before continuing:

[List each P0 with file path, line number, and specific fix required]

Fix these issues, then say "resume" to continue autonomous execution.
```

Wait for human. Do not proceed until P0s are resolved and human says "resume".

After "resume" → re-run review automatically → if 0 P0s → continue.

---

## What the user sees in autonomous mode

At the start (after kit is ready):
```
⚡ Autonomous mode active — executing all tasks automatically.
   Independent tasks run as parallel subagents.
   Review runs automatically after each phase.
   I'll only stop if a P0 is found or a task fails twice.
   To switch to manual at any time: vibe-mode: manual
```

During execution (brief updates, not verbose):
```
⚡ Wave 1: spawning [N] subagents — [TASK-IDs]
✅ Wave 1 complete ([N]m [N]s)
⚡ Wave 2: spawning [N] subagents — [TASK-IDs]
✅ Wave 2 complete ([N]m [N]s)
✅ All tasks complete — running review automatically...
```

After review passes:
```
✅ Phase complete — review passed · 0 P0s · [N] P1s logged
```

After review fails (P0s):
```
🔴 STOPPED — [N] P0 finding(s) require your attention.
[findings listed]
Fix and say "resume" to continue.
```

---

## Switching back to manual mid-session

User types: `vibe-mode: manual`

The current subagents already dispatched complete their tasks.
After they finish — execution pauses. User must say `next` to continue.
Review must be run manually with `review: phase N`.

The mode change takes effect for the NEXT task, not the current one.
