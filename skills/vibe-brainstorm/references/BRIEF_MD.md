# BRIEF_MD.md

The canonical BRIEF.md template for vibe-* projects.
Used by vibe-brainstorm to generate BRIEF.md.
Read in full before generating — every field must be filled.
No field left blank. No placeholders. Every section present.

Downstream consumers and what they read:
  architect:    problem, platform, stack, constraints, open questions
  new-app:      problem, user, core value, features, nav, stack, constraints
  vibe-agent:   problem, user, constraints, integrations (if agentic project)
  change-spec:  core value, feature set (original intent baseline)
  review:       problem, core value (sanity check against implementation)

---

## PERSONAL PROJECT TEMPLATE

```markdown
# BRIEF.md
> Created: [date] via brainstorm: | Path: Personal | Complexity: [S/M/L/XL]

---

## Problem

**The problem:**
[One precise sentence. Names who has it, what fails, what it costs in time/effort/frustration.]

**Current workaround:**
[How people solve this today — specific app, spreadsheet, manual process, or nothing.]

**Why the workaround fails:**
[One or two sentences. The specific gap that makes the current approach painful.]

---

## User

**Primary user:**
[Specific description — not "people", not "users". E.g. "Freelance designers managing
3-8 client projects simultaneously, switching between projects daily."]

**Usage frequency and context:**
[When and how often. E.g. "Daily, brief sessions — checking in takes under 2 minutes.
Longer sessions weekly when reviewing progress."]

**Building for:**
[ ] Myself only
[ ] Others (not me)
[ ] Both

---

## Core value

**The one thing:**
[Single outcome statement. Not a feature. What changes for the user because this exists.
E.g. "At a glance, I always know which client project needs attention today."]

**How we'll know it's working:**
[The observable signal. E.g. "User opens the app daily and logs an entry without
prompting. Weekly active rate above 70% after 4 weeks."]

---

## Features — v1

**In scope (v1):**
| Feature | Why it serves core value |
|---------|------------------------|
| [Feature 1] | [One sentence] |
| [Feature 2] | [One sentence] |
| [Feature 3] | [One sentence] |

**Navigation structure:**
[Top-level destinations, locked. E.g. "Today / Projects / History"]

**Deferred to v2:**
- [Feature] — [one sentence reason for deferral]
- [Feature] — [one sentence reason for deferral]

**Non-goals (v1 explicitly does NOT include):**
- [Statement of what this is not building]
- [Statement of what this is not building]
- [At least 2 non-goals. These prevent scope creep mid-build.]

---

## UI direction

**Platform:** [Mobile-first / Desktop-first / Both]
**Session type:** [Quick (under 2 min) / Deep (20+ min) / Both]
**Feel:** [One word: calm / powerful / playful / minimal / premium / editorial]
**UI references:** [App names the user loves, even if unrelated to this product]
**Direction:** [One sentence describing the overall visual and interaction approach]

---

## Tech stack

**Recommended stack:**
| Layer | Choice | Reason |
|-------|--------|--------|
| Frontend | [choice] | [reason] |
| Backend | [choice or "none — client-side only"] | [reason] |
| Database | [choice or "none"] | [reason] |
| Auth | [choice or "none"] | [reason] |
| Hosting | [choice] | [reason] |

**Third-party services:**
- [Service] — [what it does in this project]
- (none if no third-party services)

**User accounts required:** [Yes / No]
**Data persistence:** [Local only / Cloud synced / Both]

---

## Constraints

**Timeline:** [Realistic v1 delivery — e.g. "4 weekends of build time"]
**Infrastructure budget:** [Monthly cap, e.g. "$20/month" or "free tier only"]
**Platform requirements:** [Browser targets, OS, device constraints]
**Compliance:** [None / GDPR / other — be specific]

---

## Risks

| Risk | Implication | Mitigation |
|------|-------------|------------|
| [Specific risk] | [What breaks or costs more] | [Simpler alternative or plan] |
| [Specific risk] | [What breaks or costs more] | [Simpler alternative or plan] |

---

## Complexity estimate

**Size:** [S / M / L / XL]

| Signal | Value |
|--------|-------|
| v1 features | [N] |
| Backend needed | [Yes / No] |
| Auth needed | [Yes / No] |
| Third-party integrations | [N] |
| Real-time / sync | [Yes / No] |
| Agentic / AI | [Yes / No] |

**Rough build estimate:** [N weeks at [N] hours/week]
**Complexity driver:** [The one thing that makes this harder than it looks]

---

## Open questions

- [ ] [Question that must be resolved before architect:]
- [ ] [Question that must be resolved before architect:]
(Delete section if no open questions)

---

## Agentic flag

**Contains AI agent logic:** [Yes / No]
[If Yes:]
**Agent type:** [Single agent / Multi-agent pipeline / Orchestrator + subagents]
**Next step:** Run `agent:` before `architect:` to design the agent architecture.
[If No:]
**Next step:** `architect: confirm`
```

---

## CLIENT PROJECT TEMPLATE

```markdown
# BRIEF.md
> Created: [date] via brainstorm: | Path: Client | Complexity: [S/M/L/XL]

---

## Client context

**Client:** [Name / company]
**Industry:** [What they do, business size]
**Project type:** [New product / Replacing X / Extending existing system]
**Trigger:** [Why this project, why now — pain point, deadline, competitor, opportunity]
**Previous attempts:** [What they tried before and why it failed, or "First attempt"]
**Client technical level:** [Non-technical / Technical / Mixed]

---

## Problem

**The problem:**
[One precise sentence. Names who has it, what fails, what it costs.]

**Current workaround:**
[How they solve it today.]

**Cost of the problem:**
[Quantified — time lost, money lost, errors, customers lost. "Frustrating" is not a cost.
E.g. "3 hours per invoice × 40 invoices/month = 120 hours/month lost to manual reconciliation."]

---

## Stakeholders

**Decision-maker (approves spec and delivery):**
[Name and role. Not "the team." One person.]

**Day-to-day contact:**
[Name and role — may differ from decision-maker]

**Actual users:**
[Specific description. E.g. "Warehouse staff, 20-30 people, logging inventory on tablets
while standing at shelves. Non-technical. Often wearing gloves."]

**Other stakeholders with opinions:**
[IT, legal, finance, other departments — or "None identified"]

**Sign-off process:**
[One person / Committee — how many rounds of approval expected]

---

## Success definition

**Primary metric:**
[Quantified. E.g. "Invoice processing time reduced from 3h to 30min per invoice."]

**Secondary metrics:**
- [Metric] — [target]
- [Metric] — [target]

**Failure definition:**
[What would make the client consider this a failure — their words, not ours.
This is the most important question. Surfaces hidden expectations.]

**Hard deadline:** [Date or "None — preference only"]
**Consequence of missing deadline:** [What happens if late]

**3-month picture:** [What does successful v1 look like in use]
**12-month picture:** [What does the platform look like a year from delivery]

---

## User

**Primary user:**
[Specific. E.g. "Warehouse staff, 20-30 people, logging inventory on shared tablets.
Non-technical. Context: standing, sometimes wearing gloves, spotty WiFi."]

**Usage frequency and context:**
[When and how often. Include physical/environmental constraints.]

**Technical comfort level:** [Non-technical / Basic / Technical]

**Workflow constraints:**
[Anything that breaks standard patterns — always mobile, offline, accessibility needs, etc.
Or "None identified"]

---

## Core value

**The one thing:**
[Single outcome for users. Not a feature. What changes for them because this exists.]

**Alignment with success metric:**
[One sentence confirming core value and primary metric point in the same direction.
If they don't align — flag explicitly and resolve before proceeding.]

---

## Features — v1

**In scope (v1):**
| Feature | Origin | Why it serves core value |
|---------|--------|------------------------|
| [Feature] | [Client-requested / Framework-derived] | [One sentence] |
| [Feature] | [Client-requested / Framework-derived] | [One sentence] |

**Navigation structure:**
[Top-level destinations, locked.]

**Deferred to v2:**
- [Feature] — [reason] — [client acceptance: confirmed / pending]

**Non-goals (v1 explicitly does NOT include):**
- [Statement of what this is not building]
- [Statement of what this is not building]
- [At least 3 non-goals for client projects — scope creep risk is higher]

**Client-requested features not serving core value:**
- [Feature] — [recommended action: defer to v2 / remove / reframe]
(Delete row if none)

---

## Build vs buy

**Decision:** [Build / Buy / Hybrid]
**Alternatives considered:** [Off-the-shelf solutions evaluated]
**Reason for decision:** [Why build over buy, or why this specific hybrid]

---

## Competitive landscape

**Known competitors / adjacent tools:**
- [Tool/competitor] — [what they do well] — [gap this product fills]

**Differentiation:** [One sentence — what this does that nothing else does for this user]

---

## UI direction

**Platform:** [Mobile-first / Desktop-first / Both]
**Session type:** [Quick / Deep / Both]
**Feel:** [One word]
**Brand constraints:** [Existing design system / Brand guidelines URL / Colors / Fonts / None]
**UI references:** [Apps or sites the client likes]
**Direction:** [One sentence]

---

## Tech stack

**Mandated by client:**
- [Technology or constraint mandated — or "None"]

**Recommended stack:**
| Layer | Choice | Mandated / Recommended | Reason |
|-------|--------|----------------------|--------|
| Frontend | [choice] | [M/R] | [reason] |
| Backend | [choice] | [M/R] | [reason] |
| Database | [choice] | [M/R] | [reason] |
| Auth | [choice] | [M/R] | [reason] |
| Hosting | [choice] | [M/R] | [reason] |

**Existing systems to integrate:**
- [System] — [integration type] — [complexity: Low/Medium/High]

**Third-party services:**
- [Service] — [purpose] — [client has account: Yes/No/Unknown]

---

## Constraints

**Timeline:** [v1 delivery date — hard or preference]
**Budget:** [Monthly infrastructure cap]
**Compliance:** [GDPR / HIPAA / Financial / Industry-specific / None]
**IP ownership:** [Client owns all code / Agency retains license / Other]
**Access timeline:** [When credentials and assets are available — risk if delayed]

---

## Risks

**Product risks:**
| Risk | Implication | Mitigation |
|------|-------------|------------|
| [Specific risk] | [Impact] | [Plan] |

**Client/process risks:**
| Risk | Status |
|------|--------|
| Scope creep (informal mid-build requests) | [Formal change process agreed: Yes/No] |
| Approval delays | [Review turnaround agreed: Yes/No — [N] business days] |
| Access delays | [Credentials requested before Phase 1: Yes/No] |
| Stakeholder misalignment | [Single sign-off confirmed: Yes/No] |
| "Done" redefined at delivery | [Delivery criteria in formal agreement: Yes/No] |

---

## Delivery terms

**Handoff:** [Documentation / Training / Support period — or "None agreed"]
**Acceptance testing:** [Client tests before sign-off / Spec completion sign-off]
**Post-delivery:** [Client handles own maintenance / Retainer / Handoff to client dev team]

---

## Complexity estimate

**Size:** [S / M / L / XL]

| Signal | Value |
|--------|-------|
| v1 features | [N] |
| Backend needed | [Yes / No] |
| Auth needed | [Yes / No] |
| Third-party integrations | [N] |
| Existing system integrations | [N] |
| Compliance requirements | [Yes / No] |
| Real-time / sync | [Yes / No] |
| Agentic / AI | [Yes / No] |

**Rough build estimate:** [N weeks at [N] hours/week]
**Complexity driver:** [The one thing that makes this harder than it looks]
**Delivery risk:** [Low / Medium / High] — [one sentence reason]

---

## Open questions

- [ ] [Question requiring client confirmation before architect:]
- [ ] [Question requiring client confirmation before architect:]
(Delete section if no open questions — resolve all before proceeding)

---

## Agentic flag

**Contains AI agent logic:** [Yes / No]
[If Yes:]
**Agent type:** [Single agent / Multi-agent pipeline / Orchestrator + subagents]
**Next step:** Run `agent:` before `architect:` to design the agent architecture.
[If No:]
**Next step:** `architect: confirm`
```

---

## Complexity sizing guide

Use this to assign the Size field:

**S — Small (1-2 weeks):**
- 3-5 features, no backend or simple backend
- No auth or basic auth (Supabase/Auth0 drop-in)
- No third-party integrations or one simple one
- Client-side data or simple CRUD

**M — Medium (3-6 weeks):**
- 5-8 features, full-stack
- Auth with roles/permissions
- 1-3 third-party integrations
- Standard data model (5-10 tables)
- No real-time, no AI

**L — Large (6-12 weeks):**
- 8-15 features, full-stack
- Complex auth or multi-tenant
- 3+ integrations or one complex integration
- Complex data model or non-trivial migrations
- Real-time features OR basic AI/LLM calls

**XL — Extra Large (12+ weeks):**
- 15+ features
- Multi-agent AI pipeline
- Multiple complex integrations
- Compliance requirements (GDPR, HIPAA, financial)
- Multi-tenant with complex permissions
- Mobile + web + backend simultaneously
