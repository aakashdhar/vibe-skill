# SPEC_REVIEW_REPORT.md

Summary format for vibe-spec-review Step 3. Save the completed summary to
`vibe/spec-reviews/[YYYY-MM-DD]-[trigger].md`.

The full record (every finding, every answer, every round) lives in the goldfish review
at `vibe/goldfish/<target>/resolution.md`. This summary is the one page someone reads to
know whether the spec is ready, so it never copies the findings out in full.

---

```markdown
# Spec Review — [Project Name]
> Triggered by: [brainstorm / agent / architect / new-app / init / add-feature / manual]
> Date: [date]
> Reviewed by: vibe-goldfish · [reviewers] · isolation [full | partial] · [N] rounds

## Documents reviewed
- [x] BRIEF.md
- [x] vibe/SPEC.md
- [ ] vibe/features/.../FEATURE_SPEC.md — not present

## Verdict
[✅ SPEC READY | ⚠️ SPEC READY WITH ACCEPTED RISKS | 🔴 SPEC NOT READY: reason]

## Findings
| | P0 | P1 | P2 |
|---|---|---|---|
| Found | [n] | [n] | [n] |
| Fixed | [n] | [n] | [n] |
| Contested with evidence | [n] | [n] | [n] |
| Accepted as a risk | [n] (by a person only) | [n] | [n] |
| Declined | — | — | [n] |

## Needs attention
[Only what a reader must know: each accepted risk with who accepted it, each open
escalation with the question for the person, any reviewer that did not run.
"Nothing" if empty.]

## Full record
vibe/goldfish/<target>/resolution.md
```
