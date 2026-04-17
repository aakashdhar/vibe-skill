---
name: vibe-review
description: >
  Evidence-based code review skill — mandatory gate after every phase completes.
  Triggers on "review:" prefix, "review the code", "code review", "audit the codebase",
  "check code quality", "review phase N", "is the code ready", "quality check".
  Mandatory gate: Phase N cannot proceed to Phase N+1 without review passing with no P0 issues.
  Final phase review blocks deploy until all P0 and P1 issues are resolved.
  Acts as Senior Engineer, Architect, and Code Quality Auditor.
  Gracefully handles missing ARCHITECTURE.md — reviews against PLAN.md patterns instead.
  Automated checks adapt to project stack (not npm-only).
  Every finding backed by file path and line number. No vague feedback.
---

# Vibe Review Skill

Mandatory quality gate after every phase.
Acts as **Senior Engineer, Architect, and Code Quality Auditor**.
Evidence-based. Every finding backed by file path and line number.

**Always run in Plan Mode (Shift+Tab). Never writes feature code.**

---

## The O'Reilly principle this enforces

Issues caught at Phase 1: cheap — fix once, never propagates.
Issues caught at Phase 3: expensive — retrofit across every feature.
Issues caught at deploy: very expensive — production risk.

Without a review gate, bad patterns from Phase 1 get copied into every feature.
Architecture drifts silently. Duplication builds. Quality degrades.

---

## When this skill runs

**Mandatory — phase gates:**
```
Phase 1 complete → review: phase 1 → gate passed? → Phase 2 begins
Phase 2 complete → review: phase 2 → gate passed? → Phase 3 begins
Final phase      → review: final  → gate passed? → deploy unlocked
```

**On demand:**
```
review: phase 2 invoice management
review: audit the Supabase integration
review: full codebase before new team member
```

**Gate rules:**
- P0 → blocks progression, fix tasks in TASKS.md immediately
- P1 → logged to backlog.md, must resolve before deploy
- Final phase: P0 AND P1 both must be zero before deploy
- No P0s → gate passes, next phase begins

---

## Documents this skill reads

Read in this order. Note if any are missing.

1. `vibe/ARCHITECTURE.md` — primary reference for drift detection
2. `vibe/CODEBASE.md` — exact file paths as-built
3. `vibe/SPEC.md` — acceptance criteria to verify against
4. `vibe/DECISIONS.md` — past decisions, context for why things are as they are
5. `vibe/PLAN.md` — phase scope, what was meant to be built
6. `vibe/TASKS.md` — what tasks completed this phase
7. `vibe/reviews/` — all previous review files for carryover tracking
8. `BRIEF.md` *(if exists)* — original intent and core value
9. `CLAUDE.md` — boundaries and conventions

**If vibe/ARCHITECTURE.md does not exist:**
> Flag this as a finding in the report: "ARCHITECTURE.md not found — no explicit architecture
> decisions documented. Pattern compliance reviewed against PLAN.md and CODEBASE.md instead."
> Use PLAN.md folder structure, tech stack, and conventions as the reference baseline.
> Recommend running `architect:` to formalise decisions. This is a P1 finding.

---

## Step 0A — Concept boundary pre-screening (graph-assisted)

**Check for dependency graph before reading any source files:**
```bash
ls vibe/graph/CONCEPT_GRAPH.json 2>/dev/null && echo "GRAPH EXISTS" || echo "NO GRAPH"
```

**If graph exists — run boundary pre-screening:**

Read `vibe/graph/DEPENDENCY_GRAPH.json` and check for cross-concept imports
that violate ARCHITECTURE.md patterns:

```python
import json

dep_g = json.load(open('vibe/graph/DEPENDENCY_GRAPH.json'))
arch_violations = []

for file_path, node in dep_g.items():
    file_concept = node.get('concept', 'foundation')
    for imported in node.get('imports', []):
        imported_node = dep_g.get(imported, {})
        imported_concept = imported_node.get('concept', 'foundation')

        if file_concept != imported_concept and imported_concept != 'foundation':
            # Frontend component importing backend/agent directly → DIP violation
            if node.get('type') == 'component' and imported_node.get('type') in ['agent', 'service', 'model']:
                arch_violations.append({'file': file_path, 'imports': imported,
                    'issue': 'Frontend directly imports backend — DIP violation', 'severity': 'P1'})
            # Agent calling another agent directly (bypasses orchestrator)
            elif node.get('type') == 'agent' and imported_node.get('type') == 'agent':
                if 'base_agent' not in imported:
                    arch_violations.append({'file': file_path, 'imports': imported,
                        'issue': 'Agent directly imports agent — bypasses orchestrator', 'severity': 'P1'})

for v in arch_violations:
    print(f"{v['severity']}: {v['file']} → {v['imports']} ({v['issue']})")
```

**Flagged files** → deep review (read source, check thoroughly)
**Clean files** → standard review (check naming, size, test coverage only)

This pre-screening surfaces most P1 architectural findings before reading
a single source file. On a clean codebase: 0 violations, shallower reads.
On a drifting codebase: violations surface immediately, guide where to look.

**If no graph exists — proceed with standard full read:**
No pre-screening available. Read all files in the phase as normal.

---

## Step 0 — Run automated checks first

Run these before reading any code. Adapt to the project stack from CODEBASE.md section 2.

**Node / npm projects:**
```bash
npm test              # Failures are P0
npx eslint . --quiet  # Errors are P0, warnings are P2
npx tsc --noEmit      # TypeScript errors are P0
npm audit             # High/critical = P0, moderate = P1
```

**Python projects:**
```bash
pytest                # Failures are P0
ruff check .          # Errors are P0
mypy .                # Type errors are P0
pip-audit             # Critical vulnerabilities are P0
```

**Flutter / Dart projects:**
```bash
flutter test          # Failures are P0
flutter analyze       # Errors are P0
dart pub audit        # Critical vulnerabilities are P0
```

**No test runner configured:**
Flag as P1: "No automated test runner configured. Tests exist but cannot be run automatically."

Include full tool output in the review report.
If a check fails with P0-level findings: document output, do not stop — continue full review.
Machines verify first, agent verifies second.

---

## Step 1 — Establish review scope

**Scoping rule:** If this phase modified more than 30 files, review feature by feature.
Generate a sub-report per feature, then synthesise into one phase report.
Do not attempt to review 30+ files in a single pass — quality degrades.

**Review focus by phase:**

Phase 1 — Foundation integrity:
Is this a solid base? Patterns, abstractions, folder structure, TypeScript setup, shared utilities.

Phase 2+ — Incremental delta + integration:
What this phase added + does it integrate cleanly? Cross-phase consistency. Emerging duplication.

Final phase — Full production readiness:
Everything. Performance, security, accessibility, error handling, bundle size. Strictest gate.

---

## Step 2 — Carryover check

Read all `vibe/reviews/phase-N-review.md` files. Read `vibe/reviews/backlog.md`.

**If no previous reviews exist** (this is Phase 1):
State: "No previous reviews — this is the first review. No carryover to check."
Skip carryover section in the report.

**If previous reviews exist:**
For each previously logged issue, check current state:
```
✅ P1-001 — [Issue] — RESOLVED
⚠️ P1-002 — [Issue] — STILL PRESENT — escalating to P0 (appeared in 2+ reviews)
❌ P1-003 — [Issue] — NOT ADDRESSED — remains P1
```

Escalation rule: unresolved P0 from previous phase → highest priority.
P1 appearing unresolved across 2+ phase reviews → escalate to P0.
P2 appearing unresolved across 3+ phase reviews → escalate to P1.

---

## Step 3 — Architecture drift detection

**Most important section. Check ARCHITECTURE.md (or PLAN.md if no ARCHITECTURE.md) first.**

For each documented decision, check the actual code.

Drift format:
```
🔴 ARCHITECTURE DRIFT — [Section violated]
   Decision: "[exact quote from ARCHITECTURE.md or PLAN.md]"
   Found: [file path] line [N]
          [exact violation]
   Decision origin: [architect: session / D-ID / PLAN.md]
   Impact: [what breaks or degrades]
   Fix: [specific action]
```

Check:
- Folder structure — all new files in correct folder?
- Naming conventions — files, components, hooks, utilities match exactly?
- State management — correct layer for each type of state?
- Data fetching — all calls going through the abstraction layer?
- Component patterns — functional, one per file, props typed?
- TypeScript — strict mode, no any, all params typed?
- Error handling — following the documented strategy?
- Testing — co-located files, names describe behaviour?

Any violation = P0. Architecture drift that propagates is expensive.

---

## Step 4 — SOLID principles review

Read each source file created or modified this phase. Every violation cites file path and line.

**SRP:** Each component/hook/service has one reason to change.
- >500 lines → P1. >1000 lines → P0 CRITICAL.
- Component handling both UI AND business logic → extract hook.

**OCP:** New features added without modifying existing working code?
- Conditional chains replacing polymorphism? Flag.

**LSP:** Components/functions behave consistently across implementations?
- Hook return shapes consistent — all returning `{ data, loading, error }`?

**ISP:** Props interfaces not forcing unused props?
- Props interface >10 props (especially optional) → P1.

**DIP:** High-level components depend on abstractions, not concrete implementations?
- Direct DB client import in component → P0 CRITICAL
- Direct localStorage in component → P1

---

## Step 5 — Platform-specific review

Read `references/PLATFORM_CHECKS.md`. Apply the section matching this project's stack
(from CODEBASE.md section 2).

Platforms covered: React Web · React Native · Node/Express · Supabase · Security (universal)

---

## Step 6 — Code quality analysis

**Component size audit:** Log every component exceeding thresholds.
**Duplication analysis:** Patterns repeated across 3+ files → extract.
**TypeScript quality:** Count `any` usages — each is P0.
**Test quality:** Names describe behaviour, not implementation. AAA structure present.

---

## Step 7 — Security review

**Universal — all projects, all phases:**
```bash
# Include npm audit / pip-audit output from Step 0
```
- [ ] Hardcoded secrets, tokens, API keys → P0 CRITICAL
- [ ] `.env` in `.gitignore` → P0 if missing
- [ ] User input rendered without sanitisation (XSS) → P0
- [ ] Auth checks before protected content → P0 if missing
- [ ] Sensitive data not logged → P1
- [ ] Input validation at API boundary → P1 if missing
- [ ] Dependency vulnerabilities: high/critical = P0, moderate = P1

**Final phase review only (additional checks):**
- [ ] CORS not configured as `*` in production → P1
- [ ] Security headers (Helmet or equivalent) → P1
- [ ] Rate limiting on public endpoints → P1
- [ ] HTTPS enforced in production config
- [ ] Content Security Policy (CSP) headers set
- [ ] Session management correct
- [ ] Zero high/critical dependency vulnerabilities (must be zero before deploy)

---

## Step 8 — Testing review

- Tests present for all business logic? (missing → P1)
- Test names describe behaviour? (implementation names → P2)
- AAA structure? (missing → P2)
- Edge cases and error states covered for critical paths? (missing → P1)
- Coverage estimate >70% on business logic? (below → P1)

---

## Step 9 — Generate the review report

Read `references/REVIEW_REPORT.md` for the full template.

Save to `vibe/reviews/phase-[N]-review.md`.

**Quality score formula:**
- Start at 10.0
- Subtract 1.0 per P0 finding
- Subtract 0.5 per P1 finding
- Subtract 0.2 per P2 finding
- Subtract 0.1 per P3 finding
- Subtract 0.5 additional per architecture drift violation

**Evidence standard — non-negotiable:**
Every P0 and P1 must have file path + line number + specific actionable recommendation.
"Some components are too complex" — rejected, no file path.
If a finding cannot be backed by evidence — it does not go in the report.

---

## Step 10 — Update vibe/TASKS.md

**P0 issues found — insert blocking tasks:**
```
🔴 Review fixes required — Phase [N] gate (0/N)
   Must complete before Phase [N+1] begins.
   [ ] RFX-001 · [P0 fix — plain English]
                 File: [path] · Issue: [one line]
   → Full report: vibe/reviews/phase-[N]-review.md

## Phase gates
Phase [N] → Phase [N+1]:  🔴 BLOCKED — [N] P0 issues, fix tasks above
```

**No P0 issues — update gate status:**
```
## Phase gates
Phase [N] → Phase [N+1]:  ✅ reviewed [date] — 0 P0, [N] P1 logged to backlog
```

---

## Step 11 — Update vibe/reviews/backlog.md

Add all P1/P2/P3 findings. Use the format in `references/REVIEW_REPORT.md`.

---

## Step 12 — Update vibe/ARCHITECTURE.md (if gaps found)

If review reveals a pattern being used that isn't documented:
- Add to the relevant section with `> 📝 [date] · Added during phase-[N] review`
- Log in DECISIONS.md if it changes something previously decided

---

## Step 13 — Signal done and generate hooks

**Read execution mode:**
```bash
grep "VIBE_MODE" CLAUDE.md 2>/dev/null | cut -d= -f2 | tr -d ' '
```

**Standard output (both modes):**
```
## Phase [N] Review Complete

📊 Score: [X/10] — Grade [A-F]
🏗️  Architecture drift: [N issues / none]
🔴 P0 issues: [N — fix tasks in TASKS.md / none]
🔶 P1 issues: [N — logged to backlog]
📋 Report: vibe/reviews/phase-[N]-review.md
```

**If `manual` or not set — standard gate message:**
```
Gate decision:
[✅ PASS — Phase [N+1] may begin. Say "next" to continue.]
[🔴 BLOCKED — complete RFX tasks in TASKS.md first, then say "next".]
```

**If `autonomous` — structured signal for calling skill:**

On PASS (0 P0s):
```
REVIEW_RESULT: PASS
P0: 0 | P1: [N] | P2: [N]
AUTONOMOUS: Phase [N] complete — proceeding to next phase automatically.
```
Return control to the calling skill. It continues the autonomous loop.

On FAIL (any P0s):
```
REVIEW_RESULT: FAIL
P0: [N] | P1: [N] | P2: [N]
AUTONOMOUS: PAUSED — [N] P0 issue(s) require human resolution.

[List each P0 with file path, line, and specific fix]

Fix the above, then say "resume" to continue autonomous execution.
```
Wait for human. Do not proceed. When human says "resume" — re-run
this review step automatically, then signal result again.

---

## Step 14 — Generate .claude/settings.json hooks (Phase 1 review only)

After the very first phase review (Phase 1), check if `.claude/settings.json`
has a PostToolUse lint hook. If not — offer to add it:

> "Phase 1 review complete. One quick setup: adding a lint+typecheck hook
> will catch TypeScript errors and ESLint violations as soon as they're
> introduced rather than at the next phase gate. Want me to add it? (y/n)"

If yes — create or update `.claude/settings.json`:

```bash
# Create .claude directory if needed
mkdir -p .claude

# Write settings.json with PostToolUse hook
cat > .claude/settings.json << 'EOF'
{
  "hooks": {
    "PostToolUse": [
      {
        "matcher": "Edit|Write",
        "hooks": [
          {
            "type": "command",
            "command": "npm run lint --silent 2>&1 | tail -10 || true"
          }
        ]
      }
    ]
  }
}
EOF
```

For Python projects:
```json
{
  "hooks": {
    "PostToolUse": [{
      "matcher": "Edit|Write",
      "hooks": [{
        "type": "command",
        "command": "ruff check . 2>&1 | tail -10 || true"
      }]
    }]
  }
}
```

For TypeScript projects with typecheck:
```json
{
  "hooks": {
    "PostToolUse": [{
      "matcher": "Edit|Write",
      "hooks": [{
        "type": "command",
        "command": "npm run lint --silent 2>&1 | tail -5; npx tsc --noEmit 2>&1 | tail -5 || true"
      }]
    }]
  }
}
```

Tell the user:
> "Hook added to .claude/settings.json. From now on, lint runs automatically
> after every file edit. ESLint errors surface immediately — no more discovering
> them at phase gate review."

If `.claude/settings.json` already has hooks — skip this step silently.
If the user says no — skip and note they can add it manually later.

---

## Always-flag anti-patterns

**P0 — Critical:**
1. Direct DB client import in component (DIP violation)
2. Component >1000 lines (SRP violation CRITICAL)
3. `any` type anywhere (TypeScript violation)
4. Hardcoded secrets/tokens/API keys (security CRITICAL)
5. Auth check missing on protected route/endpoint (security CRITICAL)
6. Architecture drift from ARCHITECTURE.md (or PLAN.md if no ARCHITECTURE.md)
7. npm/pip audit high/critical vulnerability
8. TypeScript compilation errors
9. All tests failing (if test runner exists)

**P1 — Fix before deploy:**
9. Component >500 lines (SRP violation)
10. Direct storage/localStorage without abstraction (DIP)
11. Missing error boundaries on data-fetching components
12. Hooks managing multiple unrelated concerns
13. Props interface >10 props (ISP violation)
14. console.log in production code
15. Test names describing implementation not behaviour
16. Missing tests for business logic
17. ARCHITECTURE.md not present (recommend running architect:)

---

## Pre-submission checklist

- [ ] Automated checks run — output included in report
- [ ] Every P0 and P1 has file path and line number
- [ ] Drift checked against ARCHITECTURE.md (or PLAN.md if missing) — not generic rules
- [ ] Carryover from previous reviews addressed (or stated as first review)
- [ ] Quality score calculated using the formula — not estimated
- [ ] Strengths acknowledged with file references
- [ ] RFX tasks in TASKS.md for all P0 issues
- [ ] P1/P2/P3 logged to vibe/reviews/backlog.md
- [ ] Gate decision stated clearly
- [ ] No section TBD or skipped
- [ ] Report saved to vibe/reviews/phase-[N]-review.md
