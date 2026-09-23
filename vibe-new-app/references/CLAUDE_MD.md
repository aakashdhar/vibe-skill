# CLAUDE_MD.md Template

Used by vibe-new-app Step 6 to generate the project-root `CLAUDE.md` for a
greenfield project. Fill every `[placeholder]` from SPEC.md / PLAN.md /
ARCHITECTURE.md. Unlike the retrofit CLAUDE.md (vibe-init), the greenfield
CLAUDE.md **has phase gates** — the build runs Phase 1 → gate → Phase 2 → …

The "Per-task sequence", "Investigation discipline", and "Session completion
checklist" blocks below are inserted **verbatim** — they are the contract every
other vibe-* skill relies on.

---

```markdown
# CLAUDE.md — [Project Name]
> [1-2 sentences: what this app is, who it's for.]
> Single source of truth for how this project is built. Read at every session start.

---

## Execution mode
VIBE_MODE=manual
<!-- manual: wait for "next" between tasks, wait for "review:" after phases.
     autonomous: run tasks automatically, subagents in parallel, auto-review.
     Change with `vibe-mode: autonomous` / `vibe-mode: manual`. -->

## Model guidance (per-task tiering)
> Default build model: [claude-sonnet-5]. See vibe-cost references/PRICING.md
> for the current lineup and the per-task-type model-selection table. Raise to
> claude-opus-5 for the hardest architecture/diagnosis work; drop to
> claude-haiku-4-5 for mechanical/high-volume tasks. Use adaptive thinking with
> `output_config.effort` (high/xhigh) on reasoning-heavy steps.

---

## Project overview
[2-3 sentences from SPEC.md: core value, primary users, v1 boundary.]

## Tech stack
[Copy the stack table from PLAN.md / ARCHITECTURE.md — do not invent.]

## Commands
```bash
# Development
[dev command]
# Build
[build command]
# Test
[test command]
# Lint
[lint command]
# Database migrations (if applicable)
[migration command]
```

## Session startup — read in this order
1. CLAUDE.md (this file)
2. vibe/TASKS.md — what to build next
3. vibe/ARCHITECTURE.md — how to build it
4. vibe/CODEBASE.md — what already exists
5. The active FEATURE_TASKS.md / BUG_TASKS.md (if any)

## Code style and conventions
[Naming, structure, and style rules from ARCHITECTURE.md or PLAN.md.]

## Architecture rules
[The Always / Ask First / Never boundaries from ARCHITECTURE.md.]

## Working rules (every task — forbid-style, checkable)
- **Surgical edits.** Change the minimum lines needed. Do not reformat, reorder, or rename anything you were not asked to change; match the file's existing style. Remove only the imports/vars YOUR change made unused — nothing else.
- **Do not rewrite tests to pass.** Never edit an existing test to make failing code pass. If a test is wrong, say so and stop; fix the code, not the assertion.
- **Do not guess unknown values.** If you need a fact you were not given (a name, id, path, env/config value), output `MISSING: <exactly what you need>` and stop. Never invent a plausible default and continue.
- **Ask before destructive actions.** Stop and ask before: dropping a table, force-push, rewriting git history, deleting a file you did not create, or running a migration against anything not local.
- **Do not add dependencies.** Use what is in the manifest. To add one: name it, name what it replaces, stop, and wait for approval.
- **Comments say why, not what.** Do not restate the code; explain intent only where it is non-obvious.
- **After any context compaction, re-read this file before the next edit.**

---

## Per-task sequence (runs on every "next")

1. Verify acceptance criteria in FEATURE_TASKS.md are all ticked
2. Run tests: `[test command]` — must pass before commit
3. Run lint: `[lint command] --silent` — must pass before commit
4. Commit code changes — stage the files THIS task touched, not `git add -A`
   (blanket-staging risks committing .env, build artifacts, or stray files):
   git add [the specific paths this task created/modified]
   git commit -m "feat([scope]): [TASK-ID] — [one line plain English description]"
   (Ensure .gitignore covers .env*, node_modules, build output before the first commit.)
5. Commit doc updates separately:
   git add vibe/TASKS.md vibe/DECISIONS.md vibe/CODEBASE.md
   git commit -m "docs(TASKS): mark [TASK-ID] done — [plain English]"
6. Update "What just happened" and "What's next" in vibe/TASKS.md
7. Re-read vibe/TASKS.md silently
8. State next task in plain English and confirm before starting

Rules:
- NEVER skip the commit step — uncommitted work is invisible to vibe-graph and vibe-review
- Code commit and doc commit are ALWAYS separate — never mix feat and docs in one commit
- If tests fail — fix before committing, do not commit broken code
- If lint fails — fix before committing, do not commit with lint errors

## Investigation discipline
For requests under 10 words: restate intent in one sentence before reading any files.
Data/state operations (reset, clear, seed, refresh) are not code bugs — do not investigate code.
Confirm the actual request before opening any file.

## Session completion checklist
- [ ] Acceptance criteria ticked
- [ ] Tests pass · Lint passes
- [ ] Code committed (feat) and docs committed (docs) — separately
- [ ] vibe/TASKS.md "What just happened" / "What's next" updated
- [ ] vibe/DECISIONS.md updated if anything drifted from the plan
- [ ] vibe/CODEBASE.md updated if files were added/removed

---

## Phase gates — ENFORCED, not advisory
> A phase cannot advance until `review:` passes with **0 open P0 AND 0 open P1**.
> P1s block the gate — never deferred past their phase; only P2/P3 carry to the final
> cleanup pass. Final phase also requires P2/P3 addressed or accepted. Holds in manual mode.

- Phase 1 → run `review: phase 1`
- Phase 2 → run `review: phase 2`
- Final → run `review: final`

**Advancement rule (check every time before starting a new phase):**
Before the FIRST task of Phase N+1, read `vibe/.gates.json`. If
`phases["N"].review` is not `"passed"`, **STOP** and say:
"Phase N's review gate is [status] — run `review: phase N` before Phase N+1."
Do not start the next phase until it passes. Same rule for the design gate
(no UI-feature build before `design` when no design system exists) and the
deploy gate (no `deploy:` until `final.review` is `passed`).

When the last task of a phase is done, run the phase review immediately
(autonomous) or announce and run it (manual) — don't drift into the next phase.
The hard lock is the git pre-push hook installed at setup (blocks a push while any
gate in `vibe/.gates.json` is open; override once with `git push --no-verify`, logged
in DECISIONS.md).

## Active feature
> Set when `feature:` runs. Cleared when the feature completes.
(none)

## Active bug
> Set when `bug:` runs. Cleared when the bug is fixed.
(none)
```
