# CODEBASE_TO_GRAPH.md

Read during vibe-graph: build (existing projects via vibe-init).
How to parse CODEBASE.md into graph nodes and edges.
Includes: relationship confidence tagging, rationale extraction, god node computation.

---

## Relationship confidence tagging

Every edge written to DEPENDENCY_GRAPH.json carries a `source` tag.
This is mandatory — never write an edge without a source tag.

```
EXTRACTED  — found directly in source (import statement, explicit call, route definition)
             confidence: always 1.0
             never ambiguous

INFERRED   — reasonable inference (concept assignment, naming pattern, FEATURE_TASKS.md Touches field)
             confidence: 0.6–0.95 depending on evidence strength
             always include evidence string

AMBIGUOUS  — agent couldn't determine clearly, flagged for human review
             confidence: < 0.6
             surface in vibe-graph: status as unresolved
```

**Confidence scale for INFERRED edges:**

| Evidence | Confidence |
|----------|-----------|
| Explicit in FEATURE_TASKS.md Touches field | 0.95 |
| File naming clearly matches concept (guardian_agent → brand-dna-extraction) | 0.85 |
| Docstring/comment explains concept membership | 0.90 |
| File location strongly implies concept (src/agents/scout*) | 0.80 |
| Agent reasoning from file content | 0.70 |
| Weak naming signal (utils.py, helpers.py) | 0.60 |

**Edge format with confidence tagging:**

```json
"src/agents/scout_agent.py": {
  "state": "built",
  "concept": "competitor-discovery",
  "concept_source": "EXTRACTED",
  "concept_confidence": 1.0,
  "concept_evidence": "vibe/features/2026-04-01-competitor-discovery/FEATURE_TASKS.md Touches field",
  "imports": [
    {
      "file": "src/agents/base_agent.py",
      "source": "EXTRACTED",
      "confidence": 1.0,
      "evidence": "line 3: from agents.base import BaseAgent"
    },
    {
      "file": "src/tools/tavily.py",
      "source": "EXTRACTED",
      "confidence": 1.0,
      "evidence": "line 7: from tools.tavily import TavilySearch"
    }
  ],
  "imported_by": [
    {
      "file": "src/graph/pipeline.py",
      "source": "EXTRACTED",
      "confidence": 1.0,
      "evidence": "pipeline.py line 12: from agents.scout import ScoutAgent"
    }
  ]
}
```

**When source is INFERRED — always include evidence:**

```json
{
  "file": "src/utils/rate_limiter.py",
  "source": "INFERRED",
  "confidence": 0.75,
  "evidence": "ScoutAgent instantiates RateLimiter at line 34 — indirect dependency not in CODEBASE.md"
}
```

**When source is AMBIGUOUS — flag explicitly:**

```json
{
  "file": "src/shared/validator.py",
  "source": "AMBIGUOUS",
  "confidence": 0.45,
  "evidence": "Used in multiple concepts, unclear primary ownership",
  "review_note": "Human should verify which concept owns this file"
}
```

---

## Rationale extraction

When indexing a file, extract `rationale_for` nodes.
These capture *why* a file is structured the way it is —
not just what it does.

**Patterns to look for:**

```python
# WHY: ...
# NOTE: ...
# HACK: ...
# IMPORTANT: ...
# REASON: ...
# DECISION: ...
# TRADEOFF: ...
# WARNING: ...
```

Also extract:
- First paragraph of module-level docstrings (explains purpose and rationale)
- `TODO:` and `FIXME:` comments (technical debt markers)
- Class-level docstrings that explain design choices

**Rationale node format:**

```json
"src/agents/scout_agent.py": {
  "rationale": [
    {
      "type": "WHY",
      "text": "Directory-first approach chosen over API-first because Tavily directory has better SMB coverage than LinkedIn API which requires OAuth per user",
      "line": 12,
      "source": "EXTRACTED"
    },
    {
      "type": "HACK",
      "text": "Rate limiting at 2s delay — Tavily free tier hard limit, upgrade to paid tier removes this",
      "line": 47,
      "source": "EXTRACTED"
    },
    {
      "type": "DECISION",
      "text": "Returns top 5 competitors only — UI constraint from IdentityScreen layout, not a search limitation",
      "line": 89,
      "source": "EXTRACTED"
    },
    {
      "type": "docstring",
      "text": "ScoutAgent discovers competitors for a given brand by searching the Tavily business directory. Stateless by design — all results written to Supabase immediately, no agent-level caching.",
      "line": 1,
      "source": "EXTRACTED"
    }
  ]
}
```

**What rationale nodes enable:**

- vibe-fix-bug: reads rationale before diagnosing — knows *why* the file works the way it does before proposing a fix
- vibe-review: detects intent drift — code that contradicts documented rationale is a P1 finding
- vibe-document: generates accurate WHY documentation rather than inferring from code alone
- vibe-handoff: surfaces design decisions automatically in CONTEXT_DUMP.md and ONBOARDING.md

**When indexing CODEBASE.md:**
If the source file is accessible (`cat [file]`), extract rationale comments directly.
If only CODEBASE.md is available (no source files yet), mark rationale as empty `[]`.
Rationale gets populated on first `vibe-graph: update` after files are read.

---

## CODEBASE.md structure → graph mapping

CODEBASE.md is organised by section type. Each section maps to
a node type in DEPENDENCY_GRAPH.json.

### Routes section → route nodes

```
## Routes
POST /api/brand-dna
  Handler: src/api/brand_dna.py:create_brand_dna
  Auth: required
  Body: {url: string}
  Response: BrandDNA schema
  Calls: GuardianAgent.extract()
  DB: writes to brand_dna table
```

→ Route node:
```json
"POST /api/brand-dna": {
  "state": "built",
  "type": "route",
  "handler_file": "src/api/brand_dna.py",
  "handler_function": "create_brand_dna",
  "auth_required": true,
  "calls_agent": "GuardianAgent",
  "writes_model": "BrandDNA",
  "concept": "brand-dna-extraction",
  "concept_source": "EXTRACTED",
  "concept_confidence": 1.0,
  "concept_evidence": "CODEBASE.md Routes section, explicit feature grouping"
}
```

→ File node for handler:
```json
"src/api/brand_dna.py": {
  "state": "built",
  "type": "route-handler",
  "concept": "brand-dna-extraction",
  "concept_source": "EXTRACTED",
  "concept_confidence": 1.0,
  "concept_evidence": "CODEBASE.md Routes section",
  "api_routes": ["POST /api/brand-dna"],
  "imports": [],
  "imported_by": [],
  "rationale": []
}
```

---

### Models section → model nodes

```
## Models
BrandDNA
  Fields: id, url, voice_attributes[], mission, audience, tagline, clarity_score
  Relations: belongs to User, has many Competitors
  File: prisma/schema.prisma
  Created by: GuardianAgent
  Read by: ScoutAgent, StrategistAgent, BrandDNACard
```

→ Model node:
```json
"BrandDNA": {
  "state": "built",
  "type": "model",
  "concept": "brand-dna-extraction",
  "concept_source": "EXTRACTED",
  "concept_confidence": 1.0,
  "concept_evidence": "CODEBASE.md Models section",
  "file": "prisma/schema.prisma",
  "written_by": [
    {
      "file": "src/agents/guardian_agent.py",
      "source": "EXTRACTED",
      "confidence": 1.0,
      "evidence": "CODEBASE.md: Created by GuardianAgent"
    }
  ],
  "read_by": [
    {
      "file": "src/agents/scout_agent.py",
      "source": "EXTRACTED",
      "confidence": 1.0,
      "evidence": "CODEBASE.md: Read by ScoutAgent"
    },
    {
      "file": "src/components/BrandDNACard.tsx",
      "source": "EXTRACTED",
      "confidence": 1.0,
      "evidence": "CODEBASE.md: Read by BrandDNACard"
    }
  ],
  "relations": ["User", "Competitor"],
  "rationale": []
}
```

---

### Components section → component nodes

```
## Components
BrandDNACard
  File: src/components/BrandDNACard.tsx
  Props: brandDNA: BrandDNA, onConfirm: () => void
  Used by: IdentityScreen
  Reads: BrandDNA model (via API)
```

→ Component node:
```json
"src/components/BrandDNACard.tsx": {
  "state": "built",
  "type": "component",
  "concept": "brand-dna-extraction",
  "concept_source": "EXTRACTED",
  "concept_confidence": 1.0,
  "concept_evidence": "CODEBASE.md Components section",
  "imports": [],
  "used_by": [
    {
      "file": "src/screens/IdentityScreen.tsx",
      "source": "EXTRACTED",
      "confidence": 1.0,
      "evidence": "CODEBASE.md: Used by IdentityScreen"
    }
  ],
  "api_routes_consumed": ["POST /api/brand-dna"],
  "models_displayed": ["BrandDNA"],
  "rationale": []
}
```

---

### Agents section → agent nodes

```
## Agents
GuardianAgent
  File: src/agents/guardian_agent.py
  Inherits: BaseAgent
  Tools: web_fetch
  Verifier: GuardianVerifier (src/agents/verifiers/guardian_verifier.py)
  Input: url: string
  Output: BrandDNA
  Called by: POST /api/brand-dna handler
```

→ Agent node:
```json
"src/agents/guardian_agent.py": {
  "state": "built",
  "type": "agent",
  "concept": "brand-dna-extraction",
  "concept_source": "EXTRACTED",
  "concept_confidence": 1.0,
  "concept_evidence": "CODEBASE.md Agents section",
  "imports": [
    {
      "file": "src/agents/base_agent.py",
      "source": "EXTRACTED",
      "confidence": 1.0,
      "evidence": "CODEBASE.md: Inherits BaseAgent"
    }
  ],
  "imported_by": [],
  "tools": ["web_fetch"],
  "verifier": {
    "file": "src/agents/verifiers/guardian_verifier.py",
    "source": "EXTRACTED",
    "confidence": 1.0,
    "evidence": "CODEBASE.md: Verifier field"
  },
  "called_by": [
    {
      "file": "src/api/brand_dna.py",
      "source": "EXTRACTED",
      "confidence": 1.0,
      "evidence": "CODEBASE.md: Called by POST /api/brand-dna handler"
    }
  ],
  "produces": "BrandDNA",
  "test_file": "tests/test_guardian_agent.py",
  "rationale": []
}
```

---

## Concept assignment for existing projects

**Priority order — use the first signal that applies:**

1. **EXTRACTED (confidence 1.0):** vibe/features/ folder — file listed in FEATURE_TASKS.md Touches field
2. **EXTRACTED (confidence 0.95):** CODEBASE.md section header makes concept membership explicit
3. **INFERRED (confidence 0.85–0.90):** file naming strongly matches concept name
4. **INFERRED (confidence 0.80):** file location in a concept-named folder
5. **INFERRED (confidence 0.70):** agent reasoning from file content/docstring
6. **INFERRED (confidence 0.60):** weak signal — assign to `foundation`, flag for review
7. **AMBIGUOUS:** multiple signals conflict — flag in status, assign to `foundation` temporarily

```python
# Concept assignment logic
def assign_concept(file_path, codebase_md, feature_folders, concept_graph):

    # Signal 1: explicit feature folder listing
    for folder in feature_folders:
        tasks_file = f"vibe/features/{folder}/FEATURE_TASKS.md"
        if file_path in read_touches_field(tasks_file):
            return {
                "concept": folder_to_concept(folder),
                "source": "EXTRACTED",
                "confidence": 1.0,
                "evidence": f"{tasks_file} Touches field"
            }

    # Signal 2: naming match against known concepts
    for concept_name in concept_graph:
        slug = concept_name.replace("-", "_")
        if slug in file_path.lower():
            return {
                "concept": concept_name,
                "source": "INFERRED",
                "confidence": 0.85,
                "evidence": f"File name contains concept slug '{slug}'"
            }

    # Fallback: foundation
    return {
        "concept": "foundation",
        "source": "INFERRED",
        "confidence": 0.70,
        "evidence": "No matching concept found — assigned to foundation"
    }
```

---

## God node computation

Run after DEPENDENCY_GRAPH.json is written (build, update, or rebuild).
God nodes = highest-degree files in the dependency graph.
They are the most-connected, highest-impact files in the project.

```python
import json
from pathlib import Path

def compute_god_nodes(graph_path, top_n=5):
    graph = json.loads(Path(graph_path).read_text())

    degree = {}
    for file_path, node in graph.items():
        if not isinstance(node, dict):
            continue
        # Count imports (files this node depends on)
        imports = node.get("imports", [])
        import_count = len(imports) if isinstance(imports[0], str) else len(imports)
        # Count imported_by (files that depend on this node)
        imported_by = node.get("imported_by", [])
        importedby_count = len(imported_by) if not imported_by or isinstance(imported_by[0], str) else len(imported_by)
        # Total degree
        degree[file_path] = import_count + importedby_count

    # Sort by degree descending
    god_nodes = sorted(degree.items(), key=lambda x: x[1], reverse=True)[:top_n]

    result = []
    for file_path, connections in god_nodes:
        node = graph.get(file_path, {})
        entry = {
            "file": file_path,
            "connections": connections,
            "concept": node.get("concept", "foundation"),
            "type": node.get("type", "unknown"),
            "risk": "HIGH" if connections > 10 else "MEDIUM" if connections > 5 else "LOW"
        }
        # Flag for SRP review if high coupling
        if connections > 10:
            entry["srp_flag"] = True
            entry["srp_note"] = f"{connections} connections — consider splitting. Review for SRP violation."
        result.append(entry)

    return result
```

**Write god nodes to .graph-meta.json:**

```json
{
  "god_nodes": [
    {
      "file": "src/agents/base_agent.py",
      "connections": 14,
      "concept": "foundation",
      "type": "agent",
      "risk": "HIGH",
      "srp_flag": true,
      "srp_note": "14 connections — consider splitting. Review for SRP violation."
    },
    {
      "file": "src/models/brand_dna.py",
      "connections": 8,
      "concept": "brand-dna-extraction",
      "type": "model",
      "risk": "MEDIUM"
    },
    {
      "file": "src/graph/pipeline.py",
      "connections": 7,
      "concept": "foundation",
      "type": "service",
      "risk": "MEDIUM"
    }
  ],
  "god_nodes_computed_at": "[ISO timestamp]"
}
```

**God nodes are surfaced in vibe-graph: status** and passed to:
- vibe-review: read god nodes first, highest coupling = highest review priority
- vibe-fix-bug: if suspected file IS a god node, flag large blast radius before diagnosis
- vibe-parallel: god node files are never written by two waves simultaneously
- vibe-cost: god nodes loaded in every session = CP-01 pattern candidate

---

## Handling AMBIGUOUS edges in status

```python
def collect_ambiguous(graph):
    ambiguous = []
    for file_path, node in graph.items():
        # Check concept assignment
        if node.get("concept_source") == "AMBIGUOUS":
            ambiguous.append({
                "file": file_path,
                "issue": "Concept ownership unclear",
                "note": node.get("concept_evidence", "")
            })
        # Check import edges
        for imp in node.get("imports", []):
            if isinstance(imp, dict) and imp.get("source") == "AMBIGUOUS":
                ambiguous.append({
                    "file": file_path,
                    "issue": f"Ambiguous dependency on {imp['file']}",
                    "note": imp.get("review_note", "")
                })
    return ambiguous
```

Surface AMBIGUOUS items in `vibe-graph: status` under "Needs review".
Never silently discard them. Never treat AMBIGUOUS as EXTRACTED.
