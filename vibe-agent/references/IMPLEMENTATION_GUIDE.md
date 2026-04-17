# IMPLEMENTATION_GUIDE.md

Read during Step 10 of vibe-agent.
Provides framework-specific boilerplate, common patterns, and anti-patterns.

---

## Anti-patterns to always flag

These appear in almost every first-attempt agentic system.
Raise them as risks in AGENT_ARCH.md if the system design suggests any of them.

### AP-01 — Full history injection
Every LLM call receives the entire conversation history.
History grows unboundedly. Call N has N× the context of call 1.
**Fix:** Pass only the task spec + relevant prior outputs.

### AP-02 — Fat state serialisation
The entire state object is serialised into every agent prompt.
`f"Here is the full state: {json.dumps(state)}\nNow do: {task}"`
**Fix:** Pass only the state slice this agent needs.

### AP-03 — Unstructured output
Agent returns prose. Next agent re-parses the prose.
Errors compound across hops.
**Fix:** Structured output with JSON schema on every agent.

### AP-04 — Sequential calls with no dependency
Agent A finishes, then Agent B starts — but B doesn't need A's output yet.
**Fix:** Map true data dependencies. Parallelise independent calls.

### AP-05 — Retry without backoff
```python
for attempt in range(3):
    try: result = llm.invoke(...)
    except: continue  # immediately hammers the API
```
**Fix:** Exponential backoff: `await asyncio.sleep(2 ** attempt)`

### AP-06 — No call timeout
A hung LLM call blocks the entire pipeline indefinitely.
**Fix:** `asyncio.wait_for(llm.invoke(...), timeout=30.0)`

### AP-07 — Unbounded verification loop
`while not verified: draft = agent(); verified = verifier(draft)`
Could loop forever. Cost multiplies with each iteration.
**Fix:** `MAX_ATTEMPTS = 2` guard. Second failure → HITL.

### AP-08 — Redundant data fetching
GuardianAgent fetches the website.
ScoutAgent also fetches the website to get the industry.
**Fix:** Pass extracted data between agents. No agent fetches what another already extracted.

---

## LangGraph — production patterns

### State with message accumulation
```python
from typing import Annotated
import operator

class State(TypedDict):
    messages: Annotated[list, operator.add]  # accumulates, never overwrites
    brand_dna: dict | None
    verified: bool
    attempts: int
```

### Conditional routing after verifier
```python
def route_after_verifier(state: State) -> str:
    if state["verified"]:
        return "next_step"
    elif state["attempts"] < 2:
        return "retry_agent"
    else:
        return "hitl_checkpoint"

graph.add_conditional_edges(
    "verifier_node",
    route_after_verifier,
    {
        "next_step": "next_agent",
        "retry_agent": "agent_node",
        "hitl_checkpoint": "hitl_node"
    }
)
```

### HITL with LangGraph interrupts
```python
from langgraph.checkpoint.memory import MemorySaver

# Compile with interrupt
memory = MemorySaver()
app = graph.compile(
    checkpointer=memory,
    interrupt_before=["send_email"]  # pause before this node
)

# Run until interrupt
config = {"configurable": {"thread_id": "run-1"}}
state = app.invoke({"url": "https://example.com"}, config)

# Human reviews state["draft_email"]
print(state["draft_email"])
human_decision = input("Approve? (y/n): ")

if human_decision == "y":
    app.update_state(config, {"human_approved": True})
    final = app.invoke(None, config)  # resume
```

### Parallel sub-agents with LangGraph
```python
from langgraph.graph import START, END

# Fan out to parallel nodes
graph.add_edge(START, "agent_a")
graph.add_edge(START, "agent_b")
graph.add_edge(START, "agent_c")

# Fan in from parallel nodes
graph.add_edge("agent_a", "aggregator")
graph.add_edge("agent_b", "aggregator")
graph.add_edge("agent_c", "aggregator")
graph.add_edge("aggregator", END)
```

### Subgraph for reusable agent+verifier pairs
```python
# Build agent+verifier as a reusable subgraph
def build_verified_agent(agent_fn, verifier_fn, name: str):
    subgraph = StateGraph(State)
    subgraph.add_node(f"{name}", agent_fn)
    subgraph.add_node(f"{name}_verifier", verifier_fn)
    subgraph.add_edge(f"{name}", f"{name}_verifier")
    subgraph.add_conditional_edges(
        f"{name}_verifier",
        lambda s: "done" if s["verified"] else "retry" if s["attempts"] < 2 else "escalate",
        {"done": END, "retry": f"{name}", "escalate": "hitl"}
    )
    subgraph.set_entry_point(f"{name}")
    return subgraph.compile()
```

---

## CrewAI — production patterns

### Sequential crew with verification
```python
from crewai import Agent, Task, Crew, Process

# Each agent has a verifier task after it
guardian = Agent(role="Brand Guardian", ...)
guardian_verifier = Agent(role="Brand DNA Validator", ...)

extract_task = Task(
    description="Extract brand DNA from {url}",
    expected_output="JSON with voiceAttributes, mission, audience, clarityScore",
    agent=guardian,
    output_json=BrandDNASchema  # structured output
)

verify_task = Task(
    description="Verify the brand DNA extraction meets all criteria",
    expected_output="PASS or FAIL with specific fix instructions",
    agent=guardian_verifier,
    context=[extract_task]  # receives extract_task output
)

crew = Crew(
    agents=[guardian, guardian_verifier, scout, ...],
    tasks=[extract_task, verify_task, ...],
    process=Process.sequential
)
```

---

## Vercel AI SDK — production patterns

### Multi-step pipeline with structured output
```typescript
import { generateObject, generateText } from 'ai'
import { anthropic } from '@ai-sdk/anthropic'
import { z } from 'zod'

// Step 1: Guardian Agent — structured output
const brandDNASchema = z.object({
  voiceAttributes: z.array(z.string()),
  missionStatement: z.string(),
  targetAudience: z.string(),
  clarityScore: z.number().min(0).max(100)
})

const { object: brandDNA } = await generateObject({
  model: anthropic('claude-sonnet-4-6'),
  schema: brandDNASchema,
  prompt: `Extract brand DNA from this website: ${url}`
})

// Step 2: Verifier — checks the output
const verifierResult = await generateObject({
  model: anthropic('claude-sonnet-4-6'),
  schema: z.object({
    passed: z.boolean(),
    contractCheck: z.boolean(),
    specCheck: z.boolean(),
    qualityCheck: z.boolean(),
    fixInstructions: z.string().optional()
  }),
  prompt: `Verify this brand DNA extraction:
    ${JSON.stringify(brandDNA)}

    Criteria:
    - All required fields present (voiceAttributes, mission, audience, score)
    - clarityScore between 0-100
    - voiceAttributes has at least 2 items
    - missionStatement is at least 20 words`
})

if (!verifierResult.object.passed) {
  // Retry with fix instructions
  // ...
}
```

### Streaming with tool calls
```typescript
import { streamText, tool } from 'ai'
import { z } from 'zod'

const result = await streamText({
  model: anthropic('claude-sonnet-4-6'),
  tools: {
    searchCompetitors: tool({
      description: 'Search for competitor companies in a given industry',
      parameters: z.object({
        industry: z.string(),
        employeeRange: z.enum(['1-10', '11-50', '51-200', '201-500', '500+'])
      }),
      execute: async ({ industry, employeeRange }) => {
        return await tavilySearch(`${industry} companies ${employeeRange} employees`)
      }
    })
  },
  prompt: `Find 5 real competitors for a ${brandDNA.targetAudience} brand in ${industry}`,
  onFinish: ({ text, toolResults }) => {
    // Handle completion
  }
})

for await (const chunk of result.textStream) {
  process.stdout.write(chunk)
}
```

---

## Custom implementation — production patterns

### Async pipeline with retry
```python
import asyncio
from anthropic import AsyncAnthropic
from typing import TypedDict

client = AsyncAnthropic()

async def call_with_retry(prompt: str, schema: dict, max_attempts: int = 2):
    """LLM call with structured output and retry logic."""
    for attempt in range(max_attempts):
        try:
            response = await asyncio.wait_for(
                client.messages.create(
                    model="claude-sonnet-4-6",
                    max_tokens=1000,
                    messages=[{"role": "user", "content": prompt}]
                ),
                timeout=30.0
            )
            result = parse_structured_output(response, schema)
            if result:
                return result
        except asyncio.TimeoutError:
            if attempt == max_attempts - 1:
                raise
        except Exception as e:
            if attempt == max_attempts - 1:
                raise
        await asyncio.sleep(2 ** attempt)  # exponential backoff

async def run_verified_agent(agent_fn, verifier_fn, state: dict, max_retries: int = 1):
    """Run agent with verification and retry."""
    for attempt in range(max_retries + 1):
        output = await agent_fn(state)
        verdict = await verifier_fn(output, state)

        if verdict["passed"]:
            return output, verdict

        if attempt < max_retries:
            state["fix_instructions"] = verdict["fix_instructions"]
            continue

        # Second failure — return for HITL escalation
        return None, verdict
```

---

## Observability recommendations

Every production agentic system needs these three:

### 1. Token counting per run
```python
total_input_tokens = 0
total_output_tokens = 0

# After each LLM call:
total_input_tokens += response.usage.input_tokens
total_output_tokens += response.usage.output_tokens

# Log at end of run:
logger.info(f"Run complete: {total_input_tokens} in, {total_output_tokens} out, "
            f"est. cost: ${(total_input_tokens * 3 + total_output_tokens * 15) / 1_000_000:.4f}")
```

### 2. Verification verdict logging
```python
logger.info(f"VERIFIER: {verifier_name} | VERDICT: {verdict['passed']} | "
            f"Contract: {verdict['contract']} | Spec: {verdict['spec']} | "
            f"Quality: {verdict['quality']} | Attempt: {attempt}")
```

### 3. Stage timing
```python
import time

stage_start = time.time()
output = await agent_fn(state)
logger.info(f"STAGE: {agent_name} | DURATION: {time.time() - stage_start:.2f}s")
```
