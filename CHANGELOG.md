# Changelog

All notable changes to the **vibe-\*** skill framework are documented here.

The format follows [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).
The current version is tracked in [`VERSION`](VERSION); each release is cut as an
annotated git tag (`vX.Y.Z`), which GitHub surfaces as a Release. See
[`VERSIONING.md`](VERSIONING.md) for the release process.

## [2.8.0] — 2026-10-30

Theme: **review before approval, approval before anything is derived.** v2.7.0 made
every planning review independent, but most planning skills still asked a person to
approve a draft before that review ran, and generated files from documents that hadn't
been reviewed yet, so a review fix could not reach them. Every planning skill now
follows one rule: write → independent goldfish review → fixes, and only then approval
and derived files, both from the reviewed text. (vibe-new-app and vibe-add-feature ask
for approval first and then derive; vibe-init and vibe-agent derive SPEC_INDEX/PLAN/TASKS
and the diagrams just before approval, so the person sees them.)

**Upgrading.** Reviews from v2.7.0 stay valid: rounds recorded before this release are
compared with the old hash. A v2.7.0 `spec` review covered TASKS.md and CLAUDE.md, which
the `spec` preset no longer reviews, so the first `spec-review:` after upgrading starts a
fresh review cycle for it. PLAN.md feature entries gain a `**Status:**` line;
`feature:` adds it to older entries when it starts them.

### Changed
- **vibe-new-app is reordered.** It drafts SPEC.md (with its UI Specification), the PLAN.md
  feature map and vibe/ARCHITECTURE.md, then runs the spec review (Step 6), then the spec
  gate on the reviewed plan (Step 10S), and only then writes SPEC_INDEX.md, CLAUDE.md,
  TASKS.md, CODEBASE.md and its DECISIONS entries (Step 10F), then the graph (10G), the
  design gate (10C) and the pre-push hook (10D). CLAUDE.md now reads an ARCHITECTURE.md that
  exists. The labels 10S, 10C and 10D are kept because other skills cite them.
- **vibe-add-feature reviews in two stages.** FEATURE_SPEC + FEATURE_PLAN are reviewed
  (Trigger 4, preset `feature`) and approved before any task is written; FEATURE_TASKS is
  then reviewed on its own for the zero-decision rule (Trigger 4T, preset `feature-tasks`).
  The CLAUDE.md scope lines, the TASKS.md mirror, the DECISIONS task range and the PLAN.md
  feature-map line are written only after both. A feature whose review stops writes
  nothing derived. Graph update and vibe-test run before the phase gate, and a passed
  phase gate is reopened as well as the final one.
- **vibe-brainstorm** writes the brief, has it reviewed, then asks for approval of the
  reviewed brief. Its pre-write check is now gap questions, not a self-graded verdict.
  Gaps the person accepted with "let's build" are recorded as theirs, and the review's
  findings on them are answered with that acceptance. Agentic detection and sizing re-run
  when review fixes change the scope.
- **vibe-agent** approves AGENT_ARCH.md after its review, generates the diagrams from the
  reviewed document, and hands off to `architect:` instead of straight to code.
- **vibe-architect** reads AGENT_ARCH.md, approves after its review, and no longer appends
  its decisions to the already-reviewed BRIEF.md. Its template has Always / Ask First /
  Never tiers and a literal "Never commit secrets" rule.
- **vibe-init** reviews ARCHITECTURE, CODEBASE, SPEC and CLAUDE.md, with the person's
  verification of the code-derived SPEC inside the review loop, then generates
  SPEC_INDEX.md, a PLAN.md feature map of the existing features (new PLAN_RETROFIT.md),
  TASKS.md with its spec gate, and the onboarding entry. Boundary tiers come only from
  evidence in the code; an empty tier says so instead of inventing rules.
- **vibe-change-spec** re-runs the review on every reviewed document it changes (Trigger 6),
  updates documents upstream first, keeps the PLAN.md feature map and in-progress feature
  documents in step, sets an approved spec gate back to pending, and can resume an
  unfinished change (`change: resume D-[ID]`).
- **vibe-design** stops at its Step 3.5 checkpoint at a design gate in manual mode too: the
  critique and fix loop run before anyone approves, and production UI is built afterwards.
- **Upstream checks.** architect, agent and new-app check that the brief, agent
  architecture and architecture they build on have a converged review (`goldfish.py
  status`), and offer to run it when they don't.
- **No more "always Plan Mode" in skills that write files.** Each now lists exactly the
  files it writes (brainstorm, agent, architect, new-app, init, add-feature, change-spec,
  fix-bug, doctor).
- **vibe-goldfish presets.** `spec` reviews SPEC, ARCHITECTURE and the PLAN.md feature map
  (TASKS.md and CLAUDE.md are now derived after the review); `init` adds CODEBASE.md;
  `feature` is split into `feature` and `feature-tasks`.
- HEADLESS.md §5 resumes setups that stopped before TASKS.md exists (new-app, init), an
  unfinished scope change, and setup steps that never ran (graph, pre-push hook).

### Added
- `goldfish.py resolve ... --as duplicate --of PRIMARY`: when several reviewers raise the
  same problem, it is answered once (the proof run had 12 escalations for 6 decisions).
- **Faster reviews.** The reviewer agents run on Sonnet (`model: sonnet`) instead of the
  session's model: they only read and report, so each round is quicker. On a small
  project (BRIEF.md sized S), one clean round with no P0/P1 converges instead of two;
  `goldfish.py init --thorough` keeps two rounds.
- `goldfish.py archive <target>`: a from-scratch rewrite starts a fresh review instead of
  inheriting settled findings.
- `vibe_state.py gate set spec --by human` records `reviewed: false` (with a note) when
  the goldfish review isn't converged on the current text.

### Fixed
- **Recording a sign-off made the review look stale.** `gate set` rewrites the TASKS.md
  gate line and vibe-mode rewrites CLAUDE.md, both hashed by the review. The hash now
  ignores that bookkeeping, and the feature-map status flips, the CLAUDE.md Active
  Feature section and CODEBASE.md "Verified during" lines (feature names still count).
- The vibe-new-app per-task sequence and TASKS template now match their references
  (including `## Spec gate`); the minimal ARCHITECTURE.md it generates has boundary tiers.
- vibe-change-spec's backlog jump pointed at the wrong step and skipped DECISIONS.md.
- vibe-brainstorm's step counts and agentic flag wording agree with what downstream reads.
- vibe-init no longer claims PLAN.md is unnecessary; vibe-add-feature handles a project
  without one instead of calling every feature unplanned.
- goldfish self-test grows to 21 scenarios (small-project convergence, duplicates and their loopholes, per-file
  bookkeeping with the real PLAN/CLAUDE formats, v2.7.0 ledgers, archive, the
  `reviewed: false` sign-off).
- **Proof-run findings.** A headless `new:` on a small brief skipped vibe-new-app and built
  the code directly; the skill's description now says it runs however small the project
  is. With the skill invoked, the order held (brief reviewed first, SPEC/PLAN/ARCHITECTURE
  drafted, no derived file before the review), but the brief review ran 12 rounds:
  reviewers judged a brief at spec level, and the agent raised its own round cap. Every
  preset now passes an **altitude** line (what the document is for; a detail the next
  document decides is at most P2), raising the round cap needs `--human`, and RESOLVE.md
  says when a P2 fix is worth the round it costs.
- Review findings fixed before release: hashing is per file and versioned; duplicate
  chains and churn hidden in a duplicate are refused, and a re-raise carrying a
  comprehension duplicate is never settled by an old contest; `new:` "start fresh" resets
  the spec gate; vibe-init projects are always reviewed with the `init` preset and a new
  feature in their PLAN.md is not "unplanned"; FEATURE_TASKS reviews aren't re-run once a
  build has started; resume paths for an unfinished vibe-init re-run and for manual
  scope changes.

## [2.7.0] — 2026-10-30

Theme: **the author never grades its own work.** Until now every review in vibe ran in
the conversation that wrote the thing being reviewed: spec-review audited specs in the
author's own context and, in autonomous mode, fixed and re-passed its own findings. This
release adds an independent review layer on the elephant-goldfish model, and fixes the
pipeline defects that a verified audit found in how runs are counted, gated and resumed.

### Added
- **vibe-goldfish** (new skill, the 27th). The agent that wrote a document (the
  elephant) never reviews it. Fresh read-only subagents that never saw the conversation
  or CLAUDE.md (the goldfish) read it cold, each with one job: rubric, comprehension,
  zoom-out, design critic, implementation readiness, codebase fit. The elephant answers
  every finding as fix, contest (with evidence the reviewer could read), escalate (a
  person decides) or decline (P2 only). The review ends after two clean rounds in a row,
  is capped at 5 rounds, and stops for a person on churn or an escalation.
  - A review runs again when the reviewed documents change: the two clean rounds must
    be on the same text, so a converged review of an older version no longer counts.
  - In autonomous mode an escalated P0 or P1 stops the run, unless the agent writes the
    missing fact into the document (the next round then checks it). Only a P2
    escalation may be accepted as a risk by the agent.
  - `scripts/goldfish.py` keeps the ledger and enforces the rules: stable finding IDs,
    a reviewer that didn't run is never "no findings", settled findings stay settled, a
    fixed one that comes back reopens, comprehension findings can't be contested,
    severities can't be changed.
  - Six reviewer agents (`agents/vibe-gf-*.md`): tools `Read, Grep, Glob` only,
    `omitClaudeMd: true`. A live probe confirmed they see neither the project CLAUDE.md
    nor the parent conversation.
  - `scripts/isolation_check.py` checks that (static, and `--live` through the CLI).
  - `scripts/test_goldfish.py` is a self-test of the review rules and the goldfish gate
    checks in vibe_state.py (10 scenarios, stdlib only).
  - Presets per document type (`references/PRESETS.md`), the dispatch rules
    (`references/DISPATCH.md`: reviewers get file paths, never explanations) and the
    answer rules (`references/RESOLVE.md`).
- **`vibe-mode: resume`**: a person's answer to a stop. It resets the saved budgets, then
  runs. Drivers keep using `run`, which never resets them.
- **vibe_state.py**: `mode --run`, `attempt`, `cycle`, `counters`, `gate reopen`, and
  checks inside `gate set` (below).
- **lint.py** checks: no `grep VIBE_MODE CLAUDE.md`, goldfish reviewers stay read-only
  with CLAUDE.md hidden, every preset reviewer has an agent file, and a warning for skill
  descriptions over 1024 characters.

### Changed
- **vibe-spec-review runs through vibe-goldfish.** It no longer audits documents in the
  author's context or re-passes its own fixes. Its checklists moved to
  `references/CHECKLISTS.md` (unchanged except a note that check 3A also counts
  commands written to CLAUDE.md), which the rubric reviewer applies. Trigger 4 now reviews
  FEATURE_SPEC, FEATURE_PLAN and FEATURE_TASKS together. The report in
  `vibe/spec-reviews/` is a one-page summary that links to the full goldfish record.
- **An agent can't sign off the spec or the design on its own judgment.** `gate set spec
  --by agent-autonomous` needs `--report vibe/goldfish/spec` pointing at a converged
  review (`--backfill` for projects that predate the gate). `gate set design --status
  approved` refuses while the critique has MUST-FIX > 0. Approving with items open needs
  `--by human --accept-open "why"`, which the skills reserve for a person (the helper
  can't verify who runs it).
- **Every spec-review caller stops when the review needs a person.** vibe-new-app,
  vibe-init, vibe-add-feature, vibe-architect, vibe-agent and vibe-brainstorm check
  `run-state show` right after spec-review returns and end the session on `needs_human`
  instead of carrying on. In manual mode a 🔴 SPEC NOT READY verdict goes back through
  spec-review's own rounds; findings are never fixed outside vibe-goldfish.
- **Deploy: an open P1 always stops.** The "Deploy anyway?" override is gone, and a P1
  tagged "won't fix (accepted risk)" no longer clears the gate (P2/P3 still can be
  accepted). Deploy Step 0.5 runs `perf:` Entry C when `vibe/perf/baseline.json` exists or
  you ask for it (otherwise it says perf was not run), and stops while the latest result
  has `findings.p0 > 0`.
- **vibe-perf** writes open P0s (not only P1/P2) to `backlog.md` and every result to
  `vibe/perf/baseline.json`. It no longer claims deploy triggers it automatically.
- **A passed review gate is reopened when source changes after it.** `gate reopen` sets
  the gate back to `open`, so `review:` must run again before the next phase or deploy.
  vibe-perf (after its fixes) and vibe-fix-bug (after the fix task) reopen the final gate
  if it passed, else the current phase. vibe-deploy reopens the final gate when Step 2
  patches source files. vibe-add-feature reopens it when a feature is built after the
  final review passed.
- **vibe-add-feature runs the full design gate** for new UI work: `design: critique`, up
  to 2 `design: fix must` passes while MUST-FIX > 0, then `gate set design` per
  APPROVALS, or a `needs_human` stop (`design_must_fix`). When a design system already
  exists (here and in vibe-new-app) and the gate was never recorded, the critique still
  runs before approval.
- **HEADLESS.md §2.2** no longer tells the agent to accept its own drafts. Documents that
  spec-review covers are accepted when their goldfish review converges. The rest
  (wireframe, PLAN.md feature map, BUG_SPEC/PLAN, design contract) are not yet covered,
  and the DECISIONS entry says so.
- `sync-install.sh` also installs the reviewer agents into `~/.claude/agents`, and the
  README install uses it (the old `mv` one-liner failed when run a second time).
- vibe-mode's description is under 1024 characters.

### Fixed
- **`vibe-mode: run` didn't force autonomous mode.** The execution block re-read the mode
  and stopped on `manual`. It now reads `mode --run`.
- **Retry and fix-cycle budgets lived only in the conversation**, so every new session
  started with a fresh budget. They are saved in `vibe/.run_state.json` (2 dispatches per
  task, 2 fix cycles per gate). The "use judgment, maybe one more try" softness is gone.
- **PARTIAL tasks stalled builds.** `[~]` is now retried once like a failure, then `[!]`
  and a stop. It never unlocks dependents, and a unit with `[~]`/`[!]` left is never
  reported complete. On resume, `[~]`/`[!]` count as unfinished.
- **The autonomous design gate approved after one fix pass** without checking MUST-FIX.
  It now runs up to 2 passes, and stops for a person if items are still open.
- HEADLESS.md tells drivers to stop on `needs_human` instead of relaunching.
- **Task IDs collided when vibe-parallel pooled several files.** Feature tasks are now
  `<PREFIX>-NNN`, with a short prefix unique in the project (e.g. `CSVX-001`), and bug
  tasks `BUG-<short-slug>-N` on both the trivial and significant paths. waves.py takes
  `"done": [...]` (completed task IDs a pooled task may depend on) and exits with an error
  on duplicate task IDs or on a dep that is neither in the pool nor in `done`.
- **RFX fix-task IDs restarted at RFX-001 for every gate**, so a later gate's fix task
  inherited an earlier one's saved retry budget. They are now numbered project-wide from
  the highest RFX id in TASKS.md and never reused.
- **A bug's regression test is meant to fail.** The BUG test task declares
  `- **Expect:** red: <test>`, and the subagent report lists that test under
  `tests.expected_failing`. The task can be `[x]` with only those tests failing; a task
  without `Expect: red` can never use that list.
- **DECISIONS.md was rewritten from the template** when it already existed. It is
  append-only now (vibe-new-app, vibe-init, vibe-spec-review, HEADLESS.md): existing
  entries are kept and `D-NNN` numbering continues from the highest ID.
- **vibe-init overwrote an existing vibe/ folder.** It now regenerates files one by one,
  deletes nothing in `vibe/`, and appends its onboarding entry to DECISIONS.md.
- **Skills read the mode by grepping CLAUDE.md**, which ignored `VIBE_*` env overrides and
  broke on the inline comment vibe-mode writes. vibe-fix-bug, vibe-add-feature,
  vibe-review, vibe-new-app and vibe-parallel now read it with `vibe_state.py mode`
  (`mode --run` when entered from `vibe-mode: run`).

## [2.6.0] — 2026-09-23

From the second headless proof run (a three-phase build driven by Reeve): Phase 2 was
planned as four features, three of them marked `Parallel with` each other, yet they were
built strictly one after another and vibe-parallel never ran.

### Added
- **Independent features build together.** The autonomous phase loop now works through
  a phase's feature lines in batches: every unfinished feature whose `Needs:` are met.
  A batch of 2+ is planned first (`feature: [name] plan-only`), then all of its tasks
  run through vibe-parallel as one pool. The phase gate still runs once, after the
  last feature.
- **vibe-parallel Entry point E**: several `FEATURE_TASKS.md` files as one task pool.
  The usual write-write and read-write passes keep features that share a file (e.g.
  `app.js`) in separate waves.
- **vibe-add-feature `plan-only`**: stop after the spec review, build nothing, skip the
  phase-gate step (the caller runs it).

## [2.5.2] — 2026-09-23

Findings from the first end-to-end headless run (Reeve driving `vibe-mode: run` from a
brief to a complete two-phase build with no human input). The run succeeded; these are
the places it took a shortcut the contract doesn't allow.

### Fixed
- **vibe-review fixed a P1 inside the review** and recorded the gate as passed. Review
  now states explicitly that it never fixes what it finds, however small: every P0/P1
  becomes an RFX task and the gate is recorded `open`, so the fix goes through the fix
  loop and a fresh review.
- **Independent tasks were built inline instead of through vibe-parallel.** The
  autonomous block now says to *always* use vibe-parallel for 2+ independent tasks —
  it's what checks conflicts and writes `vibe/parallel/wave-N-status.md`, which
  anyone watching the build (e.g. Reeve's panel) reads.
- **TASKS.md "What's next" went stale** mid-build. The autonomous block now rewrites
  "What just happened" / "What's next" after every wave and before every stop.

## [2.5.1] — 2026-09-23

### Fixed
- **The autonomous design gate built the UI before anyone approved it.** At the design
  gate (vibe-new-app Step 10C in autonomous mode, and `vibe-mode: run`), `design:` ran its
  full pass — production pages and components — and only then asked for sign-off. It now
  stops at vibe-design's own Step 3.5 checkpoint (contract, tokens, click-through preview);
  the production UI is built afterwards by the build's UI tasks from the approved
  contract. Manual mode is unchanged (you approve at 3.5 in chat, then it continues).

## [2.5.0] — 2026-09-23

Theme: **vibe can run with no one watching.** Autonomous mode used to cover only the
inside of one phase: every planning step still waited for a person, a failing review
waited for "resume" in chat, every phase ended with a stop, and nothing on disk said
why a session stopped. This release adds an opt-in headless contract so a driver (Reeve,
CI, a `claude -p` session) can run the same skills end to end. **Manual use is
unchanged** — every new behaviour is off by default.

### Added
- **`vibe-mode/references/HEADLESS.md`** — the contract: three settings, how every
  "wait" behaves in autonomous mode, the two human sign-offs, run state, and resume.
- **`vibe-mode/scripts/vibe_state.py`** — one deterministic helper for all of it:
  `mode` (resolve settings), `run-state set|show`, `gate set|check|show spec|design`.
  No skill hand-writes this JSON.
- **Two new settings** alongside `VIBE_MODE` in CLAUDE.md: `APPROVALS=human|auto` (who
  signs off the spec and design) and `PHASES=stop|continue` (carry on after a passed
  gate). Env vars `VIBE_MODE` / `VIBE_APPROVALS` / `VIBE_PHASES` override the file, so a
  driver can set them before CLAUDE.md exists.
- **`vibe/.run_state.json`** — written at every stop (`running`, `phase_done`,
  `needs_human`, `failed`, `complete`) with the reason and next action.
- **`vibe-mode: run`** — resume a build from the files alone: no plan → `new:`, spec
  gate, design gate, current phase, final gate. The single entry point for a driver.
- **Spec and design sign-offs are machine-readable**: `spec` / `design` entries in
  `vibe/.gates.json`, mirrored on new `## Spec gate` / existing `## Design gate` lines in
  TASKS.md. vibe-new-app records both (new Step 10S for the spec).
- **`design: critique` and `design: fix [must|must+consider|all]`** in vibe-design —
  writes `vibe/design/critique.md` (MUST-FIX / CONSIDER / NIT), then applies notes and
  regenerates the preview.
- **Task metadata in TASKS.md**: Phase 1 and Phase 3 tasks carry
  `size · deps · touches`, so vibe-parallel builds real waves; Phase 3 items are now
  executable `P3-NNN` tasks.
- **waves.py `unknown-writes`**: a task whose files are unknown (`"writes": null`) runs
  alone instead of being assumed conflict-free.

### Changed
- **Autonomous planning never waits.** brainstorm, agent, architect, new-app,
  spec-review, design, design-md, add-feature, fix-bug, change-spec, init and test follow
  HEADLESS.md §2 in autonomous mode: take the recommended option, accept their own draft
  after a self-check, log every choice to DECISIONS.md, and stop only when a person is
  genuinely required.
- **vibe-new-app writes the resolved settings** into CLAUDE.md instead of hardcoding
  `VIBE_MODE=manual`, and in autonomous mode never skips the design gate
  (`design:` → critique → one `fix must` pass → sign-off).
- **A failing phase gate is cleared, not parked.** The autonomous block runs the review's
  RFX tasks and re-reviews, up to 2 cycles, before stopping for a person. vibe-review
  returns FAIL to the block instead of waiting in chat.
- **spec-review in autonomous mode** fixes its own P0/P1 findings and re-reviews (up to 2
  rounds); open P0s stop the build.
- **Phase continuation** (`PHASES=continue`): after a passed gate the block moves to the
  next phase, running `feature:` for each planned feature in build order, then the final
  gate.
- vibe-review no longer offers to edit `.claude/settings.json` in autonomous mode.
- README vibe-mode docs updated (and a stale `mode: supervised` command removed).

### Compatibility
- Defaults (`manual` / `human` / `stop`) keep every skill's interactive behaviour.
- Projects scaffolded before 2.5.0 have no `spec` / `design` sign-off; `vibe-mode: run`
  backfills them when the build is already past that point (HEADLESS.md §5), so
  in-flight builds don't stall.
- The helper script is unit-tested; the headless behaviour of the skills themselves is
  prompt-level and should be verified with a real end-to-end run.

## [2.4.1] — 2026-09-23

Theme: **The rules agree with each other.** An audit of the framework as an orchestrator
would drive it found several places where one file said one thing and another did the
opposite. This release makes them consistent. No new behaviour.

### Fixed
- **One gate bar everywhere: 0 P0 AND 0 P1.** The written rule (v2.3.0) said P1 blocks a
  phase gate, but the `.gates.json` writer marked a phase `passed` whenever P0 was 0, and
  vibe-mode said P1s were "logged, build continues". The writer, `REVIEW_RESULT` signal,
  `AUTONOMOUS_EXECUTION_BLOCK`, vibe-mode, `GATES.md`, `PLAN_MD.md` and the review report
  template now all use the same bar, at every phase and at the final gate.
- **One gate-line format in TASKS.md.** vibe-review used to append a separate
  `## Phase gates` section that new-app never writes (and vibe-progress only read that
  one). Review now edits the `## Phase N gate` line in place (`✅ passed` / `🔴 blocked`)
  with RFX tasks beneath it; vibe-progress reads those lines and prefers `.gates.json`.
- **The pre-push hook could never fire.** It grepped `backlog.md` for open P0s, but P0s go
  to RFX tasks, never to the backlog. It now reads `vibe/.gates.json` and blocks while any
  gate is `open`.
- **vibe-graph god nodes.** `graph.py godnodes` wrote `degree`, but vibe-parallel and
  vibe-review read `connections` / `risk` / `srp_flag`. It now writes all of them. Rationale
  entries are read from `type` (what the build spec writes), with `kind` as a fallback.
- **vibe-graph update saw nothing after a commit.** It diffed `HEAD`, which is empty once
  tasks are committed. It now diffs from the `last_commit` recorded in `.graph-meta.json`,
  plus uncommitted changes.
- **waves.py could put a task in the same wave as a task that depends on it** when a
  conflict deferral pushed it forward. A dependency re-layering pass now runs after every
  deferral, until stable.
- **Subagent report state rules disagreed.** `_finalize` and `determine_state` gave
  different answers for failing tests with unmet criteria, and a `PARTIAL` report could be
  marked complete. Both now follow one rule: failing tests → `[!]`, DONE + all met → `[x]`,
  anything else → `[~]`.
- **Doc contradictions:** spec-review said "never modifies files" while always writing its
  report; review said "always Plan Mode" while writing its artifacts; add-feature claimed
  vibe-init creates `.gates.json`; the vibe-init CLAUDE.md had no `## Execution mode`
  section, so `vibe-mode` had nothing to switch.

### Added
- **waves.py size-aware fast lanes** (WAVE_BUILDER.md Pass 4, previously documented but not
  implemented). A task that doesn't depend on or conflict with a wave's L task starts as
  soon as that wave's S/M tasks finish. Reported under `fast_lanes` in `--json` output;
  `waves` keeps its existing shape.
- The subagent report template in `SUBAGENT_CONTEXT.md` now asks for the `decisions` field
  that REPORTING.md already parses.

## [2.4.0] — 2026-09-21

Theme: **The codebase records its own reasoning.** Every build now keeps an append-only
log of *why* it was built the way it was, and vibe-graph derives a live map of *how*
execution travels — both readable by humans (onboarding) and by future AI sessions (so a
settled choice isn't re-derived or re-litigated).

### Added
- **`vibe/IMPLEMENTATION_LOG.md` — append-only implementation-decision log.** Code-altitude
  "why this approach, why this library," distinct from `DECISIONS.md` (spec/scope). Always-on:
  scaffolded by `vibe-new-app` / `vibe-init`, appended by the build skills when a choice clears
  the "meaningful" bar (hard to reverse · picks among real alternatives · would surprise a future
  reader · deviates from ARCHITECTURE.md). Append-only with supersede; each entry's `Touches:`
  links to graph nodes. Canonical template + rules in
  `vibe-new-app/references/IMPLEMENTATION_LOG_MD.md`.
- **`vibe-graph` execution-flow layer.** New `graph.py flow` command derives
  `vibe/graph/FLOW.md` — entry points (`"entrypoint": true` nodes) → the modules and functions
  each reaches, confidence-marked, with import-cycle detection. Optional function-level `calls`
  edges give the "which function calls which" detail. **Derived and regenerated on every graph
  update — never hand-written, so it can't rot.** Entry-point nodes are highlighted in
  `graph.html`. Wired into `vibe-graph` init/build/update/rebuild and the status output.

### Changed
- **`vibe-parallel` subagent report** gains a `decisions[]` field (title / why / touches);
  the main session promotes non-empty ones into `IMPLEMENTATION_LOG.md` after each wave.
  `IMPLEMENTATION_LOG.md` added to `MAIN_SESSION_OWNED_FILES` (conflict detection skips it).
- **`vibe-review`** reads `IMPLEMENTATION_LOG.md` and flags **significant undocumented
  decisions** as P2 findings in Step 3 (drift detection) — keeping the "why" from silently
  rotting out of the record.
- **`vibe-new-app` / `vibe-add-feature` / `vibe-fix-bug`** per-task/close-out sequences now
  append meaningful decisions to `IMPLEMENTATION_LOG.md` and include it in the doc commit.

## [2.3.0] — 2026-09-19

Theme: **P1 blocks the phase gate, and findings must be machine-readable.** Closes a
gate that could pass a phase with open P1s and leave them invisible/unfixable.

### Changed
- **`vibe-review` gate rule — P0 AND P1 block a phase gate** (was: P0 blocks, P1→backlog
  before deploy). A P1 is never deferred past the phase that introduced it; only P2/P3
  carry to the final cleanup pass. Step 10's gate-status lines updated to match
  ("BLOCKED — N P0 + M P1"; "✅ 0 P0, 0 P1").
- **`vibe-new-app` CLAUDE.md template** — phase-gate line now reads "0 open P0 AND 0
  open P1" (was "0 P0 findings"), so every generated project inherits the correct bar.

### Added
- **`vibe-review`: the machine-readable ` ```json ` findings block is now MANDATORY**,
  not optional — a prose summary or markdown table alone is rejected. Tooling (the gate,
  the panel's findings/fix UI) parses that block; without it findings are invisible and
  unfixable and the gate can't count them. This was a real failure: a review wrote a
  findings table but no json block, so 3 open P1s showed no fix path and the gate read
  "passed."

Theme: **tighter CLAUDE.md rules the model can actually follow.** Adds a compact,
forbid-style "Working rules" block to the generated project CLAUDE.md — every rule
checkable, one line, and of the kind that changes an output (distilled from the
"21 CLAUDE.md rules" analysis). Backward-compatible: the load-bearing per-task
sequence and phase-gate machinery other skills parse is unchanged.

### Added
- **`vibe-new-app` + `vibe-init` CLAUDE.md templates — a "Working rules" block:**
  - **Surgical edits** — minimum lines, no unrequested reformat/reorder/rename, match
    existing style, remove only the imports your change made unused.
  - **Do not rewrite tests to pass** — if a test is wrong, say so and stop; fix the code.
  - **Do not guess unknown values** — output `MISSING: <what>` and stop rather than
    inventing a plausible default (the highest-value rule; complements needs_pm for
    decisions and the "never fabricate data" rule).
  - **Ask before destructive actions** — concrete list (drop table, force-push, rewrite
    history, delete a file you didn't create, non-local migration) instead of a vague feeling.
  - **Do not add dependencies** without naming it + what it replaces + waiting.
  - **Comments say why, not what.**
  - **Re-read CLAUDE.md after any context compaction** — persistence insurance for long runs.

### Changed
- Nothing renamed or removed; the block is additive guidance layered onto the existing
  templates, so the generated-artifact contract downstream skills rely on is unchanged.

## [2.1.0] — 2026-09-19

Theme: **observe before you ship, and try to break it.** A set of cross-skill
methodology additions — no renamed files, no changed artifact contracts — that push
every skill from asserting toward verifying, and from confirming toward falsifying.

### Added
- `vibe-design`: **Step 3.5 — the reviewable click-through prototype.** The design step
  now emits a single self-contained `vibe/design/preview.html` rendering every primary
  screen with real sample content, inline-JS navigation between screens, and the key
  states — so a person approves the direction by clicking through it, not by reading the
  Markdown contract. It is the one sanctioned all-in-one HTML file; production files still
  follow one-per-page.
- `vibe-review`: **the falsifying stance.** The reviewer's job is to prove a change is
  unsafe, incorrect, or unnecessarily complex — construct the breaking input, the unhandled
  failure, the simpler equivalent, the security hole — not to bless it. A finding must carry
  the concrete trigger scenario. Sharpens second-opinion reviews especially.
- `vibe-review`: **runtime evidence** for UI/runnable changes — boot it, exercise the primary
  flow, check console/stderr; a blank screen or console error is a finding with the observed
  symptom as its evidence, not something inferable from reading the diff.
- `vibe-test`: **assertions derived from intended behaviour** (spec / acceptance criteria,
  not the implementation — no tautological tests), plus the explicit **generate → run →
  observe → repair** loop with failure classification (wrong test vs real bug vs flaky).
  Green must be green for the right reason; assertions are never weakened to reach it.
- `vibe-fix-bug`: **multi-hypothesis diagnosis** — enumerate 2–3 competing hypotheses with
  both confirming and disconfirming evidence, reject before committing, and reproduce the
  failure before the fix / confirm the fix removes that reproduction. Don't let the first
  plausible cause win.
- `vibe-doctor`: when a reported symptom maps to several checks, list the candidate causes
  and confirm which one actually fires before remediating.
- `vibe-e2e`: **console/page-error capture as a first-class failure**, screenshot-as-evidence
  at each flow's key state, and blank/error screens treated as failures even when no assertion
  tripped — observing the page, not just probing it.

### Changed
- Nothing renamed or removed; every addition is backward-compatible methodology layered
  onto existing steps, so downstream artifact contracts are unchanged.

## [2.0.0] — 2026-09-11

A full capability re-architecture. The framework was authored for a Sonnet 4.6-era
model and its design assumed a weaker, lower-trust model: rigid checkpoints,
aggressive context rationing, regex-parsed sub-agent reports, and a single hardcoded
model everywhere. This release removes constraints that no longer bind and adopts
capabilities that didn't exist before, targeting the current lineup
(Sonnet 5 · Opus 5 · Fable 5.1 · Haiku 4.5).

### Added
- Executable, deterministic engines invoked by their skills instead of being mentally
  simulated: `vibe-graph/scripts/graph.py` (god-nodes, blast-radius, stats, HTML),
  `vibe-parallel/scripts/waves.py` (dependency waves, conflict detection, estimates).
- `scripts/lint.py` — a stdlib-only framework self-linter that flags dangling
  `references/*.md`, duplicate step headings, stale model IDs, non-compiling scripts,
  and a README skill-count mismatch; exits non-zero so it can gate CI.
- Per-task model tiering (Haiku ↔ Fable ↔ Sonnet ↔ Opus) plus extended-thinking effort
  callouts at the high-leverage one-shot decisions (brief synthesis, architecture
  trade-offs, bug diagnosis, agent-pattern selection, review judgment).
- Structured, schema-validated JSON sub-agent reports in `vibe-parallel`, replacing the
  regex-parsed free-text `TASK_COMPLETE:` blocks.
- Anthropic-native agents (Agent SDK / Tool Runner / Managed Agents) as a first-class
  option in `vibe-agent`'s framework roster.
- Delegation to first-party skills/commands — `/code-review`, `/security-review`,
  `frontend-design`, `design:accessibility-review` — plus a real screenshot-verification
  loop and browser-rendered token extraction in `vibe-design-md`.
- `vibe-brainstorm` Mode C and a bounded AI co-founder posture (research + advisory
  readiness); `vibe-design-md` mode to ingest a design the user already made.
- Prompt-caching guidance (AP-09) in `vibe-perf`; the six previously-missing reference
  templates cited by skills.

### Changed
- **Model IDs refreshed** to the current lineup, single-sourced through
  `vibe-cost/references/PRICING.md` (default model, cost math, and Fable/Opus tiers now
  live in one place). This includes the IDs baked into generated `config.py`.
- `vibe-graph` repurposed from a token-savings context-slicer to a semantic-navigation /
  blast-radius / intent-drift overlay with a cached hybrid baseline — sub-agents now get
  cached full context instead of lossy slices.
- Quality gates are actually enforced rather than merely asserted: the deploy gate reads
  `vibe/reviews/` and blocks on open P0 / final-gate findings; the auto-test handoff is
  real (`vibe-add-feature`, `vibe-fix-bug` invoke `vibe-test` on the blast radius); the
  god-node parallel-safety check is wired into the wave builder; `architect:` now triggers
  `spec-review`; design artifacts (`DESIGN.md`, `CONTRACT.md`) are wired into build.
- Diagnosis-first, self-verifying retry and looser triage/question ergonomics in place of
  retry-once-then-stop and forced single-question checkpoints.
- `vibe-perf` token counting switched from `tiktoken` (gpt-4 tokenizer) to
  `messages.count_tokens`.
- `vibe-deploy` split from a ~940-line monolith into per-platform configs under
  `references/platforms/*`, loading only the triggered platform.
- Install paths de-hardcoded to resolve across flat and plugin/marketplace layouts.

### Fixed
- `vibe-progress` cost row read a flat array as `.sessions`, always showing $0.00 / 0
  sessions.
- `CODEBASE.md` was marked both concurrent-safe and main-session-only, risking corruption
  during parallel runs.
- `vibe-review` overwrote `.claude/settings.json` wholesale, clobbering existing hooks and
  permissions.
- `vibe-handoff` portal derived the project name from a fixed directory depth and a
  hyphen-truncating regex (e.g. "Ride-Tribe" → "Ride").
- Three rounds of independent blind re-audit findings and own-regression fixes closed.
- Stripped leftover client fingerprints (personal names, Mumbai region default,
  Gemini/OpenWeather example keys) from templates.

### Removed
- Legacy `.claude-plugin` marketplace metadata and the nested `plugins/` structure;
  skills now live flat at the repository root.

## [1.0.0] — 2026-04-17

Initial tagged release. All 26 vibe-\* skills covering the software development lifecycle
(plan → design → build → ship → close), flattened to the repository root with a GitHub
Pages landing page and `git clone` install instructions.

[2.8.0]: https://github.com/aakashdhar/vibe-skill/compare/v2.7.0...v2.8.0
[2.7.0]: https://github.com/aakashdhar/vibe-skill/compare/v2.6.0...v2.7.0
[2.6.0]: https://github.com/aakashdhar/vibe-skill/compare/v2.5.2...v2.6.0
[2.5.2]: https://github.com/aakashdhar/vibe-skill/compare/v2.5.1...v2.5.2
[2.5.1]: https://github.com/aakashdhar/vibe-skill/compare/v2.5.0...v2.5.1
[2.5.0]: https://github.com/aakashdhar/vibe-skill/compare/v2.4.1...v2.5.0
[2.4.1]: https://github.com/aakashdhar/vibe-skill/compare/v2.4.0...v2.4.1
[2.4.0]: https://github.com/aakashdhar/vibe-skill/compare/v2.3.0...v2.4.0
[2.3.0]: https://github.com/aakashdhar/vibe-skill/compare/v2.2.0...v2.3.0
[2.2.0]: https://github.com/aakashdhar/vibe-skill/compare/v2.1.0...v2.2.0
[2.1.0]: https://github.com/aakashdhar/vibe-skill/compare/v2.0.0...v2.1.0
[2.0.0]: https://github.com/aakashdhar/vibe-skill/compare/v1.0.0...v2.0.0
[1.0.0]: https://github.com/aakashdhar/vibe-skill/releases/tag/v1.0.0
