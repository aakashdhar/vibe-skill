#!/usr/bin/env python3
"""
vibe state helper — the deterministic half of the headless contract
(vibe-mode/references/HEADLESS.md).

Skills call this instead of hand-writing JSON, so the state an outside driver or UI
reads is always well-formed. Zero dependencies (stdlib only). Run from the project root.

  vibe_state.py mode                       # resolved settings as JSON
  vibe_state.py run-state set --status S [--phase N] [--reason R] [--next A]
  vibe_state.py run-state show
  vibe_state.py gate set spec|design --status pending|approved|skipped|na
                                   [--report PATH] [--by human|agent-autonomous]
  vibe_state.py gate check spec|design     # exit 0 if approved/skipped/na, else 1
  vibe_state.py gate show

Settings (resolved in this order — first hit wins):
  1. environment: VIBE_MODE, VIBE_APPROVALS, VIBE_PHASES   (set by a driver)
  2. CLAUDE.md `## Execution mode` lines: VIBE_MODE= / APPROVALS= / PHASES=
  3. defaults: VIBE_MODE=manual, APPROVALS=human, PHASES=stop
"""
import argparse
import datetime
import json
import os
import re
import sys
from pathlib import Path

SETTINGS = {
    # key in CLAUDE.md : (env var, default, allowed values)
    "VIBE_MODE": ("VIBE_MODE", "manual", {"manual", "autonomous"}),
    "APPROVALS": ("VIBE_APPROVALS", "human", {"human", "auto"}),
    "PHASES": ("VIBE_PHASES", "stop", {"stop", "continue"}),
}
RUN_STATUSES = {"running", "phase_done", "needs_human", "failed", "complete"}
GATE_KINDS = {"spec", "design"}
GATE_STATUSES = {"pending", "approved", "skipped", "na"}
CLEARED = {"approved", "skipped", "na"}

RUN_STATE = Path("vibe/.run_state.json")
GATES = Path("vibe/.gates.json")
TASKS = Path("vibe/TASKS.md")
CLAUDE = Path("CLAUDE.md")


def _now():
    return datetime.datetime.now().astimezone().isoformat(timespec="seconds")


def _read_json(p, default):
    try:
        text = p.read_text()
        return json.loads(text) if text.strip() else default
    except (OSError, ValueError):
        return default


def _write_json(p, data):
    p.parent.mkdir(parents=True, exist_ok=True)
    tmp = p.with_suffix(p.suffix + ".tmp")
    tmp.write_text(json.dumps(data, indent=2) + "\n")
    tmp.replace(p)          # atomic: a reader never sees a half-written file


# ---------------------------------------------------------------- settings

def resolve():
    from_file = {}
    try:
        for line in CLAUDE.read_text().splitlines():
            m = re.match(r"\s*(VIBE_MODE|APPROVALS|PHASES)\s*=\s*([A-Za-z_]+)", line)
            if m and m.group(1) not in from_file:
                from_file[m.group(1)] = m.group(2).strip().lower()
    except OSError:
        pass
    out, source, warnings = {}, {}, []
    for key, (env, default, allowed) in SETTINGS.items():
        val, src = default, "default"
        for cand, where in ((os.environ.get(env, "").strip().lower(), "env"),
                            (from_file.get(key, ""), "CLAUDE.md")):
            if not cand:
                continue
            if cand in allowed:
                val, src = cand, where
                break
            warnings.append(f"{key}={cand!r} from {where} is not one of {sorted(allowed)}; ignored")
        out[key.lower()] = val
        source[key.lower()] = src
    out["source"] = source
    if warnings:
        out["warnings"] = warnings
    return out


def cmd_mode(_args):
    print(json.dumps(resolve(), indent=2))


# ---------------------------------------------------------------- run state

def cmd_run_state_set(args):
    if args.status not in RUN_STATUSES:
        sys.exit(f"ERROR: status must be one of {sorted(RUN_STATUSES)}")
    prev = _read_json(RUN_STATE, {})
    entry = {"status": args.status, "phase": args.phase, "reason": args.reason or "",
             "next_action": args.next or "", "at": _now()}
    history = (prev.get("history") or [])
    if prev.get("status"):
        history.append({k: prev.get(k) for k in ("status", "phase", "reason", "at")})
    entry["history"] = history[-20:]
    _write_json(RUN_STATE, entry)
    print(f"run state → {args.status}" + (f" (phase {args.phase})" if args.phase else "")
          + (f": {args.reason}" if args.reason else ""))


def cmd_run_state_show(_args):
    print(json.dumps(_read_json(RUN_STATE, {}), indent=2))


# ---------------------------------------------------------------- gates

_MARK = {"pending": "⬜", "approved": "✅", "skipped": "➖", "na": "➖"}


def _label(status, date):
    return {"pending": "pending", "approved": f"approved {date}",
            "skipped": f"skipped {date}", "na": "n/a (non-UI project)"}[status]


def _flip_tasks_line(kind, status, date):
    """Rewrite the gate line under `## Spec gate` / `## Design gate` in TASKS.md, keeping
    any ` · description` suffix. Silently does nothing if the heading isn't there."""
    try:
        lines = TASKS.read_text().splitlines()
    except OSError:
        return False
    head = re.compile(rf"^##\s+{kind}\s+gate\b", re.I)
    gate = re.compile(rf"^(\s*)(⬜|✅|➖|🔴)\s*{kind}:\s*(.*)$", re.I)
    for i, line in enumerate(lines):
        if not head.match(line):
            continue
        for j in range(i + 1, min(i + 6, len(lines))):
            if lines[j].startswith("## "):
                break
            m = gate.match(lines[j])
            if m:
                rest = m.group(3)
                suffix = rest[rest.index(" · "):] if " · " in rest else ""
                lines[j] = f"{m.group(1)}{_MARK[status]} {kind}: — {_label(status, date)}{suffix}"
                TASKS.write_text("\n".join(lines) + "\n")
                return True
        break
    return False


def cmd_gate_set(args):
    if args.kind not in GATE_KINDS:
        sys.exit(f"ERROR: gate must be one of {sorted(GATE_KINDS)}")
    if args.status not in GATE_STATUSES:
        sys.exit(f"ERROR: status must be one of {sorted(GATE_STATUSES)}")
    g = _read_json(GATES, {})
    g.setdefault("phases", {})
    date = datetime.date.today().isoformat()
    entry = {"status": args.status, "date": date, "by": args.by}
    if args.report:
        entry["report"] = args.report
    g[args.kind] = entry
    _write_json(GATES, g)
    flipped = _flip_tasks_line(args.kind, args.status, date)
    print(f"{args.kind} gate → {args.status}" + (" (TASKS.md line updated)" if flipped else ""))


def cmd_gate_check(args):
    status = (_read_json(GATES, {}).get(args.kind) or {}).get("status", "")
    print(status or "unset")
    sys.exit(0 if status in CLEARED else 1)


def cmd_gate_show(_args):
    print(json.dumps(_read_json(GATES, {}), indent=2))


# ---------------------------------------------------------------- cli

def main():
    ap = argparse.ArgumentParser(prog="vibe_state.py")
    sub = ap.add_subparsers(dest="cmd", required=True)

    sub.add_parser("mode").set_defaults(fn=cmd_mode)

    rs = sub.add_parser("run-state").add_subparsers(dest="sub", required=True)
    s = rs.add_parser("set")
    s.add_argument("--status", required=True)
    s.add_argument("--phase")
    s.add_argument("--reason")
    s.add_argument("--next")
    s.set_defaults(fn=cmd_run_state_set)
    rs.add_parser("show").set_defaults(fn=cmd_run_state_show)

    gt = sub.add_parser("gate").add_subparsers(dest="sub", required=True)
    s = gt.add_parser("set")
    s.add_argument("kind")
    s.add_argument("--status", required=True)
    s.add_argument("--report")
    s.add_argument("--by", default="human", choices=["human", "agent-autonomous"])
    s.set_defaults(fn=cmd_gate_set)
    c = gt.add_parser("check")
    c.add_argument("kind")
    c.set_defaults(fn=cmd_gate_check)
    gt.add_parser("show").set_defaults(fn=cmd_gate_show)

    args = ap.parse_args()
    args.fn(args)


if __name__ == "__main__":
    main()
