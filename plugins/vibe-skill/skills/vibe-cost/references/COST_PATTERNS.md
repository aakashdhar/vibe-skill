# COST_PATTERNS.md

Read during Step 4 of vibe-cost before generating recommendations.
Six cost patterns with detection signals, root causes, and specific fixes.

---

## CP-01 — Large context overhead

**What it is:**
The baseline cost of loading project context (CLAUDE.md, CODEBASE.md,
ARCHITECTURE.md) before any task-specific work begins.
This overhead is paid on every task in every session.

**Detection signal:**
- CODEBASE.md > 20KB
- Cost per simple (S) task > $0.15
- Context overhead estimated > 40% of session total

**Root cause:**
As the project grows, CODEBASE.md grows. Every task loads it in full.
A 40KB CODEBASE.md adds ~40,000 input tokens to every task —
that's ~$0.12 per task just for context, before any work begins.

**Fix options (in order of impact):**

1. **Use vibe-context (when available)**
   Load only the relevant section of CODEBASE.md per task type.
   API task → load only src/api/ section.
   Frontend task → load only src/components/ section.
   Est. saving: 40-60% of context overhead.

2. **Split CODEBASE.md by domain**
   Create CODEBASE_API.md, CODEBASE_FRONTEND.md, CODEBASE_AGENTS.md.
   Load only the relevant file per task.
   Est. saving: 50-70% of context overhead.

3. **Add CODEBASE.md summary index**
   Create a 500-token summary at the top of CODEBASE.md.
   Most tasks only need the summary, not the full file.
   Est. saving: 30-40% of context overhead on routine tasks.

4. **Enable prompt caching on CODEBASE.md**
   If CODEBASE.md is stable within a session, it should cache.
   Verify it's positioned early in the prompt (before task-specific content).
   Cache reads cost 90% less than standard input.
   Est. saving: 60-80% of context cost if cache hits.

---

## CP-02 — Repeated file reads across tasks

**What it is:**
Multiple tasks in the same session each independently reading
the same large files — no shared context between tasks.

**Detection signal:**
- Multiple tasks in one session touching the same files
- Session cost higher than expected for number of tasks completed
- Visible in Mode B: high input tokens relative to output

**Root cause:**
Each task starts fresh. If TASK-001 reads prisma/schema.prisma (3,000 tokens)
and TASK-003 also reads prisma/schema.prisma, that's 6,000 tokens for
one file. At scale across 10 tasks, this compounds significantly.

**Fix:**
Use context summarisation between tasks.
After TASK-001, have the agent produce a brief summary of what it read
that's relevant for future tasks. Pass this summary instead of
re-reading the full file.

For parallel subagents (vibe-parallel), this is unavoidable —
each subagent needs its own context. Accept the cost or
pre-populate a shared summary file each subagent reads instead.

Est. saving: 15-30% on sessions with 4+ tasks touching shared files.

---

## CP-03 — Unstructured output where JSON would do

**What it is:**
Agent generating verbose prose responses where a compact JSON
schema would convey the same information in 3-5× fewer tokens.

**Detection signal (Mode B):**
Output tokens > 2× expected for the task size.
Agent tasks in agentic systems are the primary culprit.

**Example:**
Bad prompt result (GuardianAgent):
> "After carefully analysing the website at https://example.com, I found
> the following brand attributes. The voice appears to be professional
> and informative, with a focus on technical accuracy. The mission
> seems to be centred around helping developers build better software.
> The target audience appears to be mid-level software engineers
> working in enterprise environments. I would estimate the clarity
> score to be around 82 out of 100 based on the consistency
> of messaging across the pages I reviewed..."
(~120 tokens for what should be 20 tokens)

Good prompt result (with structured output):
```json
{"voice":["professional","informative","technical"],
"mission":"Help developers build better software",
"audience":"Mid-level enterprise software engineers",
"clarityScore":82}
```
(~25 tokens)

**Fix:**
Add to agent system prompt:
`"Respond ONLY in valid JSON. No prose. No explanation. Schema: {schema}"`

Or use `response_format={"type":"json_object"}` in the API call.

Est. saving: 50-80% reduction on output tokens for agent tasks.
On a project with 5 agents running 10 times each, this can save $5-20.

---

## CP-04 — Parallel subagent cost multiplication

**What it is:**
vibe-parallel spawns N subagents, each with a full context window.
The cost is N× a single session, not 1× with parallel speedup.
This is expected behaviour — but worth flagging when it's disproportionate.

**Detection signal:**
- vibe-parallel was used this session
- Session cost > 3× typical session cost
- Number of subagents > 4

**When it's worth it:**
4 subagents running in parallel reduces wall-clock time by ~75%.
If your time is worth more than $0.50/hour, parallel almost always wins
on medium/large tasks. The cost is real but the tradeoff is usually good.

**When it's not worth it:**
If the tasks are S-sized and sequential would take 20 minutes,
paying 4× for 5 minutes instead is probably not worth it.

**Fix for over-parallelisation:**
Review wave structure. If Wave 1 has 6 subagents but 4 of them are
S-sized tasks taking <5 minutes each, consider batching into 2 sequential
passes rather than 6 parallel subagents.

**Fix for high per-subagent cost:**
Each subagent loads full CODEBASE.md. Consider the CP-01 fixes above
to reduce per-subagent context size before running parallel.

Est. saving: depends on task count and context size. Rule of thumb:
fixing CP-01 before running CP-04 reduces parallel cost by 30-50%.

---

## CP-05 — Low prompt cache hit rate

**What it is:**
Prompt caching is Anthropic's built-in mechanism to dramatically
reduce cost on repeated large contexts. Cache reads cost 90% less
than standard input reads. If the cache isn't hitting, you're
paying full price every time for content that hasn't changed.

**Detection signal (Mode B only):**
cache_read_tokens / total_input_tokens < 20% on sessions > $0.50

**Root causes:**

1. **CLAUDE.md changes frequently**
   If CLAUDE.md is modified mid-session (ACTIVE FEATURE section updated,
   VIBE_MODE changed), the cache is invalidated every time.
   Fix: Move frequently-changing content out of CLAUDE.md.
   Keep CLAUDE.md stable. Use TASKS.md for session-to-session state.

2. **Content not at prompt start**
   Caching only activates on content at the beginning of the prompt.
   If CLAUDE.md is injected after task-specific content → no caching.
   Fix: Ensure CLAUDE.md loads first, before any task prompt.

3. **Cache timeout between sessions**
   Standard cache TTL is 5 minutes. If sessions are hours apart,
   cache doesn't help for session-to-session reuse.
   Extended cache (1 hour TTL) costs 2× to write but helps for long sessions.
   Fix: For large stable contexts, use extended cache TTL.

Est. saving: 40-70% on input token costs for large, stable contexts.
On a mature project with 40KB CODEBASE.md, this is $0.20-0.50/session.

---

## CP-06 — Over-sized planning sessions

**What it is:**
Planning sessions (brainstorm, architect, spec) consuming more tokens
than the features they enable. Planning should be a small fraction of
build cost, not the dominant cost.

**Detection signal:**
Any single planning session > $0.50
Planning sessions > 30% of total project cost

**Root cause:**
Excessive back-and-forth in planning conversations.
Each exchange adds to context. A 20-turn brainstorm session at
5,000 tokens per turn = 100,000 input tokens just for planning.

**Fix:**
Use plan mode (read-only, no file writes) to limit turns.
Set a mental budget: brainstorm ≤ 10 turns, architect ≤ 8 turns.
When the skill asks clarifying questions, answer concisely.
Use BRIEF.md to capture decisions — don't re-explain context
the skill has already read.

The spec should get more expensive as the project gets more complex,
but planning cost should never exceed build cost for any single feature.

Est. saving: 20-40% reduction on planning session costs with
disciplined context management.

---

## Quick reference: expected costs by project size

Use these as sanity checks. If actuals are significantly higher,
investigate which pattern is responsible.

| Project size | Phases | Expected total cost (Sonnet) |
|-------------|--------|------------------------------|
| Small (2-4 weeks, 1 dev) | 2 | $8-20 |
| Medium (6-10 weeks, 2 devs) | 3 | $25-60 |
| Large (3-6 months, team) | 4+ | $80-200 |
| Agency client project (6-12 weeks) | 3 | $30-80 |

If you're above these ranges by >50% → run `cost:` and check for
CP-01 (context bloat) and CP-03 (unstructured output) first.
These two patterns account for 70%+ of unexpected cost overruns.

---

## CP-07 — Environment debugging waste

**Signal:**
- Session starts with shell error, startup failure, or config problem
- Multiple Bash tool calls early in session with no Edit/Write output
- Session ends with config fix rather than feature progress
- High command failure count (108+ across a project is a red flag)

**Common culprits:**
- node_modules missing or stale (package.json changed)
- Tailwind v3/v4 syntax mismatch
- dotenv loaded after process.env usage
- Vite HMR WebSocket not configured
- husky hooks not executable
- Nested .git directory

**Root cause:** Environment not checked at session start. Same failures
rediscovered fresh each session because nothing verifies state upfront.

**Fix:**
- Install vibe-doctor and run at session start
- Add PostToolUse hook for lint+typecheck after edits
- One-time fix of each recurring env issue — log in DECISIONS.md
  so it's never rediscovered

**Est. saving:** 15-30 minutes per affected session.
High-frequency projects may see $5-20 in wasted diagnostic tokens per week.

---

## CP-08 — Over-investigation overhead

**Signal:**
- High Read tool count with no Edit/Write output in first 10 messages
- Agent reads 5+ files for a request under 10 words
- Session spent debugging "working code" (data reset misread as bug)
- Agent investigates state/data operations as if they were code bugs

**Common culprits:**
- Ambiguous short requests ("reset", "clear", "fix")
- Agent defaulting to code investigation before confirming intent
- Missing intent-clarification rule in CLAUDE.md

**Root cause:** Agent reads files to understand context before confirming
what the user actually wants. For state operations and data resets,
this is expensive and unnecessary.

**Fix:**
Add to CLAUDE.md:
```
## Investigation discipline
For requests under 10 words: restate intent in one sentence before
reading any files. Data/state operations (reset, clear, seed, refresh)
are not code bugs — do not investigate code. Confirm the actual request
before opening any file.
```

**Est. saving:** 500-2,000 tokens per over-investigation event.
At ~10 events per project, CP-08 costs $0.50-3.00 in avoidable reads.

---

## Updated quick reference

| Pattern | Typical waste | Fix |
|---------|-------------|-----|
| CP-01 | 40-60% context bloat | Graph slicing, CODEBASE.md pruning |
| CP-02 | 20-40% repeated reads | Session discipline, SPEC_INDEX |
| CP-03 | 3-5x output tokens | JSON output format |
| CP-04 | N× parallel cost | Graph context slicing per subagent |
| CP-05 | 20-30% cache misses | Stable CLAUDE.md, session discipline |
| CP-06 | Planning > build cost | Time-box planning phases |
| CP-07 | 15-30 min/session | vibe-doctor at session start |
| CP-08 | 500-2000 tokens/event | Intent-confirm rule in CLAUDE.md |
