# DELIVERY_TEMPLATE.md

Used by vibe-handoff Step 3 to generate DELIVERY.md.
Client-facing. Plain English. Zero jargon.
Fill from BRIEF.md, SPEC.md, DECISIONS.md.

---

```markdown
# [Project Name] — Delivery Summary
**Prepared by:** BetaCraft
**Delivered to:** [Client name]
**Date:** [date]
**Delivery type:** [Phase [N] completion / Full project delivery]

---

## What we built

[One paragraph, 3-5 sentences. What problem does this solve?
What can the client or their users do now that they couldn't before?
No technical terms. No framework names without explanation.
Written as if the client is explaining it to their board.]

Example:
"Brandbot is an AI-powered content tool that reads your website,
understands your brand's voice and positioning, and helps you create
articles that sound genuinely like you — not like a generic AI.
You paste your URL, confirm the brand profile it extracts, select
a content angle, and get a publication-ready draft in minutes.
It replaces hours of competitive research and writing with a
guided process that keeps your voice consistent every time."

---

## How it works

[The user journey, step by step, in plain English.
No code. No architecture. Just what the user sees and does.
Numbered steps, present tense.]

1. **[Step name]** — [what the user does and what happens]
2. **[Step name]** — [what the user does and what happens]
3. **[Step name]** — [what the user does and what happens]
[...]

---

## What's included

[Feature list sourced from SPEC.md, translated to plain English.
One bullet per feature. What it does, not how it works.]

- **[Feature name]** — [what it does for the user]
- **[Feature name]** — [what it does for the user]
- **[Feature name]** — [what it does for the user]
[...]

---

## What's not included (and why)

[Deferred items from DECISIONS.md and SPEC.md out-of-scope section.
Honest tone. Opportunity framing, not apologetic.
"Not included in this version" not "unfortunately we couldn't build."]

- **[Item]** — [why it was deferred — brief, honest reason]
  [When it might be added: v1.1 / future phase / on request]

[If nothing deferred:]
Everything agreed in scope has been delivered.

---

## How to access it

**Live URL:** [production URL]
**Login:** [how to create an account or where login details were sent]
**Browser:** [supported browsers — e.g. "Works in Chrome, Safari, Firefox. Not optimised for IE."]
**Mobile:** [works on mobile / desktop only / etc.]

---

## Key decisions we made along the way

[Sourced from DECISIONS.md — translate each technical decision
into a plain English explanation of the trade-off and outcome.
Client doesn't need to know what framework was chosen.
They do need to know why something works the way it does.]

**[Decision in plain English]**
[One or two sentences: what the choice was, why it was made,
what it means for the client going forward.]

Example:
"We built the competitor research on live data rather than a stored database.
This means results are always current — your competitors' latest articles
are included every time — but the first analysis takes 10-15 seconds
while it fetches fresh data. We chose live data because stale competitor
analysis is worse than slightly slower analysis."

[Repeat for 2-4 most significant decisions]

---

## What happens next

[For milestone delivery:]
Phase [N+1] begins on [date] and will deliver: [brief description].
We'll be in touch by [date] to [next action].

[For full project delivery:]
The project is complete. Your support process going forward is described
in SUPPORT.md. If you'd like to add features or make changes, contact
[PM name] at [email].

---

*Prepared by [BetaCraft PM] · [date]*
*Full technical documentation available on request.*
```
