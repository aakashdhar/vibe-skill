---
name: vibe-agent
description: >
  Standalone agentic architecture skill. Designs complete multi-agent AI systems
  from scratch — no other vibe-* skills required. Deep knowledge of LangGraph,
  LangChain, CrewAI, AutoGen, Vercel AI SDK, and custom implementations.
  Produces AGENT_ARCH.md covering pattern selection, agent roles, tool mapping,
  state design, HITL checkpoints, VerifierAgent rubrics, implementation order,
  stack recommendations, and boilerplate folder structure. Generates both an
  interactive inline topology diagram and an exportable static SVG.
  Triggers on "agent:" prefix, "design an agent system", "I want to build an agent",
  "multi-agent pipeline", "orchestrator and sub-agents", "agentic workflow",
  "which agent framework should I use", "how do I structure my agents",
  "build a workflow with AI agents", "human in the loop", "LangGraph architecture".
  Always use when designing any system involving AI agents — standalone, no dependencies.
---

# Vibe Agent — Standalone Agentic Architecture Skill

Designs complete multi-agent AI systems from first principles.
No other skills required. No BRIEF.md needed. Works anywhere.

Produces AGENT_ARCH.md — a complete implementation blueprint —
and two topology diagrams: interactive (inline) and static (exportable).

**No application code. The only files this skill writes are:** `AGENT_ARCH.md` and
`agent-architecture.svg` at the project root, what vibe-spec-review writes when it runs
(its records under `vibe/goldfish/` and `vibe/spec-reviews/`, accepted fixes to the
documents it reviews (AGENT_ARCH.md, and BRIEF.md when Step 0 reviews it),
`vibe/DECISIONS.md`), the approval entry in `vibe/DECISIONS.md`, and
`vibe/.run_state.json` on a stop.

**The order:** gather facts and settle choices (Steps 1–11) → write AGENT_ARCH.md (Step 12)
→ independent review (Step 13) → diagrams from the reviewed text (Step 14) → the
person approves the reviewed design (Step 15) → architect:. Nothing is approved before
the review, and nothing derived is built from an unreviewed draft.

> **Autonomous / headless mode.** At startup resolve the settings with
> `python3 ~/.claude/skills/vibe-mode/scripts/vibe_state.py mode` (`mode --run` when the
> caller says this skill was entered from `vibe-mode: run`). If `vibe_mode` is
> `autonomous`, every "wait", "ask", "confirm" and approval step in this skill follows
> vibe-mode's `references/HEADLESS.md` §2 instead: take the recommended option, accept a draft
> only as §2.2 allows (after its independent goldfish review where one runs), log each choice to `vibe/DECISIONS.md`, never ask the
> user, and stop — writing `vibe/.run_state.json` — only when a person is genuinely required.

---

## What makes a great agentic architecture

Before asking any questions, understand this:

Most agentic systems fail not because of bad code — but because of bad design.
Agents with unclear responsibilities. State shared without ownership.
Verification bolted on as an afterthought. Humans inserted too late to matter.

This skill fixes that by designing the system before implementation begins.
Twenty minutes of architecture here prevents weeks of structural refactoring.

The five decisions that determine whether an agentic system works:

1. **Pattern** — the right structural pattern for the problem
2. **Roles** — each agent has exactly one job
3. **State** — one writer per piece of state, always
4. **Verification** — every agent's output is checked before it proceeds
5. **HITL** — humans placed where their judgment genuinely adds value

---

## Step 0 — Context gathering

Check for existing context:
```bash
ls BRIEF.md AGENT_ARCH.md 2>/dev/null
```

**If AGENT_ARCH.md already exists:**
> "An AGENT_ARCH.md already exists. Do you want to update it or redesign from scratch?"
Wait for answer. On "redesign from scratch", the old review is archived in Step 12, right
before the new document is written.

**If BRIEF.md exists:** check its review first:
```bash
python3 ~/.claude/skills/vibe-goldfish/scripts/goldfish.py status brief
```
Exit 0 means the brief's review converged on its current text. Anything else (2, 3, or a
"no goldfish review" error) means it was never reviewed, or changed since. Manual: say so
in one line and offer to run `spec-review:` on BRIEF.md now *(recommended)* or continue.
Autonomous: run vibe-spec-review on BRIEF.md (preset `brief`) first, and stop with it if
it stops.

Then read it fully. Extract problem, users, constraints, integrations.
Skip any questions already answered. Surface gaps only.

**If neither exists:** Run Steps 1–2 fully.

---

## Step 1 — Understand the system

Ask all at once. Do not ask one by one.

> **Tell me about the system you're building:**
>
> 1. What is the core task this agent system accomplishes?
>    Be specific. "Help users" is not enough.
>    "Draft, review, and send brand-aligned articles based on competitor analysis" is.
>
> 2. What triggers it?
>    (User message · scheduled job · webhook · another system · event)
>
> 3. What does success look like?
>    What is the final output or action when the system works correctly?
>
> 4. What external data, APIs, or services does it need to touch?
>
> 5. Are there steps where a human must approve before continuing?
>    If yes — which steps? What would they approve?
>
> 6. What happens if the system produces wrong output?
>    (Just annoying · costs money · irreversible · embarrassing · dangerous)

Synthesise answers. Confirm before proceeding.

The confirmations in Steps 1–5 gather facts and settle working choices (framework,
pattern, roster). They are not the sign-off: the person approves the whole design once,
on the reviewed AGENT_ARCH.md, in Step 15.

---

## Step 2 — Complexity and constraints

> **Scope and constraints:**
>
> 1. How many distinct task types does this system handle?
>    (1–3 = simple · 4–10 = medium · 10+ = complex)
>
> 2. Latency requirement?
>    (Real-time <2s · Interactive <30s · Async minutes/hours ok)
>
> 3. Stack preference?
>    Python / TypeScript / No preference
>
> 4. Any existing infrastructure to work with?
>    (Existing DB · auth system · APIs already in use)
>
> 5. v1 proof-of-concept or production-grade from day one?

---

## Step 3 — Framework selection

> 🧠 **Effort:** framework and pattern choice shapes the entire build — reason at
> high/xhigh effort with adaptive thinking and compare options against the actual
> requirements before deciding, rather than defaulting to the most familiar one.

Read `references/FRAMEWORKS.md` before this step.

Based on Steps 1–2, recommend one framework with full reasoning.

Present as:

> **Recommended framework: [Framework Name]**
>
> **Why this fits your system:**
> [3-4 sentences grounded in their specific requirements — complexity, latency, cyclic vs linear, team familiarity]
>
> **What this gives you:**
> [Concrete capabilities — state management, tool calling, human-in-the-loop support, streaming]
>
> **Trade-offs:**
> [What this framework gives up vs alternatives — be honest]
>
> **Runner-up: [Framework]** — would work, but loses because [specific reason for this system]

**Framework selection rules:**
- Anthropic-only, want model-native control (thinking/effort/caching/subagents):
  coding/filesystem agent → **Claude Agent SDK**; loop over your own tools →
  **Tool Runner**; hosted/scheduled/stateful with no loop code → **Managed Agents**
- Cyclic workflows, complex state, self-correction loops → **LangGraph**
- Linear chains, simple tool use, fast to prototype → **LangChain**
- Role-based teams, natural language task delegation → **CrewAI**
- Conversational back-and-forth between agents → **AutoGen**
- TypeScript stack, Next.js, Vercel deployment → **Vercel AI SDK**
- Maximum control, no framework overhead, custom needs → **Custom implementation**
- Need provider portability (Claude + others) → LangGraph / Custom, not the
  Anthropic-native options

Wait for the person's choice before proceeding (a working choice, not the sign-off).

---

## Step 4 — Pattern selection

Read `references/PATTERNS.md` before this step.

Select one primary pattern. Present recommendation with reasoning:

> **Recommended pattern: [Pattern Name]**
>
> **Why:** [2–3 sentences grounded in their specific problem]
>
> **How this maps to their system:** [Concrete description — what plays what role]
>
> **Trade-offs accepted:** [What this pattern gives up]
>
> **Alternative considered:** [Runner-up and why it loses here]

**Pattern selection rules:**
- Linear, deterministic steps, no branching → **Sequential Pipeline**
- One complex task, needs tools, variable path → **Single Agent + Tools**
- Multiple independent task types in parallel → **Parallel Specialists**
- Complex coordination, planning, delegation → **Orchestrator + Sub-agents**
- Any irreversible actions or external comms → add **HITL layer**
- Never recommend Orchestrator + Sub-agents when Single Agent + Tools suffices.
  Complexity must be earned.

Wait for the person's choice (a working choice, not the sign-off).

---

## Step 5 — Agent role definition

For each agent in the system:

> **Agent roster:**
>
> | Agent | Responsibility | Inputs | Outputs | Autonomy |
> |-------|---------------|--------|---------|---------|
> | [Name] | [One sentence — what it does and nothing else] | [From: user/orchestrator/agent X] | [Produces: type + shape] | [Decides: X · Escalates: Y] |

**Role definition rules:**
- One primary responsibility per agent. "And also" = split the agent.
- Orchestrator only routes and coordinates — never does domain work.
- Name agents by what they do: `ResearchAgent` not `Agent2`.
- Human-in-the-loop modelled as an agent with infinite latency and final authority.

Present roster. Ask: "Does each agent have a single clear responsibility? Any overlap or gap?"

Wait for the answer (a working choice, not the sign-off).

---

## Step 6 — VerifierAgent design

Every agent in the system gets a VerifierAgent. No exceptions.

For each agent, define its verifier:

> **VerifierAgent rubrics:**
>
> | Verifier | Checks agent | Contract | Spec compliance | Quality bar | Consistency |
> |----------|-------------|---------|----------------|------------|-------------|
> | [AgentNameVerifier] | [AgentName] | [exact output schema] | [acceptance criteria] | [quality threshold] | [prior outputs to align with] |

**Verdict format — always structured:**
```
VERDICT: PASS | FAIL
CHECKS:
  Contract:    pass | fail — [reason]
  Spec:        pass | fail — [reason]
  Quality:     pass | fail — [reason]
  Consistency: pass | fail — [reason]
FIX INSTRUCTIONS: [specific, actionable — only on FAIL]
```

**Retry logic baked into every pattern:**
```
Agent output → Verifier checks
  PASS → proceed
  FAIL (attempt 1) → send output + fix instructions back to Agent
  Agent retries
  PASS → proceed
  FAIL (attempt 2) → escalate to HITL
```

Shared vs dedicated verifiers: if two agents have near-identical rubrics → one shared verifier.

---

## Step 7 — Tool and MCP mapping

For each agent, map every tool it needs:

> | Agent | Tool | Type | Purpose | Risk level |
> |-------|------|------|---------|-----------|
> | [Name] | [tool] | read/write/compute/MCP/handoff | [why this agent, not another] | [low/medium/high] |

**Tool types:**
- **Read** — web search, document retrieval, DB query, API GET
- **Write** — send email, create ticket, write file, API POST/PUT
- **Compute** — code execution, data transformation, calculations
- **MCP** — Jira, Slack, Google Drive, Salesforce, Notion, etc.
- **Handoff** — passing control to another agent

**Flag immediately:**
- Any write tool assigned to more than one agent → coordination risk
- Any write tool that produces irreversible output → HITL required before use
- Any tool requiring credentials → note in implementation section

---

## Step 8 — State and memory design

> **State architecture:**
>
> **Session state** (lives for one pipeline run):
> - What: [list of state keys]
> - Owner: [which agent writes each key]
> - Format: [dict / typed schema / message list]
>
> **Cross-run memory** (persists between invocations):
> - Storage: [none / SQLite / Postgres / vector DB / Redis]
> - Schema: [key fields]
> - Use case: [what it remembers and why]
>
> **State ownership table:**
> | Key | Owner (writes) | Readers | Format |
> |-----|---------------|---------|--------|
> | [key] | [agent] | [agents] | [type] |

**State design rules:**
- One agent owns each state key. Others read. Only the owner writes.
- Prefer message-passing over shared mutable stores.
- HITL checkpoints are state transitions — system pauses at known state, human acts, resumes.
- If cross-run memory uses a DB: define the schema now. Retrofitting mid-build is expensive.

Flag any multi-writer state as a race condition risk.

---

## Step 9 — Human-in-the-loop design

**Non-negotiable HITL triggers:**
- Agent sends external communications (email, Slack, SMS, social)
- Agent executes financial transactions
- Agent deletes or permanently modifies data
- Agent operates in regulated domain (legal, medical, financial)
- Agent output will be seen by external parties before human review

For each checkpoint:

> | # | Location | What human sees | Actions available | Timeout behaviour |
> |---|---------|----------------|-----------------|------------------|
> | 1 | After [step] | [context shown — enough to decide] | Approve / Reject / Edit / Redirect | [escalate / cancel / flag and continue] |

**HITL interface requirements:**
- Human must see enough context to make a good decision — not just "approve Y/N?"
- Actions must be unambiguous
- Timeout must be handled — never leave the system blocked indefinitely
- State at checkpoint must be durable — if human takes 2 hours, state is not lost

---

## Step 10 — Implementation plan

Read `references/IMPLEMENTATION_GUIDE.md` before this step.

Produce a concrete implementation plan:

### Framework setup

For the recommended framework, provide exact setup:

**LangGraph:**
```python
# Core dependencies
pip install langgraph langchain-anthropic

# State definition
from typing import TypedDict, Annotated
from langgraph.graph import StateGraph, END
import operator

class AgentState(TypedDict):
    # [state keys from Step 8]
    messages: Annotated[list, operator.add]
    [key]: [type]

# Graph construction pattern
graph = StateGraph(AgentState)
graph.add_node("[agent_name]", [agent_function])
graph.add_edge("[agent_a]", "[agent_b]")
graph.set_entry_point("[first_agent]")
```

**CrewAI:**
```python
pip install crewai crewai-tools

from crewai import Agent, Task, Crew, Process

[agent_name] = Agent(
    role="[role]",
    goal="[goal]",
    backstory="[context]",
    tools=[],
    verbose=True
)
```

**Vercel AI SDK:**
```typescript
npm install ai @ai-sdk/anthropic

import { generateText, tool } from 'ai'
import { anthropic } from '@ai-sdk/anthropic'
```

### Implementation order

Tasks in this exact sequence:

```
Phase 1 — Foundation
  [ ] Set up project structure (see boilerplate below)
  [ ] Install framework dependencies
  [ ] Define state schema
  [ ] Implement base agent class / shared utilities
  [ ] Create mock tool responses for testing

Phase 2 — Agents (in dependency order)
  [For each agent in dependency order:]
  [ ] Implement [AgentName] — [one line description]
  [ ] Write [AgentName]Verifier
  [ ] Unit test: agent produces correct output shape
  [ ] Integration test: verifier correctly passes/fails

Phase 3 — Orchestration
  [ ] Implement orchestrator / graph routing
  [ ] Wire agent-to-agent handoffs
  [ ] Implement HITL checkpoints
  [ ] Implement retry logic (retry once → escalate)
  [ ] End-to-end test: full pipeline with mock data

Phase 4 — Production hardening
  [ ] Replace mock tools with real implementations
  [ ] Add timeout handling on all agent calls
  [ ] Add exponential backoff on LLM failures
  [ ] Add state persistence (if cross-run memory needed)
  [ ] Load test: concurrent pipeline runs
```

### Boilerplate folder structure

```
[project-name]/
├── agents/
│   ├── __init__.py
│   ├── base.py              ← shared agent utilities, retry logic
│   ├── [agent_name].py      ← one file per agent
│   └── verifiers/
│       ├── __init__.py
│       └── [agent_name]_verifier.py
├── tools/
│   ├── __init__.py
│   └── [tool_name].py       ← one file per tool/MCP integration
├── state/
│   ├── __init__.py
│   └── schema.py            ← TypedDict / Pydantic state definitions
├── graph/
│   ├── __init__.py
│   ├── nodes.py             ← node functions for LangGraph
│   ├── edges.py             ← routing logic, conditional edges
│   └── pipeline.py          ← assembled graph / crew / pipeline
├── hitl/
│   ├── __init__.py
│   └── checkpoints.py       ← HITL pause/resume logic
├── memory/
│   ├── __init__.py
│   └── store.py             ← cross-run persistence (if needed)
├── tests/
│   ├── test_agents.py
│   ├── test_verifiers.py
│   └── test_pipeline.py
├── config.py                ← model names, timeouts, thresholds
├── main.py                  ← entry point
└── requirements.txt
```

---

## Step 11 — Synthesise and check

> **Agentic architecture summary — [System Name]:**
>
> **Framework:** [chosen] — [one sentence why]
> **Pattern:** [chosen]
> **Agents:** [N] — [name list]
> **Verifiers:** [N] — [shared/dedicated breakdown]
> **Tools:** [N] across [N] agents ([write tools flagged])
> **State:** [session / cross-run / both]
> **HITL checkpoints:** [N] — [where in the flow]
> **Implementation phases:** 4 · Est. [N] days
>
> Did I get anything wrong from your answers? Anything to adjust before I write
> AGENT_ARCH.md? (This is a check of the facts, not the sign-off: you approve the design
> after the independent review.)

Wait for the answer. Note every adjustment: Step 12 writes them in.

---

## Step 12 — Write AGENT_ARCH.md

**Redesign from scratch only** (the person chose it in Step 0): set the old review aside
first, so findings settled on the old design can't settle findings on the new one:
```bash
python3 ~/.claude/skills/vibe-goldfish/scripts/goldfish.py archive agent-arch
```

Read `references/AGENT_ARCH_TEMPLATE.md` for the full format.

Fill every section from the decisions in Steps 1–10 and every adjustment the person made
in Step 11. Where an adjustment changes a Step 1–10 decision, the adjustment wins.
Save as `AGENT_ARCH.md` at project root.

Every section must be grounded in decisions made — no placeholders.

Write nothing else yet. The diagrams are built from the reviewed document (Step 14).

---

## Step 13 — Hand off to spec-review

Announce:
> "AGENT_ARCH.md written. Running an independent review of the agent design..."

Invoke `vibe-spec-review` with:
- Trigger source: `agent` (Trigger 2, preset `agent-arch`)
- Scope: AGENT_ARCH.md (BRIEF.md, if it exists, is read as a related file)

**If spec-review stopped the run** (`python3 ~/.claude/skills/vibe-mode/scripts/vibe_state.py run-state show`
says needs_human from spec review), **stop here too**: end the session, don't continue,
don't report the step as done. In manual mode, a 🔴 verdict means follow spec-review
Step 3 (more rounds, rework, or the person accepts). Never fix findings outside vibe-goldfish.

After spec-review completes without stopping, continue to Step 14.

---

## Step 14 — Generate topology diagrams

Generate **both** diagrams now, from AGENT_ARCH.md as the review left it (fixes
included). They are derived from the reviewed text, never from the draft. If AGENT_ARCH.md
changes again (an edit at Step 15, then a new review), generate both again.

### Diagram 1 — Interactive inline diagram

Use the `show_widget` visualizer tool.

The diagram must show:
- **Trigger** — entry point (coral pill, top)
- **Orchestrator** — if present (purple, large, below trigger)
- **Agents** — specialist nodes (teal, medium)
- **Verifiers** — between each agent and its output (green, smaller)
- **Retry arrows** — dashed from verifier back to agent (labelled "retry + fix")
- **Escalation arrows** — solid from verifier to HITL on second fail
- **HITL checkpoints** — amber, dashed border, full width
- **Tools** — small gray pills connected to their agent by dashed lines
- **State store** — green rounded rect on the side if cross-run memory exists
- **Output** — coral pill at bottom

Every node is clickable — `sendPrompt('Tell me more about [NodeName]')`.

**Visual hierarchy:**
- Flow direction: top to bottom
- Orchestrator centred
- Sub-agents spread horizontally
- Verifiers inline between agent and next step
- Tools as satellites — never in the main flow

### Diagram 2 — Static exportable SVG

After the interactive diagram, generate a clean static SVG version.

Same topology, same colour coding.
No JavaScript. No event handlers. No interactive elements.
Clean enough to paste into a Notion page, Figma, or a slide deck.

Write the SVG to `agent-architecture.svg` at the project root and tell the user the
path (e.g. "Static diagram saved to agent-architecture.svg — open it or drop it into
a doc/slide"). Use SendUserFile to surface it if that tool is available; otherwise
just state the path. Do not reference any `present_files` tool — it does not exist.

---

## Step 15 — Approve the reviewed design and tell the user

**Check the review is current:**
```bash
python3 ~/.claude/skills/vibe-goldfish/scripts/goldfish.py status agent-arch
```
Exit 0 means the review converged on AGENT_ARCH.md as it is now. Anything else: manual,
tell the person plainly and offer to run `spec-review:` on AGENT_ARCH.md now; autonomous,
go back to Step 13. Never hand off a document whose status is not 0. The only exceptions are the person's own choices in spec-review: continuing without a
review (⚠️ SPEC NOT REVIEWED) or continuing anyway on a 🔴 (status stays 3). Then ask for
approval as below, name that choice in the DECISIONS entry and on the card, and hand off.

**Manual mode: the person approves the reviewed text.** Show what the review changed, one
line per fix (from `vibe/goldfish/agent-arch/resolution.md`), then ask:
> "This is AGENT_ARCH.md after the independent review. Do you approve it as it is now?"

- **Approved:** append to `vibe/DECISIONS.md` (append-only: create it with its canonical
  header only if it doesn't exist, continue the `D-NNN` numbering):
  ```
  ### D-[ID]: AGENT_ARCH.md approved
  - **Type**: approval
  - **Skill / step**: vibe-agent · Step 15 (after the independent review)
  - **Approved**: AGENT_ARCH.md as reviewed · record: vibe/goldfish/agent-arch/resolution.md
  - **Approved by**: human
  ```
- **The person wants changes:** make them in AGENT_ARCH.md. The edit re-opens the review
  by itself, so go back to Step 13 (review), then Step 14 (diagrams again), then ask again
  here. Never hand off an edited document without that review.

**Autonomous mode:** the converged review is the acceptance (HEADLESS §2.2). Don't ask,
and don't add a self-approval.

Then print:

```
✅ Agentic architecture complete — [System Name]

AGENT_ARCH.md written and independently reviewed — [N] sections
Framework:    [framework] — [one line why]
Pattern:      [pattern]
Agents:       [N] ([names])
Verifiers:    [N] ([shared/dedicated])
Tools:        [N] ([write tools: N])
HITL gates:   [N]
Impl phases:  4 phases · est. [N] days
Review:       [✅ / ⚠️ verdict] · [N] fixes · vibe/goldfish/agent-arch/resolution.md
Approved by:  [human / review converged (autonomous)]

DIAGRAMS (from the reviewed document)
  Interactive: rendered above (clickable)
  Static SVG:  agent-architecture.svg (download below)

NEXT STEPS
  1. architect: reads AGENT_ARCH.md and carries the framework, agents, state, tools,
     HITL checkpoints and folder structure into ARCHITECTURE.md (reviewed in turn)
  2. new: turns the implementation order into SPEC.md, PLAN.md and tasks, reviewed and
     signed off at the spec gate
  3. The build starts after the spec gate, not before. Wire the orchestrator last,
     after all agents are tested individually.

The AGENT_ARCH.md is self-contained. Share it with your team.
It has everything needed to implement this system from scratch.
```

---

## Conversation principles

**Framework recommendation is opinionated.** Don't list all six and ask the user to choose.
Recommend one. Explain why it fits their specific system. Let them override.

**Pattern recommendation is opinionated.** Same principle.
Complexity must be earned — don't recommend Orchestrator + Sub-agents when
Single Agent + Tools would do the job.

**Roles must be singular.** Push back on "and also."
An agent that does two things is two agents that haven't been separated yet.

**Verification is non-negotiable.** Every agent gets a verifier.
"We'll add verification later" means it never happens.

**HITL placement is a design decision, not a checkbox.**
"Add a human checkpoint" is meaningless. "Human sees the competitor list
and confirms before content strategy begins" is a design decision.

**Be honest about trade-offs.** Every framework choice and pattern choice
gives something up. Surface what's lost, not just what's gained.

**The diagram is part of the deliverable.** Not an afterthought.
A well-designed agentic system should be explainable in one diagram.
If the diagram is too complex to read, the system is too complex to build.
