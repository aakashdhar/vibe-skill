# PATTERNS.md

Read in full during Step 4 of vibe-agent before recommending a pattern.
Four primary patterns plus HITL and VerifierAgent layers.

---

## Pattern 1 — Sequential Pipeline

**Structure:**
```
Input → Agent A → VerifierA → Agent B → VerifierB → Agent C → VerifierC → Output
```

**When to use:**
- Tasks are inherently linear (step 2 always follows step 1)
- Each step transforms the output of the previous step
- No conditional branching needed
- Low to medium complexity, deterministic flow

**Examples:**
- Document ingestion → extraction → formatting → storage
- URL → Brand DNA → competitor list → content gaps → article draft
- Raw transcript → digest → action items → Jira tickets

**Strengths:** Simple to reason about, easy to debug, predictable cost, easy to test
**Weaknesses:** No parallelism, a failure in step N blocks everything downstream

**LangGraph implementation hint:**
```python
graph.add_edge("agent_a", "verifier_a")
graph.add_conditional_edges("verifier_a", route_verifier_a,
    {"pass": "agent_b", "fail": "agent_a", "escalate": "hitl"})
graph.add_edge("agent_b", "verifier_b")
# ...
```

---

## Pattern 2 — Single Agent + Tools

**Structure:**
```
Input → Agent (decides tool calls) → VerifierAgent → Output
         ↕ tools ↕
    [tool1, tool2, tool3]
```

**When to use:**
- One primary task type, but path to completion varies
- Agent needs to retrieve, compute, or act — but no specialised sub-expertise
- Real-time or low-latency requirement (fewer round-trips)
- v1 / proof of concept

**Examples:**
- Customer support (search KB, check order, create ticket, send email)
- Research assistant (web search, summarise, cite, draft)
- Code assistant (read files, write code, run tests)

**Strengths:** Simple architecture, easy to debug, low overhead, fast to build
**Weaknesses:** Context window pressure with many tools, harder to specialise at scale

**Tool selection rules:**
- Include a "clarify" tool to let the agent ask for more info before acting
- Separate read-only from write tools — write tools should confirm before executing
- Cap at 8-10 tools — more than that degrades tool selection quality

---

## Pattern 3 — Parallel Specialists

**Structure:**
```
Input → Router → [Specialist A → VerifierA | Specialist B → VerifierB | Specialist C → VerifierC] → Aggregator → Output
```

**When to use:**
- Multiple distinct task types, each needing different expertise
- Tasks can run independently without needing each other's output
- Different domains that shouldn't share context
- Higher throughput needed

**Examples:**
- Document processing: legal + financial + technical specialists in parallel
- Content pipeline: researcher + writer + SEO specialist (aggregated)
- Multi-market analysis: each market analysed independently

**Strengths:** Specialisation, parallelism, clean separation of concerns
**Weaknesses:** Requires aggregation step, routing errors send tasks to wrong specialist

**Implementation notes:**
- Router must have clear, unambiguous classification rules
- Specialists are ignorant of each other — share nothing except the original input
- Aggregator must handle partial failures (some specialists succeeded, some failed)
- All specialists need a shared output schema — define it in the state

---

## Pattern 4 — Orchestrator + Sub-agents

**Structure:**
```
Input → Orchestrator (plans + delegates)
              ↓ tasks
    ┌─────────┼─────────┐
SubAgent A  SubAgent B  SubAgent C
VerifierA   VerifierB   VerifierC
    └─────────┼─────────┘
              ↓ verified results
         Orchestrator (synthesises)
              ↓
           Output
```

**When to use:**
- Complex task requiring coordination of multiple specialised capabilities
- The path to completion is not known upfront — requires planning
- Sub-tasks have dependencies on each other's outputs
- Different sub-agents genuinely need different tools or expertise
- You've outgrown Single Agent + Tools

**Examples:**
- Software engineering agent (planner → code writer → test runner → reviewer)
- Research pipeline (query planner → search agents → synthesis → citation checker)
- Brandbot (guardian → scout → analyst → strategist → creator)

**Strengths:** Handles genuine complexity, specialisation, scalable
**Weaknesses:** High complexity, harder to debug, cost multiplies with sub-agent calls

**Orchestrator rules (only these responsibilities):**
- Decompose the goal into sub-tasks
- Assign sub-tasks to sub-agents
- Track completion and handle failures
- Synthesise verified results into final output
- The orchestrator NEVER does domain work itself

**Sub-agent rules:**
- Execute exactly one task type
- Return a structured result matching the state schema
- Escalate if they cannot complete their task (don't guess)

---

## HITL Layer (applied on top of any pattern)

**Checkpoint types:**

| Type | Trigger | Human action |
|------|---------|-------------|
| Approval gate | Before irreversible action | Approve / reject |
| Review gate | After draft output | Edit / approve / reject |
| Escalation gate | Verifier fails twice | Redirect / clarify / abort |
| Exception gate | Error or edge case | Handle manually / retry |

**When HITL is non-negotiable:**
- Agent sends external communications (email, Slack, social media)
- Agent executes financial transactions
- Agent deletes or permanently modifies data
- Agent operates in regulated domain (legal, medical, financial)
- Agent's output will be seen by external parties before human review

**Implementation pattern (LangGraph):**
```python
from langgraph.checkpoint.memory import MemorySaver

# interrupt_before pauses before node executes
# interrupt_after pauses after node executes
app = graph.compile(
    checkpointer=MemorySaver(),
    interrupt_before=["send_email_node"]
)

# Run until HITL checkpoint
state = app.invoke(input, config)
# User reviews state["draft_email"]...
# Update state with human decision
app.update_state(config, {"human_approved": True})
# Resume
final = app.invoke(None, config)
```

---

## VerifierAgent Layer (mandatory on every pattern)

Every agent in every pattern gets a VerifierAgent. No exceptions.

**Why mandatory:**
Without verification, errors propagate silently through the pipeline.
A GuardianAgent that hallucinated the wrong brand voice poisons every
downstream agent. Catching it at the source costs one retry.
Catching it at the output costs rebuilding the entire pipeline.

**Verifier responsibilities:**
1. Check output matches expected contract (schema, fields, types)
2. Check output satisfies spec acceptance criteria
3. Check output meets quality bar (completeness, accuracy, tone)
4. Check output is consistent with prior agent outputs in this run

**Verifier rules:**
- Verifier NEVER rewrites the agent's output — it only judges
- Verifier always returns structured PASS/FAIL with specific fix instructions
- Verifier has no write tools — reads only
- Keep verifier context tight: output to check + rubric + prior outputs only

**Retry and escalation loop (every pattern, every agent):**
```
Agent produces output
    ↓
VerifierAgent checks (attempt 1)
    ↓
PASS → proceed to next step
FAIL → send output + verdict + fix instructions back to Agent
    ↓
Agent retries with fix instructions (attempt 2)
    ↓
VerifierAgent checks (attempt 2)
    ↓
PASS → proceed
FAIL → escalate to HITL checkpoint
    ↓
Human sees: original task + both outputs + both verdicts
Human decides: override / redirect / abort
```

**LangGraph verifier pattern:**
```python
def verifier_node(state: State) -> State:
    output = state["agent_output"]
    rubric = state["verifier_rubric"]

    verdict = check_contract(output, rubric["schema"])
    verdict &= check_spec(output, rubric["criteria"])
    verdict &= check_quality(output, rubric["quality_bar"])
    verdict &= check_consistency(output, state["prior_outputs"])

    return {
        "verified": verdict.passed,
        "verdict": verdict,
        "attempts": state["attempts"] + 1
    }

def route_after_verifier(state: State) -> str:
    if state["verified"]:
        return "next_agent"
    elif state["attempts"] < 2:
        return "retry_agent"
    else:
        return "hitl_checkpoint"
```

---

## Pattern selection quick guide

```
Is it TypeScript?
  └─ Consider Vercel AI SDK regardless of pattern

Is the workflow cyclic (needs loops)?
  └─ LangGraph — Sequential Pipeline or Orchestrator + Sub-agents

Is it a conversational back-and-forth?
  └─ AutoGen

Does it map to a "team" with natural roles?
  └─ CrewAI — Parallel Specialists or Sequential Pipeline

One agent with multiple tools?
  └─ LangChain or Custom — Single Agent + Tools

Multiple specialists with dependencies?
  └─ LangGraph — Orchestrator + Sub-agents

Maximum simplicity?
  └─ Custom implementation — any pattern

Always add HITL if: irreversible actions, external comms, regulated domain
Always add VerifierAgents: on every agent, in every pattern, always
```
