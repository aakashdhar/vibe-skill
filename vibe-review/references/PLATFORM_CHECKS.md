# PLATFORM_CHECKS.md

Used by vibe-review Step 5. Apply **only** the section(s) matching the project's
stack (read the stack from CODEBASE.md). Each check names a severity — findings
still require a file path + line number to be logged (see REVIEW_REPORT.md).

> If the session has the first-party `/security-review` command available, run
> it for the Security section instead of hand-checking — it is deeper and
> produces structured findings. Use the checklist below as the fallback and to
> confirm project-specific concerns.

---

## React Web

- [ ] Components over ~200 lines or with >1 responsibility → P2 (extract)
- [ ] Business/data logic inside components instead of hooks/services → P1
- [ ] `useEffect` with missing/incorrect dependency array → P1 (stale data / loops)
- [ ] Direct `fetch`/DB access in a component (not a hook/service layer) → P1
- [ ] Keys using array index on reorderable lists → P2
- [ ] State that should be derived stored in `useState` → P2
- [ ] No error boundary around async/route-level UI → P1
- [ ] Uncontrolled re-renders (unmemoised expensive children) → P2
- [ ] Accessibility: interactive elements without roles/labels/keyboard support → P1

## React Native

- [ ] Business logic in screen components rather than hooks/services → P1
- [ ] Lists rendered with `.map` instead of `FlatList`/`SectionList` at scale → P1
- [ ] Missing `keyExtractor` / stable keys → P2
- [ ] Blocking work on the JS thread (no `InteractionManager`/async) → P1
- [ ] Images without dimensions or caching strategy → P2
- [ ] Platform-specific code not guarded (`Platform.select`) → P2
- [ ] No safe-area handling on notched devices → P2

## Node / Express

- [ ] Business logic in route handlers instead of a service layer → P0
- [ ] Direct DB queries outside a repository/data layer → P0
- [ ] No input validation at the API boundary (Zod/Joi/etc.) → P1
- [ ] Errors not funnelled through centralised error middleware → P1
- [ ] `async` route handlers without error propagation (unhandled rejection) → P1
- [ ] Secrets read inline instead of from validated config/env → P1
- [ ] No request timeouts / unbounded body size → P2
- [ ] Blocking synchronous calls on the event loop → P1

## Supabase

- [ ] Row Level Security (RLS) not enabled on user-facing tables → P0
- [ ] Service-role key used in client-side code → P0 CRITICAL
- [ ] Policies missing for insert/update/delete (read-only assumed) → P1
- [ ] Auth checks relying on client state instead of RLS/session → P0
- [ ] Storage buckets public when they should be private → P1
- [ ] Direct table access where an RPC/edge function is warranted → P2

## Security (universal — apply on every project)

See Step 7 in SKILL.md for the full universal + final-phase security checklist.
Key P0s: hardcoded secrets, `.env` not gitignored, unsanitised user input (XSS),
missing auth on protected routes, high/critical dependency vulnerabilities.
