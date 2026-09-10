# GATES.md — the gate enforcement protocol

The framework's quality gates (phase review, design, final-before-deploy) only have
value if they actually hold. A markdown skill can't halt an LLM mid-turn, so
enforcement is built in three layers — flow, state, and a hard machine lock — so the
gates hold in **manual mode too**, not just autonomous.

Every execution-driving skill (vibe-new-app, vibe-add-feature, vibe-fix-bug,
vibe-parallel, vibe-review, vibe-deploy) follows this protocol.

---

## Layer 1 — One flow, gates always invoked

The build always flows through the same pattern; gates are steps in it, not optional
detours:

```
feature: / bug:  →  (design: if new UI, when no design system)  →  build tasks
                 →  test: (blast radius)  →  [phase boundary?] → review: (phase gate)
Phase N complete →  review: phase N  →  gate recorded  →  Phase N+1 may start
Final phase      →  review: final  →  0 P0 + 0 P1  →  deploy: unlocked
```

- The **last task of a phase** triggers `review:` automatically in autonomous mode,
  and prompts for it in manual mode ("Phase N tasks complete — running the phase
  review gate now").
- `vibe-deploy` Step 0.5 already enforces the final gate (STOP on open P0/P1).

## Layer 2 — A checkable state file: `vibe/.gates.json`

`vibe-review` writes this on every run; advancement logic reads it. This is what
makes a gate *checkable* rather than remembered.

```json
{
  "phases": {
    "1": { "review": "passed", "p0": 0, "p1": 2, "date": "2026-09-10", "report": "vibe/reviews/phase-1-review.md" },
    "2": { "review": "open" }
  },
  "design":  { "status": "passed" },        // passed | skipped | na (non-UI)
  "final":   { "review": "not_run" }         // passed only when 0 P0 + 0 P1
}
```

`review` status values: `not_run` | `open` (P0s outstanding) | `passed` | `failed`.

**Advancement rule (enforced by the generated CLAUDE.md constitution, every session):**
> Before starting the FIRST task of Phase N+1, read `vibe/.gates.json`. If
> `phases[N].review` is not `"passed"`, STOP: "Phase N's review gate is not passed
> (status: X). Run `review: phase N` before starting Phase N+1." Do not proceed —
> in manual or autonomous mode.

The same rule guards the design gate (no UI-feature build before `design`) and the
deploy gate (no `deploy:` before the final gate).

## Layer 3 — The hard lock: a git pre-push hook

The only true machine-level enforcement. Offered during setup by vibe-new-app
(Step 10D). It blocks a push while P0s are open, so the gate holds even if an agent or
human ignores layers 1-2.

`.git/hooks/pre-push` (or a husky `pre-push`):
```bash
#!/usr/bin/env bash
# vibe gate: block push while any P0 review finding is open
if [ -f vibe/reviews/backlog.md ] && grep -qiE '^\s*-\s*\[ \].*\bP0\b' vibe/reviews/backlog.md; then
  echo "✗ vibe gate: open P0 review findings in vibe/reviews/backlog.md — resolve before pushing."
  echo "  (override once with: git push --no-verify)"
  exit 1
fi
# Optional stricter form: also read vibe/.gates.json and block if final.review != passed
exit 0
```
`--no-verify` is the deliberate, visible override — enforcement with an explicit
escape hatch, not a trap.

---

## Writing the state (vibe-review)

At the end of a review, vibe-review updates `vibe/.gates.json`:
- Set `phases[N].review` to `passed` (0 P0) / `open` (P0s found) / `failed`.
- Record `p0`, `p1`, `date`, `report` path.
- For a `review: final` run, set `final.review` to `passed` only when P0 == 0 AND P1 == 0.
Merge into the existing file (never clobber other phases' entries).

## Honest scope
Layers 1-2 are convention the agent follows reliably because they are wired into the
default flow and backed by a state file it must check; Layer 3 is the only part a
machine enforces. Together they make the gates real without overstating that a prompt
can physically prevent a determined bypass — `--no-verify` and an explicit "skip
gate" remain available and are logged in DECISIONS.md when used.
