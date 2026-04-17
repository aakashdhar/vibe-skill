# BRIEF_RUBRIC.md

Reference rubric for auditing BRIEF.md in Step 1 of vibe-spec-review.
Contains examples of good vs bad for each criterion.

---

## Problem definition

**P0 — Missing user:**
No specific user type defined. The agent cannot make design decisions
without knowing who the product is for.

Bad: "This app helps people manage tasks."
Good: "This app helps freelance developers track billable hours across client projects."

**P1 — Vague problem:**
Problem stated too broadly to drive specific decisions.

Bad: "People struggle with productivity."
Good: "Freelance developers lose ~3h/week manually reconciling time tracking
sheets with invoices because their tools don't talk to each other."

---

## Success criteria

**P0 — Untestable criterion:**

Bad: "Users should feel confident using the app."
(How would you test "feel confident"?)

Good: "New user completes account setup and sends first invoice within 10 minutes
of signup, measured by time between account_created and first_invoice_sent events."

Bad: "The app should be fast."
Good: "Dashboard loads in under 2 seconds on a 4G connection."

**P1 — No quantitative metric:**

Bad: "Users can track their time effectively."
Good: "Users log at least 3 time entries per week in the first month (retention signal)."

---

## Constraints

**P1 — Missing technical constraints:**

Bad: [no constraints section]
Good:
- Must work offline (PWA)
- Must support iOS Safari 15+
- Budget: $50/month infrastructure
- Must integrate with Stripe (not other payment processors)
- Must not store credit card data directly (use Stripe hosted checkout)

**P1 — Missing non-goals:**

Bad: [no non-goals section]
Good:
- v1 does NOT include team/multi-user support
- v1 does NOT include mobile app (web only)
- v1 does NOT include Quickbooks integration (deferred to v2)
- We are NOT building a time tracking tool — this is invoicing only

Without non-goals, an agent will attempt to build features that
were never intended, wasting build time and breaking scope.

---

## Risk assessment

**P1 — Missing external dependencies:**

Bad: [no mention of third-party services]
Good:
- Depends on Stripe API for payment processing
- Depends on Resend for transactional email
- Depends on Supabase for auth and database
Risk: if Stripe API changes, invoice generation flow is affected.

**P2 — Missing open questions:**

Good brief documents what isn't yet decided:
- Open: Should we support multiple currencies in v1?
- Open: Do we need GDPR compliance from day one?
These questions need answers before ARCHITECTURE.md locks decisions.

---

## Specificity test

Ask this about every statement in BRIEF.md:
"Could two different developers, reading only this statement,
build the same thing?"

If the answer is no — it needs more specificity.

Examples that fail the test:
- "Modern, clean UI" (what does modern mean? clean compared to what?)
- "Scalable architecture" (scales to what? 100 users? 1M users?)
- "Secure" (which threats? auth? encryption at rest? PII handling?)
- "Fast" (what metric? whose connection? what device?)

Examples that pass:
- "Mobile-first responsive UI, tested on iOS Safari and Chrome Android"
- "Handles 1000 concurrent users on a $50/month Supabase Pro instance"
- "All user PII encrypted at rest, HTTPS only, JWT with 24h expiry"
- "API responses under 500ms at p95 on a standard 4G connection"
