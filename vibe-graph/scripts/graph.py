#!/usr/bin/env python3
"""
vibe-graph engine — deterministic graph computation.

The LLM's job is EXTRACTION: reading code and writing vibe/graph/DEPENDENCY_GRAPH.json
(what imports what, with confidence + evidence). This script does the COMPUTATION over
that JSON — degree/god-nodes, blast-radius queries, stats, and the HTML render — so the
model never has to mentally sort dictionaries or traverse a graph (a silent-error risk).

Zero dependencies (stdlib only). Node schema (flat dict of path → node):
  { "src/x.py": { "state","concept","type"?,
                  "imports":[{"file","source","confidence","evidence"}|"path", ...],
                  "imported_by":[...], "rationale":[{"kind","line","text"}]? } }

Usage:
  python3 graph.py godnodes [--top N] [--graph PATH] [--meta PATH]   # compute + write .graph-meta.json
  python3 graph.py query <file> [--depth N]                          # blast radius (certain/probable/ambiguous)
  python3 graph.py stats                                             # node/edge/confidence summary
  python3 graph.py html [--out vibe/graph/graph.html]                # render interactive graph
"""
import json, sys, argparse
from pathlib import Path

DEFAULT_GRAPH = "vibe/graph/DEPENDENCY_GRAPH.json"
DEFAULT_META  = "vibe/graph/.graph-meta.json"
DEFAULT_FLOW  = "vibe/graph/FLOW.md"


def load_graph(path):
    p = Path(path)
    if not p.exists():
        sys.exit(f"ERROR: {path} not found. Run `vibe-graph: build` first (the LLM writes it).")
    try:
        data = json.loads(p.read_text())
    except json.JSONDecodeError as e:
        sys.exit(f"ERROR: {path} is not valid JSON: {e}")
    # tolerate an optional {"nodes": {...}} wrapper
    return data.get("nodes", data) if isinstance(data, dict) else {}


def edge_file(e):
    return e if isinstance(e, str) else (e.get("file") or "")

def edge_meta(e):
    if isinstance(e, str):
        return {"file": e, "source": "EXTRACTED", "confidence": 1.0}
    return {"file": e.get("file", ""), "source": e.get("source", "EXTRACTED"),
            "confidence": float(e.get("confidence", 1.0)), "evidence": e.get("evidence", "")}


def degrees(graph):
    """Total degree = imports + imported_by per node."""
    deg = {}
    for path, node in graph.items():
        if not isinstance(node, dict):
            continue
        imp = node.get("imports", []) or []
        impby = node.get("imported_by", []) or []
        deg[path] = len(imp) + len(impby)
    return deg


def cmd_godnodes(args):
    graph = load_graph(args.graph)
    deg = degrees(graph)
    ranked = sorted(deg.items(), key=lambda kv: kv[1], reverse=True)[:args.top]
    god = [{"file": f, "degree": d,
            "concept": (graph.get(f, {}) or {}).get("concept", "")} for f, d in ranked if d > 0]
    meta_path = Path(args.meta)
    meta = {}
    if meta_path.exists() and meta_path.read_text().strip():
        try: meta = json.loads(meta_path.read_text())
        except json.JSONDecodeError: meta = {}
    meta["god_nodes"] = god
    meta_path.parent.mkdir(parents=True, exist_ok=True)
    meta_path.write_text(json.dumps(meta, indent=2) + "\n")
    print(f"God nodes (top {args.top}, by degree) → {args.meta}:")
    for g in god:
        print(f"  {g['degree']:>3}  {g['file']}" + (f"  [{g['concept']}]" if g['concept'] else ""))
    if not god:
        print("  (no edges yet — graph may be spec-only / not built)")


def cmd_query(args):
    graph = load_graph(args.graph)
    seed = args.file
    if seed not in graph:
        # tolerate suffix match (user passes a bare filename)
        matches = [k for k in graph if k.endswith(seed)]
        if len(matches) == 1:
            seed = matches[0]
        elif len(matches) > 1:
            sys.exit(f"Ambiguous '{args.file}' — matches: {', '.join(matches)}")
        else:
            sys.exit(f"'{args.file}' not in graph.")

    # BFS out to depth over both directions; classify by weakest edge confidence on the path
    from collections import deque
    seen = {seed: ("EXTRACTED", 1.0)}
    q = deque([(seed, 1.0, "EXTRACTED", 0)])
    while q:
        cur, conf, src, d = q.popleft()
        if d >= args.depth:
            continue
        node = graph.get(cur, {}) or {}
        for e in (node.get("imports", []) or []) + (node.get("imported_by", []) or []):
            m = edge_meta(e); f = m["file"]
            if not f or f == seed:
                continue
            path_conf = min(conf, m["confidence"])
            path_src = "AMBIGUOUS" if "AMBIGUOUS" in (src, m["source"]) else \
                       ("INFERRED" if "INFERRED" in (src, m["source"]) else "EXTRACTED")
            if f not in seen or path_conf > seen[f][1]:
                seen[f] = (path_src, path_conf)
                q.append((f, path_conf, path_src, d + 1))
    seen.pop(seed, None)

    certain  = sorted(f for f, (s, c) in seen.items() if s == "EXTRACTED")
    probable = sorted((f, seen[f][1]) for f in seen if seen[f][0] == "INFERRED")
    ambig    = sorted(f for f, (s, c) in seen.items() if s == "AMBIGUOUS")

    print(f"Blast radius for {seed} (depth {args.depth}):")
    print(f"\nCERTAIN — EXTRACTED path ({len(certain)}):")
    for f in certain: print(f"  ✓ {f}")
    print(f"\nPROBABLE — INFERRED path ({len(probable)}):")
    for f, c in probable: print(f"  ~ {f}  (confidence {c:.2f})")
    if ambig:
        print(f"\nAMBIGUOUS — human review ({len(ambig)}):")
        for f in ambig: print(f"  ? {f}")
    # rationale for the seed, if present
    rat = (graph.get(seed, {}) or {}).get("rationale") or []
    if rat:
        print("\nRATIONALE (why this file is the way it is):")
        for r in rat:
            print(f"  {r.get('kind','NOTE')} [line {r.get('line','?')}]: {r.get('text','')}")


def cmd_stats(args):
    graph = load_graph(args.graph)
    nodes = [n for n in graph.values() if isinstance(n, dict)]
    edges = []
    for n in nodes:
        for e in (n.get("imports", []) or []):
            edges.append(edge_meta(e))
    by_src = {}
    for e in edges:
        by_src[e["source"]] = by_src.get(e["source"], 0) + 1
    states = {}
    for n in nodes:
        states[n.get("state", "unknown")] = states.get(n.get("state", "unknown"), 0) + 1
    print(f"Nodes: {len(nodes)}")
    print(f"Import edges: {len(edges)}")
    print("  by confidence source: " + ", ".join(f"{k}={v}" for k, v in sorted(by_src.items())))
    print("  by state: " + ", ".join(f"{k}={v}" for k, v in sorted(states.items())))
    amb = sum(1 for e in edges if e["source"] == "AMBIGUOUS")
    if amb:
        print(f"⚠ {amb} AMBIGUOUS edge(s) — need human review (never silently promoted).")


MARK = {"EXTRACTED": "✓", "INFERRED": "~", "AMBIGUOUS": "?"}


def entrypoints(graph):
    """Files the LLM marked as execution entry points (`"entrypoint": true`) —
    server bootstrap, CLI main, worker entry, route roots. Flow starts here."""
    return sorted(p for p, n in graph.items()
                  if isinstance(n, dict) and n.get("entrypoint"))


def _file_flow_tree(graph, start, max_depth=6):
    """DFS over `imports` from an entry point → indented lines showing the order
    execution reaches each module. Confidence-marked; de-duped so a re-visited
    file is shown once as `(above)` instead of re-expanded (keeps cycles finite)."""
    lines, seen = [], set()

    def walk(path, depth, src):
        mark = MARK.get(src, "·")
        node = graph.get(path, {}) or {}
        concept = node.get("concept", "")
        label = f"{'  ' * depth}{mark} {path}" + (f"  [{concept}]" if concept else "")
        if path in seen:
            lines.append(label + "  (above)")
            return
        seen.add(path)
        lines.append(label)
        # function-level detail, when the LLM extracted calls for this file
        for c in (node.get("calls", []) or []):
            frm, to = c.get("from", "?"), c.get("to", "?")
            tof = c.get("to_file", "")
            lines.append(f"{'  ' * (depth + 1)}↳ {frm}() → " + (f"{tof}:{to}()" if tof else f"{to}()"))
        if depth >= max_depth:
            return
        for e in (node.get("imports", []) or []):
            m = edge_meta(e)
            if m["file"]:
                walk(m["file"], depth + 1, m["source"])

    walk(start, 0, "EXTRACTED")
    return lines


def _find_cycles(graph):
    """Import cycles (execution loops back on itself) — worth surfacing since they
    make 'order of execution' ambiguous. Returns a de-duped list of cycle paths."""
    cycles, WHITE, GREY, BLACK = [], 0, 1, 2
    color = {}

    def dfs(node, stack):
        color[node] = GREY
        stack.append(node)
        for e in (graph.get(node, {}) or {}).get("imports", []) or []:
            f = edge_file(e)
            if not f or f not in graph:
                continue
            if color.get(f, WHITE) == GREY:
                cyc = stack[stack.index(f):] + [f]
                if cyc not in cycles:
                    cycles.append(cyc)
            elif color.get(f, WHITE) == WHITE:
                dfs(f, stack)
        stack.pop()
        color[node] = BLACK

    for n in graph:
        if color.get(n, WHITE) == WHITE:
            dfs(n, [])
    return cycles


def cmd_flow(args):
    """Regenerate FLOW.md — a human- and AI-readable map of how execution travels
    (entry points → the modules/functions each reaches). DERIVED from the graph and
    rewritten every run, so it never rots. Owned by vibe-graph; hand edits are lost."""
    graph = load_graph(args.graph)
    eps = entrypoints(graph)
    L = ["<!-- AUTO-GENERATED by vibe-graph (graph.py flow). Do not edit — regenerated on every graph update. -->",
         "# Execution Flow", "",
         "_How execution travels through this codebase: entry points and the modules "
         "(and functions, where known) each one reaches. Derived from "
         "`DEPENDENCY_GRAPH.json` — never hand-written._", ""]
    if not eps:
        L += ["> **No entry points marked yet.** During extraction, set "
              "`\"entrypoint\": true` on the files where execution starts "
              "(server bootstrap, CLI `main`, worker entry, route roots), then "
              "re-run `vibe-graph: update` to populate this map."]
    else:
        L.append(f"**Entry points ({len(eps)}):** " + ", ".join(eps))
        for ep in eps:
            L += ["", f"## ▶ {ep}"]
            L += _file_flow_tree(graph, ep, args.depth)
    cyc = _find_cycles(graph)
    if cyc:
        L += ["", "## ⟳ Cycles — execution loops back (review; makes ordering ambiguous)"]
        L += [f"- {' → '.join(c)}" for c in cyc]
    L += ["", "---",
          "Legend: `✓` verified import · `~` inferred · `?` ambiguous · "
          "`↳` function call · `(above)` already shown."]
    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text("\n".join(L) + "\n")
    print(f"Wrote execution flow ({len(eps)} entry point(s), {len(cyc)} cycle(s)) → {args.out}")


def cmd_html(args):
    graph = load_graph(args.graph)
    deg = degrees(graph)
    payload = json.dumps({"graph": graph, "degree": deg})
    html = """<!doctype html><meta charset=utf-8><title>vibe-graph</title>
<style>body{margin:0;font:14px system-ui;background:#0e1116;color:#e6e6e6}
#c{width:100vw;height:100vh}.legend{position:fixed;top:8px;left:8px;font-size:12px;opacity:.8}</style>
<div class=legend>node size = degree · green = entry point · red edge = AMBIGUOUS · amber = INFERRED · gray = EXTRACTED</div>
<canvas id=c></canvas><script>
const DATA=__PAYLOAD__;const g=DATA.graph,deg=DATA.degree;
const nodes=Object.keys(g).map((id,i)=>({id,d:deg[id]||0,x:Math.cos(i)*300+innerWidth/2+Math.random()*40,y:Math.sin(i*1.7)*300+innerHeight/2+Math.random()*40}));
const idx=Object.fromEntries(nodes.map((n,i)=>[n.id,i]));const edges=[];
for(const id in g){for(const e of (g[id].imports||[])){const f=typeof e==='string'?e:e.file;if(idx[f]!=null)edges.push({s:idx[id],t:idx[f],src:(e.source||'EXTRACTED')});}}
const cv=document.getElementById('c'),cx=cv.getContext('2d');function size(){cv.width=innerWidth;cv.height=innerHeight}size();onresize=size;
function draw(){cx.clearRect(0,0,cv.width,cv.height);
for(const e of edges){const a=nodes[e.s],b=nodes[e.t];cx.strokeStyle=e.src==='AMBIGUOUS'?'#e5484d':e.src==='INFERRED'?'#f5a623':'#39404d';cx.beginPath();cx.moveTo(a.x,a.y);cx.lineTo(b.x,b.y);cx.stroke();}
for(const n of nodes){const ep=g[n.id]&&g[n.id].entrypoint;const r=4+Math.min(n.d,12)*1.6;cx.fillStyle=ep?'#3fb950':(n.d>=8?'#7c9cff':'#9aa4b2');cx.beginPath();cx.arc(n.x,n.y,r,0,7);cx.fill();if(ep){cx.strokeStyle='#3fb950';cx.lineWidth=2;cx.beginPath();cx.arc(n.x,n.y,r+3,0,7);cx.stroke();cx.lineWidth=1;}if(ep||n.d>=6){cx.fillStyle=ep?'#7ee787':'#cfd6e4';cx.fillText((ep?'▶ ':'')+n.id.split('/').pop(),n.x+r+2,n.y+3);}}}
// tiny force sim
for(let step=0;step<220;step++){for(const a of nodes){let fx=0,fy=0;for(const b of nodes){if(a===b)continue;let dx=a.x-b.x,dy=a.y-b.y,d2=dx*dx+dy*dy||1;fx+=dx/d2*800;fy+=dy/d2*800;}a.x+=Math.max(-6,Math.min(6,fx));a.y+=Math.max(-6,Math.min(6,fy));}
for(const e of edges){const a=nodes[e.s],b=nodes[e.t],dx=b.x-a.x,dy=b.y-a.y;a.x+=dx*0.01;a.y+=dy*0.01;b.x-=dx*0.01;b.y-=dy*0.01;}}
draw();
</script>"""
    html = html.replace("__PAYLOAD__", payload)
    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(html)
    print(f"Rendered {len([n for n in graph.values() if isinstance(n,dict)])} nodes → {args.out}")


def main():
    ap = argparse.ArgumentParser(prog="graph.py")
    ap.add_argument("--graph", default=DEFAULT_GRAPH)
    sub = ap.add_subparsers(dest="cmd", required=True)
    g = sub.add_parser("godnodes"); g.add_argument("--top", type=int, default=5); g.add_argument("--meta", default=DEFAULT_META); g.set_defaults(fn=cmd_godnodes)
    q = sub.add_parser("query"); q.add_argument("file"); q.add_argument("--depth", type=int, default=2); q.set_defaults(fn=cmd_query)
    s = sub.add_parser("stats"); s.set_defaults(fn=cmd_stats)
    fl = sub.add_parser("flow"); fl.add_argument("--out", default=DEFAULT_FLOW); fl.add_argument("--depth", type=int, default=6); fl.set_defaults(fn=cmd_flow)
    h = sub.add_parser("html"); h.add_argument("--out", default="vibe/graph/graph.html"); h.set_defaults(fn=cmd_html)
    args = ap.parse_args()
    args.fn(args)


if __name__ == "__main__":
    main()
