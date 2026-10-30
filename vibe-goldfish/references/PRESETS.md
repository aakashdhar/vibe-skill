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
| `spec` | `spec` | `vibe/SPEC.md` · `vibe/ARCHITECTURE.md` · `vibe/PLAN.md` | rubric · comprehension · readiness | `SR/CHECKLISTS.md` §3, §4, §6 · `SR/SPEC_RUBRIC.md` | `BRIEF.md` · `AGENT_ARCH.md` |
| `init` | `spec` | `vibe/SPEC.md` · `vibe/ARCHITECTURE.md` · `vibe/CODEBASE.md` · `CLAUDE.md`² | rubric · comprehension · codebase | `SR/CHECKLISTS.md` §3, §4, §6 · `SR/SPEC_RUBRIC.md` | none (the codebase is the source) |
| `feature` | `feature-<folder>` | `FEATURE_SPEC.md` · `FEATURE_PLAN.md` (in the feature folder) | rubric · comprehension · zoom-out · design-critic · codebase¹ | `SR/CHECKLISTS.md` §5A, §5B, §6 · `SR/SPEC_RUBRIC.md` (FEATURE_SPEC_RUBRIC section) | `vibe/SPEC.md` · `vibe/ARCHITECTURE.md` · `vibe/CODEBASE.md` · `vibe/PLAN.md` |
| `feature-tasks` | `feature-<folder>-tasks` | `FEATURE_TASKS.md` (in the feature folder) | rubric · readiness · codebase¹ | `SR/CHECKLISTS.md` §5C · `SR/SPEC_RUBRIC.md` (FEATURE_SPEC_RUBRIC section: task quality) | the feature's `FEATURE_SPEC.md` · `FEATURE_PLAN.md` · `vibe/ARCHITECTURE.md` · `vibe/CODEBASE.md` |
| `all` | `all` | every planning document that exists | rubric · comprehension · zoom-out | every section of `SR/CHECKLISTS.md` + all three rubrics | none (everything is a document) |

¹ `codebase` runs only when the project already has source code (anything outside
`vibe/`, docs and config). On a greenfield project there is nothing to check against.
Leave it out rather than recording it as not run.

² `CLAUDE.md` is reviewed (not read as instructions) because vibe writes the project's
commands and boundaries there. Listing it as a document is the one case where a goldfish
opens it.

**Review before anything is derived.** Each preset covers the documents a person
decides on. The files generated from them (SPEC_INDEX.md, TASKS.md, CLAUDE.md, the TASKS
mirror of a feature, the PLAN.md feature-map line) are written only after the review
converges and the person approves, so a review fix never has to chase a copy.
- `spec`: SPEC, ARCHITECTURE (checked against §4 even when vibe-new-app generated it
  because `architect:` was skipped) and the PLAN.md feature map, which the readiness
  reviewer uses to judge whether a fresh agent could plan each feature from it.
- `feature` then `feature-tasks`: the design (what and how) is reviewed and approved
  before any task is written; the tasks are then reviewed on their own for the
  zero-decision rule. Two small targets converge faster than one big one.
- `init`: CODEBASE.md is reviewed too, because every later skill builds on it and the
  codebase reviewer can check it against the real code. CLAUDE.md is a reviewed document
  here, not a derived one: vibe-init writes it before the review, and regenerates only
  SPEC_INDEX.md, PLAN.md, TASKS.md and its DECISIONS entry afterwards.

## Altitude: the level each document is judged at

Every reviewer is told what kind of document it is reading and what that document is
for, so it judges it at the right level. A detail that the next document down decides
is not a gap here: at most a P2 note. Without this, fresh reviewers find a new edge case
in every round (what happens on an invalid flag value?) and a brief or a spec never
converges. Pass the line for the preset, word for word, in the dispatch template.

| Preset | Altitude line |
|---|---|
| `brief` | A product brief. Judge the problem, the users, the core value, v1 scope and non-goals, success criteria and constraints. Behaviour details (error handling, input validation, exact output formats, edge cases) are decided later in SPEC.md: their absence is at most P2. |
| `agent-arch` | An agent system design. Judge the agents' roles, tools, state ownership, human checkpoints, verifiers and implementation order. Code-level details are decided later: at most P2. |
| `architecture` | An architecture document. Judge structure, patterns, conventions, boundaries and fit with the stack. Feature behaviour belongs to SPEC.md: at most P2. |
| `spec` | A v1 product spec with its architecture and feature map. Judge behaviour and acceptance criteria for every v1 feature, consistency with the architecture, and whether the feature map's order and dependencies are complete. File-level task breakdown is decided per feature later (`feature:`): at most P2. |
| `init` | The same as `spec`, for documents derived from existing code: judge them against the code. |
| `feature` | One feature's spec and plan. Judge its behaviour, acceptance criteria, design and fit with the code. The task breakdown comes next in FEATURE_TASKS.md: at most P2. |
| `feature-tasks` | Build tasks. The zero-decision rule applies in full: every decision a builder would have to make is a finding. |
| `all` | Each document at the altitude of its own preset above. |

## Picking the target slug

The slug names the folder under `vibe/goldfish/`. A later review of the same document
reuses the slug, so settled findings stay settled. For a feature, use the feature
folder's name: `vibe/features/2026-10-30-csv-export/` → `feature-2026-10-30-csv-export`,
and `feature-2026-10-30-csv-export-tasks` for its tasks.

**A from-scratch rewrite starts a fresh review.** When a skill throws a document away and
writes it again (vibe-agent "redesign from scratch", vibe-architect "start fresh", vibe-init re-run over an existing
vibe/, vibe-new-app "start fresh"), run `goldfish.py archive <target>` first. Otherwise
findings settled on the old document would be linked to the new one and stay settled.

## Small work skips the goldfish

A calling skill may skip the review for work too small to repay it, and must say so in
one line: a trivial bug (vibe-fix-bug's trivial path), a one-task change, a typo-level
doc edit. Anything that creates a SPEC, a FEATURE_SPEC or an architecture is never small.
