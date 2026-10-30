# PRESETS.md

Which goldfish review which document, with which standards, and which other files they
may read. A calling skill names a preset; vibe-goldfish takes everything else from here.

`SR` below is `$HOME/.claude/skills/vibe-spec-review/references`. Expand it to an absolute
path before putting it in a reviewer's task: subagents need absolute paths.

**Related files** are upstream documents a reviewer may read to check consistency. They
are never the author's reasoning: DECISIONS.md, IMPLEMENTATION_LOG.md, review reports and
earlier goldfish rounds are never related files.

| Preset | Target slug | Documents reviewed | Reviewers | Rubric standards | Related files (when they exist) |
|---|---|---|---|---|---|
| `brief` | `brief` | `BRIEF.md` | rubric · comprehension · zoom-out | `SR/CHECKLISTS.md` §1, §6 · `SR/BRIEF_RUBRIC.md` | none |
| `agent-arch` | `agent-arch` | `AGENT_ARCH.md` | rubric · comprehension · design-critic · zoom-out | `SR/CHECKLISTS.md` §2, §6 · `SR/AGENT_ARCH_RUBRIC.md` | `BRIEF.md` |
| `architecture` | `architecture` | `ARCHITECTURE.md` (root or `vibe/`) | rubric · design-critic · zoom-out · codebase¹ | `SR/CHECKLISTS.md` §4, §6 · `SR/SPEC_RUBRIC.md` (ARCHITECTURE_RUBRIC section) | `BRIEF.md` · `AGENT_ARCH.md` |
| `spec` | `spec` | `vibe/SPEC.md` · `vibe/ARCHITECTURE.md` · `vibe/PLAN.md` · `vibe/TASKS.md` · `CLAUDE.md`² | rubric · comprehension · readiness | `SR/CHECKLISTS.md` §3, §4, §6 · `SR/SPEC_RUBRIC.md` | `BRIEF.md` · `AGENT_ARCH.md` |
| `init` | `spec` | `vibe/SPEC.md` · `vibe/ARCHITECTURE.md` · `CLAUDE.md`² | rubric · comprehension · codebase | `SR/CHECKLISTS.md` §3, §4, §6 · `SR/SPEC_RUBRIC.md` | none (the codebase is the source) |
| `feature` | `feature-<folder>` | `FEATURE_SPEC.md` · `FEATURE_PLAN.md` · `FEATURE_TASKS.md` (whichever exist in the feature folder) | rubric · comprehension · zoom-out · design-critic · readiness · codebase¹ | `SR/CHECKLISTS.md` §5, §6 · `SR/SPEC_RUBRIC.md` (FEATURE_SPEC_RUBRIC section) | `vibe/SPEC.md` · `vibe/ARCHITECTURE.md` · `vibe/CODEBASE.md` |
| `all` | `all` | every planning document that exists | rubric · comprehension · zoom-out | every section of `SR/CHECKLISTS.md` + all three rubrics | none (everything is a document) |

¹ `codebase` runs only when the project already has source code (anything outside
`vibe/`, docs and config). On a greenfield project there is nothing to check against.
Leave it out rather than recording it as not run.

² `CLAUDE.md` is reviewed (not read as instructions) because vibe writes the project's
commands and boundaries there. Listing it as a document is the one case where a goldfish
opens it.

For `spec`, vibe-new-app has already written PLAN.md and TASKS.md when spec-review runs,
so they are reviewed together with the SPEC: the readiness reviewer needs the tasks to
judge whether a fresh agent could build it, and ARCHITECTURE.md is checked against §4
even when vibe-new-app generated it because `architect:` was skipped.

## Picking the target slug

The slug names the folder under `vibe/goldfish/`. A later review of the same document
reuses the slug, so settled findings stay settled. For a feature, use the feature
folder's name: `vibe/features/2026-10-30-csv-export/` → `feature-2026-10-30-csv-export`.

## Small work skips the goldfish

A calling skill may skip the review for work too small to repay it, and must say so in
one line: a trivial bug (vibe-fix-bug's trivial path), a one-task change, a typo-level
doc edit. Anything that creates a SPEC, a FEATURE_SPEC or an architecture is never small.
