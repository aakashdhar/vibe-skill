# vibe-skill Framework — Analysis & Upgrade Plan

> **Status:** Analysis complete (7-layer deep read). **Wave 0 ✅ · Wave 1 ✅ · Wave 2 ✅ · Wave 3 ✅ done** (committed & synced to `~/.claude/skills`). Wave 4 (hygiene) pending.
> **Core goal:** Not a version-string sweep. Re-architect the framework to exploit the *capabilities* of the current Anthropic model generation (Sonnet 5, Opus 5, Fable 5.1, Haiku 4.5). The framework was authored for Sonnet 4.6, whose capabilities defined its design constraints at the time; those constraints no longer bind.

---

## 0. North star — this is a capability upgrade

When this framework was written for **Sonnet 4.6**, its design made sense *for that model*: babysit the model with rigid checkpoints, ration context aggressively because windows were smaller and every 25K tokens hurt, parse free-text sub-agent reports with regex, and hardcode a single model everywhere. Those were correct decisions **for 4.6-era capabilities**.

The newer models change the underlying assumptions the framework was built on. The upgrade is about **removing constraints that no longer exist and adopting capabilities that didn't exist before** — the hardcoded model IDs are just the most visible symptom, not the goal.

Capability shifts to design around (map each to concrete framework changes below):

| New capability | What it makes possible in vibe-skill |
|---|---|
| **Larger / stronger long-context reasoning** | Retire aggressive graph-slicing as a *cost* strategy; feed sub-agents cached full context instead of lossy slices; raise the rigid file-count read caps. |
| **Extended / interleaved thinking with tunable effort** | Add explicit "think harder" budgets at the high-leverage one-shot decisions (brief synthesis, architecture trade-offs, bug diagnosis, agent-pattern selection, review judgment). |
| **Reliable structured outputs / strict tool schemas** | Replace regex-parsed `TASK_COMPLETE:` blocks and prose status lines with schema-validated JSON — kills a whole `parse_error → FAILED` failure class and unlocks CI/dashboards. |
| **Wider, cheaper capability spread (Haiku 4.5 ↔ Fable 5.1 ↔ Sonnet 5 ↔ Opus 5)** | Per-task model tiering: mechanical passes on cheap tiers, judgment/architecture on strong tiers — the framework already has vibe-cost to measure it. |
| **Mature prompt caching** | Cache-friendly prompt conventions (stable prefixes: ARCHITECTURE.md, shared instructions) as a bigger cost lever than context-slicing ever was. |
| **Stronger agentic reliability** | Loosen low-trust ergonomics — fewer forced human checkpoints, smarter retry than retry-once-then-stop, self-verification passes. |
| **First-party skills & commands** (`/code-review`, `/security-review`, `frontend-design`, `design:accessibility-review`) | Delegate to these instead of hand-rolling grep-based checks and duplicating design guidance. |
| **Multimodal / vision** | Real screenshot-driven design verification loop instead of a rhetorical "imagine you screenshot this." |
| **Native sub-agent / Agent SDK orchestration** | Offer it as a first-class agent-framework option; lean on native dispatch instead of reimplementing wave orchestration by hand. |

**Bottom line:** the model-ID refresh is the smallest piece. The value is (a) making the framework's advertised integration actually real, and (b) letting current models do more with less scaffolding.

---

## 1. The headline

- The "built for Sonnet 4.6" problem is **real but narrow** at the string level — hardcoded old IDs live in only three places.
- The larger story: the framework is architected for a **weaker, lower-trust model era**, and — most urgently — **much of its advertised cross-skill integration is aspirational**: declared in one skill, never enforced in the other. For a "one-stop framework," that wiring gap is a bigger risk than any stale model string.

Findings sort into four buckets, in priority order: **correctness bugs → wiring integrity → model/capability modernization → architecture modernization**, plus hygiene.

---

## 2. Cross-cutting themes

### 2.1 Silent correctness bugs (model-independent — fix regardless)
| Bug | Where | Effect |
|---|---|---|
| Cost row reads a flat array as `.sessions` | `vibe-progress/SKILL.md:64-71` | Dashboard **always shows $0.00 / 0 sessions** |
| CODEBASE.md marked both concurrent-safe *and* main-session-only | `vibe-parallel/references/WAVE_BUILDER.md:54-59` vs `vibe-parallel/SKILL.md:489` | Parallel runs can **corrupt CODEBASE.md** |
| `cat > .claude/settings.json <<EOF` full overwrite | `vibe-review/SKILL.md:438-457` | **Clobbers** existing hooks/permissions (incl. vibe-doctor's) |
| Portal name from fixed dir depth + hyphen-truncating regex | `vibe-handoff/scripts/generate_portal.py:614,619` | Wrong project name; "Ride-Tribe" → "Ride" |

### 2.2 Missing / broken reference files (functional — skills cite files that don't exist)
- **vibe-new-app** cites 4 templates (`CLAUDE_MD.md`, `TASKS_MD.md`, `CODEBASE_MD.md`, `ARCHITECTURE_MD.md`); only `PLAN_MD.md` exists → every greenfield `CLAUDE.md`/`TASKS.md`/`CODEBASE.md` is **improvised inline**, breaking the "structurally consistent for downstream parsing" contract. *(Verified directly.)*
- **vibe-review** cites `references/PLATFORM_CHECKS.md` + `references/REVIEW_REPORT.md` — neither exists; its report format + platform step are unimplementable as written.
- **vibe-spec-review** Steps 4/5 point at `ARCHITECTURE_RUBRIC.md` / `FEATURE_SPEC_RUBRIC.md` that don't exist (content is embedded inside `SPEC_RUBRIC.md`).

### 2.3 Aspirational wiring — the "one-stop" integrity problem
The framework repeatedly promises handoffs the receiving skill knows nothing about:
- **The deploy gate is fiction.** review + perf both claim to "block deploy until P0/P1 resolved." `vibe-deploy` (906 lines) never reads `vibe/reviews/`. The central safety guarantee isn't enforced.
- **Auto-test is fiction.** vibe-test claims it "runs automatically after add-feature/fix-bug." Neither caller invokes it — they run inline `npm test`.
- **god-node parallel-safety** is documented in vibe-graph + coded in `check_parallel_safety()`, but WAVE_BUILDER's actual 4-pass pipeline never calls it.
- **architect never triggers spec-review** (brainstorm + agent do) → ARCHITECTURE.md only audited indirectly, later.
- **Design artifacts orphaned:** new-app/add-feature read `DESIGN_SYSTEM.md` but never `DESIGN.md` or the design `CONTRACT.md` that vibe-design/design-md treat as law.

### 2.4 Model-era rot (the literal ask — smaller than expected)
- **Hardcoded old IDs** in just three spots: vibe-agent references (`claude-sonnet-4-6`, incl. **baked into every generated `config.py`** via `AGENT_ARCH_TEMPLATE.md:332`), `vibe-cost/references/PRICING.md`, and `vibe-parallel/references/{REPORTING,SUBAGENT_CONTEXT}.md`.
- **PRICING.md** lists `opus-4-6`/`sonnet-4-6`/`haiku-4-5`, default `sonnet-4-6`, **no Fable tier, no Opus in the selection guide**. Every dollar figure in the framework flows from this one table.
- **Wrong tokenizer:** `vibe-perf/references/AGENTIC_PERF.md:169` uses `tiktoken.encoding_for_model("gpt-4")` to count *Claude* tokens.
- Stale pins: Playwright 1.44 / TS 5.4, Node 20, `python:3.12-slim`, GH Actions `@master`.

### 2.5 "Built for a weaker model" architecture (the deep upgrade)
- **Aggressive context-slicing (vibe-graph)** justified by 25K-token CODEBASE.md pain + "60-70% cheaper" claims. With current windows + caching, that math largely dissolves, and slices have a real failure mode (files not yet in the graph). → **Keep vibe-graph, repurpose from token-savings to semantic navigation / blast-radius / intent-drift; give sub-agents cached full context.**
- **Regex-parsed free-text sub-agent reports** → structured tool outputs.
- **No extended thinking** anywhere, including the highest-leverage one-shot decisions.
- **No model-tiering** (Haiku/Fable/Sonnet/Opus per task) despite vibe-cost existing to track it.
- **No prompt-caching conventions**, though vibe-cost flags cache waste as a pattern.
- **Rigid low-trust ergonomics:** "ask ONE clarifying question," retry-once-then-stop, fixed step counts, hard file-count caps.

### 2.6 Not leveraging new first-party capabilities
- Quality layer hand-rolls grep instead of using **`/code-review` and `/security-review`**.
- Design layer **mis-invokes + duplicates** the first-party `frontend-design` skill (hardcoded `~/.claude/skills/...` path → silently degrades on plugin installs), and never runs a **real screenshot-verification loop**. vibe-design-md extracts tokens via `curl` static HTML — blind to SPA/CSS-in-JS.
- No **structured (JSON) findings output** anywhere, though vibe-graph already proves the JSON-contract pattern.

### 2.7 Portability & hygiene
- **Hardcoded `~/.claude/skills/...` paths** in new-app, vibe-mode block, design, handoff, ledger, cost → break on the plugin/marketplace install actually shipped.
- **Leftover client fingerprints:** personal names (Mayuresh, Dhiraj, Deepak, Aakash) in handoff templates; `primary_region="bom"` (Mumbai); `GEMINI_API_KEY`/`OPENWEATHER_API_KEY` as default examples in a *Claude* framework; Supabase/Stripe/NextAuth hardcoded.
- **Duplication, no single source of truth:** anti-generic rules (3 files), cost math (3 files), default-model string (2), post-task checklist (2).
- **vibe-deploy is a 906-line monolith** doing 4 jobs × 7 platforms inline — every run pays context cost for 6 platforms it isn't using.

---

## 3. Per-layer summary

| Layer | Skills | Top issue(s) |
|---|---|---|
| **1. Planning/Spec** | brainstorm, architect, agent, spec-review, change-spec | Stale IDs ship into generated `config.py`; 2 broken rubric pointers; duplicate "Step 13"; architect→spec-review gap; no extended thinking at synthesis points |
| **2. Project setup** | new-app, init, mode | 4 missing templates (greenfield artifacts improvised); hardcoded install path; retrofit CLAUDE.md lacks VIBE_MODE; low-trust checkpoint cadence |
| **3. Coding/Build** | add-feature, fix-bug, parallel, graph | CODEBASE.md concurrency bug; god-node check unwired; stale pricing constants; regex report parsing; **vibe-graph slicing needs re-litigating vs. big context + caching** |
| **4. Quality/Test** | review, test, e2e, doctor, perf | Deploy gate not enforced; auto-test handoff fictional; missing ref files; settings.json clobber; tiktoken gpt-4; ignores `/code-review` + `/security-review` |
| **5. Design** | design, design-md | Mis-invokes/duplicates `frontend-design`; no screenshot loop; curl-based token extraction; stale font zeitgeist; unversioned external catalog dep |
| **6. Delivery/Docs** | document, handoff, changelog, deploy | Deploy gate absent; deploy monolith; hardcoded Node/py/region/API-key defaults; personal names in templates; portal script path/regex fragility |
| **7. Observability/Meta** | cost, ledger, progress | Stale PRICING table + no Fable/Opus; progress $0 bug; 2 default-model strings; no per-task model field for mixed-model sessions |

*Full per-layer findings (with line numbers and recommendations) were produced by the analysis pass and can be regenerated on request.*

---

## 4. Upgrade roadmap (sequenced)

**Wave 0 — Correctness (cheap, model-independent, first): ✅ DONE.** progress $0 bug; CODEBASE.md concurrency; settings.json clobber; portal path/regex; created the 6 missing reference files; fixed the 2 broken rubric pointers.

**Wave 1 — Model & capability refresh: ✅ DONE.** rewrote PRICING.md to the current lineup (Fable 5.1 + Opus 5 + Sonnet 5 + Haiku 4.5) as the single source of truth; single-sourced the default model; replaced hardcoded IDs in vibe-agent templates (incl. generated config.py) with per-role tiering; swapped tiktoken → `messages.count_tokens`; added the per-task model-tiering table + effort/adaptive-thinking guidance; added AP-09 (prompt caching) to vibe-perf. *Carried to Wave 3:* injecting extended-thinking effort into each skill's high-leverage steps, and adding the Claude Agent SDK / native sub-agents as a first-class option in vibe-agent's framework roster.

**Wave 2 — Wiring integrity (makes "one-stop" real): ✅ DONE.** enforced the deploy gate inside vibe-deploy (Step 0.5 reads vibe/reviews/, blocks on open P0/final-gate, warns on P1); made the test handoff real (vibe-add-feature Step 13, vibe-fix-bug Step 11 invoke vibe-test on the blast radius); wired the god-node safety check into WAVE_BUILDER as Pass 2.5; tagged review findings `performance` + suggest `perf:` (perf↔review); added architect→spec-review (Step 7.5 + spec-review Trigger 2.5); wired DESIGN.md / vibe/design/CONTRACT.md into vibe-new-app Step 3 and vibe-add-feature Step 5.

**Wave 3 — Architecture modernization (the deep one): ✅ DONE.** structured schema-validated subagent JSON reports (vibe-parallel, replacing regex); repurposed vibe-graph to a semantic-navigation / focus-overlay model with a cached hybrid baseline; extended-thinking effort callouts at the high-leverage one-shot decisions (brainstorm/architect/agent/new-app/fix-bug/review); diagnosis-first self-verifying retry + looser triage/question ergonomics; Anthropic-native agents (Agent SDK / Tool Runner / Managed Agents) as a first-class framework option; delegate to `/code-review`, `/security-review`, `frontend-design` (proper Skill invocation) + a real screenshot loop + `design:accessibility-review`; browser-rendered token extraction in design-md. *Note:* structured JSON findings live in vibe-review; extending the same to vibe-perf/vibe-test reports is a small follow-up.

**Wave 4 — Hygiene:** de-hardcode install paths; strip client fingerprints; dedupe single-source files; split vibe-deploy into `references/platforms/*`.

---

## 5. Strategic take

The bones are strong — the artifact chain, phase gates, and lifecycle coverage are well-conceived and unusually complete. Two things stand between it and a dependable one-stop tool:
1. **Wiring gaps (Wave 2)** — the framework *says* it's integrated more than it *is*.
2. **Low-trust ergonomics (Wave 3)** — it babysits a model that no longer needs it.

The capability upgrade (Waves 1 + 3) is where the framework stops being a 4.6-era harness and starts being something the current models can drive far harder — which is the actual goal.
