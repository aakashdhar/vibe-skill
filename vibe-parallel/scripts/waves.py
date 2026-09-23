#!/usr/bin/env python3
"""
vibe-parallel wave engine — deterministic scheduling.

The LLM's job is EXTRACTION: read the task file and write a tasks JSON (each task's
id, deps, the files it writes/reads, and size). This script does the COMPUTATION —
dependency layering, write-write + read-write conflict resolution, god-node deferral,
size-aware fast-lane splitting, and the time estimate — so the model never
hand-simulates the scheduling algorithm (a real silent-error risk).

Zero dependencies (stdlib only).

Input JSON (default: vibe/parallel/tasks.json):
{
  "tasks": [
    {"id":"TASK-001","deps":[],"writes":["src/a.py"],"reads":[],"size":"M"},
    {"id":"TASK-002","deps":["TASK-001"],"writes":["src/b.py"],"reads":["src/a.py"],"size":"S"}
  ],
  "main_session_owned": ["vibe/CODEBASE.md","vibe/DECISIONS.md","vibe/IMPLEMENTATION_LOG.md","vibe/TASKS.md","CLAUDE.md"],
  "god_nodes": ["src/core.py"]          // optional; pairs coupled to same god node deferred
}

Usage:
  python3 waves.py plan [tasks.json]     # prints the wave plan + conflicts + estimate
  python3 waves.py plan --json [file]    # machine-readable plan (for the orchestrator)
"""
import json, sys, argparse
from collections import defaultdict, deque
from pathlib import Path

SIZE_HOURS = {"S": 1.5, "M": 3.0, "L": 5.0}
DEFAULT_OWNED = {"vibe/CODEBASE.md", "vibe/DECISIONS.md", "vibe/IMPLEMENTATION_LOG.md", "vibe/TASKS.md", "CLAUDE.md"}


def load(path):
    p = Path(path)
    if not p.exists():
        sys.exit(f"ERROR: {path} not found. The LLM writes it from the task file first.")
    try:
        data = json.loads(p.read_text())
    except json.JSONDecodeError as e:
        sys.exit(f"ERROR: {path} invalid JSON: {e}")
    tasks = {t["id"]: t for t in data.get("tasks", [])}
    if not tasks:
        sys.exit("ERROR: no tasks in file.")
    owned = set(data.get("main_session_owned", DEFAULT_OWNED))
    gods = set(data.get("god_nodes", []))
    return tasks, owned, gods


def build_waves(tasks):
    """Kahn-style layering: a task is in wave N if its deepest dependency is in N-1."""
    indeg = {tid: 0 for tid in tasks}
    children = defaultdict(list)
    for tid, t in tasks.items():
        for d in t.get("deps", []):
            if d in tasks:
                indeg[tid] += 1
                children[d].append(tid)
    # detect cycles up front
    layer = [tid for tid in tasks if indeg[tid] == 0]
    if not layer:
        sys.exit("ERROR: dependency cycle — no task with zero deps.")
    waves, seen = [], set()
    frontier = layer
    while frontier:
        wave = sorted(frontier)
        waves.append(wave)
        seen.update(wave)
        nxt = []
        for tid in wave:
            for c in children[tid]:
                indeg[c] -= 1
                if indeg[c] == 0:
                    nxt.append(c)
        frontier = nxt
    if len(seen) != len(tasks):
        missing = sorted(set(tasks) - seen)
        sys.exit(f"ERROR: dependency cycle involving: {', '.join(missing)}")
    return waves


def _unknown(t): return t.get("writes", []) is None   # touches unknown → run alone
def _writes(t): return set(t.get("writes") or [])
def _reads(t):  return set(t.get("reads", []))


def defer(waves, losers, wave_idx):
    """Move losers out of wave_idx into the front of the next wave (create if needed)."""
    if not losers:
        return
    waves[wave_idx] = [t for t in waves[wave_idx] if t not in losers]
    if wave_idx + 1 < len(waves):
        waves[wave_idx + 1] = sorted(set(losers) | set(waves[wave_idx + 1]))
    else:
        waves.append(sorted(losers))


def resolve_write_write(waves, tasks, owned, log):
    for i in range(len(waves)):
        claimed, losers = {}, set()
        for tid in sorted(waves[i]):
            for f in _writes(tasks[tid]):
                if f in owned:
                    continue          # main-session-owned: never a subagent write
                if f in claimed:
                    losers.add(tid)
                    log.append(f"write-write: {tid} deferred from wave {i+1} "
                               f"(conflicts with {claimed[f]} on {f})")
                    break
                claimed[f] = tid
        defer(waves, losers, i)


def resolve_read_write(waves, tasks, owned, log):
    for i in range(len(waves)):
        writers = {}
        for tid in waves[i]:
            for f in _writes(tasks[tid]):
                if f not in owned:
                    writers[f] = tid
        losers = set()
        for tid in sorted(waves[i]):
            for f in _reads(tasks[tid]):
                if f in writers and writers[f] != tid:
                    losers.add(tid)
                    log.append(f"read-write: {tid} deferred from wave {i+1} "
                               f"(reads {f} written by {writers[f]} same wave)")
                    break
        defer(waves, losers, i)


def resolve_unknown(waves, tasks, log):
    """A task whose written files are unknown (`"writes": null`) could conflict with
    anything, so it never shares a wave: keep it alone, defer everything else."""
    for i in range(len(waves)):
        if len(waves[i]) < 2:
            continue
        unknown = sorted(t for t in waves[i] if _unknown(tasks[t]))
        if not unknown:
            continue
        keep = unknown[0]
        losers = set(waves[i]) - {keep}
        log.append(f"unknown-writes: {keep} runs alone in wave {i+1} "
                   f"(its files are unknown); deferred {', '.join(sorted(losers))}")
        defer(waves, losers, i)


def resolve_god_nodes(waves, tasks, gods, log):
    if not gods:
        return
    for i in range(len(waves)):
        losers, touched_by = set(), {}
        for tid in sorted(waves[i]):
            files = _writes(tasks[tid]) | _reads(tasks[tid])
            hit = files & gods
            for g in hit:
                if g in touched_by:
                    losers.add(tid)
                    log.append(f"god-node WARN: {tid} deferred from wave {i+1} "
                               f"(couples to {g} with {touched_by[g]})")
                    break
                touched_by[g] = tid
        defer(waves, losers, i)


def enforce_deps(waves, tasks, log):
    """Conflict deferral only ever pushes a task later, which can land it in the same
    wave as (or after) one of its own dependents. Re-layer so every task sits strictly
    after all of its dependencies, cascading as needed. Returns the new wave list."""
    wave_of = {tid: i for i, w in enumerate(waves) for tid in w}
    changed = True
    while changed:
        changed = False
        for tid, t in tasks.items():
            need = max((wave_of[d] + 1 for d in t.get("deps", []) if d in wave_of), default=0)
            if wave_of[tid] < need:
                log.append(f"dependency: {tid} moved from wave {wave_of[tid]+1} to wave "
                           f"{need+1} (must follow its dependencies)")
                wave_of[tid] = need
                changed = True
    out = [[] for _ in range(max(wave_of.values(), default=-1) + 1)]
    for tid, i in wave_of.items():
        out[i].append(tid)
    return [sorted(w) for w in out]


def _conflicts(a, b):
    """True if two tasks can't run at the same time (shared write, or one reads what
    the other writes)."""
    wa, wb, ra, rb = _writes(a), _writes(b), _reads(a), _reads(b)
    return bool(wa & wb or ra & wb or rb & wa)


def fast_lanes(waves, tasks, owned, gods, log):
    """Size-aware splitting (WAVE_BUILDER.md Pass 4). When wave N holds an L task beside
    S/M tasks, a wave N+1 task that does not depend on (or conflict with) any L task can
    start as soon as wave N's S/M tasks finish — it runs alongside the L task instead of
    waiting for it. Promoted tasks move out of wave N+1 into wave N's fast lane.
    Returns {wave_number (1-based): {"tasks": [...], "unlock_after": [...]}}."""
    lanes = {}
    for i in range(len(waves) - 1):
        wave = waves[i]
        big = [t for t in wave if tasks[t].get("size", "M") == "L"]
        small = [t for t in wave if tasks[t].get("size", "M") in ("S", "M")]
        if not big or not small:
            continue
        big_set = set(big)
        promoted, stay = [], []
        for tid in waves[i + 1]:
            t = tasks[tid]
            deps = set(t.get("deps", []))
            files = (_writes(t) | _reads(t)) - owned
            if (deps & big_set or _unknown(t) or any(_unknown(tasks[b]) for b in big)
                    or any(_conflicts(t, tasks[b]) for b in big)
                    or any(_conflicts(t, tasks[p]) for p in promoted)
                    or (gods and files & gods)):
                stay.append(tid)
            else:
                promoted.append(tid)
        if promoted:
            waves[i + 1] = stay
            lanes[i + 1] = {"tasks": sorted(promoted), "unlock_after": sorted(small)}
            log.append(f"fast lane: {', '.join(sorted(promoted))} promoted into wave {i+1} "
                       f"(start after {', '.join(sorted(small))}; run beside {', '.join(sorted(big))})")
    return lanes


def schedule(tasks, owned, gods):
    """Full deterministic plan: layer, resolve conflicts, re-layer for dependency safety
    (repeat until stable), then size-aware fast lanes."""
    waves, log = build_waves(tasks), []
    for _ in range(len(tasks) + 1):
        before = [list(w) for w in waves]
        resolve_write_write(waves, tasks, owned, log)
        resolve_read_write(waves, tasks, owned, log)
        resolve_god_nodes(waves, tasks, gods, log)
        resolve_unknown(waves, tasks, log)
        waves = enforce_deps([w for w in waves], tasks, log)
        if waves == before:
            break
    waves = [w for w in waves if w]
    lanes = fast_lanes(waves, tasks, owned, gods, log)
    waves = [w for w in waves if w]
    return waves, lanes, log


def estimate(waves, tasks, lanes=None):
    h = lambda t: SIZE_HOURS.get(tasks[t].get("size", "M"), 3.0)
    seq = sum(h(t) for t in tasks)
    par = 0.0
    for i, w in enumerate(waves, 1):
        span = max((h(t) for t in w), default=0)
        lane = (lanes or {}).get(i)
        if lane:   # fast lane starts once the S/M tasks finish, runs beside the L task
            small = max((h(t) for t in lane["unlock_after"]), default=0)
            span = max(span, small + max((h(t) for t in lane["tasks"]), default=0))
        par += span
    return seq, par


def cmd_plan(args):
    tasks, owned, gods = load(args.file)
    waves, lanes, log = schedule(tasks, owned, gods)
    seq, par = estimate(waves, tasks, lanes)

    if args.json:
        print(json.dumps({"waves": waves,
                          "fast_lanes": {str(k): v for k, v in lanes.items()},
                          "conflicts": log, "seq_hours": seq, "par_hours": par}, indent=2))
        return
    print(f"Wave plan — {len(tasks)} tasks in {len(waves)} wave(s):\n")
    for i, w in enumerate(waves, 1):
        rows = ", ".join(f"{t}({tasks[t].get('size','M')})" for t in w)
        print(f"  Wave {i}: {rows}")
        if i in lanes:
            lane = lanes[i]
            lr = ", ".join(f"{t}({tasks[t].get('size','M')})" for t in lane["tasks"])
            print(f"    fast lane: {lr} — starts when {', '.join(lane['unlock_after'])} finish")
    print("\nConflict resolutions:" if log else "\nNo conflicts — all waves clean.")
    for line in log:
        print(f"  • {line}")
    saved = seq - par
    print(f"\nEstimate: sequential ~{seq:.1f}h · parallel ~{par:.1f}h"
          f" · saved ~{saved:.1f}h ({(saved/seq*100 if seq else 0):.0f}%)")
    print("(Dollar cost: annotate from actual /cost per vibe-cost; hours are S/M/L heuristics.)")


def main():
    ap = argparse.ArgumentParser(prog="waves.py")
    sub = ap.add_subparsers(dest="cmd", required=True)
    p = sub.add_parser("plan")
    p.add_argument("file", nargs="?", default="vibe/parallel/tasks.json")
    p.add_argument("--json", action="store_true")
    p.set_defaults(fn=cmd_plan)
    args = ap.parse_args()
    args.fn(args)


if __name__ == "__main__":
    main()
