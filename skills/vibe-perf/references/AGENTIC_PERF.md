# AGENTIC_PERF.md

Read this file in full during Step 3 of vibe-perf before auditing agent files.
Contains patterns, anti-patterns, and measurement approaches for LLM-based systems.

---

## Token cost model

Token costs are not just monetary — they drive latency directly.
More tokens in = longer TTFT (time to first token).
More tokens out = longer total generation time.

**Rough latency impact (Claude Sonnet, typical):**
- 1000 input tokens ≈ +50ms latency
- 1000 output tokens ≈ +200ms latency
- Each additional agent hop ≈ +500ms–2s end-to-end

At 5 agents each with 4000-token contexts: ~100s minimum theoretical latency
just from token processing, before any tool calls or external requests.

Token efficiency is the single highest-leverage performance lever in agentic systems.

---

## Anti-pattern catalogue

### AP-01 — Full history injection
**What it looks like:**
```python
messages = conversation_history + [{"role": "user", "content": task}]
response = llm.invoke(messages)
```
**Why it's slow:** History grows unboundedly. Call N has N× the context of call 1.
**Fix:** Pass only the task spec + relevant prior outputs. Never the full history.
**Estimated saving:** 40–80% token reduction on calls 3+.

---

### AP-02 — Fat state serialisation
**What it looks like:**
```python
prompt = f"Here is the full system state: {json.dumps(state)}\nNow do: {task}"
```
**Why it's slow:** State objects contain everything — including data the sub-agent
doesn't need (brand DNA sent to the DB writer, competitor list sent to the creator).
**Fix:** Pass only the state slice relevant to this agent's task.
**Estimated saving:** 30–60% depending on state size.

---

### AP-03 — Unstructured output where JSON would do
**What it looks like:**
```python
prompt = "Analyse these competitors and tell me what gaps you see."
# Agent returns 800 words of prose
# Next agent re-reads and re-parses the prose
```
**Why it's slow:** Prose is verbose. The next agent must re-interpret it.
Errors compound across hops.
**Fix:** Use structured output with JSON schema. Compact, parseable, reliable.
```python
response_format = {"type": "json_object"}
# Schema: {"gaps": [{"angle": str, "rationale": str, "priority": int}]}
```
**Estimated saving:** 40–70% output token reduction. Better downstream reliability.

---

### AP-04 — Sequential calls with no dependency
**What it looks like:**
```python
brand_dna = await guardian_agent(url)
competitors = await scout_agent(brand_dna)  # doesn't use brand_dna yet
content_map = await analyst_agent(competitors)
```
Wait — does Scout actually need brand_dna to find competitors?
If Scout only needs the industry (one field), it can run earlier.
**Fix:** Map true data dependencies. Parallelise independent calls with `asyncio.gather`.
**Estimated saving:** Latency reduction proportional to parallelised call count.

---

### AP-05 — No retry backoff
**What it looks like:**
```python
for attempt in range(3):
    try:
        result = await llm.invoke(messages)
        break
    except RateLimitError:
        continue  # immediately retries
```
**Why it's bad:** Hammers the API. Triggers more rate limits. Cascading failure.
**Fix:**
```python
import asyncio
for attempt in range(3):
    try:
        result = await llm.invoke(messages)
        break
    except RateLimitError:
        await asyncio.sleep(2 ** attempt)  # 1s, 2s, 4s
```

---

### AP-06 — No call timeout
**What it looks like:**
```python
result = await llm.invoke(messages)  # no timeout
```
**Why it's bad:** A hanging LLM call blocks the entire pipeline indefinitely.
**Fix:**
```python
import asyncio
result = await asyncio.wait_for(llm.invoke(messages), timeout=30.0)
```
Recommended timeouts: sub-agents 30s, orchestrator calls 60s, E2E pipeline 300s.

---

### AP-07 — Unbounded verification loop
**What it looks like:**
```python
while not verified:
    draft = await creator_agent(task)
    verified = await verifier_agent(draft)
```
**Why it's bad:** Could loop forever. Cost multiplies with each iteration.
**Fix:**
```python
MAX_ATTEMPTS = 2
for attempt in range(MAX_ATTEMPTS):
    draft = await creator_agent(task, feedback=last_feedback)
    verdict = await verifier_agent(draft)
    if verdict.passed:
        break
    last_feedback = verdict.fix_instructions
else:
    # escalate to human
    await hitl_checkpoint(draft, verdict)
```

---

### AP-08 — Redundant data fetching
**What it looks like:**
```python
# GuardianAgent fetches the website
brand_dna = await guardian_agent(url)

# ScoutAgent also fetches the website to get the industry
scout_result = await scout_agent(url)  # re-fetches what Guardian already got
```
**Fix:** Pass extracted data between agents. Scout receives `brand_dna.industry`,
not the raw URL. Orchestrator owns the data flow — no agent fetches what another
already extracted.

---

## Measurement approach

For agentic audits without instrumentation in place, estimate from code:

1. Count tokens in each agent's system prompt using:
   ```python
   import tiktoken
   enc = tiktoken.encoding_for_model("gpt-4")
   token_count = len(enc.encode(system_prompt))
   ```

2. Trace data flow through the orchestrator to find sequential vs parallelisable calls.

3. Check for the anti-patterns above — each confirmed AP maps to a finding severity:
   - AP-01, AP-02, AP-07: P1 (high impact)
   - AP-03, AP-04: P1 (medium-high impact)
   - AP-05, AP-06: P1 (reliability + cost)
   - AP-08: P2 (efficiency)

---

## Safe fixes for agentic layer

All of the following are Category A (safe to auto-write):

| Fix | What to write | Where |
|-----|--------------|-------|
| Trim system prompt | Remove boilerplate, examples, redundant instructions | Agent file |
| Structured output | Add `response_format={"type":"json_object"}` + schema comment | Agent file |
| State slicing | Extract only needed keys before passing to sub-agent | Orchestrator |
| Retry backoff | Replace bare retry with exponential backoff | Agent file |
| Call timeout | Wrap `llm.invoke` with `asyncio.wait_for` | Agent file |
| Loop cap | Add `MAX_ATTEMPTS = 2` guard to verification loops | Orchestrator |

Category B (need approval):
- Restructuring parallel dispatch (changes execution order — test impact)
- Changing token budget on a verifier (affects pass/fail threshold)
