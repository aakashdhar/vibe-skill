# BRIEF_QUALITY_CHECK.md

Run this check before writing BRIEF.md.
Based on the confirmed answers from the brainstorm conversation,
evaluate whether each field will be strong or weak.

Re-open weak fields with a targeted follow-up question.
Only proceed to writing when all P0 items pass.
P1 items: attempt to resolve, document as open question if unresolvable.

This check is not shown to the user. It is internal.
The user sees only the follow-up questions if any are triggered.

---

## P0 checks — must pass before writing

### P0-1: User is specific

**Pass:** Can you describe the user in one sentence that would let a designer draw them?
"Freelance designers managing 3-8 client projects, switching between them daily"
"Warehouse staff logging inventory on tablets while standing at shelves"

**Fail signals:**
- "Everyone", "people", "users", "anyone who..."
- No frequency or context
- Profession named but no specificity about their situation

**If failing — ask:**
> "Who specifically — can you describe a real person who has this problem?
> What do they do, how often does this come up, and in what context?"

---

### P0-2: Core value is a single outcome, not a list

**Pass:** One clear statement of what changes for the user.
"At a glance I always know which client needs attention today"
"I never lose track of a billable hour again"

**Fail signals:**
- Multiple outcomes listed ("it helps with X, Y, and Z")
- Feature described as value ("users can track time and generate invoices")
- Vague benefit ("makes life easier", "saves time", "improves workflow")

**If failing — ask:**
> "If you had to pick the ONE thing someone would say makes this indispensable —
> the thing that makes them say 'I can't go back to not having this' — what is it?"

---

### P0-3: Success criteria is measurable

**Personal:** At least one observable signal of the core value working.
**Client:** At least one quantified metric with a target number.

**Pass (personal):** "User opens daily and logs an entry without prompting. 70% weekly active after 4 weeks."
**Pass (client):** "Invoice processing time under 30 minutes, down from 3 hours. Measured by average time-to-send per invoice."

**Fail signals (personal):** "Users like it", "it gets used", "people find it helpful"
**Fail signals (client):** "Improves efficiency", "saves time", "users are happy"

**If failing (personal) — ask:**
> "How will you know in 4 weeks whether this is working?
> What would you see that tells you users are getting the core value?"

**If failing (client) — ask:**
> "What number would make the client consider this a success?
> '[Outcome] by how much?' — push for a target."

---

### P0-4: Non-goals are explicitly stated

**Pass:** At least 2 things that v1 explicitly does NOT include.
These must be real boundary decisions, not just "we won't add random features."

**Pass examples:**
"v1 does NOT include team/multi-user support"
"v1 does NOT include a mobile app — web only"
"v1 does NOT integrate with Quickbooks — deferred to v2"
"We are NOT building a time tracking tool — invoicing only"

**Fail:** No non-goals mentioned, or only vague "we'll keep it simple."

**If failing — ask:**
> "What's something people might expect this to do that v1 deliberately won't?
> What's out of scope — even if it sounds reasonable?"

---

### P0-5: v1 feature set has a clear boundary

**Pass:** Feature list is finite, every feature clearly serves the core value,
and the user has confirmed what's in vs out.

**Fail signals:**
- Features listed that don't connect to core value
- "Maybe in v1" or "probably" for multiple items
- No conversation about what gets cut

**If failing — prompt a cut:**
> "Of these features, which 3 are absolutely essential to deliver the core value?
> The others move to v2 — this keeps v1 achievable."

---

## P1 checks — resolve if possible, document as open question if not

### P1-1: Stack recommendation fits the actual requirements

Check the recommended stack against these constraints:
- Does it need a backend? (auth, server-side data, third-party webhooks, notifications)
- Does it need real-time? (websockets vs polling vs none)
- Does it need mobile? (PWA vs native)
- Is the complexity appropriate? (don't recommend Next.js for a static site)

If the stack seems over-engineered or under-powered for what was described —
flag it and adjust before writing.

---

### P1-2: Risks are specific, not generic

**Pass:** Each risk names a specific feature or decision, its implication, and a simpler alternative.
"Daily notifications require a backend even though everything else is client-side.
Simpler: weekly email digest instead — no backend needed."

**Fail:** Generic risks that apply to any project.
"It might take longer than expected." (not a risk, it's a certainty)
"The client might change their mind." (too vague to act on)

---

### P1-3: Client path — stakeholders have one sign-off point (client projects only)

**Pass:** One named person who approves spec and signs off on delivery.

**Fail:** "The team will decide", multiple names for sign-off, unclear.

**If failing — flag:**
> "Unclear sign-off authority is one of the most common sources of project delays.
> Can you confirm one person who approves spec changes and signs off on delivery?"

---

### P1-4: Client path — cost of problem is quantified (client projects only)

**Pass:** Time lost, money lost, or errors per period.
"120 hours/month at £50/hour = £6,000/month cost"

**Fail:** "It's frustrating", "wastes time", "causes issues"

**If failing — attempt:**
> "Can we put a number on it? How many hours per week does this cost,
> or how many errors per month? That number justifies the project cost."

---

## Agentic detection

Run after features are locked. Before writing BRIEF.md.

Scan the confirmed feature set and description for these signals:

```
AGENTIC_SIGNALS = [
    "AI agent", "LLM", "language model", "GPT", "Claude", "Gemini",
    "autonomous", "tool use", "function calling", "orchestrat",
    "multi-agent", "pipeline", "workflow automation", "AI decides",
    "AI generates", "AI extracts", "AI classifies", "AI summarises",
    "AI writes", "AI scrapes", "AI researches", "verifier", "subagent",
    "web search", "web scraping", "AI-powered", "intelligent",
    "automat* the *ing", "agent that", "bot that"
]
```

If 2+ signals found:

**High confidence — announce and flag:**
> "This project involves AI agent logic — I can see [signal A] and [signal B].
> Before architect:, run `agent:` to design the agent architecture.
> This affects your data model, error handling, and cost structure significantly."

Set `agentic_flag: true` in the brief.
Set `next_step: agent: before architect:` in the brief.

If 1 signal found:

**Ask to confirm:**
> "Will [feature] involve an AI model making decisions or taking actions autonomously,
> or is it a simpler API call? This affects which planning path to take."

If 0 signals:
No flag. Set `agentic_flag: false` in the brief.

---

## Fast path quality floor

When the fast path is triggered (message richness = high),
run ONLY the P0 checks before generating BRIEF.md.
Do not run the full conversation — confirm gaps in one exchange.

Fast path message to user:
> "You've given me a solid picture. Let me check two things before writing the brief:
> [Only ask about whichever P0 checks fail — maximum 2 questions]"

If all P0 checks pass from the original message — generate immediately without asking anything.

---

## Quality summary output (internal, after checks complete)

Before writing BRIEF.md, state internally:

```
PRE-WRITE QUALITY CHECK
P0: [N/5] passing
  ✅ User specificity
  ✅ Core value (single outcome)
  ❌ Success criteria — re-asked, answer confirmed
  ✅ Non-goals present
  ✅ Feature boundary clear

P1: [N/4] passing
  ✅ Stack fits requirements
  ⚠️ Risks too generic — will sharpen in brief
  ✅ Sign-off confirmed (client path)
  ✅ Cost quantified (client path)

Agentic: [Detected / Not detected]
Proceeding to write BRIEF.md.
```

This check is never shown to the user.
