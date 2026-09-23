# REVIEW_REPORT.md

Used by vibe-review Step 9 (report) and Step 11 (backlog). Every P0 and P1 entry
**must** carry a file path + line number + a specific, actionable recommendation.
No evidence → the finding does not go in the report.

---

## Phase review report template

Save to `vibe/reviews/phase-[N]-review.md`:

```markdown
# Phase [N] Review — [Project Name]
> Reviewed [date] · Reviewer: vibe-review · Commit: [git short sha]

## Verdict
[✅ PASS — 0 P0] | [🔴 BLOCKED — [N] P0 must be fixed before Phase [N+1]]
Quality score: [X.X]/10

## Scope
Files reviewed: [count] · Phase [N] changes since [previous gate/sha].
[If >30 files: reviewed feature by feature — list the slices.]

## Findings

### P0 — Critical (block the phase gate)
- **[P0-1] [One-line title]**
  - File: `path/to/file.ts:LINE`
  - Issue: [what is wrong, concretely]
  - Fix: [specific actionable recommendation]

### P1 — High (blocks this phase's gate; fix via RFX tasks)
- **[P1-1] [Title]** — `path:LINE` — [issue] → [fix]

### P2 — Medium (should fix)
- **[P2-1] [Title]** — `path:LINE` — [issue] → [fix]

### P3 — Low / nits
- **[P3-1] [Title]** — `path:LINE` — [note]

## Structured findings (machine-readable)
```json
{
  "phase": [N],
  "date": "[ISO date]",
  "score": [X.X],
  "counts": { "P0": 0, "P1": 0, "P2": 0, "P3": 0 },
  "findings": [
    { "id": "P0-1", "severity": "P0", "category": "security|solid|quality|testing|drift|platform|performance",
      "file": "path/to/file.ts", "line": 0, "issue": "…", "fix": "…" }
  ]
}
```
> The JSON block lets vibe-progress / vibe-cost / CI read P0/P1 counts without
> scraping prose. Keep it in sync with the human list above.

## Architecture drift
[Any deviation from vibe/ARCHITECTURE.md — each is P0. Cite file:line + the rule.]

## What was done well
[1-3 genuine positives — keeps the report honest and calibrated.]
```

---

## Backlog entry format (Step 11 → vibe/reviews/backlog.md)

```markdown
## Outstanding P1 Issues
- [ ] [P1-1] [Title] — `path:LINE` — [issue] → [fix] — found phase [N] ([date])

## Outstanding P2 Issues
- [ ] [P2-1] [Title] — `path:LINE` — [issue] → [fix] — found phase [N] ([date])

## Resolved Issues
- [x] [P1-x] [Title] — resolved phase [M] ([date])
```

## Escalation rules (applied when logging to backlog)
- A P1 unresolved across **2+** phase reviews → escalate to P0.
- A P2 unresolved across **3+** phase reviews → escalate to P1.
- Exception: an item the user has explicitly accepted as "won't fix (accepted
  risk)" is tagged as such and does **not** auto-escalate — record the reason.
