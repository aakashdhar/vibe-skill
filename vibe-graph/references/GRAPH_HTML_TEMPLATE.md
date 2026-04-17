# GRAPH_HTML_TEMPLATE.md

Read during vibe-graph: init, build, and update when generating graph.html.
The interactive visual for developers. No external libraries.
Pure HTML + CSS + vanilla JavaScript. Self-contained single file.

---

## Visual design

### Node colours by type
```
agent        → #6366f1  (indigo)
verifier     → #22c55e  (green)
component    → #f97316  (orange)
route        → #3b82f6  (blue)
model        → #a855f7  (purple)
service      → #06b6d4  (cyan)
test         → #84cc16  (lime)
tool         → #64748b  (slate)
config       → #94a3b8  (light slate)
foundation   → #cbd5e1  (very light slate)
```

### Node states — visual treatment
```
planned  → dashed border, 40% opacity, lighter fill
partial  → solid border, 70% opacity
built    → solid border, 100% opacity
deleted  → strikethrough label, very low opacity
```

### Node sizing
Size by connection count (degree centrality):
```
0-2 connections  → small node (r=8)
3-6 connections  → medium node (r=14)
7-12 connections → large node (r=20)
13+ connections  → hub node (r=28) — flag these, may indicate SRP violation
```

---

## Two views

**File view** — shows DEPENDENCY_GRAPH (technical)
Toggle button: "File view | Concept view"

Nodes = source files
Edges = import relationships
Edge direction: A → B means A imports B

**Concept view** — shows CONCEPT_GRAPH (semantic)
Nodes = concepts (features, agents, etc)
Node size = number of files in concept
Edges = concept dependencies
Edge colour: green = healthy, red = potential violation

---

## Interaction

**Click node** → sidebar shows:
- Full node data from JSON
- Direct connections listed
- Blast radius files listed
- Last modified date
- State (planned/partial/built)
- Link to open file in editor (if supported)

**Hover node** → highlight all connected nodes
Unhighlighted nodes fade to 20% opacity.

**Search bar** → filter nodes by name
Matching nodes highlight, others fade.

**Filter by type** → checkboxes per node type
Hide/show agents, components, routes, models independently.

**Filter by concept** → dropdown
Show only files belonging to selected concept.
Useful for understanding one feature's file set.

**Filter by state** → planned / partial / built
Show only planned nodes to see what's not built yet.
Show only built nodes to see the real codebase.

---

## HTML template structure

```html
<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>[Project Name] — Dependency Graph</title>
  <style>
    /* embed all styles — no external CSS */
    * { box-sizing: border-box; margin: 0; padding: 0; }
    body { font-family: system-ui, sans-serif; background: #0f172a; color: #e2e8f0; }

    #canvas { width: 100vw; height: 100vh; }

    #controls {
      position: fixed; top: 16px; left: 16px;
      background: #1e293b; border-radius: 8px; padding: 12px;
      display: flex; gap: 8px; align-items: center;
    }

    #sidebar {
      position: fixed; right: 0; top: 0; bottom: 0; width: 320px;
      background: #1e293b; padding: 20px; overflow-y: auto;
      transform: translateX(100%); transition: transform 0.2s;
    }
    #sidebar.open { transform: translateX(0); }

    .node-type-[type] { fill: [colour]; }
    .node-planned { opacity: 0.4; stroke-dasharray: 4; }
    .node-built { opacity: 1; }

    .edge { stroke: #334155; stroke-width: 1; marker-end: url(#arrow); }
    .edge-violation { stroke: #ef4444; stroke-width: 2; }
  </style>
</head>
<body>

<div id="controls">
  <input type="text" id="search" placeholder="Search files..." />
  <button id="toggle-view">Concept view</button>
  <select id="filter-concept">
    <option value="all">All concepts</option>
    <!-- populated from CONCEPT_GRAPH.json -->
  </select>
  <label><input type="checkbox" id="show-planned" checked> Show planned</label>
  <span id="stats">[N] nodes · [N] edges</span>
</div>

<svg id="canvas">
  <defs>
    <marker id="arrow" viewBox="0 0 10 10" refX="8" refY="5"
            markerWidth="6" markerHeight="6" orient="auto">
      <path d="M2 1L8 5L2 9" fill="none" stroke="#475569"
            stroke-width="1.5" stroke-linecap="round"/>
    </marker>
  </defs>
  <!-- nodes and edges rendered here by JavaScript -->
</svg>

<div id="sidebar">
  <h3 id="node-name"></h3>
  <div id="node-details"></div>
  <div id="blast-radius">
    <h4>Blast radius</h4>
    <ul id="blast-list"></ul>
  </div>
</div>

<script>
  // Embed graph data directly — no fetch needed, fully offline
  const DEPENDENCY_GRAPH = [DEPENDENCY_GRAPH_JSON];
  const CONCEPT_GRAPH = [CONCEPT_GRAPH_JSON];

  // Force-directed layout using basic physics simulation
  // No D3 — pure vanilla JS force simulation
  class ForceGraph {
    constructor(nodes, edges) {
      this.nodes = nodes.map(n => ({ ...n, x: Math.random() * 800, y: Math.random() * 600, vx: 0, vy: 0 }));
      this.edges = edges;
      this.alpha = 1;
    }

    tick() {
      // Repulsion between all nodes
      for (let i = 0; i < this.nodes.length; i++) {
        for (let j = i + 1; j < this.nodes.length; j++) {
          const a = this.nodes[i], b = this.nodes[j];
          const dx = b.x - a.x, dy = b.y - a.y;
          const dist = Math.sqrt(dx*dx + dy*dy) || 1;
          const force = (300 * 300) / (dist * dist);
          a.vx -= force * dx / dist;
          a.vy -= force * dy / dist;
          b.vx += force * dx / dist;
          b.vy += force * dy / dist;
        }
      }

      // Attraction along edges
      for (const edge of this.edges) {
        const a = this.nodes.find(n => n.id === edge.source);
        const b = this.nodes.find(n => n.id === edge.target);
        if (!a || !b) continue;
        const dx = b.x - a.x, dy = b.y - a.y;
        const dist = Math.sqrt(dx*dx + dy*dy) || 1;
        const force = (dist - 120) * 0.05;
        a.vx += force * dx / dist;
        a.vy += force * dy / dist;
        b.vx -= force * dx / dist;
        b.vy -= force * dy / dist;
      }

      // Apply velocity with damping
      this.alpha *= 0.995;
      for (const node of this.nodes) {
        node.x += node.vx * this.alpha;
        node.y += node.vy * this.alpha;
        node.vx *= 0.9;
        node.vy *= 0.9;
      }
    }

    run(iterations = 300) {
      for (let i = 0; i < iterations; i++) this.tick();
    }
  }

  // Render function — called on init and on view toggle
  function render(graphData, view) {
    // Build nodes and edges from graph JSON
    // Render SVG elements
    // Attach click/hover handlers
  }

  // Sidebar population
  function showNodeDetails(nodeId) {
    const node = DEPENDENCY_GRAPH[nodeId] || CONCEPT_GRAPH[nodeId];
    // Populate sidebar with node data and blast radius
    document.getElementById('sidebar').classList.add('open');
  }

  // Search
  document.getElementById('search').addEventListener('input', e => {
    const q = e.target.value.toLowerCase();
    // Fade non-matching nodes
  });

  // Init
  render(DEPENDENCY_GRAPH, 'file');
</script>

</body>
</html>
```

---

## graph.html generation rules

**Always self-contained.** No CDN links. No external fonts. No fetch calls.
The file must open offline in a browser and work completely.

**Embed graph data as JavaScript constants.**
Replace `[DEPENDENCY_GRAPH_JSON]` and `[CONCEPT_GRAPH_JSON]`
with the actual JSON content, serialised as a JS object literal.

**Keep it under 500KB.**
Large projects with 200+ nodes should use node clustering —
group nodes by concept into cluster nodes, expand on click.

**Update incrementally.**
On `vibe-graph: update`, re-embed only the changed node data.
Full re-render is triggered by reloading the HTML in the browser.
No server required. Open the file directly.
