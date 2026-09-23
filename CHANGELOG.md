# Changelog

All notable changes to the **vibe-\*** skill framework are documented here.

The format follows [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).
The current version is tracked in [`VERSION`](VERSION); each release is cut as an
annotated git tag (`vX.Y.Z`), which GitHub surfaces as a Release. See
[`VERSIONING.md`](VERSIONING.md) for the release process.

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
