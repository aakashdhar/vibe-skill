# HEADLESS.md — running vibe with no human at the keyboard

The vibe skills are written for a person in the terminal: they ask questions, wait for
approval, and stop at the end of every phase. This file is the contract for running the
same skills with **no one watching** — from a driver like Reeve, a CI job, or a
`claude -p` session — without inventing a second workflow.

**Nothing here changes manual use.** With the defaults (`VIBE_MODE=manual`,
`APPROVALS=human`, `PHASES=stop`) every skill behaves exactly as before.

All state is read and written through one deterministic helper, so nothing depends on
a model hand-writing JSON correctly:

```bash
VS="$HOME/.claude/skills/vibe-mode/scripts/vibe_state.py"   # installed location
python3 "$VS" mode                                           # resolved settings
```
(If the skills are installed elsewhere, use that copy of `vibe-mode/scripts/vibe_state.py`.
Every command below is run from the project root.)

---

## 1. The three settings

Written in the `## Execution mode` section of `CLAUDE.md`:

```
## Execution mode
VIBE_MODE=manual        # manual | autonomous — wait for "next", or run tasks automatically
APPROVALS=human         # human | auto — who signs off the spec and the design
PHASES=stop             # stop | continue — after a phase gate passes
```

Resolved in this order (first hit wins): environment variables `VIBE_MODE`,
`VIBE_APPROVALS`, `VIBE_PHASES` (how a driver sets them before `CLAUDE.md` exists) →
the `CLAUDE.md` lines → the defaults above. `vibe_state.py mode` prints the result;
**every skill below resolves settings this way, not by grepping CLAUDE.md itself.**

---

## 2. Autonomous planning — the rule every "wait" follows

When `VIBE_MODE=autonomous`, **no skill asks the user anything and no skill waits.**
Every step that says "wait for approval", "wait for answer", "ask", "confirm", "(y/n)"
or "iterate until approved" is replaced by this rule:

1. **Choosing between options** (update vs fresh, skip vs run, install a hook, a stack
   choice, a UI layout question): take the option the skill marks as recommended; if none
   is marked, take the conservative default that keeps the build moving and changes the
   least. Never pick "skip" for a quality step (spec review, design, tests, review).
2. **Approving your own draft** (brief, architecture, SPEC, wireframe, feature map,
   FEATURE_SPEC/PLAN, BUG_SPEC/PLAN, design contract): accept it. Before accepting,
   re-read it once against the brief and fix anything obviously wrong.
3. **Missing information:** make the most reasonable assumption the brief supports and
   write it down (step 4). Plan Mode does not apply — there is no one to exit it.
4. **Record it.** For every approval or assumption, append one entry to
   `vibe/DECISIONS.md` (create the folder if needed):
   ```
   ### D-[ID] — Autonomous: [what was decided]
   - **Type**: autonomous-approval | autonomous-assumption
   - **Skill / step**: [skill · step]
   - **Chose**: [option or assumption] — **Why**: [one line]
   - **Approved by**: agent-autonomous
   ```
   One entry per skill run is fine if it lists each item.
5. **Stop for a person only when a person is genuinely required:** credentials or
   secrets, spending money, deleting user data, a paid third-party service, or a
   contradiction in the brief that no assumption can resolve. Then write the run state
   (section 4) as `needs_human` with the exact question, and end the session.

The two human sign-offs (spec and design) are **not** governed by this rule — see
section 3.

---

## 3. Approvals — the spec gate and the design gate

Two decisions stay with a person by default: signing off the **spec** (the plan the
build will follow) and the **design** (the visual language UI is built on). Both are
recorded in `vibe/.gates.json` so any tool can read and write them:

```json
"spec":   { "status": "pending|approved|skipped|na", "date": "...", "by": "human|agent-autonomous", "report": "vibe/spec-reviews/..." },
"design": { "status": "pending|approved|skipped|na", "date": "...", "by": "...", "report": "vibe/design/critique.md" }
```

`vibe_state.py gate set spec|design --status …` writes this **and** flips the matching
`## Spec gate` / `## Design gate` line in `vibe/TASKS.md`. Approving from any UI means
running that command (or writing the same JSON). `vibe_state.py gate check spec` exits 0
when the gate is cleared (`approved`, `skipped` or `na`).

- **`APPROVALS=human`** (default): when the spec or design is ready, set it `pending`,
  write the run state `needs_human` (`reason: spec_approval` / `design_approval`), and end
  the session. The next session resumes after a person approves.
- **`APPROVALS=auto`**: set it `approved --by agent-autonomous` and continue.
- In **manual** mode the person approves in chat; the skill then records it with
  `gate set … --status approved`.

Non-UI projects set the design gate `na`. Choosing "skip design" sets it `skipped` (and is
logged in DECISIONS.md as before).

---

## 4. Run state — why the session stopped

`vibe/.run_state.json` answers "what is happening, and why did it stop?" for anyone
outside the session. Write it with `vibe_state.py run-state set`:

| status | when | `reason` / `next_action` |
|---|---|---|
| `running` | a session starts or resumes work on a phase | phase number |
| `phase_done` | a phase gate passed and `PHASES=stop` | next: "start phase N+1" |
| `needs_human` | an approval is pending, a gate could not be cleared, a task failed twice, or real information is missing | the exact question / what to do |
| `failed` | something broke that retrying won't fix (tooling, environment) | the error |
| `complete` | every phase and the final gate have passed | — |

**Write it at every stop**, in manual and autonomous mode alike — before printing the
stop message, not instead of it. A session that ends without writing it is treated as
interrupted (for example, it ran out of context) and simply resumed.

---

## 5. Resuming — `vibe-mode: run`

A fresh session that is told `vibe-mode: run` (or "continue the build") works out where
the project is from the files alone and continues from the earliest unfinished step:

1. **No `vibe/TASKS.md`?** If `BRIEF.md` exists, run `new:` (vibe-new-app). Otherwise
   write `needs_human` — "no brief: run brainstorm: first" — and stop.
2. **Spec gate:** `gate check spec`. If not cleared → follow section 3 (pending + stop, or
   auto-approve).
3. **Design gate** (TASKS.md has a `## Design gate` line and it is not `na`):
   if no design artifacts exist (`DESIGN.md`, `vibe/design/CONTRACT.md`,
   `vibe/DESIGN_SYSTEM.md`), run `design:`, then `design: critique` and one
   `design: fix must` pass. Then `gate check design` → section 3.
4. **Build:** the current phase is the first `## Phase N` with unfinished tasks or a gate
   that has not passed in `vibe/.gates.json` (0 P0 and 0 P1). Write `running`, then run
   `references/AUTONOMOUS_EXECUTION_BLOCK.md` for that phase.
5. **All phases passed?** Run `review: final`. Passed → write `complete`.

**Projects that predate these gates.** A project scaffolded before vibe v2.5.0 has no
`spec` / `design` entry in `.gates.json`. Don't stall a build that is already under way:
- no `spec` entry and any Phase 1 task is already `[x]` → treat the spec as signed off:
  `gate set spec --status approved --by agent-autonomous` + a DECISIONS.md note
  ("spec gate backfilled — build predates the gate").
- no `design` entry, design artifacts exist, and any Phase 2+ task is already `[x]` →
  the same for `design`.
Otherwise the gates apply as normal (a design that exists but was never approved still
waits for approval under `APPROVALS=human`).

This is the single entry point a driver needs: start `claude -p "vibe-mode: run"` with the
three settings in the environment, read `vibe/.run_state.json` when it ends, repeat.
