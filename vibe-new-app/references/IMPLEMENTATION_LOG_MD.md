# IMPLEMENTATION_LOG.md — canonical template & rules

This is the template for `vibe/IMPLEMENTATION_LOG.md`. Skills scaffold the file from the
block below and then only ever **append** to it. The file is self-documenting — its own
header carries the schema and rules, so appending skills point here instead of repeating them.

## What it is (and how it differs from DECISIONS.md)
- `IMPLEMENTATION_LOG.md` = **implementation-decision** journal at *code* altitude:
  "why this approach, why this library, why this data shape." Append-only ADR log.
- `DECISIONS.md` = **spec/scope** drift-and-change log (product-level: what we're building
  and why we changed it).
- The per-task `Decisions:` fields in FEATURE_TASKS.md / BUG_TASKS.md are the *source* —
  meaningful ones get promoted (aggregated) into IMPLEMENTATION_LOG.md so there is one
  durable, greppable, graph-linked history instead of decisions buried per-task-file.

## Both audiences
Written for **humans** (onboarding: "how did this codebase get this way?") and for **AI
sessions** (so a future session doesn't re-derive or re-litigate a settled choice). Hence:
prose a person can read, but fixed fields an agent can parse.

## The "meaningful decision" bar (always-on ≠ log everything)
Append an entry ONLY when the choice:
- is hard to reverse, OR
- picked among real alternatives (a library, a pattern, a data model, an API shape, a tradeoff), OR
- would surprise a future reader, OR
- deviates from ARCHITECTURE.md.
Do **not** log routine or obvious implementation. Noise defeats the purpose.

## Append-only + supersede
Never edit or delete a past entry. If a decision is reversed, add a NEW entry and set the
old one's `Status:` to `superseded by D-NNN`. History stays truthful.

## Bounded read-back (token discipline)
Don't load the whole file every session. Scan `^## D-` headings for the one-line index,
then read only the recent / relevant entries. `Touches:` links each decision to its
graph nodes, so `vibe/graph/FLOW.md` + `DEPENDENCY_GRAPH.json` are the *map* and this log
is the *why* behind it.

---

## FILE TEMPLATE — write this verbatim to `vibe/IMPLEMENTATION_LOG.md` at scaffold time:

```markdown
# Implementation Log

> Append-only record of **implementation** decisions — why this approach, why this library.
> Code-altitude companion to DECISIONS.md (spec/scope). Read by humans (onboarding) and AI
> (so settled choices aren't re-litigated).
>
> **Rules:** Append only — never edit/delete; to reverse a decision add a new entry and mark
> the old one `superseded by D-NNN`. Log only *meaningful* choices (hard to reverse · picks
> among real alternatives · would surprise a reader · deviates from ARCHITECTURE.md) — not
> routine code. To read: scan `## D-` headings for the index, then read recent entries.
> `Touches:` links to vibe-graph nodes (see vibe/graph/FLOW.md).
>
> Entry schema — copy per decision, newest at the bottom:
> ## D-NNN · <one-line decision>
> - Date / cycle: <YYYY-MM-DD> · <feature|bug|task id>
> - Status: accepted            (or: superseded by D-NNN)
> - Context: <the constraint that forced a choice>
> - Decision: <what was chosen>
> - Why / alternatives: <why this; why this library; what was rejected and why>
> - Touches: <files / functions — the graph nodes this changed>
> - Tradeoff: <what we accept in return>   (optional)

<!-- entries below, newest last -->

_No implementation decisions logged yet._
```

## Worked example entry
```markdown
## D-014 · Validate the API boundary with Zod
- Date / cycle: 2026-09-21 · feature: sponsor-ingestion (T-015)
- Status: accepted
- Context: untrusted ATS payloads reach the extraction agent unchecked
- Decision: parse every inbound payload with Zod schemas defined in shared/
- Why / alternatives: Zod over io-ts (better DX, already pulled in via tRPC); hand-written
  type guards rejected — drift risk as payload shapes evolve
- Touches: shared/schemas/ats.ts, server/src/search/extract.ts
- Tradeoff: small runtime cost on the hot path — accepted (payloads are tiny)
```
