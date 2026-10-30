# ARCHITECTURE_MD.md Template (minimal / auto-generated)

Used by vibe-new-app Step 5 **only when `architect:` was skipped** — it
generates a minimal `vibe/ARCHITECTURE.md` from PLAN.md so that `review:` has an
architecture to check against from Phase 1. When `architect:` was run, its own
richer template (`vibe-architect/references/ARCHITECTURE_MD.md`) is the source
of truth and this file is not used.

Fill every `[placeholder]` from PLAN.md decisions — never invent. Apply the
**O'Reilly principles** and **Never list** sections verbatim (they are what
`review:` enforces). Keep the **Boundaries** section too, labelled as framework
defaults: the spec review (Step 6) checks this file for Always / Ask First / Never tiers
and a "never commit secrets" rule, and CLAUDE.md copies its tiers.

---

```markdown
# ARCHITECTURE — [Project Name]
> ⚠️ Auto-generated from PLAN.md — architect: was not run.
> Consider running architect: to make these decisions explicit and add missing sections.
> Every agent session reads this file before writing code.

## Project type
[Web app / Mobile app / API service / CLI tool / Full-stack]
[Framework + version, from PLAN.md]

## Folder structure
```
[project-root]/
├── [folder]/     ← [purpose — from PLAN.md]
└── [folder]/     ← [purpose — from PLAN.md]
```

## Naming conventions
[Extract from PLAN.md; if unspecified, state the framework default and mark it TODO.]

## State management
[From PLAN.md, or "not yet decided — run architect:".]

## Backend patterns (if applicable)
- API style: [REST / tRPC / GraphQL]
- Business logic: [route handlers / service layer]
- Input validation: [Zod / Pydantic / …]

## Error handling
[Pattern from PLAN.md (e.g. typed errors from services, one error boundary per page); if
unspecified, state the framework default and mark it TODO.]

## Testing philosophy
- Runner: [from PLAN.md]
- What must have tests before a phase gate: [critical paths, per PLAN.md]

## Code quality
- Linter / formatter: [from PLAN.md]
- TypeScript strictness: [strict / lenient]

## Boundaries
> Framework defaults, not decisions made in architect:. Adjust them in `architect:`.

**Always:** run tests and lint before every commit · validate input on every user-facing
route · follow the folder structure above.
**Ask First:** adding a dependency · changing the data model or a public API shape ·
dropping a table or running a migration against anything not local · deleting a file you
did not create.
**Never:** commit secrets or `.env` files · hardcode credentials or API keys · force-push
or rewrite git history.

## The O'Reilly principles (enforced by review:)

**Spec before code** — no task starts without acceptance criteria in FEATURE_TASKS.md.
**Context preservation** — CLAUDE.md, CODEBASE.md, ARCHITECTURE.md, TASKS.md read every session.
**Incremental progress** — one task at a time. Confirm → build → verify → commit.
**Drift prevention** — every deviation from this document logged in DECISIONS.md.

## Never list

The following are P0 review findings — they block phase gates:

- [ ] Using `any` type in TypeScript
- [ ] Business logic in route handlers (belongs in services)
- [ ] Direct database queries outside repositories
- [ ] Hardcoded credentials or API keys in code
- [ ] Frontend component importing directly from backend module
- [ ] Agent calling another agent directly (bypassing orchestrator)
- [ ] Skipping input validation on any user-facing route
- [ ] Inline styles overriding design tokens
- [ ] [Project-specific never — add during architect:]

## Architecture decisions log
> Full history in DECISIONS.md.

| Decision | Choice | Reason | Date |
|----------|--------|--------|------|
| [Decision] | [choice] | [reason] | [date] |
```
