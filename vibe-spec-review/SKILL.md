---
name: vibe-spec-review
description: >
  Spec quality gate: an independent review of planning documents before any code is
  written. Runs on BRIEF.md (after vibe-brainstorm), AGENT_ARCH.md (after vibe-agent),
  ARCHITECTURE.md (after vibe-architect), SPEC.md (after vibe-new-app / vibe-init) and
  FEATURE_SPEC/PLAN/TASKS (after vibe-add-feature). The agent that wrote the documents
  never judges them: vibe-goldfish sends fresh read-only subagents that never saw the
  conversation to check them against the vibe rubrics, for comprehension, scope, design,
  readiness and fit with the code. P0 and P1 findings block until fixed, contested with
  evidence, or accepted by a person; P2 are notes. Triggers on "spec-review:", "review the spec", "check the brief",
  "audit the spec", "is the spec ready", "review before we build". Always use when
  planning documents exist and a build is about to begin.
---

# Vibe Spec Review Skill

Checks every planning document before a line of code is written, for gaps,
contradictions, untestable criteria and missing boundaries that would cause failures,
confusion or rework during the build.

> **Autonomous / headless mode.** At startup resolve the settings with
> `python3 ~/.claude/skills/vibe-mode/scripts/vibe_state.py mode` (`mode --run` when
> entered from `vibe-mode: run`). If `vibe_mode` is `autonomous`, nothing here waits for
> the user: vibe-goldfish applies fixes and records answers on its own (its Step 6), and
> stops, writing `vibe/.run_state.json`, only when a person is required.

A bad spec is the most expensive bug in software. This skill finds it before it costs
anything.

---

## The principle

The O'Reilly northstar is clear: "Most agent files fail because they're too vague."
Vague specs produce vague code. Untestable criteria produce unverifiable builds.
Missing boundaries produce agents that go off-script at the worst moment.

This skill asks: **if an agent read only these documents, would it build the right
thing?** The only honest way to answer that is to give the documents to an agent that
has read only them. The session that wrote a spec can't answer it, because it fills
every gap from memory without noticing. So this skill never audits documents in the
author's context. It hands them to **vibe-goldfish**, whose reviewers start fresh with
the files and nothing else, and it keeps the vibe rubrics (`references/`) as the
standard they apply.

---

## Trigger points: how this skill is invoked

Most of the time another skill hands off to this one (Triggers 1 to 4). The user can also
run it on demand with `spec-review:` (Trigger 5). Each trigger maps to a vibe-goldfish
**preset** (`vibe-goldfish/references/PRESETS.md`), which fixes the documents, reviewers
and standards.

| Trigger | Invoked by | Announcement | Preset |
|---|---|---|---|
| 1 | final step of `vibe-brainstorm`, after BRIEF.md | *"BRIEF.md written. Running an independent spec review before architect:..."* | `brief` |
| 2 | final step of `vibe-agent`, after AGENT_ARCH.md | *"AGENT_ARCH.md written. Running an independent review of the agent design..."* | `agent-arch` |
| 2.5 | final step of `vibe-architect`, after ARCHITECTURE.md | *"Architecture drafted. Running an independent review before you scaffold..."* | `architecture` |
| 3 | `vibe-new-app` Step 6, after SPEC.md, PLAN.md and vibe/ARCHITECTURE.md are drafted (before any derived file) / `vibe-init` Stage 6 | *"SPEC, PLAN and ARCHITECTURE drafted. Running an independent spec review before you sign off..."* | `spec` (new-app) · `init` (vibe-init) |
| 4 | `vibe-add-feature`, after FEATURE_SPEC + FEATURE_PLAN | *"Feature designed. Running an independent review before the tasks are written..."* | `feature` (with the feature folder) |
| 4T | `vibe-add-feature`, after FEATURE_TASKS | *"Tasks written. Running an independent readiness review before the build..."* | `feature-tasks` (with the feature folder) |
| 6 | `vibe-change-spec`, after it edits reviewed documents | *"Scope changed. Re-running the independent review on the changed documents..."* | the preset of each changed document (`brief`, `architecture`, `spec`, `init`, `feature`, `feature-tasks`) |
| 5 | the user types `spec-review:` | none needed | `all`, or the preset matching a named document |

What each review catches, by trigger:
- **1:** vague goals, untestable success criteria, missing user definition, undefined constraints.
- **2:** missing VerifierAgents, undefined HITL gates, hallucinated tools, agents with several jobs, state with several writers.
- **2.5:** missing patterns and conventions, empty Always/Ask First/Never tiers, no "never commit secrets" rule, stack drift from the brief.
- **3:** spec-architecture contradictions, missing acceptance criteria, an undefined stack, a provisional SPEC.md (vibe-init).
- **4:** untestable feature criteria, missing scope boundaries, contradictions with SPEC.md, plans that ignore the code that exists.
- **4T:** tasks without files, tasks that leave a design decision to the builder, an order that breaks the build, a missing test plan.
- **6:** whatever the change broke: a new criterion that contradicts the brief, a plan that no longer matches the spec.

---

## Step 0 — Detect what exists

```bash
ls BRIEF.md AGENT_ARCH.md SPEC.md ARCHITECTURE.md CLAUDE.md \
   vibe/SPEC.md vibe/ARCHITECTURE.md vibe/PLAN.md vibe/CODEBASE.md \
   vibe/features/*/FEATURE_SPEC.md vibe/features/*/FEATURE_PLAN.md \
   vibe/features/*/FEATURE_TASKS.md 2>/dev/null
```

Keep only the documents that exist. Never fail because one is missing: review what's
there. If nothing exists:
> "No planning documents found. Run `brainstorm:` to start."
Stop.

---

## Step 1 — Run the independent review

Invoke **vibe-goldfish** with the preset for this trigger (and the feature folder for
`feature`). If this skill was entered from `vibe-mode: run`, say so to vibe-goldfish, so
it reads the settings with `mode --run` too. It does all of this:

- starts one fresh, read-only reviewer per lens. The rubric reviewer applies
  `references/CHECKLISTS.md` and the example rubrics (`BRIEF_RUBRIC.md`,
  `AGENT_ARCH_RUBRIC.md`, `SPEC_RUBRIC.md`) literally; the others check comprehension,
  scope, design, readiness and the code;
- has the author (this session) answer every finding under its rules: fix, contest with
  evidence, escalate to a person, or decline a P2;
- repeats with fresh reviewers until two rounds in a row are clean, or stops for a
  person on escalation, churn or the round cap;
- records everything in `vibe/goldfish/<target>/`.

Don't run the checklists yourself, before or after. A self-audit next to the goldfish
review would bring back exactly the bias this skill exists to remove.

**If vibe-goldfish reports "not run: no subagent tool"**, the review did not happen. Never
substitute a self-review. Manual mode: tell the user plainly and offer **(a)** stop here
and run `spec-review:` from a normal session *(recommended)*, or **(b)** continue without
a review. On (b) the verdict is ⚠️ SPEC NOT REVIEWED: skip the `goldfish.py status` call
in Step 2, and in Step 4 write a standalone DECISIONS.md entry
(`### D-[ID] — Spec review not run: [trigger]`, with the reason and that the user chose to
continue). Autonomous mode: write
`run-state set --status needs_human --reason "spec review could not run: no subagent tool"`
and stop.

---

## Step 2 — Verdict

Read the result: `python3 ~/.claude/skills/vibe-goldfish/scripts/goldfish.py status <target> --json`.

| Goldfish result | Verdict |
|---|---|
| `converged`, nothing accepted as a risk | ✅ **SPEC READY.** Proceed to [next step]. |
| `converged`, some findings accepted as risks (escalated and accepted: P0/P1 by a person, P2 by a person or the agent) | ⚠️ **SPEC READY WITH ACCEPTED RISKS.** List them, with who accepted each. |
| `needs_human`, or a person stopped the loop | 🔴 **SPEC NOT READY.** Give the reason from `status` and what the person needs to decide. |
| not run (no subagent tool), the user chose to continue | ⚠️ **SPEC NOT REVIEWED.** Say plainly that no independent review happened. |

P0 means the build cannot proceed or will build the wrong thing. P1 means likely rework.
Both block until they are fixed, contested with evidence, or accepted as a risk by a
person. An agent may accept only a P2 (vibe-goldfish Step 6), and goldfish.py refuses
anything more. P2 is a note.

---

## Step 3 — Present and hand back

Write `vibe/spec-reviews/[YYYY-MM-DD]-[trigger].md` from
`references/SPEC_REVIEW_REPORT.md`: a one-page summary that links to the full record in
`vibe/goldfish/<target>/resolution.md`.

Show the user the verdict in this shape:

```
SPEC REVIEW — [Project Name] — [trigger]
══════════════════════════════════════════
Documents:  [list]
Reviewed by: [reviewers] · fresh subagents, isolation [full|partial] · [N] rounds
Found:      P0 [n] · P1 [n] · P2 [n]
Answered:   [n] fixed · [n] contested with evidence · [n] escalated · [n] declined (P2)
Verdict:    [✅ / ⚠️ / 🔴 line from Step 2]
Full record: vibe/goldfish/<target>/resolution.md
```

**Manual mode, 🔴 verdict:** the person decides, as vibe-goldfish Step 7 asks: more
rounds, rework the documents, or "continue anyway". "Continue anyway" is recorded as the
person accepting the documents as they are (DECISIONS.md and the report). Then return to
the calling skill.

**Autonomous mode:** vibe-goldfish has already applied the fixes and recorded the
answers. ✅/⚠️ → return to the caller. 🔴 → vibe-goldfish has written `needs_human`. Stop,
because a spec with an open question a person must answer must not be built.

**The caller asks for approval after this review, never before.** A person approves the
documents as the review left them, fixes included. A caller that asked for approval on
the draft asks again on the reviewed text (manual), or records the gate per APPROVALS
(autonomous). Files derived from the reviewed documents are generated only after that.

This skill never sets the spec **gate** itself. The calling skill (vibe-new-app Step 10S, vibe-init Stage 8)
records the sign-off once the plan is final, and an agent's sign-off is accepted only
with `--report vibe/goldfish/spec` pointing at a converged review (vibe_state.py checks).

---

## Step 4 — Record the decision

`vibe/DECISIONS.md` is append-only. If it doesn't exist, create it with its canonical
header (vibe-new-app's DECISIONS template). Otherwise add to the end and never rewrite
existing entries. vibe-goldfish has already written its own `Goldfish review` entry; add
one line under it:

```
- **Spec review verdict** ([trigger]): [READY | READY WITH ACCEPTED RISKS | NOT READY: reason] · report: vibe/spec-reviews/[date]-[trigger].md
```

---

## Absolute rules

**The author never audits its own documents.** The review happens in fresh subagents
through vibe-goldfish, or it doesn't happen and the user is told so. No self-check stands
in for it.

**Documents change only through answered findings.** The only edits this skill makes are
fixes to findings, made the way vibe-goldfish allows: proposed and accepted by the user in
manual mode, applied and recorded in autonomous mode. Never silently rewrite a spec.

**Every finding is specific.** "The spec is vague" is not a finding. "vibe/SPEC.md ·
Login: 'users should have a good experience' is untestable, no measurable criterion" is.
Severity follows the rubrics: P0 is reserved for build-breaking gaps.

**Settled findings stay settled.** A finding the user accepted, or that was contested with
evidence, is not raised again: vibe-goldfish links repeats to it and settles them.

**Cross-document consistency always runs.** Whenever two or more documents are in scope,
the rubric reviewer checks them against each other (CHECKLISTS.md §6). Contradictions
between documents are where the most dangerous gaps hide.
