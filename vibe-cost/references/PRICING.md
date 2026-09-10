# PRICING.md

Current Anthropic model pricing and the per-task model-selection guide for the
vibe-* framework. This file is the **single source of truth** for pricing — other
skills (vibe-ledger, vibe-parallel, vibe-add-feature) should reference these
numbers, not hardcode their own.

Last updated: **2026-09** (verify at https://anthropic.com/pricing if this is
more than ~90 days old — see the staleness check in vibe-cost Step 0).

All prices are per million tokens (MTok).

---

## Current model pricing

| Model | ID | Context | Input | Output | Cache write | Cache read |
|-------|----|---------|-------|--------|-------------|------------|
| Claude Fable 5.1 | `claude-fable-5-1` | 1M | $10.00 | $50.00 | $12.50 | $1.00 |
| Claude Opus 5 | `claude-opus-5` | 1M | $5.00 | $25.00 | $6.25 | $0.50 |
| Claude Sonnet 5 | `claude-sonnet-5` | 1M | $2.00 | $10.00 | $2.50 | $0.20 |
| Claude Haiku 4.5 | `claude-haiku-4-5` | 200K | $1.00 | $5.00 | $1.25 | $0.10 |

**Default assumption if the running model is unknown: `claude-sonnet-5`** — the
framework's build-loop workhorse. This is the *one* place the default lives;
vibe-cost reads it from here.

Notes:
- Cache write ≈ 1.25× input, cache read ≈ 0.1× input (standard 5-minute cache;
  extended 1-hour cache doubles the write cost). Fable 5.1 has a lower published
  cache-read rate — verify against the pricing page before relying on it.
- Model IDs are complete as-is — never append a date suffix.
- Older IDs (`claude-opus-4-6`, `claude-sonnet-4-6`, …) are only for projects
  explicitly pinned to them; look them up on the pricing page.

---

## Cost calculation formula

```python
PRICING = {
    #                 input  output  cache_write  cache_read   (per MTok)
    "claude-fable-5-1": {"input": 10.0, "output": 50.0, "cache_write": 12.50, "cache_read": 1.00},
    "claude-opus-5":    {"input":  5.0, "output": 25.0, "cache_write":  6.25, "cache_read": 0.50},
    "claude-sonnet-5":  {"input":  2.0, "output": 10.0, "cache_write":  2.50, "cache_read": 0.20},
    "claude-haiku-4-5": {"input":  1.0, "output":  5.0, "cache_write":  1.25, "cache_read": 0.10},
}
DEFAULT_MODEL = "claude-sonnet-5"

def calculate_cost(input_tokens, output_tokens, model,
                   cache_read_tokens=0, cache_write_tokens=0):
    pricing = PRICING.get(model, PRICING[DEFAULT_MODEL])
    standard_input = max(0, input_tokens - cache_read_tokens - cache_write_tokens)
    cost = (
        (standard_input      / 1_000_000) * pricing["input"]
        + (cache_read_tokens  / 1_000_000) * pricing["cache_read"]
        + (cache_write_tokens / 1_000_000) * pricing["cache_write"]
        + (output_tokens      / 1_000_000) * pricing["output"]
    )
    return round(cost, 4)
```

---

## Model selection guide (per-task tiering)

The current lineup spans a wide capability/price range — use it. Match the model
to the task instead of running one model everywhere.

| Task type | Recommended model | Why |
|-----------|-------------------|-----|
| brainstorm, architect, agent design | `claude-opus-5` | Hardest one-shot reasoning; shapes everything downstream |
| Hard bug diagnosis (root cause unknown) | `claude-opus-5` | Discovery reasoning; worth the premium when stuck |
| spec / PLAN.md feature map | `claude-sonnet-5` (opus-5 for XL) | Quality matters; sonnet handles most |
| Main build loop / complex feature (L) | `claude-sonnet-5` | Workhorse: strong multi-file coding at ⅖ Opus cost |
| Test generation | `claude-sonnet-5` | Pattern matching is subtle |
| Review (phase gates) | `claude-sonnet-5` (opus-5 for final gate) | Needs strong pattern/security detection |
| Simple scaffold / boilerplate (S) | `claude-haiku-4-5` | Template-like, mechanical |
| Documentation generation | `claude-haiku-4-5` | Lower reasoning bar |
| Trivial bug fix (root cause known) | `claude-haiku-4-5` | Mechanical application |
| Verifier / rubric / schema checking | `claude-haiku-4-5` | Deterministic checking, not reasoning |
| Most demanding long-horizon agentic work | `claude-fable-5-1` | Most capable; premium price — reserve for the hardest |

**Reach for the cheaper tier when:** the task has a clear template, the output is
structured (JSON) rather than prose reasoning, the root cause is already known, or
a verifier will catch mistakes.

**Stay on Opus/Sonnet when:** architecture decisions are being made, the root
cause is unknown, the output is client-facing, or the task sets the pattern for
everything that follows.

### Effort & thinking (a lever *within* a model, before you switch models)
Current models use **adaptive thinking** (`thinking: {type: "adaptive"}`) plus
`output_config.effort` (`low` → `max`) — the old fixed `budget_tokens` is
deprecated and rejected on the current lineup.
- Coding and long-horizon agentic work respond strongly to higher effort —
  `high`/`xhigh` for the build loop, review, and hard diagnosis.
- Mechanical / high-volume subagent work does well at `low` (fewer, terser tool
  calls) — cheaper than dropping to a weaker model, and it keeps one cache
  namespace. **Measure the newest model at lower effort before building a
  multi-model cascade** — lower effort on Sonnet 5 often beats a prior-gen model
  at high effort, and a cascade forfeits cache reuse (caches are model-scoped).

---

## Practical cost benchmarks

Reference points at **`claude-sonnet-5` pricing** ($2 in / $10 out). Scale by the
input/output ratio in the table above for other models (Opus ≈ 2.5×, Haiku ≈ 0.5×,
Fable ≈ 5×), and lean on caching for the big wins below.

| Session | Typical tokens (in / out) | Sonnet 5 cost |
|---------|---------------------------|---------------|
| Small planning (brainstorm: simple app) | 15-25k / 3-5k | ~$0.07-0.10 |
| Medium feature build (one M feature) | 60-100k / 8-15k | ~$0.20-0.35 |
| Large build (Phase 1, parallel subagents) | 150-300k / 20-40k | ~$0.50-1.00 |
| Full phase review | 80-150k / 5-10k | ~$0.20-0.40 |

**Full project (brainstorm → deploy, typical SaaS, mixed models + caching):**
Small (4-6 wks) ~$10-30 · Medium (2-3 mo) ~$40-100 · Large (6+ mo) ~$150-400.
These are estimates — real spend depends on model mix, effort, and cache hit rate.

---

## Cache economics

Prompt caching is the biggest cost lever on repeated large contexts — larger than
model choice for a session that re-reads the same CLAUDE.md / ARCHITECTURE.md.

**Without caching:** 100,000 input tokens × $2.00/MTok (Sonnet 5) = $0.20
**With caching (stable prefix cached, ~80% hit):**
- 20,000 standard input: $0.04
- 80,000 cache read: $0.016
- Total: $0.056 — **72% cheaper**

**Design for it:**
- Keep the stable prefix first — `tools` → `system`/CLAUDE.md → volatile messages.
- Any byte change in the prefix invalidates everything after it: keep CLAUDE.md
  stable during a session (track progress in TASKS.md, not CLAUDE.md), and don't
  put timestamps or per-request IDs before the last cache breakpoint.
- Caches are model-scoped — a multi-model cascade can't share a cache prefix.
- Verify with `cache_read_input_tokens` in usage; if it's zero across repeated
  requests, a silent invalidator is at work.

---

## Token count quick reference

Use the API's `messages.count_tokens` for anything that must be accurate — never
`tiktoken` (that is an OpenAI tokenizer and mis-counts Claude tokens). The
estimates below are only for rough calibration. Note the current-generation
tokenizer runs ~1×-1.35× the token count of older models for the same text.

| Content | Tokens |
|---------|--------|
| 1 line of code | ~5 |
| 100 lines of code | ~400-600 |
| CLAUDE.md (typical) | 1,000-3,000 |
| CODEBASE.md (small project) | 3,000-8,000 |
| CODEBASE.md (mature project) | 15,000-40,000 |
| SPEC.md (typical feature) | 2,000-6,000 |
| ARCHITECTURE.md (typical) | 1,500-4,000 |
| FEATURE_TASKS.md (one feature) | 1,500-3,000 |
| 1 page of English prose | ~500 |
| 1 word | ~1.3 (average) |
