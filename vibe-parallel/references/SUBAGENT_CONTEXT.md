# SUBAGENT_CONTEXT.md

Read during Step 3 of vibe-parallel.
How to build each subagent's context.

**Design note (current models):** context windows are large and prompt caching
makes a shared, stable prefix cheap to re-read. So the graph is a **focus
overlay**, not a way to *avoid* loading context. The old "slice instead of
CODEBASE.md" design traded fidelity for token savings that no longer matter much —
and a lossy slice can miss files not yet in the graph. Prefer the **hybrid** mode
below: give every subagent the same cached baseline (ARCHITECTURE.md + CODEBASE.md)
so nothing is missed, plus a graph-derived **focus block** telling it exactly which
files are in its blast radius and why (rationale). Precision without blind spots.

---

## Context modes

```
HYBRID (preferred when GRAPH_AVAILABLE):
    vibe/graph/DEPENDENCY_GRAPH.json exists
    → cached baseline prefix: ARCHITECTURE.md + CODEBASE.md (identical across
      all subagents in the wave → one cache write, N-1 cache reads)
    → per-task focus block from the graph: blast-radius files, rationale
      (WHY/HACK/DECISION), god-node warnings, concept name
    → the subagent reads the focus files fully; the baseline gives it the map

NO_GRAPH:
    DEPENDENCY_GRAPH.json not found
    → cached baseline: ARCHITECTURE.md + CODEBASE.md
    → no focus block; the subagent scopes from its task's Touches list
```

> Cache-friendliness matters more than slice size now: keep the baseline prefix
> **byte-identical** across every subagent in a wave (same file order, no
> per-task timestamps/IDs before the focus block) so the wave pays one cache
> write and reads it back cheaply for every remaining subagent. The graph
> `build_context_slice` below now produces the *focus block*, not a replacement
> for CODEBASE.md.

---

## Graph-aware context slice

### Step 1 — Load graph files

```python
import json
from pathlib import Path

graph = json.loads(Path("vibe/graph/DEPENDENCY_GRAPH.json").read_text())
concept_graph = json.loads(Path("vibe/graph/CONCEPT_GRAPH.json").read_text())
meta = json.loads(Path("vibe/graph/.graph-meta.json").read_text()) \
       if Path("vibe/graph/.graph-meta.json").exists() else {}

god_node_files = {gn["file"] for gn in meta.get("god_nodes", [])}
god_node_map = {gn["file"]: gn for gn in meta.get("god_nodes", [])}
```

### Step 2 — Build slice per task

```python
def build_context_slice(task, graph, concept_graph, god_node_files, god_node_map):
    task_files = task.get("touches", [])
    slice_data = {
        "task_files":   task_files,
        "imports":      {},    # file → list of EXTRACTED import paths
        "rationale":    {},    # file → list of rationale entries
        "concept_name": None,
        "concept_desc": None,
        "god_node_warnings": [],
        "arch_patterns": task.get("arch_ref", "")
    }

    for file_path in task_files:
        node = graph.get(file_path, {})

        # EXTRACTED imports only — verified from source, confidence 1.0
        extracted_imports = []
        for edge in node.get("imports", []):
            if isinstance(edge, str):
                # Legacy format — treat as EXTRACTED
                extracted_imports.append(edge)
            elif isinstance(edge, dict) and edge.get("source") == "EXTRACTED":
                extracted_imports.append(edge["file"])
            # INFERRED edges omitted from subagent context — not verified
        slice_data["imports"][file_path] = extracted_imports

        # Rationale — WHY/HACK/DECISION comments
        rationale = node.get("rationale", [])
        if rationale:
            slice_data["rationale"][file_path] = rationale

        # Concept from first task file that has one
        if not slice_data["concept_name"]:
            concept = node.get("concept")
            if concept and concept in concept_graph:
                slice_data["concept_name"] = concept
                c_node = concept_graph[concept]
                # Build short concept description
                files_count = len(c_node.get("files", []))
                state = c_node.get("state", "built")
                deps = c_node.get("depends_on", [])
                slice_data["concept_desc"] = (
                    f"{concept} ({state}) — "
                    f"{files_count} files"
                    + (f", depends on: {', '.join(deps)}" if deps else "")
                )

        # God node warnings
        if file_path in god_node_files:
            gn = god_node_map[file_path]
            slice_data["god_node_warnings"].append({
                "file": file_path,
                "connections": gn["connections"],
                "risk": gn["risk"],
                "srp_flag": gn.get("srp_flag", False)
            })

    return slice_data
```

### Step 3 — Render context block for subagent prompt

```python
def render_context_block(slice_data, task):
    lines = ["═══ PROJECT CONTEXT (graph-aware) ═══"]

    # Concept
    if slice_data["concept_name"]:
        lines.append(f"\nConcept: {slice_data['concept_desc']}")

    # Architecture patterns
    if slice_data["arch_patterns"]:
        lines.append(f"\nArchitecture patterns to follow:")
        lines.append(f"  {slice_data['arch_patterns']}")
        lines.append(f"  (Full rules in vibe/ARCHITECTURE.md — read the relevant section)")

    lines.append("\nYour files:")

    for file_path in slice_data["task_files"]:
        lines.append(f"\n  {file_path}")

        # Imports
        imports = slice_data["imports"].get(file_path, [])
        if imports:
            lines.append(f"  Imports (EXTRACTED — verified):")
            for imp in imports:
                lines.append(f"    → {imp}")

        # Rationale
        rationale = slice_data["rationale"].get(file_path, [])
        if rationale:
            lines.append(f"  Rationale (read before implementing):")
            for r in rationale:
                lines.append(f"    {r['type']} [line {r['line']}]: {r['text']}")

        # God node warning
        gn_warn = next(
            (w for w in slice_data["god_node_warnings"] if w["file"] == file_path),
            None
        )
        if gn_warn:
            lines.append(
                f"  ⚠️ GOD NODE — {gn_warn['connections']} connections · "
                f"{gn_warn['risk']} coupling"
            )
            lines.append(
                "  Changes here affect many files. Be surgical. "
                "Don't change anything outside your task scope."
            )

    lines.append("\nDo NOT load vibe/CODEBASE.md — your context above is sufficient.")
    lines.append("Read vibe/ARCHITECTURE.md if you need pattern details.")

    return "\n".join(lines)
```

---

## Full subagent prompt template

```python
def build_subagent_prompt(task, context_block, other_wave_files, scope_warnings):
    """
    task:             task dict
    context_block:    rendered context from render_context_block()
    other_wave_files: all Touches fields from other tasks in this wave
    scope_warnings:   upstream [~] partial warnings to include
    """

    prompt = f"""You are executing {task['id']} as part of a parallel build.

{context_block}

═══ YOUR TASK ═══
{task['id']} · {task['title']}
Size: {task['size']}

What to do:
{task['description']}

Acceptance criteria:
{chr(10).join(f'- [ ] {c}' for c in task['criteria'])}

Test requirement: {task.get('test_requirement', 'Run existing tests, add tests if the task creates new logic')}

Architecture compliance: {task.get('arch_ref', 'Follow ARCHITECTURE.md patterns')}

CODEBASE.md update required: {'Yes — ' + task.get('codebase_update_desc', '') if task.get('codebase_update') else 'No — logic only'}

═══ SCOPE BOUNDARIES ═══
Files you MAY write:
{chr(10).join(f'  {f}' for f in task['touches'])}

Files you must NOT write (assigned to other parallel tasks):
{chr(10).join(f'  {f}' for f in other_wave_files)}
"""

    if scope_warnings:
        prompt += f"""
═══ UPSTREAM WARNINGS ═══
The following tasks completed partially — account for these:
{chr(10).join(f'  ⚠️ {w}' for w in scope_warnings)}
"""

    prompt += """
═══ COMPLETION REPORT ═══
When done, end your turn with a single fenced ```json block matching this schema
exactly (see vibe-parallel/references/REPORTING.md). Do NOT edit vibe/CODEBASE.md,
DECISIONS.md, TASKS.md, or CLAUDE.md yourself — report deltas; the main session
applies them.

{
  "task_id": "{task_id}",
  "status": "DONE" | "PARTIAL" | "FAILED",
  "files_modified": ["path", ...],
  "files_created": ["path", ...],
  "tests": { "passed": N, "total": N },
  "criteria": [ { "text": "...", "met": true|false, "note": "reason if unmet" } ],
  "codebase_update": "what changed, for the main session to record | ",
  "blockers": ["anything downstream tasks must know", ...],
  "rationale_added": "WHY/DECISION comments added | ",
  "decisions": [ { "title": "...", "why": "...", "touches": ["path", ...] } ],
  "error": "failure detail | null"
}

`decisions` = implementation choices worth remembering (why this approach / library);
the main session appends them to vibe/IMPLEMENTATION_LOG.md. Use [] if none.
Do NOT edit vibe/IMPLEMENTATION_LOG.md yourself either.
""".replace("{task_id}", task['id'])

    return prompt
```

Where the runtime supports schema-validated output/tool calls, bind this schema with
`strict: true`. The orchestrator parses it JSON-first (REPORTING.md) — the legacy
text format is gone.

---

## Context size estimates

Rough numbers for the wave cost annotation. **These are an upper bound** — under
the hybrid model the ARCHITECTURE.md + CODEBASE.md baseline is a stable cached
prefix, so only the *first* subagent in a wave pays the full input cost; the rest
read it from cache at ~10% of the price (see vibe-cost/references/PRICING.md →
Cache economics). Model the wave as: baseline (once) + focus block (per task) +
output — not baseline × N.

```python
CONTEXT_TOKENS = {
    # Per-task focus block (added on top of the cached baseline)
    "graph_slice_per_file":   800,    # blast-radius file: imports + rationale
    "graph_overhead":         500,    # concept, arch patterns, warnings
    "task_prompt_base":       600,    # task description, criteria, boundaries
    "completion_report":      200,    # report template

    # Shared cached baseline (one cache write per wave, then cache reads)
    "codebase_md_avg":       25000,   # typical CODEBASE.md
    "architecture_md_avg":    3000,   # typical ARCHITECTURE.md
}

def estimate_subagent_tokens(task, use_graph=True):
    if use_graph:
        file_count = len(task.get("touches", []))
        return (
            CONTEXT_TOKENS["graph_slice_per_file"] * file_count
            + CONTEXT_TOKENS["graph_overhead"]
            + CONTEXT_TOKENS["task_prompt_base"]
            + CONTEXT_TOKENS["completion_report"]
        )
    else:
        return (
            CONTEXT_TOKENS["codebase_md_avg"]
            + CONTEXT_TOKENS["architecture_md_avg"]
            + CONTEXT_TOKENS["task_prompt_base"]
            + CONTEXT_TOKENS["completion_report"]
        )

def estimate_wave_cost(tasks, use_graph=True):
    # Rough estimate at claude-sonnet-5 input ($2/MTok). Source of truth for
    # prices: vibe-cost/references/PRICING.md. With prompt caching on a shared
    # prefix, real input cost is materially lower — this is an upper bound.
    total_tokens = sum(estimate_subagent_tokens(t, use_graph) for t in tasks)
    return {
        "tokens": total_tokens,
        "cost_usd": round(total_tokens / 1_000_000 * 2.0, 4)
    }
```

---

## Fallback — no graph available

When DEPENDENCY_GRAPH.json does not exist:

```
═══ PROJECT CONTEXT ═══
Read the following files for project context:
  vibe/CODEBASE.md         ← file map, routes, models, agents
  vibe/ARCHITECTURE.md     ← patterns and conventions to follow

Your task files: [Touches field]

Note: vibe-graph is not installed. Install it to reduce per-subagent
context cost by 60-70%.
```

No slicing, no rationale, no god node warnings.
Full CODEBASE.md loaded — standard cost.
