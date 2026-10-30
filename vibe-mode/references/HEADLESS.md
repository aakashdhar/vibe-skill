# HEADLESS.md — running vibe with no human at the keyboard

The vibe skills are written for a person in the terminal: they ask questions, wait for
approval, and stop at the end of every phase. This file is the contract for running the
same skills with **no one watching** — from an outside driver, a CI job, or a
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
2. **Approving your own draft.** You wrote it, so your own approval proves nothing.
   - Brief, agent architecture, architecture, SPEC and FEATURE_SPEC/PLAN/TASKS: these are
     accepted only through **vibe-spec-review**, which runs an independent
     **vibe-goldfish** review (fresh subagents that never saw this conversation). Accept
     the draft when that review converges. Its escalations and churn stop the run for a
     person (vibe-goldfish Step 6).
   - Wireframe, PLAN.md feature map, BUG_SPEC/PLAN and the design contract are not yet
     covered by a goldfish review. Accept them after re-reading once against the brief,
     and say in the DECISIONS.md entry that no independent review ran.
3. **Missing information:** make the most reasonable assumption the brief supports and
   write it down (step 4). Plan Mode does not apply — there is no one to exit it.
4. **Record it.** For every approval or assumption, append one entry to
   `vibe/DECISIONS.md`. It is append-only: add to the end and never rewrite it. If it
   doesn't exist yet, create it with the canonical header from vibe-new-app's DECISIONS
   template (create the folder if needed), and continue `D-NNN` numbering from the
   highest ID already there:
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
"spec":   { "status": "pending|approved|skipped|na", "date": "...", "by": "human|agent-autonomous", "report": "vibe/goldfish/spec" },
"design": { "status": "pending|approved|skipped|na", "date": "...", "by": "...", "report": "vibe/design/critique.md" }
```

`vibe_state.py gate set spec|design --status …` writes this **and** flips the matching
`## Spec gate` / `## Design gate` line in `vibe/TASKS.md`. Approving from any UI means
running that command (or writing the same JSON). `vibe_state.py gate check spec` exits 0
when the gate is cleared (`approved`, `skipped` or `na`).

- **`APPROVALS=human`** (default): when the spec or design is ready, set it `pending`,
  write the run state `needs_human` (`reason: spec_approval` / `design_approval`), and end
  the session. The next session resumes after a person approves.
- **`APPROVALS=auto`**: set it `approved --by agent-autonomous` and continue. `vibe_state.py`
  enforces two conditions and refuses otherwise. The **spec** needs
  `--report vibe/goldfish/spec`, the converged goldfish review of the spec. The **design**
  needs 0 MUST-FIX items in `vibe/design/critique.md`. If either is not met, the gate stays
  `pending`: write `needs_human` and stop.
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
| `needs_human` | an approval is pending, a gate could not be cleared, a task failed twice, a goldfish review needs a decision, or real information is missing | the exact question / what to do |
| `failed` | something broke that retrying won't fix (tooling, environment) | the error |
| `complete` | every phase and the final gate have passed | — |

**Write it at every stop**, in manual and autonomous mode alike — before printing the
stop message, not instead of it. A session that ends without writing it is treated as
interrupted (for example, it ran out of context) and simply resumed.

**Budgets survive sessions.** `vibe/.run_state.json` also holds `counters`: dispatches per
task (`vibe_state.py attempt ID`, budget 2) and fix cycles per review gate
(`vibe_state.py cycle N`, budget 2). A resumed session inherits whatever the last one
spent, so an interrupted loop can't restart its budget. A passed gate resets its own
cycles. Only a person resets task attempts, with `vibe-mode: resume` (section 5).

---

## 5. Resuming — `vibe-mode: run`

A fresh session that is told `vibe-mode: run` (or "continue the build") works out where
the project is from the files alone and continues from the earliest unfinished step:

1. **No `vibe/TASKS.md`?** If `BRIEF.md` exists, run `new:` (vibe-new-app). Otherwise
   write `needs_human` — "no brief: run brainstorm: first" — and stop.
2. **Spec gate:** `gate check spec`. If not cleared → follow section 3 (pending + stop, or
   auto-approve, which `vibe_state.py` refuses unless the goldfish review of the spec has
   converged on the current text; a previous `needs_human` from spec review therefore
   still stands). If `vibe/goldfish/spec/ledger.json` doesn't exist yet (a project from
   before v2.7.0), run `spec-review:` with the `spec` preset (`init` for a vibe-init
   project) first, then approve per section 3. If it exists and stopped for a person,
   `vibe/goldfish/spec/resolution.md` lists the exact command they run to answer.
3. **Design gate** (TASKS.md has a `## Design gate` line and it is not `na`, and the gate
   is not cleared):
   (a) if no design artifacts exist (`DESIGN.md`, `vibe/design/CONTRACT.md`,
   `vibe/DESIGN_SYSTEM.md`), run `design:` **up to its Step 3.5 checkpoint** (contract,
   tokens, `vibe/design/preview.html`) — the production UI is built later by the phase's
   UI tasks from the approved contract, never before sign-off.
   (b) in every case, including a design that already existed: `design: critique`
   and up to **2** `design: fix must` passes while MUST-FIX > 0. Still open after 2 → write
   `needs_human` (`reason: design_must_fix`) and stop. Then `gate check design` → section 3.
4. **Build:** the current phase is the first `## Phase N` with unfinished tasks or a gate
   that has not passed in `vibe/.gates.json` (0 P0 and 0 P1). Unfinished means `[ ]`,
   `[~]` or `[!]`. Write `running`, then run `references/AUTONOMOUS_EXECUTION_BLOCK.md`
   for that phase. A `[~]`/`[!]` task is dispatched again only if its saved budget allows
   (`vibe_state.py attempt`); otherwise the run stops again with the same reason, which is
   correct: it is waiting for a person.
5. **All phases passed?** Run `review: final`. Passed → write `complete`.

**Projects that predate these gates.** A project scaffolded before vibe v2.5.0 has no
`spec` / `design` entry in `.gates.json`. Don't stall a build that is already under way:
- no `spec` entry and any Phase 1 task is already `[x]` → treat the spec as signed off:
  `gate set spec --status approved --by agent-autonomous --backfill` + a DECISIONS.md note
  ("spec gate backfilled — build predates the gate").
- no `design` entry, design artifacts exist, and any Phase 2+ task is already `[x]` →
  the same for `design`: `gate set design --status approved --by agent-autonomous --backfill`
  plus the DECISIONS.md note. (The UI is already built, so no critique loop is forced on it.)
Otherwise the gates apply as normal (a design that exists but was never approved still
waits for approval under `APPROVALS=human`).

This is the single entry point a driver needs: start `claude -p "vibe-mode: run"` with the
three settings in the environment, read `vibe/.run_state.json` when it ends, and repeat
only while it says `running` or `phase_done`. On `needs_human`, stop and show the reason
to a person. Relaunching would only hit the same stop, because the budgets are saved.

**`vibe-mode: resume` is the person's answer to a stop.** It means "I have dealt with
the reason". It resets the saved counters (`vibe_state.py counters reset --all`), then
does exactly what `run` does. A driver never sends `resume`; only a person does.
