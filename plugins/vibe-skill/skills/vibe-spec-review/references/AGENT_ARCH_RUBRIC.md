# AGENT_ARCH_RUBRIC.md

Reference rubric for auditing AGENT_ARCH.md in Step 2 of vibe-spec-review.
Contains examples and edge cases for each check.

---

## Single responsibility per agent

**P1 — Multiple responsibilities:**

Bad: "GuardianAgent — scrapes the website, extracts brand DNA, AND
finds competitor URLs using the brand industry"
(Three jobs: scrape, extract, discover)

Good: "GuardianAgent — scrapes the provided URL and extracts structured
Brand DNA (voice attributes, mission, audience, tagline, clarity score)"
(One job: extract brand DNA from a URL)

**Detection pattern:**
Any agent description containing "and also", "as well as", "additionally",
or more than one verb clause describing different domains
→ P1 finding: split into two agents.

---

## VerifierAgent coverage

**P0 — Missing verifier:**

Every sub-agent must have a VerifierAgent. No exceptions.
If GuardianAgent exists and GuardianVerifier does not → P0.

Bad rubric: "GuardianVerifier checks that the output looks good"
(What does "looks good" mean? How does the agent know if it passed?)

Good rubric:
"GuardianVerifier checks:
- Contract: output contains voiceAttributes (array), mission (string),
  audience (string), tagline (string), clarityScore (0-100)
- Spec: voiceAttributes has ≥2 items, clarityScore reflects actual
  site content (not inferred), mission is ≥15 words
- Quality: confidence score ≥70% (if below, flag rather than fail)
- Consistency: N/A — first agent in chain"

**P1 — No retry logic:**

Bad: "If verifier fails, log an error"
Good: "If verifier fails:
  Attempt 1: send output + FAIL verdict + fix instructions back to agent
  Attempt 2: if still fails → HITL checkpoint with both outputs shown"

---

## HITL checkpoints

**P0 — Missing HITL before irreversible action:**

Any agent that:
- Sends email, Slack, SMS, social media posts
- Executes financial transactions
- Deletes or permanently modifies data
- Operates in regulated domain (legal, medical, financial)

...MUST have a HITL checkpoint before execution. Missing = P0.

**P1 — Vague HITL definition:**

Bad: "Human reviews the output before it's sent."
(What does the human see? What can they do? What happens if they reject?)

Good:
"HITL Checkpoint 2 — Before article is sent to client:
Human sees: full article text, ContentVerifier score card (quality/voice/gap),
strategic insight summary, estimated read time
Actions: Approve (publishes) / Reject (discards) / Edit (opens editor) /
Redirect to Strategist (choose different angle)
Timeout: 24h → sends reminder, 48h → auto-escalates to [person]"

---

## State ownership

**P0 — Multi-writer state key:**

Bad:
brand_dna: written by GuardianAgent AND updated by StrategistAgent

Good:
brand_dna: written by GuardianAgent only
         read by: ScoutAgent, AnalystAgent, StrategistAgent, CreatorAgent
         StrategistAgent writes to: content_strategy (separate key)

Any state key with two writers is a race condition waiting to happen
in parallel execution. Flag immediately.

**P1 — Unowned state:**

Bad: "The session stores brand_dna, competitors, gaps, and the article draft"
(No owner defined for any of these)

Good:
brand_dna:      owned by GuardianAgent
competitors:    owned by ScoutAgent
content_gaps:   owned by AnalystAgent
article_angles: owned by StrategistAgent
article_draft:  owned by CreatorAgent

---

## Tool assignment

**P1 — Unassigned tool:**

Bad: "The system uses Tavily for web search" (which agent?)

Good: "ScoutAgent — uses Tavily for competitor discovery
      AnalystAgent — uses Tavily for competitor content retrieval"

**P1 — Unflagged write tool:**

Any tool that writes, sends, or modifies external state must be flagged:
- send_email → flagged: irreversible, requires HITL
- create_jira_ticket → flagged: external write, moderate risk
- publish_article → flagged: irreversible, requires HITL
- web_fetch → not a write tool, no flag needed
- web_search → not a write tool, no flag needed

**P0 — Write tool without HITL:**

If an agent has a write tool that produces irreversible output
(send_email, publish_post, execute_transaction) and there is no
HITL checkpoint before it executes → P0.

---

## Implementation order

**P0 — Misordered dependencies:**

Bad:
Phase 2, Task 1: Implement GuardianAgent
Phase 1, Task 3: Create base agent class (that GuardianAgent inherits from)

GuardianAgent cannot be implemented before the base class exists.
Implementation order must respect all inheritance and import dependencies.

Good:
Phase 1: base agent class → verifier base class → state schema
Phase 2: GuardianAgent → GuardianVerifier → ScoutAgent → ScoutVerifier → ...

---

## Framework fit

**P1 — Framework mismatch:**

If AGENT_ARCH.md recommends LangGraph but the stack is TypeScript/Next.js
(where Vercel AI SDK is the idiomatic choice) → P1 mismatch.

Framework must align with:
1. The stated programming language
2. The deployment target
3. The latency requirement
4. The complexity of the workflow (cyclic vs linear)

**Pattern complexity check:**
If the system has 2 agents and the pattern is Orchestrator+Sub-agents
→ P1: simpler pattern (Single Agent + Tools or Sequential Pipeline)
would be more appropriate and less error-prone.

Rule: pattern complexity must be earned by the problem complexity.
