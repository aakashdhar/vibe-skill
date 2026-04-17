# RUNBOOK_TEMPLATE.md

Used by vibe-handoff Step 3 to generate RUNBOOK.md for maintenance mode.
Operations guide for client's dev team taking over maintenance.
No assumed knowledge. Exact commands. What to do when things go wrong.

---

```markdown
# Operations Runbook — [Project Name]
**For:** [Client company] dev team
**Prepared by:** BetaCraft
**Date:** [date]
**Last updated:** [date]

> This runbook covers the operations a maintenance developer will
> regularly perform. For architecture context, read ARCHITECTURE_GUIDE.md.
> For known issues, read KNOWN_ISSUES.md.
> For escalation, read ESCALATION.md.

---

## System overview

**What's running where:**

| Service | Platform | URL | Access |
|---------|---------|-----|--------|
| Frontend | [e.g. Vercel] | [URL] | [how to access dashboard] |
| Backend API | [e.g. Railway] | [URL] | [how to access dashboard] |
| Database | [e.g. Supabase] | [URL] | [how to access dashboard] |
| Monitoring | [e.g. Sentry] | [URL] | [how to access] |

---

## Operation 1 — Deploying a new version

**When to use this:** When a new version of the code is ready to go live.

**Before you start:**
- [ ] All tests passing: `npm test`
- [ ] Build succeeds: `npm run build`
- [ ] Changes reviewed and approved by [who]

**Steps:**
```bash
# 1. Merge changes to main branch
git checkout main
git merge [branch name]

# 2. Push to trigger automatic deployment
git push origin main

# 3. Monitor deployment
# Open [deployment platform] dashboard
# Watch for deployment status — takes approximately [N] minutes
```

**Verify it worked:**
- [ ] Deployment shows "Success" in [platform] dashboard
- [ ] Open [production URL] — app loads correctly
- [ ] Test [specific critical path — e.g. "log in and complete one full workflow"]
- [ ] Check Sentry — no new errors in first 5 minutes

**If something goes wrong:** See Operation 2 (Rollback).

---

## Operation 2 — Rolling back a deployment

**When to use this:** When a deployment breaks something and you need
to restore the previous working version immediately.

**Steps:**
```bash
# Option A — Revert via platform dashboard (fastest)
# 1. Open [deployment platform] dashboard
# 2. Go to Deployments > [previous successful deployment]
# 3. Click "Redeploy" or "Promote to production"
# Takes approximately [N] minutes

# Option B — Git revert (if platform rollback not available)
git revert HEAD
git push origin main
```

**Verify rollback worked:**
- [ ] App loads at [production URL]
- [ ] [Critical path] works correctly
- [ ] Log the incident in [issue tracker / Slack]

**After rollback:** Investigate what caused the failure before re-deploying.
Contact BetaCraft if root cause is unclear (see ESCALATION.md).

---

## Operation 3 — Running database migrations

**When to use this:** When deploying a new version that includes
schema changes (new tables, new columns, modified relationships).

⚠️ **Always back up the database before running migrations on production.**

**Steps:**
```bash
# 1. Back up the database
# [Platform-specific backup command or dashboard steps]

# 2. Run migrations
npx prisma migrate deploy   # production-safe (no dev prompts)

# 3. Verify
npx prisma migrate status   # should show all migrations as "Applied"
```

**If a migration fails:**
```bash
# Check migration status
npx prisma migrate status

# If a migration is in "Failed" state:
# Do NOT run more migrations
# Restore from backup if data was affected
# Contact BetaCraft immediately (see ESCALATION.md)
```

---

## Operation 4 — Checking logs

**Frontend errors (Sentry):**
- URL: [Sentry project URL]
- Filter: `environment:production level:error`
- Look for: red spikes in the graph = new error introduced

**Backend logs:**
- Platform: [Railway / Render / etc.]
- Where: [exact path to logs in dashboard]
- Key patterns to look for:
  - `ERROR` — application errors
  - `500` — server errors
  - `timeout` — slow operations
  - `ANTHROPIC` — AI API issues

**Database logs:**
- Platform: [Supabase / etc.]
- Where: [exact path]

---

## Operation 5 — Common errors and fixes

| Error | What it means | Fix |
|-------|--------------|-----|
| `PrismaClientInitializationError` | Database connection failed | Check DATABASE_URL env var, verify DB is running |
| `429 Too Many Requests` (Anthropic) | AI API rate limit hit | Wait 60 seconds, retry. If frequent: check for loops |
| `ANTHROPIC_API_KEY is invalid` | Wrong or expired API key | Update in [platform] environment variables |
| `Failed to fetch` on frontend | Backend not responding | Check backend service status in [platform] dashboard |
| `Build failed: Type error` | TypeScript error in code | Run `npm run build` locally, fix errors, redeploy |

---

## Monitoring thresholds

**When to be concerned:**

| Metric | Normal | Concerned | Action |
|--------|--------|-----------|--------|
| Error rate | < 0.1% | > 1% | Check Sentry, consider rollback |
| API response time | < 500ms | > 2000ms | Check DB queries, check AI API |
| Database connections | < 80% of pool | > 90% | Contact BetaCraft |
| Deployment success rate | 100% | < 100% | Review deployment logs |

---

## Regular maintenance tasks

**Weekly:**
- [ ] Review Sentry for new errors
- [ ] Check deployment success rate

**Monthly:**
- [ ] Review database size growth
- [ ] Rotate API keys if required by security policy
- [ ] Check for dependency security alerts: `npm audit`

---

*Prepared by BetaCraft · [date]*
*Questions? See ESCALATION.md*
```
