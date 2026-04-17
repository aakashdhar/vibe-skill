# FIX_RISK_GUIDE.md

Used by vibe-perf Step 5 to classify every fix as Category A (safe) or Category B (risky).
Read this before building the fix plan.

---

## Classification rules

A fix is **Category A (safe)** if ALL of the following are true:
- Changes no public API interface or DB schema visible to other services
- Does not alter business logic — only how existing logic executes
- Can be verified by running the existing test suite
- Is reversible with a simple revert
- Affects at most 3 files

A fix is **Category B (risky)** if ANY of the following are true:
- Changes a public API response shape (adds/removes/renames fields)
- Changes a DB schema (adds/removes/modifies columns, indexes on existing data)
- Alters agent token budgets (affects output quality, may change pass/fail behaviour)
- Modifies state management in the orchestrator (changes data flow between agents)
- Splits a component into multiple (may require test updates)
- Changes import/export structure (may break tree-shaking assumptions)
- Touches a file with > 500 lines (higher blast radius, harder to reason about)

---

## Category A — Full list of safe fixes

### Frontend
| Fix | How to write | Risk if wrong |
|-----|-------------|--------------|
| Add `React.memo` | Wrap component export | Minimal — memo is opt-in |
| Add `useMemo` | Wrap expensive calculation | Low — memoisation is transparent |
| Add `useCallback` | Wrap handler passed as prop | Low |
| Add `loading="lazy"` to `<img>` | Add attribute | None |
| Migrate to `next/image` | Replace `<img>` with `<Image>` | Low — same visual output |
| Add `key` prop to mapped list | Add `key={item.id}` | None |
| Replace sequential awaits with `Promise.all` | Wrap independent fetches | Low — parallel fetch, same data |
| Add route-level code splitting | `React.lazy` + `Suspense` | Low — same routes, lazy loaded |
| Remove unused imports | Delete import line | None |

### Backend
| Fix | How to write | Risk if wrong |
|-----|-------------|--------------|
| Add DB index | `@@index([field])` in Prisma schema + migration | Low — additive, no data change |
| Add `LIMIT N` to unbounded query | Add `.take(100)` / `LIMIT 100` | Low — truncates large results |
| Add response caching header | `Cache-Control: max-age=60` on GET | Low |
| Move auth check to top of handler | Reorder existing code | Low |
| Wrap multi-step write in transaction | Add `prisma.$transaction(...)` | Low — safer, not riskier |
| Replace `SELECT *` with specific fields | List explicit columns | Low |

### Agentic
| Fix | How to write | Risk if wrong |
|-----|-------------|--------------|
| Trim system prompt | Remove boilerplate/examples | Low — same instructions, fewer tokens |
| Add structured output schema | Add `response_format` parameter | Low — more reliable, not less |
| Slice state before sub-agent call | Extract needed keys only | Low |
| Add exponential backoff | Replace bare retry | None — improves reliability |
| Add call timeout | Wrap with `asyncio.wait_for` | None |
| Add loop cap (`MAX_ATTEMPTS = 2`) | Add guard variable | None |

### Infrastructure
| Fix | How to write | Risk if wrong |
|-----|-------------|--------------|
| Add `mem_limit` to docker-compose service | Add `mem_limit: 512m` | Low |
| Add `cpus` limit to docker-compose | Add `cpus: '0.5'` | Low |
| Set Node.js heap size | Add `--max-old-space-size=1024` to start script | Low |
| Add multi-stage Dockerfile | Split build/runtime stages | Low — smaller image, same runtime |
| Add health check endpoint | Add `/health` route returning 200 | None |

---

## Category B — Full list of risky fixes

### Frontend
| Fix | Why risky | What to say to user |
|-----|----------|-------------------|
| Split large component | May break parent's test assertions | "Needs test review after split" |
| Change data fetching strategy | May change loading states/UX | "Review loading state handling" |
| Migrate state management | High blast radius | "Requires full regression test" |

### Backend
| Fix | Why risky | What to say to user |
|-----|----------|-------------------|
| Paginate list endpoint | Breaking API change — clients expect full list | "Check all API consumers first" |
| Restructure N+1 query | Changes DB access pattern, may affect data consistency | "Test with production-like data" |
| Add DB column | Schema migration on live data | "Test migration on staging first" |
| Remove field from API response | Breaking change for any consumer | "Check all callers of this endpoint" |

### Agentic
| Fix | Why risky | What to say to user |
|-----|----------|-------------------|
| Change token budget | May cause verifier pass rate to change | "Run baseline eval after change" |
| Restructure parallel dispatch | Changes execution order, test dependencies | "Re-run full E2E test suite" |
| Modify orchestrator state shape | High blast radius — all agents read state | "Review all agent state reads" |

### Infrastructure
| Fix | Why risky | What to say to user |
|-----|----------|-------------------|
| Change worker count | May overwhelm DB connection pool | "Check DB max_connections setting" |
| Change worker class (sync→async) | Requires all handlers to be async | "Audit all route handlers first" |

---

## When in doubt — Category B

If a fix doesn't clearly fit Category A by all criteria above — default to Category B.
It's better to ask once than to silently break something.
