# FRAMEWORKS.md

Read in full during Step 3 of vibe-agent before making a framework recommendation.
Deep reference on all six frameworks — capabilities, trade-offs, when to use each.

---

## Framework 1 — LangGraph

**What it is:** A graph-based orchestration framework built on LangChain.
Agents are nodes. Data flows along edges. Supports cycles — agents can loop back.

**Core concept:** StateGraph — a directed graph where state flows between nodes.
Each node is a function that receives state and returns updated state.
Conditional edges route based on state values.

**Killer feature:** Cyclic execution. Unlike linear chains, LangGraph supports
loops — an agent can feed back into itself or a previous node. This is what
makes self-correction possible. The Validator → Creator → Validator loop that
makes systems like Brandbot work requires LangGraph (or custom implementation).

**Best for:**
- Systems with self-correction loops (generate → verify → regenerate)
- Complex multi-step workflows with conditional branching
- Systems where agents need to call each other in non-linear order
- When you need fine-grained control over state transitions
- Production-grade Python systems

**Strengths:**
- Most powerful state management of any framework
- Built-in support for human-in-the-loop (interrupt before/after nodes)
- Streaming support out of the box
- Strong typing via TypedDict state schemas
- Active development and large community
- LangGraph Platform for deployment (cloud + self-hosted)

**Weaknesses:**
- Steeper learning curve than LangChain
- Graph definition can become verbose for simple systems
- Debugging complex graphs requires visualization tooling
- Overkill for simple linear pipelines

**Setup pattern:**
```python
from langgraph.graph import StateGraph, END
from typing import TypedDict

class State(TypedDict):
    input: str
    result: str
    verified: bool

def agent_node(state: State) -> State:
    # do work
    return {"result": "..."}

def verifier_node(state: State) -> State:
    # check result
    return {"verified": True}

def router(state: State) -> str:
    return "end" if state["verified"] else "agent"

graph = StateGraph(State)
graph.add_node("agent", agent_node)
graph.add_node("verifier", verifier_node)
graph.add_edge("agent", "verifier")
graph.add_conditional_edges("verifier", router, {"end": END, "agent": "agent"})
graph.set_entry_point("agent")
app = graph.compile()
```

**HITL with LangGraph:**
```python
from langgraph.checkpoint.memory import MemorySaver

# Compile with checkpointer
memory = MemorySaver()
app = graph.compile(checkpointer=memory, interrupt_before=["hitl_node"])

# Run until interrupt
config = {"configurable": {"thread_id": "1"}}
result = app.invoke(input, config)
# Human reviews result...
# Resume
final = app.invoke(None, config)
```

---

## Framework 2 — LangChain

**What it is:** The original LLM orchestration framework. Chains, agents, tools.
Linear by default. Best for chains of operations rather than cyclic graphs.

**Core concept:** Chain — a sequence of operations. LCEL (LangChain Expression Language)
composes chains using the `|` operator. Agents use ReAct or other strategies
to decide which tools to call.

**Killer feature:** Massive ecosystem. More integrations, tools, retrievers,
vector stores, and document loaders than any other framework.

**Best for:**
- Linear pipelines (A → B → C → output)
- RAG (retrieval-augmented generation) applications
- Simple tool-using agents that don't need complex orchestration
- Fast prototyping
- Teams already using LangChain infrastructure

**Strengths:**
- Vast ecosystem of integrations
- Very easy to get started
- Excellent documentation
- Built-in RAG support
- Works well for single-agent + tools pattern

**Weaknesses:**
- Poor support for cyclic workflows (use LangGraph instead)
- State management is primitive compared to LangGraph
- LCEL syntax can be confusing for complex chains
- Less control over multi-agent coordination

**Setup pattern:**
```python
from langchain_anthropic import ChatAnthropic
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.tools import tool

llm = ChatAnthropic(model="claude-sonnet-4-6")

@tool
def search_web(query: str) -> str:
    """Search the web for information."""
    # implementation
    return result

agent = llm.bind_tools([search_web])

prompt = ChatPromptTemplate.from_messages([
    ("system", "You are a helpful assistant."),
    ("human", "{input}")
])

chain = prompt | agent
result = chain.invoke({"input": "Research my competitors"})
```

---

## Framework 3 — CrewAI

**What it is:** A framework where agents are modelled as a "crew" — a team of
specialists with defined roles, goals, and backstories. Tasks are assigned to
crew members. The crew executes sequentially or in parallel.

**Core concept:** Agent + Task + Crew. Agents have roles (like job titles).
Tasks have descriptions and expected outputs. The Crew orchestrates execution.
Agents can delegate to each other.

**Killer feature:** Role-based natural language delegation. No graph configuration.
You describe what each agent does in natural language, and CrewAI handles routing.
Fastest to prototype for teams with non-technical stakeholders.

**Best for:**
- Systems that map well to human team structures
- Content creation pipelines (researcher + writer + editor)
- When team members need to understand the architecture
- Rapid prototyping before committing to LangGraph complexity
- Sequential workflows with clear role boundaries

**Strengths:**
- Most intuitive API — very close to natural language
- Role/goal/backstory maps directly to how people think about teams
- Built-in delegation between agents
- Good for sequential and parallel task execution
- Lower learning curve than LangGraph

**Weaknesses:**
- Less control over state than LangGraph
- Limited support for complex cyclic workflows
- Less mature than LangGraph for production use
- Harder to implement precise verification logic

**Setup pattern:**
```python
from crewai import Agent, Task, Crew, Process

researcher = Agent(
    role="Brand Researcher",
    goal="Extract comprehensive brand DNA from a website URL",
    backstory="You are an expert at analyzing brand voice and identity.",
    tools=[web_scraper],
    verbose=True
)

research_task = Task(
    description="Scrape {url} and extract brand voice, mission, and audience.",
    expected_output="Structured Brand DNA with voice attributes, mission, audience.",
    agent=researcher
)

crew = Crew(
    agents=[researcher, strategist, writer],
    tasks=[research_task, strategy_task, writing_task],
    process=Process.sequential,
    verbose=True
)

result = crew.kickoff(inputs={"url": "https://example.com"})
```

---

## Framework 4 — AutoGen

**What it is:** Microsoft's framework for conversational multi-agent systems.
Agents talk to each other via messages. Conversations are the coordination mechanism.

**Core concept:** ConversableAgent — an agent that can send and receive messages.
GroupChat — multiple agents in a conversation where a GroupChatManager routes turns.
Agents can be human proxies (asking for human input mid-conversation).

**Killer feature:** Human proxy agent. AutoGen makes it trivial to insert a human
into an agent conversation — the `HumanProxyAgent` simply waits for human input
before responding. The most natural HITL implementation of any framework.

**Best for:**
- Conversational workflows where agents debate and refine outputs
- Code generation with automated execution and debugging
- Systems where multiple AI agents need to negotiate an output
- When HITL needs to feel like "joining a conversation"
- Research and exploration tasks

**Strengths:**
- Most natural HITL implementation
- Excellent for code generation (built-in code execution)
- Agents can self-correct through conversation
- Good for open-ended tasks without predefined structure
- Built-in support for termination conditions

**Weaknesses:**
- Less structured than LangGraph — hard to enforce strict output schemas
- Conversation overhead can be verbose and expensive
- Harder to control exact execution flow
- Not ideal for latency-sensitive production systems

**Setup pattern:**
```python
from autogen import AssistantAgent, UserProxyAgent, GroupChat, GroupChatManager

config_list = [{"model": "claude-sonnet-4-6", "api_key": "..."}]

researcher = AssistantAgent(
    name="Researcher",
    system_message="You research brand DNA from websites.",
    llm_config={"config_list": config_list}
)

human = UserProxyAgent(
    name="Human",
    human_input_mode="ALWAYS",  # or "NEVER" for autonomous
    code_execution_config=False
)

# Simple two-agent conversation
human.initiate_chat(researcher, message="Research this brand: https://example.com")
```

---

## Framework 5 — Vercel AI SDK

**What it is:** TypeScript-first SDK for building AI applications.
Works with any LLM provider. Built for Next.js and server-side TypeScript.
`generateText`, `streamText`, `generateObject` are the core primitives.

**Core concept:** AI primitives composable with standard TypeScript patterns.
Tools are typed functions. Streaming is first-class. Works with the Vercel ecosystem.

**Killer feature:** `generateObject` with Zod schemas — structured output
enforcement baked in. The equivalent of structured output from any model,
validated automatically. Best structured output DX of any framework.

**Best for:**
- Full-stack TypeScript / Next.js applications
- When the AI is part of a web product (not a standalone pipeline)
- Real-time streaming UIs
- Teams that want to stay in TypeScript throughout
- Projects deploying to Vercel

**Strengths:**
- Best-in-class TypeScript DX
- Streaming built in from day one
- `generateObject` with Zod = automatic structured output
- Works with any LLM provider (Anthropic, OpenAI, Google, etc.)
- Easy deployment to Vercel Edge Functions

**Weaknesses:**
- No built-in multi-agent orchestration (you build it yourself)
- No graph-based workflow support
- Limited state management compared to LangGraph
- Python not supported

**Setup pattern:**
```typescript
import { generateObject, generateText, tool } from 'ai'
import { anthropic } from '@ai-sdk/anthropic'
import { z } from 'zod'

// Structured output with Zod
const brandDNA = await generateObject({
  model: anthropic('claude-sonnet-4-6'),
  schema: z.object({
    voiceAttributes: z.array(z.string()),
    missionStatement: z.string(),
    targetAudience: z.string(),
    clarityScore: z.number().min(0).max(100)
  }),
  prompt: `Extract brand DNA from: ${url}`
})

// Tool-using agent
const result = await generateText({
  model: anthropic('claude-sonnet-4-6'),
  tools: {
    searchCompetitors: tool({
      description: 'Search for competitor companies',
      parameters: z.object({ industry: z.string(), size: z.string() }),
      execute: async ({ industry, size }) => { /* ... */ }
    })
  },
  prompt: `Find competitors for a ${size} company in ${industry}`
})
```

---

## Framework 6 — Custom implementation

**What it is:** No framework. Pure Python or TypeScript with direct API calls.
You orchestrate agents using standard async patterns.

**Core concept:** Each agent is an async function. Orchestration is `asyncio.gather`
for parallel, `await` chain for sequential. State is a TypedDict or dataclass.
Verification is a function that returns pass/fail.

**Killer feature:** Zero overhead. No framework abstractions. Maximum control.
Every line of code is yours. No black boxes.

**Best for:**
- Simple systems where a framework would add more complexity than it removes
- Teams who want to understand every line of what's running
- Systems with unusual execution patterns frameworks can't express
- When framework upgrade cycles are a concern
- Performance-critical production systems

**Strengths:**
- Complete control over every detail
- No framework-imposed constraints
- No dependency on third-party package maintenance
- Easiest to debug (no framework magic)
- Lowest overhead

**Weaknesses:**
- You implement everything from scratch
- No built-in streaming, checkpointing, or state management
- HITL requires more work to implement
- More code to write and maintain

**Setup pattern:**
```python
import asyncio
from typing import TypedDict
from anthropic import AsyncAnthropic

client = AsyncAnthropic()

class PipelineState(TypedDict):
    url: str
    brand_dna: dict | None
    competitors: list | None
    article: str | None

async def guardian_agent(state: PipelineState) -> PipelineState:
    response = await client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=1000,
        messages=[{"role": "user", "content": f"Extract brand DNA from {state['url']}"}]
    )
    return {**state, "brand_dna": parse_brand_dna(response)}

async def run_pipeline(url: str) -> PipelineState:
    state: PipelineState = {"url": url, "brand_dna": None, "competitors": None, "article": None}

    # Sequential
    state = await guardian_agent(state)

    # Parallel
    competitors, analysis = await asyncio.gather(
        scout_agent(state),
        analyst_agent(state)
    )
    state = {**state, **competitors, **analysis}

    return state
```

---

## Quick selection guide

```
Is this TypeScript / Next.js / Vercel?
  └─ Yes → Vercel AI SDK

Is this a conversational system or code gen?
  └─ Yes → AutoGen

Does the system need cyclic loops (verify → retry → verify)?
  └─ Yes → LangGraph

Does it map naturally to a "team" with named roles?
  └─ Yes → CrewAI

Is it a simple linear chain (A → B → C)?
  └─ Yes → LangChain (or Custom if very simple)

Do you want maximum control and minimal dependencies?
  └─ Yes → Custom implementation

Default for production Python multi-agent systems → LangGraph
```
