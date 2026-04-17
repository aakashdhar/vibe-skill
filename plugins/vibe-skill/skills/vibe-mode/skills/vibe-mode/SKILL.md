---
name: vibe-mode
description: >
  Sets the execution mode for the vibe-* framework — manual or autonomous.
  In manual mode: waits for "next" between tasks, waits for "review:" after phases.
  In autonomous mode: executes all tasks automatically, uses subagents for
  independent tasks in parallel, auto-runs review after each phase, only stops
  on P0 findings or deploy gates.
  Triggers on "vibe-mode: autonomous", "vibe-mode: manual", "vibe-mode: status",
  "set autonomous mode", "set manual mode", "switch to autonomous",
  "turn on autonomous", "turn off autonomous", "what mode am I in".
  Always use when the user wants to control how much the framework
  runs automatically vs waits for human input.
  Writes VIBE_MODE to CLAUDE.md. All vibe-* skills read this on startup.
---

# Vibe Mode Skill

Sets and persists the execution mode for the entire vibe-* framework.
One command. Affects every skill in the session.

---

## Commands

```
vibe-mode: autonomous    ← full auto-execution, subagents, auto-review
vibe-mode: manual        ← default, waits for next and review: at each step
vibe-mode: status        ← shows current mode and what it means
```

---

## Step 1 — Read current CLAUDE.md

```bash
cat CLAUDE.md 2>/dev/null | grep "VIBE_MODE" || echo "NOT SET"
```

If `CLAUDE.md` does not exist:
> "No CLAUDE.md found — are you at the project root?
> Run this from inside a vibe-* project."
Stop.

---

## Step 2 — Apply the mode

### Setting autonomous mode

Find the `## Execution mode` section in `CLAUDE.md`.
If it exists — update the `VIBE_MODE` line.
If it doesn't exist — append the section.

```
## Execution mode
VIBE_MODE=autonomous
```

Then confirm:

```
⚡ Autonomous mode activated.

What this means for this session:
  Tasks      — execute automatically, no "next" needed
  Parallel   — independent tasks spawn as subagents simultaneously
  Sequential — dependent tasks run in order automatically
  Review     — runs automatically after each phase completes
  P0 found   — stops and waits for you to resolve
  P1/P2      — logged to backlog, build continues
  Deploy     — always manual, no exceptions

To switch back: vibe-mode: manual
```

### Setting manual mode

```
## Execution mode
VIBE_MODE=manual
```

Confirm:

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

### Status check

Read current `VIBE_MODE` from `CLAUDE.md`. Show:

```
Current mode: [autonomous | manual | not set (defaults to manual)]

[Show the relevant "what this means" block from above]

Switch with:
  vibe-mode: autonomous
  vibe-mode: manual
```

---

## How all vibe-* skills read the mode

Every skill that executes tasks reads this at startup:

```bash
grep "VIBE_MODE" CLAUDE.md 2>/dev/null | cut -d= -f2 | tr -d ' '
```

Returns `autonomous`, `manual`, or empty (treated as `manual`).

The mode check happens once per skill invocation — at the very start,
before any planning or execution. If the mode changes mid-session
(user runs `vibe-mode:` again), the next skill invocation picks it up.

---

## Absolute rules

**Deploy is always manual.** `VIBE_MODE=autonomous` never removes the
deploy gate. Shipping to production always requires a human to confirm.

**P0s always stop autonomous mode.** The autonomous loop pauses on any
P0 finding from review. The build does not continue until P0s are resolved.
This is non-negotiable — P0s exist precisely because they block progression.

**The mode persists until explicitly changed.** Setting `autonomous` at the
start of a `new:` session means it stays autonomous for every subsequent
`add-feature:`, `fix-bug:`, and `review:` in that project until you run
`vibe-mode: manual`.

**Manual mode is always safe to switch to.** At any point during an
autonomous run, `vibe-mode: manual` puts the brakes on. The current
task completes (subagents already running finish), then the session
waits for human input before proceeding.
