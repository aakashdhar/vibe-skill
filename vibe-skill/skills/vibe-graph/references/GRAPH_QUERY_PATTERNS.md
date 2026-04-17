# GRAPH_QUERY_PATTERNS.md

Read by vibe-fix-bug, vibe-test, and vibe-review at task start.
How to query the graph efficiently, filter by confidence,
read rationale nodes, and use god node data.

---

## Query pattern 1 — vibe-fix-bug (blast radius with confidence tiers)

```python
import json
from pathlib import Path

def get_blast_radius(suspect_file, graph_path="vibe/graph/DEPENDENCY_GRAPH.json"):
    graph = json.loads(Path(graph_path).read_text())
    node = graph.get(suspect_file, {})

    # Tier 1: EXTRACTED connections — load immediately, certain
    certain = set([suspect_file])
    # Tier 2: INFERRED connections — load if Tier 1 doesn't resolve the bug
    probable = set()
    # Tier 3: AMBIGUOUS — surface to human, don't load automatically

    def process_edges(edges):
        for edge in edges:
            if isinstance(edge, str):
                # Legacy format without confidence — treat as EXTRACTED
                certain.add(edge)
            elif isinstance(edge, dict):
                src = edge.get("source", "EXTRACTED")
                f = edge.get("file", "")
                if src == "EXTRACTED":
                    certain.add(f)
                elif src == "INFERRED":
                    if edge.get("confidence", 0) >= 0.80:
                        probable.add(f)
                    else:
                        probable.add(f)  # still include, but lower priority
                # AMBIGUOUS: skip, don't auto-load

    process_edges(node.get("imports", []))
    process_edges(node.get("imported_by", []))

    # Always include test file and verifier if EXTRACTED
    test_file = node.get("test_file")
    if test_file:
        certain.add(test_file)

    verifier = node.get("verifier", {})
    if isinstance(verifier, dict) and verifier.get("source") == "EXTRACTED":
        certain.add(verifier["file"])
    elif isinstance(verifier, str):
        certain.add(verifier)

    return {
        "certain": sorted(certain),       # load first
        "probable": sorted(probable),     # load if needed
        "node": node
    }
```

**Usage in vibe-fix-bug:**

```
BLAST RADIUS — src/agents/scout_agent.py
────────────────────────────────────────
CERTAIN (EXTRACTED — load immediately):
  src/agents/scout_agent.py          ← suspected file
  src/agents/base_agent.py           ← direct import [line 3]
  src/tools/tavily.py                ← direct import [line 7]
  src/graph/pipeline.py              ← imports this [line 12]
  src/agents/verifiers/scout_verifier.py ← verifier [AGENT_ARCH.md]
  tests/test_scout_agent.py          ← test file

PROBABLE (INFERRED ≥0.80 — load if certain tier doesn't resolve):
  src/utils/rate_limiter.py          ← inferred dep (confidence: 0.75)

RATIONALE (read before diagnosing):
  WHY [line 12]: Directory-first approach chosen over API-first because
    Tavily directory has better SMB coverage than LinkedIn API
  HACK [line 47]: Rate limiting at 2s — Tavily free tier hard limit
  DECISION [line 89]: Returns top 5 only — UI constraint from IdentityScreen

Total certain: 6 files (~7,200 tokens)
vs loading CODEBASE.md: 25,000 tokens
Saving: 17,800 tokens (71%)
```

**Read rationale before reading the file:**

```python
def get_rationale(file_path, graph_path="vibe/graph/DEPENDENCY_GRAPH.json"):
    graph = json.loads(Path(graph_path).read_text())
    node = graph.get(file_path, {})
    rationale = node.get("rationale", [])

    if not rationale:
        return f"No rationale recorded for {file_path}"

    output = [f"RATIONALE — {file_path}"]
    output.append("─" * 50)
    for r in rationale:
        output.append(f"{r['type']} [line {r['line']}]: {r['text']}")

    return "\n".join(output)
```

**God node check before diagnosis:**

```python
def check_if_god_node(file_path, meta_path="vibe/graph/.graph-meta.json"):
    try:
        meta = json.loads(Path(meta_path).read_text())
        god_nodes = meta.get("god_nodes", [])
        for gn in god_nodes:
            if gn["file"] == file_path:
                return gn
    except:
        return None
    return None
```

```
# If god node detected — surface before diagnosis
GOD NODE DETECTED: src/agents/base_agent.py
  Connections: 14 (HIGH coupling)
  Risk: Changes here affect 14 connected files
  SRP flag: Consider whether this file should be split
  → Proceed carefully. Root cause may be in this file
    even if bug reported elsewhere.
```

---

## Query pattern 2 — vibe-test (confidence-tiered blast radius)

```python
def get_test_scope(changed_files, graph_path="vibe/graph/DEPENDENCY_GRAPH.json"):
    graph = json.loads(Path(graph_path).read_text())

    # Tier 1: files that definitely need tests (EXTRACTED connections)
    certain_test_scope = set()
    # Tier 2: files that probably need tests (INFERRED ≥0.80)
    probable_test_scope = set()

    for file_path in changed_files:
        certain_test_scope.add(file_path)
        node = graph.get(file_path, {})

        for edge_list_key in ["imports", "imported_by"]:
            for edge in node.get(edge_list_key, []):
                if isinstance(edge, str):
                    certain_test_scope.add(edge)
                elif isinstance(edge, dict):
                    if edge.get("source") == "EXTRACTED":
                        certain_test_scope.add(edge["file"])
                    elif edge.get("source") == "INFERRED" and edge.get("confidence", 0) >= 0.80:
                        probable_test_scope.add(edge["file"])

        test_file = node.get("test_file")
        if test_file:
            certain_test_scope.add(test_file)

    return {
        "certain": sorted(certain_test_scope),
        "probable": sorted(probable_test_scope - certain_test_scope)
    }
```

**Output for vibe-test:**

```
TEST SCOPE (from graph):
────────────────────────────────────────
CERTAIN (EXTRACTED — write full regression tests):
  src/agents/scout_agent.py           ✅ test_scout_agent.py exists
  src/agents/base_agent.py            ✅ test_base_agent.py exists
  src/tools/tavily.py                 ⚠️  no test file — create tests/test_tavily.py
  src/graph/pipeline.py               ✅ test_pipeline.py exists

PROBABLE (INFERRED — write smoke tests):
  src/utils/rate_limiter.py           ⚠️  no test file — create tests/test_rate_limiter.py
    (inferred dependency, confidence: 0.75 — verify manually)

Total certain: 4 files (3 need tests, 1 needs test file created)
Total probable: 1 file
```

---

## Query pattern 3 — vibe-review (god nodes first, then concept boundaries)

```python
def review_pre_screening(graph_path="vibe/graph/DEPENDENCY_GRAPH.json",
                          meta_path="vibe/graph/.graph-meta.json"):

    graph = json.loads(Path(graph_path).read_text())
    meta = json.loads(Path(meta_path).read_text()) if Path(meta_path).exists() else {}
    god_nodes = {gn["file"] for gn in meta.get("god_nodes", [])}

    # Phase 1: Flag god nodes for priority reading
    priority_reads = []
    for gn in meta.get("god_nodes", []):
        priority_reads.append({
            "file": gn["file"],
            "reason": f"God node: {gn['connections']} connections",
            "risk": gn["risk"],
            "srp_flag": gn.get("srp_flag", False)
        })

    # Phase 2: Cross-concept boundary violations (EXTRACTED edges only)
    violations = []
    for file_path, node in graph.items():
        file_concept = node.get("concept", "foundation")
        file_type = node.get("type", "unknown")

        for edge in node.get("imports", []):
            # Only check EXTRACTED edges for violations
            # INFERRED edges at AMBIGUOUS may not be real violations
            imported_file = edge if isinstance(edge, str) else edge.get("file", "")
            edge_source = "EXTRACTED" if isinstance(edge, str) else edge.get("source", "EXTRACTED")
            edge_conf = 1.0 if isinstance(edge, str) else edge.get("confidence", 1.0)

            if edge_source == "AMBIGUOUS":
                continue  # Skip ambiguous edges for violation detection

            imported_node = graph.get(imported_file, {})
            imported_concept = imported_node.get("concept", "foundation")
            imported_type = imported_node.get("type", "unknown")

            if file_concept == imported_concept or imported_concept == "foundation":
                continue  # Same concept or foundation — not a violation

            # Frontend importing backend directly
            if file_type == "component" and imported_type in ["agent", "service"]:
                severity = "P0" if edge_source == "EXTRACTED" else "P1"
                violations.append({
                    "file": file_path,
                    "imports": imported_file,
                    "violation": "Frontend component directly imports backend/agent — DIP violation",
                    "severity": severity,
                    "edge_source": edge_source,
                    "confidence": edge_conf
                })

            # Agent calling agent directly (not through orchestrator/pipeline)
            elif file_type == "agent" and imported_type == "agent":
                if imported_file not in ["src/agents/base_agent.py", "src/agents/base.py"]:
                    violations.append({
                        "file": file_path,
                        "imports": imported_file,
                        "violation": "Agent directly imports agent — should route through orchestrator",
                        "severity": "P1",
                        "edge_source": edge_source,
                        "confidence": edge_conf
                    })

    # Phase 3: Intent drift — code that contradicts rationale
    intent_drift = []
    for file_path, node in graph.items():
        for r in node.get("rationale", []):
            if r["type"] in ["WHY", "DECISION"]:
                # Surface rationale for review — reviewer checks against actual implementation
                intent_drift.append({
                    "file": file_path,
                    "documented_intent": r["text"],
                    "type": r["type"],
                    "line": r["line"],
                    "action": "Verify implementation matches documented intent"
                })

    return {
        "priority_reads": priority_reads,
        "violations": violations,
        "intent_drift": intent_drift
    }
```

**Output for vibe-review:**

```
REVIEW PRE-SCREENING (graph-based, before reading source)
──────────────────────────────────────────────────────────
PRIORITY READS (god nodes — read these first):
  src/agents/base_agent.py     14 connections · HIGH · ⚠️ SRP check needed
  src/models/brand_dna.py       8 connections · MEDIUM
  src/graph/pipeline.py         7 connections · MEDIUM

CONCEPT VIOLATIONS (EXTRACTED — read these for deep review):
  P0: src/components/BrandDNACard.tsx → src/agents/guardian_agent.py
      Frontend component directly imports backend/agent — DIP violation

  P1: src/agents/scout_agent.py → src/agents/analyst_agent.py
      Agent directly imports agent — should route through orchestrator

INTENT DRIFT (verify implementation matches documented intent):
  src/agents/scout_agent.py [line 12]:
    WHY: "Directory-first approach — Tavily better coverage than LinkedIn API"
    Action: Verify implementation uses directory approach, not API

  src/agents/scout_agent.py [line 89]:
    DECISION: "Returns top 5 only — UI constraint from IdentityScreen"
    Action: Verify result count is still 5, check if UI constraint changed

AMBIGUOUS EDGES (human review needed):
  src/shared/validator.py → multiple concepts
  Action: Determine primary concept ownership

Deep-read required: 3 files (violations + god nodes)
Shallow review: remaining files (no violations, not god nodes)
```

---

## Query pattern 4 — vibe-parallel (conflict detection with god nodes)

```python
def check_parallel_safety(wave_tasks, graph_path, meta_path):
    graph = json.loads(Path(graph_path).read_text())
    meta = json.loads(Path(meta_path).read_text()) if Path(meta_path).exists() else {}
    god_node_files = {gn["file"] for gn in meta.get("god_nodes", [])}

    conflicts = []

    # For each pair of tasks in the same wave
    for i, task_a in enumerate(wave_tasks):
        for task_b in wave_tasks[i+1:]:
            files_a = set(task_a.get("touches", []))
            files_b = set(task_b.get("touches", []))

            # Direct file conflict
            shared = files_a & files_b
            if shared:
                conflicts.append({
                    "tasks": [task_a["id"], task_b["id"]],
                    "type": "DIRECT",
                    "files": list(shared),
                    "severity": "BLOCK"
                })
                continue

            # God node conflict — both tasks touch files connected to same god node
            for file_a in files_a:
                node_a = graph.get(file_a, {})
                for edge in node_a.get("imports", []) + node_a.get("imported_by", []):
                    shared_god = edge if isinstance(edge, str) else edge.get("file", "")
                    if shared_god in god_node_files:
                        for file_b in files_b:
                            node_b = graph.get(file_b, {})
                            b_edges = [e if isinstance(e, str) else e.get("file") 
                                      for e in node_b.get("imports", []) + node_b.get("imported_by", [])]
                            if shared_god in b_edges:
                                conflicts.append({
                                    "tasks": [task_a["id"], task_b["id"]],
                                    "type": "GOD_NODE",
                                    "god_node": shared_god,
                                    "severity": "WARN"
                                })

    return conflicts
```

---

## What to do when a file is not in the graph

If a file is queried and not found in DEPENDENCY_GRAPH.json:

1. Read the file directly
2. Extract its imports manually
3. Add it to the graph as a new node with `source: EXTRACTED`
4. Update any nodes that import it — add it to their `imported_by` list
5. Continue with accurate data

Never skip a file because it's absent from the graph.
The graph is a starting point, not a constraint.

After the session, `vibe-graph: update` will formalise the new node.
