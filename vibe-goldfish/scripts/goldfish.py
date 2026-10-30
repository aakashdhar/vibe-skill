#!/usr/bin/env python3
"""
goldfish.py: the deterministic half of a vibe-goldfish review (vibe-goldfish/SKILL.md).

A goldfish review is a set of fresh, zero-context reviewer subagents ("goldfish") reading a
document cold, while the agent that wrote it (the "elephant") answers each finding under
strict rules. This script owns everything that must not depend on a model remembering it:
finding IDs, finding states, the resolution rules, and the stopping rule.

Zero dependencies (stdlib only). Run from the project root. State lives in
vibe/goldfish/<target>/ledger.json; raw reviewer output in vibe/goldfish/<target>/round-N/.

  goldfish.py init <target> --doc PATH [--doc PATH ...] --reviewers a,b,c [--max-rounds N [--human]]
  goldfish.py round <target>                       # open the next round, print its number
  goldfish.py ingest <target> --reviewer R --file F.json
  goldfish.py ingest <target> --reviewer R --not-run --reason "..."
  goldfish.py link <target> ID --reraise-of OLD | --churn-of OLD
  goldfish.py resolve <target> ID --as fix|contest|escalate|decline [--note N] [--evidence E] [--human]
  goldfish.py resolve <target> ID --as duplicate --of PRIMARY   # same problem, same round: answer it once
  goldfish.py applied <target> ID [ID ...]         # proposed fixes are now in the document
  goldfish.py decide <target> ID --as fix|accept-risk|reject --by human|agent-autonomous [--note N]
  goldfish.py status <target> [--json]             # exit 0 converged · 2 in progress · 3 needs a person
  goldfish.py isolation <target> full|partial [--note N]   # record how isolated the reviewers were
  goldfish.py report <target>                      # write vibe/goldfish/<target>/resolution.md
  goldfish.py archive <target>                     # a from-scratch redesign: set the old review aside

Severity uses the vibe scale: P0 (blocks), P1 (blocks), P2 (note, never blocks).

The stopping rule:
  * a round is CLEAN when every reviewer ran and no P0/P1 raised in that round is
    unsettled. A P0/P1 that was fixed makes the round not clean (the document changed,
    so a fresh reviewer has to look again).
  * CONVERGED = the last two rounds are clean, were run by the current reviewers, and
    reviewed exactly the text the documents have now. On a small project (BRIEF.md sized
    S) one round is enough when it is clean AND raised no P0/P1 at all: the second pass
    mostly re-finds what the first missed, which a small project can afford to skip.
    `init --thorough` keeps two rounds anyway. Each round records a hash of the
    documents when it opens, so ANY later edit (a P2 fix, the elephant-only check, a
    person's change) means another round, and a review that converged earlier re-opens
    on its own when the documents change. Earlier findings are kept for re-raise links.
  * the review stops for a person at the round cap (default 5), on churn (a new finding
    caused by an applied fix), or while an escalation waits for a decision.
"""
import argparse
import datetime
import hashlib
import json
import re
import sys
from pathlib import Path

ROOT = Path("vibe/goldfish")
SEVERITIES = {"P0", "P1", "P2"}
BLOCKING = {"P0", "P1"}
# finding states
OPEN, FIX_PROPOSED, FIXED, ESCALATED, SETTLED = "open", "fix-proposed", "fixed", "escalated", "settled"
UNRESOLVED = {OPEN, ESCALATED}            # nothing decided yet: a new round may not start
UNSETTLED = {OPEN, FIX_PROPOSED, FIXED, ESCALATED}
CATEGORIES = {"fix", "contest", "escalate", "decline", "duplicate"}
NO_CONTEST_ROLES = {"comprehension"}      # a reader who did not understand is never wrong
RANK = {"P0": 0, "P1": 1, "P2": 2}         # lower = more severe
DEFAULT_MAX_ROUNDS = 5
GF = "python3 ~/.claude/skills/vibe-goldfish/scripts/goldfish.py"


# Bookkeeping that vibe's own tools rewrite after a review is not reviewed content.
# Recording a sign-off, starting a feature or ticking a task must never make the review
# that justified it look stale. Each rule applies only to the file that carries it:
#   CLAUDE.md        the Execution mode settings, and the "### Active Feature / Bug Fix"
#                    sections vibe-add-feature / vibe-fix-bug append
#   TASKS.md         the spec/design gate lines
#   PLAN.md          a feature entry's **Status:** and **Spec:** lines, the status marker
#                    on its heading, and the older "⬜ X → 🔄 X — spec in ..." status lines
#                    (feature names, dependencies and everything else still count)
#   CODEBASE.md      "> 📝 ... Verified during ..." changelog lines
#   FEATURE_TASKS.md task status lines and checkbox state ([x], [~], [!])
# Blank lines and bare "---" rules are formatting, never content, in every file.
_SETTINGS = re.compile(r"^\s*(?:VIBE_MODE|APPROVALS|PHASES)\s*=")
_ACTIVE = re.compile(r"^###\s+Active (?:Feature|Bug Fix)\b", re.I)
_GATE = re.compile(r"^\s*(?:⬜|✅|➖|🔴)\s*(?:spec|design):", re.I)
_PLAN_BOOK = re.compile(r"^\s*\*\*(?:Status|Spec):\*\*")
_PLAN_OLD = re.compile(r"^\s*(?:⬜|🔄|✅)\s+.*(?:→|—\s*spec in vibe/features/)")
_PLAN_HEAD = re.compile(r"^(#{2,5}\s+)(?:⬜|🔄|✅)\s+")
_VERIFIED = re.compile(r"^\s*>\s*📝 .*Verified during")
_TASK_STATUS = re.compile(r"^\s*[-*]\s*\*\*Status\*\*:")
_CHECKBOX = re.compile(r"\[(?:x|X|~|!)\]")
_RULE = re.compile(r"^\s*(?:-{3,}|\*{3,})?\s*$")
HASH_V = 2


def _normalize(name, text):
    out, skipping = [], False
    for line in text.splitlines(keepends=True):
        bare = line.rstrip("\r\n")
        if _RULE.match(bare):
            continue
        if name == "CLAUDE.md":
            if _ACTIVE.match(bare):
                skipping = True
                continue
            if skipping and bare.startswith("#"):
                skipping = False
            if skipping or _SETTINGS.match(bare):
                continue
        elif name == "TASKS.md" and _GATE.match(bare):
            continue
        elif name == "PLAN.md":
            if _PLAN_BOOK.match(bare) or _PLAN_OLD.match(bare):
                continue
            line = _PLAN_HEAD.sub(r"\1", line)
        elif name == "CODEBASE.md" and _VERIFIED.match(bare):
            continue
        elif name == "FEATURE_TASKS.md":
            if _TASK_STATUS.match(bare):
                continue
            line = _CHECKBOX.sub("[ ]", line)
        out.append(line)
    return "".join(out)


def _doc_hash(docs, version=HASH_V):
    """One hash over every reviewed document, as it is on disk right now.
    version 1 is the raw-bytes hash of vibe v2.7.0, kept so older reviews still match."""
    h = hashlib.sha256()
    for d in docs:
        h.update(d.encode() + b"\0")
        try:
            raw = Path(d).read_bytes()
            h.update(raw if version == 1 else _normalize(Path(d).name, raw.decode("utf-8", "replace")).encode())
        except OSError:
            h.update(b"<missing>")
        h.update(b"\0")
    return h.hexdigest()[:16]


_SIZE = (re.compile(r"Complexity:\s*\[?\s*(XL|S|M|L)\b"),
         re.compile(r"^\*\*Size:\*\*\s*\[?\s*(XL|S|M|L)\b", re.M),
         re.compile(r"^##\s*Complexity[^\n]*\n+\s*(XL|S|M|L)\b", re.M))


def _project_size():
    """The project's size from BRIEF.md (S/M/L/XL), or None when there is no brief."""
    try:
        text = Path("BRIEF.md").read_text(errors="replace")
    except OSError:
        return None
    for rx in _SIZE:
        m = rx.search(text)
        if m:
            return m.group(1)
    return None


def _round_matches(r, docs):
    """Did this round review the documents as they are now?"""
    return r.get("doc_hash") == _doc_hash(docs, r.get("hash_v", 1))


def _now():
    return datetime.datetime.now().astimezone().isoformat(timespec="seconds")


def _slug_ok(target):
    if not re.fullmatch(r"[a-z0-9][a-z0-9._-]{0,80}", target):
        sys.exit(f"ERROR: target '{target}' must use lowercase letters, digits, '.', '_' or '-' (e.g. spec, feature-2026-10-30-export)")


def _dir(target):
    _slug_ok(target)
    return ROOT / target


def _load(target):
    p = _dir(target) / "ledger.json"
    if not p.exists():
        sys.exit(f"ERROR: no goldfish review '{target}': run: goldfish.py init {target} ...")
    return json.loads(p.read_text())


def _save(target, data):
    d = _dir(target)
    d.mkdir(parents=True, exist_ok=True)
    tmp = d / "ledger.json.tmp"
    tmp.write_text(json.dumps(data, indent=2) + "\n")
    tmp.replace(d / "ledger.json")


def _finding(data, fid):
    f = data["findings"].get(fid)
    if not f:
        sys.exit(f"ERROR: no finding {fid}")
    return f


def _current(data):
    if not data["rounds"]:
        sys.exit("ERROR: no round open: run: goldfish.py round <target>")
    return data["rounds"][-1]


# ---------------------------------------------------------------- setup

def cmd_init(a):
    reviewers = [r.strip() for r in a.reviewers.split(",") if r.strip()]
    if not reviewers:
        sys.exit("ERROR: --reviewers needs at least one reviewer")
    p = _dir(a.target) / "ledger.json"
    if p.exists():
        data = json.loads(p.read_text())
        data["docs"], data["reviewers"] = a.doc, reviewers
        if a.max_rounds is not None:
            if a.max_rounds > data["max_rounds"] and not a.human:
                sys.exit(f"ERROR: raising the round cap ({data['max_rounds']} → {a.max_rounds}) is a person's decision. "
                         "Rerun with --human once they have said so, or stop for a person")
            data["max_rounds"] = a.max_rounds
        data["quick"] = (not a.thorough) and _project_size() == "S"
        _maybe_new_cycle(a.target, data)
        _save(a.target, data)
        print(f"goldfish '{a.target}' already exists: kept {len(data['rounds'])} round(s), updated docs/reviewers")
        return
    if a.max_rounds and a.max_rounds > DEFAULT_MAX_ROUNDS and not a.human:
        sys.exit(f"ERROR: a round cap above {DEFAULT_MAX_ROUNDS} is a person's decision: rerun with --human once they have said so")
    _save(a.target, {"target": a.target, "docs": a.doc, "reviewers": reviewers,
                     "max_rounds": a.max_rounds or DEFAULT_MAX_ROUNDS, "created": _now(),
                     "quick": (not a.thorough) and _project_size() == "S",
                     "cycle_start": 0, "rounds": [], "findings": {}})
    print(f"goldfish '{a.target}' created · reviewers: {', '.join(reviewers)}"
          + (" · small project: one clean round with no P0/P1 converges" if (not a.thorough) and _project_size() == "S" else ""))


def _converged_on_record(data):
    """Did the last two rounds of the current cycle converge on the same text?"""
    rounds = data["rounds"][data.get("cycle_start", 0):]
    if rounds and data.get("quick"):
        last = rounds[-1]
        quiet = not any(f["round"] == last["n"] and f["severity"] in BLOCKING for f in data["findings"].values())
        if _round_clean(data, last) and quiet:
            return True
    if len(rounds) < 2:
        return False
    a, b = rounds[-2], rounds[-1]
    same_text = (a.get("doc_hash") == b.get("doc_hash") and a.get("hash_v", 1) == b.get("hash_v", 1))
    return (_round_clean(data, a) and _round_clean(data, b) and same_text
            and a.get("reviewer_set") == b.get("reviewer_set"))


def _maybe_new_cycle(target, data):
    """A review that converged on older text, or with other reviewers, starts a new cycle."""
    if _converged_on_record(data) and _status(data)["verdict"] != "converged":
        data["cycle_start"] = len(data["rounds"])
        print(f"goldfish '{target}': the documents or reviewers changed since this review converged, so a new review "
              f"cycle starts (earlier findings are kept, so settled ones stay settled)")


def cmd_round(a):
    data = _load(a.target)
    _maybe_new_cycle(a.target, data)
    if data["rounds"]:
        waiting = [k for k, v in data["rounds"][-1]["reviewers"].items() if v == "pending"]
        if waiting:
            sys.exit(f"ERROR: finish round {data['rounds'][-1]['n']} first: ingest or --not-run each of {', '.join(waiting)}")
    if data.get("isolation") not in ("full", "partial"):
        sys.exit("ERROR: record how isolated the reviewers are first: goldfish.py isolation <target> full|partial "
                 "(DISPATCH.md, 'When the goldfish agents are not installed')")
    pending = [f["id"] for f in data["findings"].values() if f["state"] in UNRESOLVED]
    if pending:
        sys.exit(f"ERROR: answer every finding before the next round. Unresolved: {', '.join(pending)}")
    proposed = [f["id"] for f in data["findings"].values() if f["state"] == FIX_PROPOSED]
    if proposed:
        sys.exit(f"ERROR: apply the proposed fixes first (goldfish.py applied ...): {', '.join(proposed)}")
    st = _status(data)
    if st["verdict"] == "converged":
        sys.exit("ERROR: already converged on the current text: no further round needed")
    if st["rounds_in_cycle"] >= data["max_rounds"]:
        sys.exit(f"ERROR: round cap ({data['max_rounds']}) reached: a person decides how to proceed "
                 f"(more rounds: goldfish.py init {a.target} ... --max-rounds <n>)")
    n = len(data["rounds"]) + 1
    data["rounds"].append({"n": n, "opened": _now(), "doc_hash": _doc_hash(data["docs"]), "hash_v": HASH_V,
                           "reviewer_set": sorted(data["reviewers"]),
                           "reviewers": {r: "pending" for r in data["reviewers"]}})
    _save(a.target, data)
    (_dir(a.target) / f"round-{n}").mkdir(parents=True, exist_ok=True)
    print(n)


# ---------------------------------------------------------------- findings in

def _validate(items, reviewer):
    if isinstance(items, dict):
        items = items.get("findings", [])
    if not isinstance(items, list):
        sys.exit("ERROR: reviewer output must be a list of findings or {\"findings\": [...]}")
    out = []
    for i, it in enumerate(items, 1):
        if not isinstance(it, dict):
            sys.exit(f"ERROR: finding #{i} is not an object")
        sev = str(it.get("severity", "")).upper()
        if sev not in SEVERITIES:
            sys.exit(f"ERROR: finding #{i} severity '{it.get('severity')}' must be P0, P1 or P2")
        for k in ("location", "issue"):
            if not str(it.get(k, "")).strip():
                sys.exit(f"ERROR: finding #{i} is missing '{k}'")
        out.append({"severity": sev, "location": str(it["location"]).strip(),
                    "issue": str(it["issue"]).strip(), "why": str(it.get("why", "")).strip(),
                    "suggestion": str(it.get("suggestion", "")).strip(),
                    "evidence": str(it.get("evidence", "")).strip()})
    return out


def cmd_ingest(a):
    data = _load(a.target)
    rnd = _current(data)
    if a.reviewer not in rnd["reviewers"]:
        sys.exit(f"ERROR: '{a.reviewer}' is not a reviewer in this review ({', '.join(rnd['reviewers'])})")
    if rnd["reviewers"][a.reviewer] != "pending":
        sys.exit(f"ERROR: '{a.reviewer}' already recorded for round {rnd['n']}")
    if a.not_run:
        rnd["reviewers"][a.reviewer] = "not-run"
        rnd.setdefault("notes", {})[a.reviewer] = a.reason or ""
        _save(a.target, data)
        print(f"round {rnd['n']}: {a.reviewer} NOT RUN: this round cannot be clean")
        return
    if not a.file:
        sys.exit("ERROR: --file or --not-run is required")
    raw = Path(a.file).read_text()
    try:
        payload = json.loads(raw)
    except ValueError as e:
        sys.exit(f"ERROR: {a.file} is not valid JSON ({e}): retry the reviewer once, then record --not-run")
    if isinstance(payload, dict):
        status = str(payload.get("status", "complete")).lower()
        if status != "complete" or "findings" not in payload:
            why = payload.get("incomplete_reason") or ("no 'findings' key" if "findings" not in payload else status)
            sys.exit(f"ERROR: {a.reviewer} did not complete its review ({why}). Nothing recorded: retry it once with a "
                     f"fresh subagent, then record --not-run if it fails again.")
    understanding = payload.get("understanding", "") if isinstance(payload, dict) else ""
    items = _validate(payload, a.reviewer)
    (_dir(a.target) / f"round-{rnd['n']}" / f"{a.reviewer}.json").write_text(raw)
    for i, it in enumerate(items, 1):
        fid = f"{a.reviewer}-{rnd['n']}-{i}"
        data["findings"][fid] = {"id": fid, "round": rnd["n"], "reviewer": a.reviewer, **it,
                                 "state": OPEN, "history": [{"state": OPEN, "at": _now()}]}
    rnd["reviewers"][a.reviewer] = "ran"
    if understanding:
        rnd.setdefault("understanding", {})[a.reviewer] = understanding
    _save(a.target, data)
    counts = {s: sum(1 for it in items if it["severity"] == s) for s in ("P0", "P1", "P2")}
    print(f"round {rnd['n']}: {a.reviewer} → {len(items)} finding(s) "
          f"(P0 {counts['P0']} · P1 {counts['P1']} · P2 {counts['P2']})")


def _set(f, state, **extra):
    f["state"] = state
    f["history"].append({"state": state, "at": _now(), **{k: v for k, v in extra.items() if v}})


def cmd_link(a):
    data = _load(a.target)
    f, old = _finding(data, a.id), _finding(data, a.reraise_of or a.churn_of)
    while old.get("duplicate_of"):
        old = _finding(data, old["duplicate_of"])     # a duplicate's fate is its primary's
    if old["round"] >= f["round"]:
        sys.exit("ERROR: can only link a finding to one from an EARLIER round")
    if f["state"] != OPEN:
        sys.exit(f"ERROR: {f['id']} is already {f['state']}: link a finding before answering it")
    if a.churn_of and old["state"] != FIXED:
        sys.exit(f"ERROR: churn means a fix caused this; {old['id']} is {old['state']}, not fixed")
    if a.reraise_of:
        f["reraise_of"] = old["id"]
        roles = {f["reviewer"]} | {data["findings"][d]["reviewer"] for d in f.get("duplicates", [])}
        how = (old.get("resolution") or {}).get("category")
        covers = (RANK[f["severity"]] >= RANK[old["severity"]] and how != "decline"
                  and not (roles & NO_CONTEST_ROLES and how in ("contest", "settled-earlier")))
        if old["state"] == SETTLED and not covers:
            print(f"{f['id']}: linked to settled {old['id']}, but that answer can't cover it "
                  f"({f['severity']} vs {old['severity']}{', declined' if (old.get('resolution') or {}).get('category') == 'decline' else ''}): stays open")
        elif old["state"] == SETTLED:
            # contested, declined, accepted or rejected before: never reopened
            f["resolution"] = {"category": "settled-earlier", "note": f"same as {old['id']}, settled in round {old['round']}",
                               "by": "goldfish.py", "at": _now()}
            _set(f, SETTLED, note=f"re-raise of settled {old['id']}")
            print(f"{f['id']}: same as settled {old['id']} → settled (not reopened)")
        elif old["state"] == FIXED:
            print(f"{f['id']}: re-raise of FIXED {old['id']}: the fix did not hold, stays open")
        else:
            print(f"{f['id']}: linked to {old['id']} ({old['state']})")
    else:
        f["churn_of"] = old["id"]
        print(f"{f['id']}: CHURN, caused by the fix for {old['id']}: the review will stop for a person")
    _save(a.target, data)


# ---------------------------------------------------------------- answers

def cmd_resolve(a):
    data = _load(a.target)
    f = _finding(data, a.id)
    if f["state"] not in (OPEN,):
        sys.exit(f"ERROR: {a.id} is already {f['state']}")
    if f.get("churn_of") and not a.human:
        sys.exit(f"ERROR: {a.id} is churn (caused by the fix for {f['churn_of']}): a person decides how to resolve it; "
                 "rerun with --human once they have answered")
    if a.category == "duplicate":
        prim = _finding(data, a.of or "")
        if prim["id"] == f["id"] or prim["round"] != f["round"]:
            sys.exit("ERROR: --of must name another finding from the same round")
        if prim["state"] != OPEN or prim.get("duplicate_of"):
            sys.exit(f"ERROR: {prim['id']} is not an open primary finding: mark duplicates before answering the primary")
        if f.get("duplicates"):
            sys.exit(f"ERROR: {f['id']} is already the primary for {', '.join(f['duplicates'])}: fold those into "
                     f"{prim['id']} first, or make {f['id']} the primary")
        if f.get("churn_of") and not prim.get("churn_of"):
            prim["churn_of"] = f["churn_of"]      # the churn travels with the primary: a person answers it
        if RANK[prim["severity"]] > RANK[f["severity"]]:
            sys.exit(f"ERROR: the primary must be at least as severe: {prim['id']} is {prim['severity']}, {f['id']} is "
                     f"{f['severity']}. Make {f['id']} the primary instead")
        f["duplicate_of"] = prim["id"]
        prim.setdefault("duplicates", []).append(f["id"])
        f["resolution"] = {"category": "duplicate", "note": f"same problem as {prim['id']}",
                           "by": "human" if a.human else "elephant", "at": _now()}
        _set(f, SETTLED, note=f"duplicate of {prim['id']}")
        _save(a.target, data)
        print(f"{f['id']} → settled (duplicate of {prim['id']}; its answer covers both)")
        return
    dup_roles = {data["findings"][d]["reviewer"] for d in f.get("duplicates", [])}
    if a.category == "decline" and f["severity"] != "P2":
        sys.exit(f"ERROR: only a P2 can be declined; {a.id} is {f['severity']}: fix, contest or escalate it")
    if a.category == "contest":
        if f["reviewer"] in NO_CONTEST_ROLES or dup_roles & NO_CONTEST_ROLES:
            sys.exit(f"ERROR: a comprehension gap cannot be contested. The reader did not understand, so the document must say more. Fix it.")
        if not (a.evidence or "").strip():
            sys.exit("ERROR: --evidence is required to contest. Cite a file:line the reviewer could read that proves the finding wrong. "
                     "If the proof is only in your head or the conversation, use --as escalate.")
    f["resolution"] = {"category": a.category, "note": a.note or "", "evidence": a.evidence or "",
                       "by": "human" if a.human else "elephant", "at": _now()}
    state = {"fix": FIX_PROPOSED, "contest": SETTLED, "escalate": ESCALATED, "decline": SETTLED}[a.category]
    _set(f, state, note=a.category)
    _save(a.target, data)
    print(f"{a.id} → {state} ({a.category})")


def cmd_applied(a):
    data = _load(a.target)
    for fid in a.ids:
        f = _finding(data, fid)
        if f["state"] != FIX_PROPOSED:
            sys.exit(f"ERROR: {fid} is {f['state']}, not fix-proposed")
        _set(f, FIXED)
    _save(a.target, data)
    print(f"{len(a.ids)} fix(es) recorded as applied")


def cmd_decide(a):
    data = _load(a.target)
    f = _finding(data, a.id)
    if f["state"] != ESCALATED:
        sys.exit(f"ERROR: {a.id} is {f['state']}, not escalated")
    if a.by == "agent-autonomous" and f["severity"] in BLOCKING and a.decision != "fix":
        sys.exit(f"ERROR: an escalated {f['severity']} needs a person to accept or reject it. With no one watching, "
                 "either write the missing fact into the document (--as fix) or stop for a person")
    f["decision"] = {"as": a.decision, "by": a.by, "note": a.note or "", "at": _now()}
    if a.decision == "fix":
        f["resolution"]["category"] = "fix"
        _set(f, FIX_PROPOSED, note=f"decided by {a.by}")
    else:
        _set(f, SETTLED, note=f"{a.decision} by {a.by}")
    _save(a.target, data)
    print(f"{a.id} → {f['state']} ({a.decision} by {a.by})")


# ---------------------------------------------------------------- the stopping rule

def _round_clean(data, rnd):
    if not rnd["reviewers"] or any(v != "ran" for v in rnd["reviewers"].values()):
        return False
    for f in data["findings"].values():
        if f["round"] == rnd["n"] and f["severity"] in BLOCKING and f["state"] in UNSETTLED:
            return False
    return True


def _status(data):
    rounds = data["rounds"]
    clean = [_round_clean(data, r) for r in rounds]
    start = data.get("cycle_start", 0)
    now_set = sorted(data["reviewers"])
    streak = 0
    for r, c in zip(reversed(rounds[start:]), reversed(clean[start:])):
        # a clean round only counts if it reviewed today's text with today's reviewers
        if not c or not _round_matches(r, data["docs"]) or r.get("reviewer_set", sorted(r["reviewers"])) != now_set:
            break
        streak += 1
    docs_changed = bool(rounds) and not _round_matches(rounds[-1], data["docs"])
    fs = list(data["findings"].values())
    by_state = {}
    for f in fs:
        by_state.setdefault(f["state"], []).append(f["id"])
    escalated = [f["id"] for f in fs if f["state"] == ESCALATED]
    churn = [f["id"] for f in fs if f.get("churn_of") and f["state"] == OPEN]   # unanswered churn only
    # still needing an answer or an edit (a FIXED finding only counts against its own round)
    open_blocking = [f["id"] for f in fs if f["severity"] in BLOCKING and f["state"] in {OPEN, FIX_PROPOSED, ESCALATED}]
    not_run = [f"round {r['n']}: {k}" for r in rounds for k, v in r["reviewers"].items() if v == "not-run"]
    in_progress = bool(rounds) and any(v == "pending" for v in rounds[-1]["reviewers"].values())
    last = rounds[-1] if rounds else None
    quiet = bool(last) and not any(f["round"] == last["n"] and f["severity"] in BLOCKING for f in fs)
    if streak >= 2 or (data.get("quick") and streak >= 1 and quiet):
        verdict = "converged"
    elif escalated:
        verdict = "needs_human"            # an escalation waits for a decision
    elif churn:
        verdict = "needs_human"            # fixes are causing new problems
    elif len(rounds) - start >= data["max_rounds"] and not in_progress:
        verdict = "needs_human"            # round cap
    else:
        verdict = "in_progress"
    reason = ""
    if verdict == "needs_human":
        reason = ("escalation(s) waiting: " + ", ".join(escalated)) if escalated else \
                 ("churn: " + ", ".join(churn)) if churn else \
                 f"round cap {data['max_rounds']} reached without two clean rounds"
    return {"target": data["target"], "rounds": len(rounds), "max_rounds": data["max_rounds"],
            "clean": clean, "clean_streak": streak, "verdict": verdict, "reason": reason,
            "open_blocking": open_blocking, "escalated": escalated, "churn": churn,
            "not_run": not_run, "by_state": by_state, "rounds_in_cycle": len(rounds) - start,
            "docs_changed_since_last_round": docs_changed,
            "isolation": data.get("isolation", "unrecorded")}


def cmd_status(a):
    st = _status(_load(a.target))
    if st["docs_changed_since_last_round"] and st["verdict"] != "converged":
        st["note"] = "the documents changed after the last round, so another round is needed"
    if a.json:
        print(json.dumps(st, indent=2))
    else:
        marks = " ".join(f"R{i}:{'clean' if c else 'not clean'}" for i, c in enumerate(st["clean"], 1)) or "no rounds yet"
        print(f"goldfish '{st['target']}' · {st['verdict']} · {marks}")
        if st["reason"]:
            print(f"  why: {st['reason']}")
        if st["open_blocking"]:
            print(f"  unsettled P0/P1: {', '.join(st['open_blocking'])}")
        if st["not_run"]:
            print(f"  reviewers not run: {', '.join(st['not_run'])}")
    sys.exit({"converged": 0, "in_progress": 2, "needs_human": 3}[st["verdict"]])


def cmd_isolation(a):
    data = _load(a.target)
    data["isolation"] = a.level
    if a.note:
        data["isolation_note"] = a.note
    _save(a.target, data)
    print(f"isolation → {a.level}")


# ---------------------------------------------------------------- report

def cmd_report(a):
    data = _load(a.target)
    st = _status(data)
    L = [f"# Goldfish review: {data['target']}", "",
         f"**Verdict:** {st['verdict']}" + (f": {st['reason']}" if st["reason"] else ""),
         f"**Documents:** {', '.join(data['docs'])}",
         f"**Reviewers:** {', '.join(data['reviewers'])} · **Isolation:** {st['isolation']}",
         f"**Rounds:** " + (", ".join(f"R{i} {'clean' if c else 'not clean'}" for i, c in enumerate(st['clean'], 1)) or "none"),
         ""]
    if st["escalated"]:
        L += ["## Waiting for your decision", ""]
        for fid in st["escalated"]:
            f = data["findings"][fid]
            L += [f"- **{fid}** ({f['severity']}) {f['location']}: {f['issue']}",
                  f"  - Author's position: {f['resolution'].get('note', '')}",
                  f"  - Record your answer: `{GF} decide {data['target']} {fid} --as fix|accept-risk|reject --by human --note \"...\"`"]
        L.append("")
    if st["churn"]:
        L += ["## Churn: a fix caused a new problem", ""]
        for fid in st["churn"]:
            f = data["findings"][fid]
            L += [f"- **{fid}** ({f['severity']}) {f['location']}: {f['issue']} (caused by the fix for {f['churn_of']})",
                  f"  - Record your answer: `{GF} resolve {data['target']} {fid} --as fix|contest|escalate --human --note \"...\"`"]
        L.append("")
    for r in data["rounds"]:
        L += [f"## Round {r['n']}", ""]
        L += [f"Reviewers: " + ", ".join(f"{k} ({v})" for k, v in r["reviewers"].items()), ""]
        for who, text in (r.get("understanding") or {}).items():
            L += [f"> **{who} understood the document as:** {text}", ""]
        rows = [f for f in data["findings"].values() if f["round"] == r["n"]]
        if not rows:
            L += ["No findings.", ""]
            continue
        L += ["| ID | Sev | Where | Finding | Answer | State |", "|---|---|---|---|---|---|"]
        for f in sorted(rows, key=lambda x: (x["severity"], x["id"])):
            res = f.get("resolution") or {}
            ans = res.get("category", "—")
            if res.get("evidence"):
                ans += f": {res['evidence']}"
            elif res.get("note"):
                ans += f": {res['note']}"
            if f.get("duplicate_of"):
                ans = f"duplicate of {f['duplicate_of']}"
            if f.get("decision"):
                ans += f" → {f['decision']['as']} by {f['decision']['by']}"
            cell = lambda s: s.replace("|", "\\|").replace("\n", " ")
            L.append(f"| {f['id']} | {f['severity']} | {cell(f['location'])} | {cell(f['issue'])} | {cell(ans)} | {f['state']} |")
        L.append("")
    out = _dir(a.target) / "resolution.md"
    out.write_text("\n".join(L) + "\n")
    print(f"wrote {out}")


def cmd_archive(a):
    """A document rewritten from scratch must not inherit the old review's settled findings."""
    d = _dir(a.target)
    if not (d / "ledger.json").exists():
        print(f"no goldfish review '{a.target}': nothing to archive")
        return
    stamp = datetime.datetime.now().strftime("%Y%m%d-%H%M%S")
    dest = ROOT / "archive" / f"{a.target}-{stamp}"
    dest.parent.mkdir(parents=True, exist_ok=True)
    d.rename(dest)
    print(f"archived {d} → {dest} (the next review of '{a.target}' starts with no history)")


# ---------------------------------------------------------------- cli

def main():
    ap = argparse.ArgumentParser(prog="goldfish.py")
    sub = ap.add_subparsers(dest="cmd", required=True)

    s = sub.add_parser("init"); s.add_argument("target")
    s.add_argument("--doc", action="append", required=True)
    s.add_argument("--reviewers", required=True)
    s.add_argument("--max-rounds", type=int, default=None, help=f"round cap (default {DEFAULT_MAX_ROUNDS}; kept on re-init unless given)")
    s.add_argument("--human", action="store_true", help="a person decided this (required to raise the round cap)")
    s.add_argument("--thorough", action="store_true", help="always require two clean rounds, even on a small project")
    s.set_defaults(fn=cmd_init)

    s = sub.add_parser("round"); s.add_argument("target"); s.set_defaults(fn=cmd_round)

    s = sub.add_parser("ingest"); s.add_argument("target")
    s.add_argument("--reviewer", required=True)
    s.add_argument("--file")
    s.add_argument("--not-run", action="store_true")
    s.add_argument("--reason")
    s.set_defaults(fn=cmd_ingest)

    s = sub.add_parser("link"); s.add_argument("target"); s.add_argument("id")
    g = s.add_mutually_exclusive_group(required=True)
    g.add_argument("--reraise-of"); g.add_argument("--churn-of")
    s.set_defaults(fn=cmd_link)

    s = sub.add_parser("resolve"); s.add_argument("target"); s.add_argument("id")
    s.add_argument("--as", dest="category", required=True, choices=sorted(CATEGORIES))
    s.add_argument("--note"); s.add_argument("--evidence")
    s.add_argument("--human", action="store_true", help="the answer came from a person (required for churn)")
    s.add_argument("--of", help="with --as duplicate: the primary finding")
    s.set_defaults(fn=cmd_resolve)

    s = sub.add_parser("applied"); s.add_argument("target"); s.add_argument("ids", nargs="+")
    s.set_defaults(fn=cmd_applied)

    s = sub.add_parser("decide"); s.add_argument("target"); s.add_argument("id")
    s.add_argument("--as", dest="decision", required=True, choices=["fix", "accept-risk", "reject"])
    s.add_argument("--by", required=True, choices=["human", "agent-autonomous"])
    s.add_argument("--note")
    s.set_defaults(fn=cmd_decide)

    s = sub.add_parser("status"); s.add_argument("target"); s.add_argument("--json", action="store_true")
    s.set_defaults(fn=cmd_status)

    s = sub.add_parser("isolation"); s.add_argument("target")
    s.add_argument("level", choices=["full", "partial"]); s.add_argument("--note")
    s.set_defaults(fn=cmd_isolation)

    s = sub.add_parser("report"); s.add_argument("target"); s.set_defaults(fn=cmd_report)

    s = sub.add_parser("archive"); s.add_argument("target"); s.set_defaults(fn=cmd_archive)

    a = ap.parse_args()
    a.fn(a)


if __name__ == "__main__":
    main()
