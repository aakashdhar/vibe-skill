# CODEBASE_MD.md Template

Used by vibe-new-app Step 8. For a greenfield project, `vibe/CODEBASE.md`
starts as a **placeholder** — the last task in Phase 1 populates it fully from
the scaffolded project, and every task thereafter keeps it current.

CODEBASE.md is the map every skill reads to know what exists: vibe-add-feature,
vibe-fix-bug, vibe-review, vibe-test, and (when present) vibe-graph all rely on
it. Keep it factual — describe what is built, never what is planned.

---

## Placeholder version (written at Step 8)

```markdown
# CODEBASE — [Project Name]
> Living map of what exists in the code. Updated after every task.
> ⚠️ Placeholder — populated by the final Phase 1 task once scaffolding is done.

## Structure
(populated after Phase 1 foundation is built)

## Key modules
(none yet)

## Data model
(none yet)

## Entry points
(none yet)

## Conventions in use
See vibe/ARCHITECTURE.md — this file records what was actually built against it.
```

---

## Full version (populated from Phase 1 onward)

```markdown
# CODEBASE — [Project Name]
> Living map of what exists in the code. Updated after every task.

## Structure
```
[project-root]/
├── [folder]/     ← [purpose]
└── [folder]/     ← [purpose]
```

## Key modules
| Module / file | Responsibility | Depended on by |
|---------------|----------------|----------------|
| [path]        | [what it does] | [callers]      |

## Data model
[Entities, fields, relationships — as actually implemented.]

## Entry points
- [Frontend entry] — [path]
- [Backend/API entry] — [path]
- [Background jobs / workers] — [path]

## External services
| Service | Used for | Config / env var |
|---------|----------|------------------|
| [name]  | [purpose]| [ENV_VAR]        |

## Conventions in use
[Notable patterns actually followed — cite a file per pattern.]

## Known rough edges
[Honest list of shortcuts/tech-debt introduced, with the task ID that added them.]
```

---

## Update rules

- Update after any task that **adds, removes, or moves** a file or module.
- In autonomous/parallel runs, subagents **report** their file deltas
  (FILES_MODIFIED / FILES_CREATED) — the **main session** writes CODEBASE.md
  once per wave (see vibe-parallel). Subagents never edit it directly.
- Keep it a map, not a changelog — the "why" of changes lives in DECISIONS.md.
