# CODEBASE_MD.md — generation template

Used when `vibe/CODEBASE.md` doesn't exist yet and a feature/bug workflow needs to
create it from the actual code. CODEBASE.md is the living map every skill reads to
know what exists (vibe-add-feature, vibe-fix-bug, vibe-review, vibe-test, vibe-graph).
Fill only from observed code — never invent. Keep it a map, not a changelog (the
"why" of changes lives in DECISIONS.md).

---

```markdown
# CODEBASE — [Project Name]
> Living map of what exists in the code. Updated after every task.
> Generated [date] from the existing codebase.

## 1. Structure
```
[project-root]/
├── [folder]/     ← [purpose — observed]
└── [folder]/     ← [purpose — observed]
```

## 2. Stack & tooling
[Runtime, framework, DB, ORM, styling, test runner — with versions from the manifest.]

## 3. Key modules
| Module / file | Responsibility | Depended on by |
|---------------|----------------|----------------|
| [path]        | [what it does] | [callers]      |

## 4. Data model
[Entities, fields, relationships — as actually implemented.]

## 5. API routes / entry points
- [Method + path or entry] → [handler file]

## 6. Conventions in use
[Notable patterns actually followed — cite a file per pattern.]

## 7. External services
| Service | Used for | Config / env var |
|---------|----------|------------------|

## 8. Tests
[Runner, location, what's covered / not.]

## 9. Key file paths (quick index)
[The handful of paths a feature/bug author reaches for first.]

## 10. Known rough edges
[Honest shortcuts / tech-debt, with the task or area that introduced them.]
```

---

## Update rules
- Update after any task that adds, removes, or moves a file or module.
- In parallel/autonomous runs, subagents report file deltas; the main session writes
  CODEBASE.md once per wave (never concurrently — see vibe-parallel).
