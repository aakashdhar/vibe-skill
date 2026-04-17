# PRICING.md

Current Anthropic model pricing for cost calculations.
Last updated: April 2026. Verify at https://anthropic.com/pricing if stale.

All prices are per million tokens (MTok).

---

## Current model pricing

| Model | Input ($/MTok) | Output ($/MTok) | Cache write ($/MTok) | Cache read ($/MTok) |
|-------|---------------|----------------|---------------------|-------------------|
| claude-opus-4-6 | $15.00 | $75.00 | $18.75 | $1.50 |
| claude-sonnet-4-6 | $3.00 | $15.00 | $3.75 | $0.30 |
| claude-haiku-4-5 | $0.80 | $4.00 | $1.00 | $0.08 |

Default assumption if model unknown: claude-sonnet-4-6

---

## Cost calculation formula

```python
def calculate_cost(
    input_tokens: int,
    output_tokens: int,
    model: str,
    cache_read_tokens: int = 0,
    cache_write_tokens: int = 0
) -> float:
    pricing = PRICING[model]

    # Standard input tokens (not cached)
    standard_input = input_tokens - cache_read_tokens - cache_write_tokens
    standard_input = max(0, standard_input)

    cost = (
        (standard_input / 1_000_000) * pricing['input']
        + (cache_read_tokens / 1_000_000) * pricing['cache_read']
        + (cache_write_tokens / 1_000_000) * pricing['cache_write']
        + (output_tokens / 1_000_000) * pricing['output']
    )

    return round(cost, 4)
```

---

## Practical cost benchmarks

These are real-world reference points for calibrating estimates:

**Small planning session (brainstorm: for a simple app)**
- Typical: 15,000-25,000 input, 3,000-5,000 output
- Sonnet cost: ~$0.10-0.20

**Medium feature build session (one M-sized feature, 3-4 tasks)**
- Typical: 60,000-100,000 input, 8,000-15,000 output
- Sonnet cost: ~$0.30-0.50

**Large build session (Phase 1 with parallel subagents)**
- Typical: 150,000-300,000 input, 20,000-40,000 output
- Sonnet cost: ~$0.75-1.50

**Review session (full phase review)**
- Typical: 80,000-150,000 input, 5,000-10,000 output
- Sonnet cost: ~$0.30-0.60

**Full project (brainstorm to deploy, typical SaaS)**
- Small project (4-6 weeks): $15-40 estimated total
- Medium project (2-3 months): $60-150 estimated total
- Large project (6+ months): $200-500+ estimated total

---

## Cache economics

Prompt caching dramatically changes cost on repeated large contexts.

**Without caching:**
100,000 input tokens × $3.00/MTok = $0.30

**With caching (system prompt cached, 80% cache hit):**
- 20,000 standard input: $0.06
- 80,000 cache read: $0.024
- Total: $0.084 — 72% cheaper

**When caching activates:**
- Eligible: content at the start of the prompt (system prompt, CLAUDE.md)
- Cache duration: 5 minutes (standard) or 1 hour (extended, 2× write cost)
- Not eligible: frequently changing content (active task description, file diffs)

**Implication for vibe-* skills:**
CLAUDE.md is loaded every session. If it's stable (VIBE_MODE doesn't change,
no active feature being written to it mid-session), it should be highly cacheable.
If CLAUDE.md changes frequently → cache never activates → much higher cost.

Recommendation: keep CLAUDE.md stable during a build session.
Use TASKS.md for progress tracking, not CLAUDE.md.

---

## Model selection guide for cost optimisation

Not all tasks need the most capable model.

| Task type | Recommended model | Reason |
|-----------|------------------|--------|
| brainstorm, architect, agent design | Sonnet | Complex reasoning required |
| spec writing, planning | Sonnet | Quality matters, shapes everything |
| Complex feature implementation (L) | Sonnet | High complexity, multi-file reasoning |
| Simple scaffold tasks (S) | Consider Haiku | Straightforward, template-like |
| Test generation | Sonnet | Pattern matching is subtle |
| Documentation generation | Consider Haiku | Lower reasoning bar |
| Simple bug fixes (trivial) | Consider Haiku | Root cause already identified |
| Review (all phases) | Sonnet | Needs strong pattern detection |
| Verifier agents (in agentic systems) | Haiku | Schema/rubric checking, not reasoning |

**Haiku is appropriate when:**
- Task has a clear template to follow
- Output is JSON/structured (not prose reasoning)
- Root cause is known (not discovery)
- Mistakes are cheap to catch (verifier will check it)

**Always use Sonnet when:**
- Architecture decisions are being made
- Root cause is unknown
- Output will be read by the client
- The task sets the pattern for everything that follows

---

## Token count quick reference

**Rough token estimates for common content:**

| Content | Tokens |
|---------|--------|
| 1 line of code | ~5 tokens |
| 100 lines of code | ~400-600 tokens |
| CLAUDE.md (typical) | 1,000-3,000 tokens |
| CODEBASE.md (small project) | 3,000-8,000 tokens |
| CODEBASE.md (mature project) | 15,000-40,000 tokens |
| SPEC.md (typical feature) | 2,000-6,000 tokens |
| ARCHITECTURE.md (typical) | 1,500-4,000 tokens |
| FEATURE_TASKS.md (one feature) | 1,500-3,000 tokens |
| Agent system prompt (vibe-agent) | 800-2,000 tokens |
| 1 page of English prose | ~500 tokens |
| 1 word | ~1.3 tokens (average) |
