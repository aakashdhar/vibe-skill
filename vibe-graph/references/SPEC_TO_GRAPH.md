# SPEC_TO_GRAPH.md

Read during vibe-graph: init before building the spec graph.
How to extract planned nodes and edges from SPEC.md, ARCHITECTURE.md,
PLAN.md, and AGENT_ARCH.md before any code exists.

All spec-derived edges start as INFERRED — the spec describes intent,
not verified code relationships. Confidence is set per evidence strength.
Edges transition to EXTRACTED as code is written and imports are confirmed.

---

## Relationship tagging for spec-derived edges

Spec edges are always INFERRED at init time. No code exists yet —
every relationship is derived from reading planning documents, not source.

| Spec source | Confidence | Rationale |
|-------------|-----------|-----------|
| Explicit dependency statement in SPEC.md | 0.95 | "Feature B uses output of Feature A" — direct statement |
| Acceptance criterion references another feature | 0.90 | "POST /api/X calls AgentY" — specific reference |
| ARCHITECTURE.md pattern ("every agent has verifier") | 0.85 | Systematic pattern, high confidence |
| Feature grouping in same SPEC.md section | 0.80 | Same section = likely related, not guaranteed |
| File location inference from ARCHITECTURE.md folder structure | 0.80 | Location implies concept membership |
| Agent reasoning from feature name/description similarity | 0.70 | Semantic inference, lowest confidence |

**Edges transition from INFERRED to EXTRACTED** when:
- The file is created and the import statement is found in source
- vibe-graph: update runs after file creation and git diff confirms the relationship
- At that point: update `source` to `EXTRACTED`, `confidence` to `1.0`, update `evidence`

---

## What to extract from SPEC.md

### Features → concept nodes

Every named feature in SPEC.md becomes a concept node.
Look for: section headings, feature lists, user story groups.

```
SPEC.md: "## Brand DNA Extraction
  User pastes URL → GuardianAgent scrapes → returns structured Brand DNA"

→ Concept node: brand-dna-extraction
  type: feature
  state: planned
  planned_in: SPEC.md
```

### Acceptance criteria → concept metadata

Each acceptance criterion tells us what a concept needs:
models, routes, UI components, agents.

```
SPEC.md: "- POST /api/brand-dna returns BrandDNA object
          - BrandDNACard displays clarity score
          - GuardianAgent extracts voice attributes"

→ concept.api_routes: ["POST /api/brand-dna"]
  source: INFERRED, confidence: 0.90
  evidence: "SPEC.md acceptance criterion explicitly names route"

→ concept.models: ["BrandDNA"]
  source: INFERRED, confidence: 0.90
  evidence: "SPEC.md acceptance criterion names BrandDNA object"

→ concept.ui_components: ["BrandDNACard"]
  source: INFERRED, confidence: 0.90
  evidence: "SPEC.md acceptance criterion names BrandDNACard component"

→ concept.agents: ["GuardianAgent"]
  source: INFERRED, confidence: 0.90
  evidence: "SPEC.md acceptance criterion names GuardianAgent"
```

### Dependencies between features → concept edges

If one feature's description references another feature's output:
add a dependency edge.

```
SPEC.md: "Competitor discovery uses the brand industry from Brand DNA"

→ competitor-discovery depends_on brand-dna-extraction
  source: INFERRED, confidence: 0.95
  evidence: "SPEC.md: 'Competitor discovery uses brand industry from Brand DNA' — explicit dependency"

→ brand-dna-extraction depended_on_by competitor-discovery
  source: INFERRED, confidence: 0.95
  evidence: "Inverse of above"
```

**Concept node format at init time:**

```json
{
  "brand-dna-extraction": {
    "state": "planned",
    "type": "feature",
    "planned_in": "SPEC.md",
    "agents": [
      {
        "name": "GuardianAgent",
        "source": "INFERRED",
        "confidence": 0.90,
        "evidence": "SPEC.md acceptance criterion names GuardianAgent"
      }
    ],
    "verifiers": [],
    "api_routes": [
      {
        "route": "POST /api/brand-dna",
        "source": "INFERRED",
        "confidence": 0.90,
        "evidence": "SPEC.md acceptance criterion explicitly names route"
      }
    ],
    "models": [
      {
        "name": "BrandDNA",
        "source": "INFERRED",
        "confidence": 0.90,
        "evidence": "SPEC.md acceptance criterion names BrandDNA object"
      }
    ],
    "ui_components": [
      {
        "name": "BrandDNACard",
        "source": "INFERRED",
        "confidence": 0.90,
        "evidence": "SPEC.md acceptance criterion names BrandDNACard"
      }
    ],
    "depends_on": [],
    "depended_on_by": [
      {
        "concept": "competitor-discovery",
        "source": "INFERRED",
        "confidence": 0.95,
        "evidence": "SPEC.md: 'Competitor discovery uses brand industry from Brand DNA'"
      }
    ],
    "files": [],
    "tasks_total": 0,
    "tasks_complete": 0
  }
}
```

---

## What to extract from ARCHITECTURE.md

### Folder structure → planned file nodes

The folder structure section in ARCHITECTURE.md lists planned files.
Each becomes a planned file node.

```
ARCHITECTURE.md:
  src/
    agents/
      guardian_agent.py    ← agent for brand DNA
      scout_agent.py       ← agent for competitor discovery
    api/
      brand_dna.py         ← route handler
    models/
      brand_dna.py         ← Pydantic schema
```

→ File nodes (all state: planned):

```json
{
  "src/agents/guardian_agent.py": {
    "state": "planned",
    "type": "agent",
    "concept": "brand-dna-extraction",
    "concept_source": "INFERRED",
    "concept_confidence": 0.85,
    "concept_evidence": "ARCHITECTURE.md folder comment: 'agent for brand DNA'",
    "planned_in": "ARCHITECTURE.md",
    "imports": [],
    "imported_by": [],
    "rationale": [],
    "hash": null,
    "last_modified": null
  },
  "src/agents/scout_agent.py": {
    "state": "planned",
    "type": "agent",
    "concept": "competitor-discovery",
    "concept_source": "INFERRED",
    "concept_confidence": 0.85,
    "concept_evidence": "ARCHITECTURE.md folder comment: 'agent for competitor discovery'",
    "planned_in": "ARCHITECTURE.md",
    "imports": [],
    "imported_by": [],
    "rationale": [],
    "hash": null,
    "last_modified": null
  }
}
```

### Patterns → inferred planned edges

If ARCHITECTURE.md defines patterns, infer planned edges with INFERRED source.

```
ARCHITECTURE.md: "Every agent has a co-located verifier in verifiers/"

→ Infer planned nodes for each agent:
  src/agents/verifiers/guardian_verifier.py
    source: INFERRED, confidence: 0.85
    evidence: "ARCHITECTURE.md pattern: every agent has co-located verifier"

  src/agents/verifiers/scout_verifier.py
    source: INFERRED, confidence: 0.85
    evidence: "ARCHITECTURE.md pattern: every agent has co-located verifier"
```

### Tech stack → tooling nodes

```
ARCHITECTURE.md: "Tavily for web search, Supabase for database"

→ Tool nodes:
  tavily    | type: external-tool | used_by: []
  supabase  | type: external-service | used_by: []
  (no confidence tagging needed — these are EXTRACTED from explicit tech stack declaration)
```

---

## What to extract from AGENT_ARCH.md

### Agent roster → agent nodes with relationships

```
AGENT_ARCH.md:
  GuardianAgent → GuardianVerifier → [HITL] → ScoutAgent

→ Edges (all INFERRED at init time):
  guardian_agent.py → guardian_verifier.py
    source: INFERRED, confidence: 0.95
    evidence: "AGENT_ARCH.md explicit flow diagram"

  guardian_verifier.py → hitl-checkpoint-1
    source: INFERRED, confidence: 0.95
    evidence: "AGENT_ARCH.md explicit [HITL] marker"

  hitl-checkpoint-1 → scout_agent.py
    source: INFERRED, confidence: 0.95
    evidence: "AGENT_ARCH.md explicit flow diagram"
```

### Tool mapping → tool edges

```
AGENT_ARCH.md:
  ScoutAgent tools: web_search (Tavily), web_fetch

→ Edges:
  scout_agent.py → tavily
    source: INFERRED, confidence: 0.95
    evidence: "AGENT_ARCH.md tool assignment: ScoutAgent tools"

  scout_agent.py → web_fetch
    source: INFERRED, confidence: 0.95
    evidence: "AGENT_ARCH.md tool assignment: ScoutAgent tools"
```

### State ownership → model edges

```
AGENT_ARCH.md:
  brand_dna: owned by GuardianAgent, read by ScoutAgent, StrategistAgent

→ Edges:
  guardian_agent.py → BrandDNA (writes)
    source: INFERRED, confidence: 0.95
    evidence: "AGENT_ARCH.md state ownership: 'owned by GuardianAgent'"

  scout_agent.py → BrandDNA (reads)
    source: INFERRED, confidence: 0.95
    evidence: "AGENT_ARCH.md state ownership: 'read by ScoutAgent'"
```

---

## Concept assignment rules for ARCHITECTURE.md files

When a file in ARCHITECTURE.md belongs to a clear domain → assign to that concept.
When a file is shared infrastructure → assign to `foundation`.

| File pattern | Concept assignment | Source | Confidence |
|-------------|------------------|--------|------------|
| `src/agents/guardian*.py` | brand-dna-extraction | INFERRED | 0.85 |
| `src/agents/scout*.py` | competitor-discovery | INFERRED | 0.85 |
| `src/agents/base*.py` | foundation | INFERRED | 0.90 |
| `src/api/brand_dna.py` | brand-dna-extraction | INFERRED | 0.85 |
| `prisma/schema.prisma` | foundation | INFERRED | 0.90 |
| `src/config.py` | foundation | INFERRED | 0.95 |
| `tests/test_*.py` | same concept as tested file | INFERRED | 0.90 |
| Explicit comment in ARCHITECTURE.md | concept from comment | INFERRED | 0.85 |

---

## Output format for planned nodes

Every planned node has these minimum fields:

```json
{
  "state": "planned",
  "type": "[agent|verifier|route|model|component|tool|service|test|config]",
  "concept": "[concept-name]",
  "concept_source": "INFERRED",
  "concept_confidence": 0.85,
  "concept_evidence": "[which document, which line or section]",
  "planned_in": "[SPEC.md|ARCHITECTURE.md|AGENT_ARCH.md]",
  "imports": [],
  "imported_by": [],
  "rationale": [],
  "hash": null,
  "last_modified": null,
  "created_at": "[ISO timestamp of graph init]"
}
```

The `imports`, `imported_by`, and `rationale` fields are empty at init time.
They get populated by `vibe-graph: update` as files are created and git diff
reveals their actual import structure and inline comments.

---

## Transition rules: INFERRED → EXTRACTED

When `vibe-graph: update` runs after a file is created:

1. Check if the planned file now exists: `ls [file_path]`
2. If it exists — extract its actual imports from source
3. For each actual import found:
   - If it matches a INFERRED edge → update to EXTRACTED, confidence 1.0, add line evidence
   - If it's a new import not in the graph → add as EXTRACTED edge
   - If a planned INFERRED edge is NOT found in actual imports → mark as AMBIGUOUS, flag for review
4. Extract rationale comments from the new file and populate `rationale` array
5. Update node state: `planned` → `partial` or `built`

This transition is the moment the graph becomes ground-truth rather than prediction.
