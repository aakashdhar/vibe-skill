#!/usr/bin/env python3
"""
vibe state helper — the deterministic half of the headless contract
(vibe-mode/references/HEADLESS.md).

Skills call this instead of hand-writing JSON, so the state an outside driver or UI
reads is always well-formed. Zero dependencies (stdlib only). Run from the project root.

  vibe_state.py mode [--run]               # resolved settings as JSON (--run: forced autonomous)
  vibe_state.py run-state set --status S [--phase N] [--reason R] [--next A]
  vibe_state.py run-state show
  vibe_state.py gate set spec|design --status pending|approved|skipped|na
                                   [--report PATH] [--by human|agent-autonomous]
                                   [--accept-open REASON] [--backfill]
  vibe_state.py gate check spec|design     # exit 0 if approved/skipped/na, else 1
  vibe_state.py gate reopen N|final --reason R --by SKILL   # code changed after a passed review
  vibe_state.py gate show
  vibe_state.py attempt TASK-ID [--show]   # count a dispatch; exit 1 once the budget (2) is spent
  vibe_state.py cycle N|final [--show]     # count a gate fix cycle; exit 1 once the budget (2) is spent
  vibe_state.py counters reset [--task ID] [--phase N] [--all]
  vibe_state.py counters show

Counters live in vibe/.run_state.json, so a new session inherits the budget the last one
spent. Only a person resets them (`vibe-mode: resume`, or `counters reset`), and a passed
gate resets that gate's fix cycles.

Gate checks enforced here, so no agent can talk its way past them:
  * design approved needs 0 MUST-FIX in the critique (default vibe/design/critique.md).
    A person may approve with open MUST-FIX items only with --by human --accept-open "why".
  * spec approved --by agent-autonomous needs --report pointing at a vibe-goldfish
    review (vibe/goldfish/<target>) that converged on the documents as they are now.
  * --backfill is the one exception, for both gates: a project that predates the gates
    and is already being built (HEADLESS.md §5).

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

ATTEMPT_BUDGET = 2       # dispatches per task: the first try and one diagnosis-first retry
CYCLE_BUDGET = 2         # fix cycles per review gate
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

def resolve(run=False):
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
    if run and out["vibe_mode"] != "autonomous":
        out["vibe_mode"], source["vibe_mode"] = "autonomous", "run"
    out["source"] = source
    if warnings:
        out["warnings"] = warnings
    return out


def cmd_mode(args):
    print(json.dumps(resolve(run=getattr(args, "run", False)), indent=2))


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
    if prev.get("counters"):
        entry["counters"] = prev["counters"]      # budgets survive every status change
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


def _must_fix_count(report):
    """Open MUST-FIX items in a vibe-design critique (`## MUST-FIX (N)` heading)."""
    try:
        text = Path(report).read_text()
    except OSError:
        return None
    m = re.search(r"^##\s+MUST-FIX\s*\((\d+)\)", text, re.M | re.I)
    return int(m.group(1)) if m else None


def _goldfish_verdict(report):
    """Verdict of a vibe-goldfish review, read through goldfish.py itself."""
    import subprocess
    target = Path(report)
    if target.name == "ledger.json":
        target = target.parent
    gf = Path(__file__).resolve().parents[2] / "vibe-goldfish" / "scripts" / "goldfish.py"
    if not gf.exists() or target.parent != Path("vibe/goldfish"):
        return None
    r = subprocess.run([sys.executable, str(gf), "status", target.name, "--json"],
                       capture_output=True, text=True)
    try:
        return json.loads(r.stdout)
    except ValueError:
        return None


def cmd_gate_set(args):
    if args.kind not in GATE_KINDS:
        sys.exit(f"ERROR: gate must be one of {sorted(GATE_KINDS)}")
    if args.status not in GATE_STATUSES:
        sys.exit(f"ERROR: status must be one of {sorted(GATE_STATUSES)}")
    extra = {}
    if args.kind == "design" and args.status == "approved" and args.backfill:
        extra["backfill"] = True          # project predates the gate (HEADLESS.md §5)
    elif args.kind == "design" and args.status == "approved":
        report = args.report or "vibe/design/critique.md"
        n = _must_fix_count(report)
        if n is None:
            sys.exit(f"ERROR: no critique with a '## MUST-FIX (N)' heading at {report}. Run `design: critique` first")
        if n > 0:
            if args.by != "human" or not args.accept_open:
                sys.exit(f"ERROR: {n} MUST-FIX item(s) still open in {report}. Run `design: fix must` again, "
                         "or a person approves anyway with --by human --accept-open \"<why>\"")
            extra["accepted_open"] = {"must_fix": n, "reason": args.accept_open}
        extra["must_fix"] = n
        args.report = report
    if args.kind == "spec" and args.status == "approved" and args.by == "human" and args.report:
        st = _goldfish_verdict(args.report)
        if st is not None:
            extra["reviewed"] = st.get("verdict") == "converged"
            if not extra["reviewed"]:
                print(f"note: the goldfish review at {args.report} is '{st.get('verdict')}' on the current text; "
                      "the approval is recorded as given on unreviewed changes (reviewed: false)", file=sys.stderr)
    if args.kind == "spec" and args.status == "approved" and args.by == "agent-autonomous":
        if args.backfill:
            extra["backfill"] = True
        else:
            st = _goldfish_verdict(args.report) if args.report else None
            if not st:
                sys.exit("ERROR: an agent may approve the spec only with --report vibe/goldfish/<target> "
                         "pointing at an independent vibe-goldfish review")
            if st.get("verdict") != "converged":
                sys.exit(f"ERROR: the goldfish review is '{st.get('verdict')}' ({st.get('reason') or st.get('note') or 'not converged'}). "
                         "An agent can't sign off the spec until it converges on the current text")
            extra["goldfish"] = {"rounds": st.get("rounds"), "isolation": st.get("isolation")}
    g = _read_json(GATES, {})
    g.setdefault("phases", {})
    date = datetime.date.today().isoformat()
    entry = {"status": args.status, "date": date, "by": args.by, **extra}
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


def cmd_gate_reopen(args):
    """A skill changed code after a review passed: the review no longer covers it."""
    g = _read_json(GATES, {})
    if args.phase == "final":
        entry = g.get("final")
    else:
        entry = (g.get("phases") or {}).get(str(args.phase))
    if not entry:
        print(f"no review recorded for {args.phase} — nothing to reopen")
        return
    if entry.get("review") == "passed":
        entry["review"] = "open"
        entry["reopened"] = {"by": args.by, "reason": args.reason, "date": datetime.date.today().isoformat()}
        _write_json(GATES, g)
        print(f"review gate {args.phase} → open (reopened by {args.by}: {args.reason}) — run `review:` again")
    else:
        print(f"review gate {args.phase} already {entry.get('review')}")


# ---------------------------------------------------------------- counters

def _counters():
    rs = _read_json(RUN_STATE, {})
    c = rs.setdefault("counters", {})
    c.setdefault("attempts", {})
    c.setdefault("fix_cycles", {})
    return rs, c


def _bump(bucket, key, budget, show, label):
    rs, c = _counters()
    n = c[bucket].get(key, 0)
    if show:
        print(n)
        return
    n += 1
    c[bucket][key] = n
    _write_json(RUN_STATE, rs)
    if n > budget:
        print(f"{label} {key}: {n - 1} of {budget} already used — budget spent, STOP for a person")
        sys.exit(1)
    print(f"{label} {key}: {n} of {budget}")


def cmd_attempt(args):
    _bump("attempts", args.task, ATTEMPT_BUDGET, args.show, "attempt")


def cmd_cycle(args):
    _bump("fix_cycles", str(args.phase), CYCLE_BUDGET, args.show, "fix cycle")


def cmd_counters_reset(args):
    rs, c = _counters()
    if args.all:
        c["attempts"], c["fix_cycles"] = {}, {}
    if args.task:
        c["attempts"].pop(args.task, None)
    if args.phase:
        c["fix_cycles"].pop(str(args.phase), None)
    if not (args.all or args.task or args.phase):
        sys.exit("ERROR: say what to reset: --task ID, --phase N or --all")
    _write_json(RUN_STATE, rs)
    print("counters reset")


def cmd_counters_show(_args):
    print(json.dumps(_counters()[1], indent=2))


# ---------------------------------------------------------------- cli

def main():
    ap = argparse.ArgumentParser(prog="vibe_state.py")
    sub = ap.add_subparsers(dest="cmd", required=True)

    m = sub.add_parser("mode")
    m.add_argument("--run", action="store_true", help="invoked by `vibe-mode: run`: force autonomous")
    m.set_defaults(fn=cmd_mode)

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
    s.add_argument("--accept-open", help="design: a person approves with MUST-FIX items open, and why")
    s.add_argument("--backfill", action="store_true", help="project predates the gates (HEADLESS.md §5)")
    s.set_defaults(fn=cmd_gate_set)
    c = gt.add_parser("check")
    c.add_argument("kind")
    c.set_defaults(fn=cmd_gate_check)
    gt.add_parser("show").set_defaults(fn=cmd_gate_show)
    r = gt.add_parser("reopen")
    r.add_argument("phase")
    r.add_argument("--reason", required=True)
    r.add_argument("--by", required=True)
    r.set_defaults(fn=cmd_gate_reopen)

    a = sub.add_parser("attempt")
    a.add_argument("task"); a.add_argument("--show", action="store_true")
    a.set_defaults(fn=cmd_attempt)
    a = sub.add_parser("cycle")
    a.add_argument("phase"); a.add_argument("--show", action="store_true")
    a.set_defaults(fn=cmd_cycle)
    ct = sub.add_parser("counters").add_subparsers(dest="sub", required=True)
    a = ct.add_parser("reset")
    a.add_argument("--task"); a.add_argument("--phase"); a.add_argument("--all", action="store_true")
    a.set_defaults(fn=cmd_counters_reset)
    ct.add_parser("show").set_defaults(fn=cmd_counters_show)

    args = ap.parse_args()
    args.fn(args)


if __name__ == "__main__":
    main()
