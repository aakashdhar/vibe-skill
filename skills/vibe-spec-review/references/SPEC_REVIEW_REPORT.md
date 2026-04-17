# SPEC_REVIEW_REPORT.md

Output format template for vibe-spec-review Step 7.
Save completed report to vibe/spec-reviews/[YYYY-MM-DD]-[trigger].md

---

```markdown
# Spec Review — [Project Name]
> Triggered by: [brainstorm / agent / new-app / init / add-feature / manual]
> Date: [date]
> Reviewer: vibe-spec-review

---

## Documents audited
- [x] BRIEF.md
- [x] AGENT_ARCH.md
- [x] vibe/SPEC.md
- [x] vibe/ARCHITECTURE.md
- [ ] vibe/features/.../FEATURE_SPEC.md — [not present / audited]

---

## P0 — Critical findings ([N])

[If none:]
> ✅ No critical gaps found. Spec is ready to build.

[If found:]

### P0-001 · [Document] · [Section heading]
**Issue:** [Exact description of what is wrong — specific line or section]
**Why this matters:** [What will go wrong during the build if not fixed]
**Fix:** [Specific action — what to add, change, or remove]
**Example of good:**
```
[Show what the fixed version looks like]
```

### P0-002 · [Document] · [Section]
[repeat]

---

## P1 — Warnings ([N])

[If none:]
> ✅ No warnings.

### P1-001 · [Document] · [Section]
**Issue:** [What is weak or missing]
**Fix:** [Specific action]

[Group P1s by document for readability]

---

## P2 — Notes ([N])

[List inline — one line each]
- [Document] · [section] — [issue] — [quick fix]
- [Document] · [section] — [issue] — [quick fix]

---

## O'Reilly six core areas

| Area | Status | Notes |
|------|--------|-------|
| Commands | ✅ / ⚠️ / ❌ | [what's present or missing] |
| Testing | ✅ / ⚠️ / ❌ | [what's present or missing] |
| Project structure | ✅ / ⚠️ / ❌ | [what's present or missing] |
| Code style | ✅ / ⚠️ / ❌ | [what's present or missing] |
| Git workflow | ✅ / ⚠️ / ❌ | [what's present or missing] |
| Boundaries | ✅ / ⚠️ / ❌ | [what's present or missing] |

---

## Cross-document consistency

[If clean:]
> ✅ No contradictions found across documents.

[If issues found:]
| Contradiction | Documents | Severity |
|--------------|-----------|---------|
| Stack mismatch: SPEC says React, ARCHITECTURE says Vue | SPEC.md ↔ ARCHITECTURE.md | P0 |
| Scope conflict: feature X in FEATURE_SPEC, excluded in SPEC | FEATURE_SPEC.md ↔ SPEC.md | P0 |

---

## Verdict

```
[✅ SPEC READY]
  0 P0 · [N] P1 · [N] P2
  Proceed to [next step — architect: / new: / feature build].

[⚠️  SPEC HAS WARNINGS]
  0 P0 · [N] P1 · [N] P2
  Build can proceed. Fix warnings before Phase 2 begins.
  Say "fix all P1s" to resolve, or "continue anyway" to proceed.

[🔴 SPEC HAS CRITICAL GAPS]
  [N] P0 · [N] P1 · [N] P2
  Recommend fixing P0s before building.
  Say "fix [P0-001]" to fix specific findings.
  Say "fix all P0s" to fix all critical gaps now.
  Say "continue anyway" to proceed with findings logged.
```

---

## Actions taken
[Filled in after user responds]
- [fixed / continued with warnings / fully resolved]
- Fixed: [list of findings fixed]
- Deferred: [list of findings acknowledged but not fixed]
```
