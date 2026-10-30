---
name: vibe-mode
description: >
  Sets how the vibe-* framework runs: VIBE_MODE manual or autonomous, APPROVALS (who
  signs off the spec and design: human or auto) and PHASES (stop or continue after a
  passed phase gate). `vibe-mode: run` resumes a build from the files alone, the single
  entry point for driving vibe headlessly (e.g. `claude -p`); `vibe-mode: resume` is a
  person's answer to a stop and resets the saved retry budgets first. Autonomous mode runs
  tasks automatically with parallel subagents, auto-runs review after each phase with up
  to 2 fix cycles, and stops when a gate stays blocked, a task fails twice, a goldfish
  review or approval needs a person, or at deploy. Every stop is written to
  vibe/.run_state.json. Triggers on "vibe-mode: autonomous|manual|status|run|resume|
  approvals|phases", "continue the build", "resume the build", "set autonomous mode",
  "switch to manual", "what mode am I in". Settings are read through
  scripts/vibe_state.py (env vars override CLAUDE.md); see references/HEADLESS.md.
---

# Vibe Mode Skill

Sets and persists how the vibe-* framework runs, and resumes a build.
The full contract for running without a person watching is
[`references/HEADLESS.md`](references/HEADLESS.md).

---

## Commands

```
vibe-mode: autonomous          ← full auto-execution, subagents, auto-review
vibe-mode: manual              ← default, waits for next and review: at each step
vibe-mode: approvals human     ← default: you sign off the spec and the design
vibe-mode: approvals auto      ← the agent signs them off (logged in DECISIONS.md)
vibe-mode: phases stop         ← default: stop after each passed phase gate
vibe-mode: phases continue     ← carry on into the next phase automatically
vibe-mode: status              ← shows the current settings and what they mean
vibe-mode: run                 ← continue the build from where the files say it is
vibe-mode: resume              ← you have dealt with a stop: reset the saved budgets, then run
```

All settings are read with one helper (env vars `VIBE_MODE`, `VIBE_APPROVALS`,
`VIBE_PHASES` override CLAUDE.md, so a driver can set them before CLAUDE.md exists):

```bash
VS="$HOME/.claude/skills/vibe-mode/scripts/vibe_state.py"
python3 "$VS" mode
```

---

## Step 1 — Read current CLAUDE.md

```bash
python3 "$VS" mode
```

If `CLAUDE.md` does not exist and the command is anything other than `status`, `run` or `resume`:
> "No CLAUDE.md found — are you at the project root?
> Run this from inside a vibe-* project."
Stop.

---

## Step 2 — Apply the setting

All three settings live in one section of `CLAUDE.md`. Find `## Execution mode`; if it
doesn't exist, append it. Update only the line you were asked to change and keep the
others (add any that are missing, with their defaults):

```
## Execution mode
VIBE_MODE=manual        # manual | autonomous
APPROVALS=human         # human | auto — who signs off the spec and the design
PHASES=stop             # stop | continue — after a phase gate passes
```

### Setting autonomous mode

Set `VIBE_MODE=autonomous`. Then confirm:

```
⚡ Autonomous mode activated.

What this means for this session:
  Tasks      — execute automatically, no "next" needed
  Parallel   — independent tasks spawn as subagents simultaneously
  Sequential — dependent tasks run in order automatically
  Planning   — no questions: recommended options taken, assumptions logged to DECISIONS.md
  Review     — runs automatically after each phase; a failing gate gets up to 2 fix cycles
  Stops when — a gate is still blocked after that, a task fails twice,
               or the spec / design needs your sign-off (APPROVALS=human)
  Phases     — [stop after each passed gate | continue automatically] (PHASES)
  Deploy     — always manual, no exceptions

To switch back: vibe-mode: manual
```

### Setting manual mode

Set `VIBE_MODE=manual`. Confirm:

```
✋ Manual mode activated.

What this means for this session:
  Tasks    — say "next" after each task
  Parallel — asked once per session (y/n)
  Review   — run "review: phase N" manually after each phase
  Deploy   — manual

This is the default vibe-* behaviour.
To switch: vibe-mode: autonomous
```

### Setting approvals or phases

`vibe-mode: approvals human|auto` sets `APPROVALS=`; `vibe-mode: phases stop|continue`
sets `PHASES=`. Confirm with one line saying what changed and what it means (see the
comments in the section above).

### Status check

Run `python3 "$VS" mode` and show each setting, where it came from (env / CLAUDE.md /
default), any warnings, and the matching "what this means" block. If
`vibe/.run_state.json` exists, also show its status, reason and next action.

---

## Step 3 — `vibe-mode: run` (resume a build)

Follow [`references/HEADLESS.md`](references/HEADLESS.md) §5 exactly: work out from the
files where the build is (no plan → `new:` · spec gate · design gate · the current
phase · final gate) and continue from the earliest unfinished step, using
`references/AUTONOMOUS_EXECUTION_BLOCK.md` for execution. Always end by writing
`vibe/.run_state.json` (HEADLESS.md §4).

`vibe-mode: run` behaves as if `VIBE_MODE=autonomous` for this invocation even when
CLAUDE.md says manual — asking to "continue the build" is the instruction to run it.
Carry that through explicitly: read the settings with `python3 "$VS" mode --run`, and tell
every skill you invoke from here that it was entered from `vibe-mode: run`, so it reads
them the same way. `run` never resets the saved retry and fix-cycle budgets.

## Step 4 — `vibe-mode: resume` (after a stop)

`resume` is what a person says after dealing with the reason the build stopped (see
`python3 "$VS" run-state show`). Show that reason in one line, then:

```bash
python3 "$VS" counters reset --all     # the person has given the stuck work a new budget
```

and continue exactly as `vibe-mode: run` (Step 3). Only a person says `resume`. A driver
or an autonomous session never does, because that would undo the budgets.

---

## How all vibe-* skills read the settings

Every skill that asks questions, waits for approval, or executes tasks resolves the
settings at startup with `vibe_state.py mode` — never by grepping CLAUDE.md, because a
driver may have set them in the environment. When `vibe_mode` is `autonomous`, the
skill follows HEADLESS.md §2 instead of waiting.

The check happens once per skill invocation — at the very start, before any planning or
execution. If a setting changes mid-session, the next skill invocation picks it up.

---

## Absolute rules

**Deploy is always manual.** `VIBE_MODE=autonomous` never removes the
deploy gate. Shipping to production always requires a human to confirm.

**A phase gate always holds.** No phase starts until the previous phase's review has
0 P0 and 0 P1. Autonomous mode may fix its way to a clean review (at most 2 cycles,
counted on disk), but it never skips or overrides the gate.

**An agent never signs off its own work.** Under `APPROVALS=auto` the spec is approved only
after its independent goldfish review converges, and the design only with 0 MUST-FIX
items. `vibe_state.py` refuses anything else.

**Every stop is recorded.** Before stopping for any reason, write
`vibe/.run_state.json` so anyone outside the session can see why.

**The settings persist until explicitly changed.** Setting `autonomous` at the
start of a `new:` session means it stays autonomous for every subsequent
`feature:`, `bug:`, and `review:` in that project until you run
`vibe-mode: manual`.

**Manual mode is always safe to switch to.** At any point during an
autonomous run, `vibe-mode: manual` puts the brakes on. The current
task completes (subagents already running finish), then the session
waits for human input before proceeding.
