# PIPELINE.md — canonical order, parity routing, and the design gate

The framework is a pipeline, but you can enter it at any point (an idea brought
from elsewhere, a dropped file, an existing repo). This file defines the canonical
order, how to detect where you are, and how to route to the missing steps so the
project reaches parity instead of silently skipping stages (design most often).

Any skill that starts a build (vibe-new-app, vibe-add-feature, vibe-design) should
run the **parity check** below at entry.

---

## Canonical order

```
THINK    brainstorm:  → spec-review (auto) → architect:
SCAFFOLD new:  (greenfield)   |   vibe-init:  (existing codebase)
DESIGN   design-md: (optional, brand tokens) → design:   ← REQUIRED for UI projects
BUILD    feature: → (design: if the feature introduces new UI) → review: → test:
SHIP     doctor: → deploy: → e2e:
CLOSE    document: → changelog: → handoff:
```

DESIGN sits **between SCAFFOLD and BUILD** — it is not an optional side-track. A
UI-bearing project must have a design pass (DESIGN_SYSTEM.md, and ideally
DESIGN.md / vibe/design/CONTRACT.md) before UI features are built, or every screen
is improvised and inconsistent.

---

## Artifact → stage map (how to detect where you are)

| Artifact present | Stage reached |
|------------------|---------------|
| `BRIEF.md` (canonical) | THINK done |
| `ARCHITECTURE.md` / `vibe/ARCHITECTURE.md` | architect done |
| `vibe/PLAN.md`, `vibe/SPEC.md`, `CLAUDE.md` | SCAFFOLD done |
| `DESIGN.md` and/or `vibe/DESIGN_SYSTEM.md` / `vibe/design/CONTRACT.md` | DESIGN done |
| code + tests + `vibe/reviews/` | BUILD underway |

---

## Parity check (run at entry)

1. **Classify the project:** does it have a **user-facing UI** (web/mobile/desktop
   screens)? APIs, CLIs, libraries, and pure backends are **non-UI** — design does
   not apply to them; skip the design gate automatically for those.
2. **Detect stage** from the artifact map. If an *upstream* artifact is missing,
   offer to produce it before continuing — don't proceed on a hollow base:
   - No/empty/foreign `BRIEF.md` → route to `brainstorm:` (its Step 0 ingests an
     external or dropped brief and normalizes it — this is how a Claude-desktop
     idea reaches parity).
   - `BRIEF.md` but no `ARCHITECTURE.md` → offer `architect:` (or generate the
     minimal ARCHITECTURE.md, as new-app Step 9 already does).
   - No `vibe/` folder → run `new:` (greenfield) or `vibe-init:` (existing code).
3. **Design gate (UI projects only):** if no design system exists
   (`DESIGN_SYSTEM.md` / `DESIGN.md` / `CONTRACT.md`), the project has **not**
   passed the design gate. Before UI features are built:
   > "This is a UI project with no design pass yet. Run `design:` now so screens
   >  share one derived design language? (Optionally `design-md:` first to lock
   >  brand tokens.) — recommended. Reply 'skip design' to proceed without it."
   Require an explicit choice. If skipped, log it in `vibe/DECISIONS.md`
   ("design gate skipped by user — UI will be improvised") so it's a visible
   decision, not a silent omission.

---

## Why this exists

The framework was authored to flow front-to-back from `brainstorm:`. Entering
mid-pipeline (idea from elsewhere, empty file, existing repo) previously skipped
whatever was upstream — most damagingly the design pass, because design was a
side-track nothing gated on. The parity check + design gate make the pipeline
self-healing from any entry point.
