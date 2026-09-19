# CLAUDE_RETROFIT.md Template

Used by vibe-init Stage 5H to generate CLAUDE.md at the project root.
This is the agent's constitution — read at every session startup.
Differences from greenfield: no phase gates, session startup reads existing code.

---

```markdown
# CLAUDE.md — [Project Name]
> 📥 Onboarded via vibe-init on [date].
> This project pre-dates the vibe-* framework. All prior decisions are untracked.
> From this point forward, all decisions are logged in vibe/DECISIONS.md.

---

## Project overview

**What it is:** [2 sentences — inferred from codebase]
**Stack:** [runtime] + [framework] + [database] + [key libraries]
**Codebase scale:** [~N files, N routes, N models — from init report]

---

## Commands

```bash
# Development
[actual dev command]

# Build
[actual build command]

# Test
[actual test command — or: "not observed during init — confirm with team"]

# Lint
[actual lint command — or: "not observed during init — confirm with team"]

# Database migrations
[actual migration command — or: "not observed during init — confirm with team"]
```

---

## Session startup — read in this order

Every agent session must read these files before writing any code:

1. `CLAUDE.md` (this file) — project context and rules
2. `vibe/CODEBASE.md` — what exists, where things live
3. `vibe/ARCHITECTURE.md` — patterns to follow, conventions to maintain
4. `vibe/SPEC_INDEX.md` — compressed feature map
5. `vibe/TASKS.md` — current work in progress

**If working on a feature:** also read `vibe/features/[date-slug]/FEATURE_TASKS.md`
**If fixing a bug:** also read `vibe/bugs/[date-slug]/BUG_TASKS.md`

Do not write code before completing this read sequence.
Confirm the task before starting.

---

## Code style and conventions

[Filled from ARCHITECTURE.md observations — copy the key rules here for quick access]

**Files:** [naming convention + example]
**Functions:** [naming convention + example]
**Components:** [naming convention + example]
**Imports:** [absolute / relative / barrel — example]
**Error handling:** [observed pattern — one sentence]
**TypeScript:** [strict / lenient — any usage observed / not used]

---

## Architecture rules

[The 3-5 most important structural rules from ARCHITECTURE.md]

- [Rule 1 — e.g. "Business logic lives in services/, not in route handlers"]
- [Rule 2 — e.g. "Components are pure — no direct API calls inside components"]
- [Rule 3 — e.g. "All database access goes through Prisma — no raw SQL"]
- [Rule N]

Full detail in `vibe/ARCHITECTURE.md`.

## Working rules (every task — forbid-style, checkable)
- **Surgical edits.** Change the minimum lines needed. Do not reformat, reorder, or rename anything you were not asked to change; match the file's existing style. Remove only the imports/vars YOUR change made unused — nothing else.
- **Do not rewrite tests to pass.** Never edit an existing test to make failing code pass. If a test is wrong, say so and stop; fix the code, not the assertion.
- **Do not guess unknown values.** If you need a fact you were not given (a name, id, path, env/config value), output `MISSING: <exactly what you need>` and stop. Never invent a plausible default and continue.
- **Ask before destructive actions.** Stop and ask before: dropping a table, force-push, rewriting git history, deleting a file you did not create, or running a migration against anything not local.
- **Do not add dependencies.** Use what is in the manifest. To add one: name it, name what it replaces, stop, and wait for approval.
- **Comments say why, not what.** Do not restate the code; explain intent only where it is non-obvious.
- **After any context compaction, re-read this file before the next edit.**

---

## Session completion checklist

After every task — no exceptions:

- [ ] Code works and doesn't break existing functionality
- [ ] Follows naming conventions from ARCHITECTURE.md
- [ ] Error handling consistent with observed pattern
- [ ] `vibe/CODEBASE.md` updated if new file, route, schema, or pattern added
- [ ] `vibe/DECISIONS.md` updated if a decision was made (drift, tech choice, blocker)
- [ ] `vibe/TASKS.md` updated — "What just happened" and "What's next"
- [ ] If working a feature: `vibe/features/[slug]/FEATURE_TASKS.md` task marked done
- [ ] If fixing a bug: `vibe/bugs/[slug]/BUG_TASKS.md` task marked done

**The rule:** if something changed in the codebase, something changed in the docs.
If the docs aren't updated, the task isn't done.

---

## Active feature

[Managed by vibe-add-feature — do not edit manually]
<!-- ACTIVE FEATURE: none -->

---

## Active bug

[Managed by vibe-fix-bug — do not edit manually]
<!-- ACTIVE BUG: none -->

---

## No phase gates

This project was not built with the vibe-* framework.
There are no Phase 1 / Phase 2 / Phase 3 gates.

Use `review:` on demand — after completing a significant feature or before a release.
Use `feature:` and `bug:` to track all future work through normal vibe-* workflow.

---

## What's untracked

All work done before [date] is untracked.
`vibe/SPEC.md` is PROVISIONAL — verify before using `review:` as a correctness reference.
`vibe/DECISIONS.md` starts from today — prior decisions are unknown.

When you encounter something in the code that doesn't match ARCHITECTURE.md patterns,
log it as a `discovery` type entry in DECISIONS.md rather than treating it as drift.
It may be intentional — you don't have the history to know.
```
