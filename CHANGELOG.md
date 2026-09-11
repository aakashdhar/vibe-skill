# Changelog

All notable changes to the **vibe-\*** skill framework are documented here.

The format follows [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).
The current version is tracked in [`VERSION`](VERSION); each release is cut as an
annotated git tag (`vX.Y.Z`), which GitHub surfaces as a Release. See
[`VERSIONING.md`](VERSIONING.md) for the release process.

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

[2.0.0]: https://github.com/aakashdhar/vibe-skill/compare/v1.0.0...v2.0.0
[1.0.0]: https://github.com/aakashdhar/vibe-skill/releases/tag/v1.0.0
