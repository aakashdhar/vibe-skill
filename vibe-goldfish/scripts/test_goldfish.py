#!/usr/bin/env python3
"""
Self-test for goldfish.py and the goldfish checks in vibe_state.py. Stdlib only.

  python3 vibe-goldfish/scripts/test_goldfish.py      # exit 0 = all scenarios pass

Each scenario runs the real scripts in a throwaway project folder.
"""
import json
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
GF = HERE / "goldfish.py"
VS = HERE.parents[1] / "vibe-mode" / "scripts" / "vibe_state.py"
failures = []


class Project:
    def __init__(self):
        self.root = Path(tempfile.mkdtemp(prefix="gf-test-"))
        (self.root / "vibe").mkdir()
        self.write("vibe/SPEC.md", "spec v1\n")

    def write(self, rel, text):
        (self.root / rel).write_text(text)

    def run(self, script, *args):
        r = subprocess.run([sys.executable, str(script), *args], cwd=self.root, capture_output=True, text=True)
        return r.returncode, r.stdout + r.stderr

    def gf(self, *args):
        return self.run(GF, *args)

    def findings(self, name, items, status="complete"):
        self.write(name, json.dumps({"status": status, "findings": items}))
        return name

    def round_with(self, target, results):
        """Open a round and ingest {reviewer: findings-list}. Returns the round number."""
        code, out = self.gf("round", target)
        expect(code == 0, f"round opens: {out}")
        n = out.strip().splitlines()[-1]
        for reviewer, items in results.items():
            code, out = self.gf("ingest", target, "--reviewer", reviewer, "--file", self.findings(f"{reviewer}.json", items))
            expect(code == 0, f"ingest {reviewer}: {out}")
        return n

    def close(self):
        shutil.rmtree(self.root, ignore_errors=True)


def expect(cond, what):
    if not cond:
        failures.append(what)


def start(p, reviewers="rubric,comprehension"):
    p.gf("init", "spec", "--doc", "vibe/SPEC.md", "--reviewers", reviewers)
    p.gf("isolation", "spec", "full")


def scenario(fn):
    p = Project()
    try:
        fn(p)
    finally:
        p.close()


def converges_on_two_clean_rounds(p):
    start(p)
    p.round_with("spec", {"rubric": [], "comprehension": []})
    expect(p.gf("status", "spec")[0] == 2, "one clean round is not converged")
    p.round_with("spec", {"rubric": [], "comprehension": []})
    expect(p.gf("status", "spec")[0] == 0, "two clean rounds converge")


def isolation_must_be_recorded(p):
    p.gf("init", "spec", "--doc", "vibe/SPEC.md", "--reviewers", "rubric")
    expect(p.gf("round", "spec")[0] != 0, "round refuses before isolation is recorded")


def incomplete_reviewer_is_not_clean(p):
    start(p)
    p.gf("round", "spec")
    p.findings("inc.json", [], status="incomplete")
    expect(p.gf("ingest", "spec", "--reviewer", "rubric", "--file", "inc.json")[0] != 0, "incomplete review is refused")
    expect(p.gf("ingest", "spec", "--reviewer", "rubric", "--not-run", "--reason", "x")[0] == 0, "then --not-run works")
    p.gf("ingest", "spec", "--reviewer", "comprehension", "--file", p.findings("e.json", []))
    st = json.loads(p.gf("status", "spec", "--json")[1])
    expect(st["clean"] == [False], "a round with a reviewer not run is not clean")


def edits_reopen_a_converged_review(p):
    start(p)
    p.round_with("spec", {"rubric": [], "comprehension": []})
    p.round_with("spec", {"rubric": [], "comprehension": []})
    p.write("vibe/SPEC.md", "spec v2\n")
    expect(p.gf("status", "spec")[0] == 2, "an edited document is no longer converged")
    code, _ = p.run(VS, "gate", "set", "spec", "--status", "approved", "--by", "agent-autonomous", "--report", "vibe/goldfish/spec")
    expect(code != 0, "the spec gate refuses a review of older text")
    p.gf("init", "spec", "--doc", "vibe/SPEC.md", "--reviewers", "rubric,comprehension")
    st = json.loads(p.gf("status", "spec", "--json")[1])
    expect(st["rounds_in_cycle"] == 0, "re-init after an edit starts a new cycle")
    p.round_with("spec", {"rubric": [], "comprehension": []})
    p.round_with("spec", {"rubric": [], "comprehension": []})
    code, _ = p.run(VS, "gate", "set", "spec", "--status", "approved", "--by", "agent-autonomous", "--report", "vibe/goldfish/spec")
    expect(code == 0, "the spec gate accepts a review that converged on the current text")


def p2_edit_needs_another_round(p):
    start(p)
    p.round_with("spec", {"rubric": [], "comprehension": []})
    p.write("vibe/SPEC.md", "spec v1 with a small P2 tweak\n")
    p.round_with("spec", {"rubric": [], "comprehension": []})
    expect(p.gf("status", "spec")[0] == 2, "two clean rounds on different text don't converge")


def rules_on_answers(p):
    start(p)
    p.round_with("spec", {"rubric": [{"severity": "P0", "location": "a", "issue": "x"}],
                          "comprehension": [{"severity": "P1", "location": "b", "issue": "y"}]})
    expect(p.gf("resolve", "spec", "rubric-1-1", "--as", "decline")[0] != 0, "a P0 can't be declined")
    expect(p.gf("resolve", "spec", "comprehension-1-1", "--as", "contest", "--evidence", "f:1")[0] != 0,
           "a comprehension finding can't be contested")
    expect(p.gf("resolve", "spec", "rubric-1-1", "--as", "contest")[0] != 0, "a contest needs evidence")
    p.gf("resolve", "spec", "rubric-1-1", "--as", "escalate", "--note", "client said so")
    expect(p.gf("decide", "spec", "rubric-1-1", "--as", "accept-risk", "--by", "agent-autonomous")[0] != 0,
           "an agent can't accept an escalated P0")
    expect(p.gf("status", "spec")[0] == 3, "an escalation waits for a person")
    expect(p.gf("round", "spec")[0] != 0, "no new round while findings are unanswered")


def relinking_and_churn(p):
    start(p, "rubric")
    p.round_with("spec", {"rubric": [{"severity": "P2", "location": "a", "issue": "nit"},
                                     {"severity": "P1", "location": "b", "issue": "major"}]})
    p.gf("resolve", "spec", "rubric-1-1", "--as", "decline", "--note", "meh")
    p.gf("resolve", "spec", "rubric-1-2", "--as", "fix")
    p.gf("applied", "spec", "rubric-1-2")
    p.write("vibe/SPEC.md", "spec v2\n")
    p.round_with("spec", {"rubric": [{"severity": "P0", "location": "a", "issue": "worse"},
                                     {"severity": "P1", "location": "b", "issue": "from the fix"}]})
    p.gf("link", "spec", "rubric-2-1", "--reraise-of", "rubric-1-1")
    led = json.loads((p.root / "vibe/goldfish/spec/ledger.json").read_text())
    expect(led["findings"]["rubric-2-1"]["state"] == "open", "a declined P2 never settles a re-raised P0")
    expect(p.gf("link", "spec", "rubric-2-2", "--churn-of", "rubric-1-1")[0] != 0, "churn needs a fixed finding")
    p.gf("link", "spec", "rubric-2-2", "--churn-of", "rubric-1-2")
    expect(p.gf("resolve", "spec", "rubric-2-2", "--as", "fix")[0] != 0, "churn needs a person's answer")
    p.gf("resolve", "spec", "rubric-2-2", "--as", "fix", "--human")
    p.gf("resolve", "spec", "rubric-2-1", "--as", "fix")
    p.gf("applied", "spec", "rubric-2-1", "rubric-2-2")
    expect(p.gf("status", "spec")[0] == 2, "answered churn no longer blocks the review")


def cap_can_be_raised(p):
    start(p, "rubric")
    for i in range(5):
        p.round_with("spec", {"rubric": [{"severity": "P1", "location": f"l{i}", "issue": "x"}]})
        p.gf("resolve", "spec", f"rubric-{i + 1}-1", "--as", "fix")
        p.gf("applied", "spec", f"rubric-{i + 1}-1")
        p.write("vibe/SPEC.md", f"spec v{i + 2}\n")
    expect(p.gf("round", "spec")[0] != 0, "the round cap holds")
    expect(p.gf("init", "spec", "--doc", "vibe/SPEC.md", "--reviewers", "rubric", "--max-rounds", "7")[0] != 0,
           "an agent can't raise the round cap")
    p.gf("init", "spec", "--doc", "vibe/SPEC.md", "--reviewers", "rubric", "--max-rounds", "7", "--human")
    p.gf("init", "spec", "--doc", "vibe/SPEC.md", "--reviewers", "rubric")
    expect(p.gf("round", "spec")[0] == 0, "a raised cap survives a plain re-init")


def unfinished_round_blocks(p):
    start(p)
    p.gf("round", "spec")
    p.gf("ingest", "spec", "--reviewer", "rubric", "--file", p.findings("e.json", []))
    expect(p.gf("round", "spec")[0] != 0, "a round with a pending reviewer must be finished first")


def duplicates(p):
    start(p)
    p.round_with("spec", {"rubric": [{"severity": "P0", "location": "a", "issue": "sync contradicts storage"}],
                          "comprehension": [{"severity": "P1", "location": "a", "issue": "sync unclear"}]})
    expect(p.gf("resolve", "spec", "rubric-1-1", "--as", "duplicate", "--of", "comprehension-1-1")[0] != 0,
           "a less severe finding can't be the primary")
    expect(p.gf("resolve", "spec", "comprehension-1-1", "--as", "duplicate", "--of", "rubric-1-1")[0] == 0,
           "a duplicate folds into the primary")
    expect(p.gf("resolve", "spec", "rubric-1-1", "--as", "contest", "--evidence", "f:1")[0] != 0,
           "a primary with a comprehension duplicate can't be contested")
    p.gf("resolve", "spec", "rubric-1-1", "--as", "fix")
    p.gf("applied", "spec", "rubric-1-1")
    st = json.loads(p.gf("status", "spec", "--json")[1])
    expect(st["clean"] == [False], "the round stays not clean while its primary was fixed")


def tool_lines_are_not_content(p):
    p.write("vibe/TASKS.md", "# Tasks\n## Spec gate\n⬜ spec: — pending\n")
    p.gf("init", "spec", "--doc", "vibe/TASKS.md", "--reviewers", "rubric")
    p.gf("isolation", "spec", "full")
    p.round_with("spec", {"rubric": []})
    p.round_with("spec", {"rubric": []})
    p.write("vibe/TASKS.md", "# Tasks\n## Spec gate\n✅ spec: — approved 2026-10-30\n")
    expect(p.gf("status", "spec")[0] == 0, "flipping a TASKS.md gate line keeps the review converged")
    p.write("vibe/TASKS.md", "# Tasks changed\n## Spec gate\n✅ spec: — approved 2026-10-30\n")
    expect(p.gf("status", "spec")[0] == 2, "a content edit still re-opens it")


PLAN_BEFORE = """### Phase 2 — Core features

#### CSV export — users download their entries
**Status:** ⬜ not started
**Build order:** 1
**Depends on:** Phase 1 complete
**Spec:** `vibe/features/[date-slug]/` ← created when `feature: CSV export` runs

---

#### Sharing — users share a list
**Status:** ⬜ not started
**Depends on:** CSV export
"""


def feature_bookkeeping_is_not_content(p):
    p.write("vibe/PLAN.md", PLAN_BEFORE)
    p.write("CLAUDE.md", "# App\n## Execution mode\nVIBE_MODE=manual   # x\n")
    p.gf("init", "spec", "--doc", "vibe/SPEC.md", "--doc", "vibe/PLAN.md", "--doc", "CLAUDE.md", "--reviewers", "rubric")
    p.gf("isolation", "spec", "full")
    p.round_with("spec", {"rubric": []})
    p.round_with("spec", {"rubric": []})
    started = (PLAN_BEFORE.replace("**Status:** ⬜ not started\n**Build order:** 1", "**Status:** 🔄 in progress\n**Build order:** 1", 1)
               .replace("`vibe/features/[date-slug]/` ← created when `feature: CSV export` runs", "`vibe/features/2026-10-30-csv-export/`"))
    p.write("vibe/PLAN.md", started)
    p.write("CLAUDE.md", "# App\n## Execution mode\nVIBE_MODE=autonomous   # x\n\n---\n\n### Active Feature: CSV export\n- Files in scope: src/csv.ts\n")
    expect(p.gf("status", "spec")[0] == 0, "starting a feature (real PLAN/CLAUDE formats) keeps the spec review converged")
    p.write("vibe/PLAN.md", started.replace("**Depends on:** CSV export", "**Depends on:** nothing"))
    expect(p.gf("status", "spec")[0] == 2, "changing a dependency in the map re-opens the review")


def bookkeeping_rules_are_per_file(p):
    p.write("vibe/SPEC.md", "spec\n**Status:** ⬜ draft\n")
    start(p, "rubric")
    p.round_with("spec", {"rubric": []})
    p.round_with("spec", {"rubric": []})
    p.write("vibe/SPEC.md", "spec\n**Status:** ✅ final\n")
    expect(p.gf("status", "spec")[0] == 2, "a Status line in SPEC.md is content (only PLAN.md's is bookkeeping)")


def ledgers_from_v270_still_match(p):
    start(p, "rubric")
    p.round_with("spec", {"rubric": []})
    p.round_with("spec", {"rubric": []})
    led_path = p.root / "vibe/goldfish/spec/ledger.json"
    led = json.loads(led_path.read_text())
    import hashlib
    h = hashlib.sha256(b"vibe/SPEC.md\0" + (p.root / "vibe/SPEC.md").read_bytes() + b"\0").hexdigest()[:16]
    for r in led["rounds"]:
        r.pop("hash_v", None)
        r["doc_hash"] = h            # what v2.7.0 stored
    led_path.write_text(json.dumps(led))
    expect(p.gf("status", "spec")[0] == 0, "a review converged under v2.7.0 is still converged after the upgrade")


def duplicate_loopholes(p):
    start(p, "rubric,comprehension,zoom-out")
    p.round_with("spec", {"rubric": [{"severity": "P1", "location": "a", "issue": "x"}],
                          "comprehension": [{"severity": "P1", "location": "a", "issue": "x unclear"}],
                          "zoom-out": [{"severity": "P1", "location": "a", "issue": "x again"}]})
    p.gf("resolve", "spec", "zoom-out-1-1", "--as", "duplicate", "--of", "comprehension-1-1")
    expect(p.gf("resolve", "spec", "comprehension-1-1", "--as", "duplicate", "--of", "rubric-1-1")[0] != 0,
           "a primary with duplicates can't be folded into another primary (no chains)")
    p.gf("resolve", "spec", "comprehension-1-1", "--as", "fix")
    p.gf("resolve", "spec", "rubric-1-1", "--as", "contest", "--evidence", "SPEC.md:3")
    p.gf("applied", "spec", "comprehension-1-1")
    p.write("vibe/SPEC.md", "spec v2\n")
    p.round_with("spec", {"rubric": [{"severity": "P1", "location": "b", "issue": "y"}],
                          "comprehension": [{"severity": "P1", "location": "b", "issue": "y unclear"}],
                          "zoom-out": []})
    p.gf("resolve", "spec", "comprehension-2-1", "--as", "duplicate", "--of", "rubric-2-1")
    p.gf("link", "spec", "rubric-2-1", "--reraise-of", "rubric-1-1")
    led = json.loads((p.root / "vibe/goldfish/spec/ledger.json").read_text())
    expect(led["findings"]["rubric-2-1"]["state"] == "open",
           "an old contest never settles a re-raise that carries a comprehension duplicate")


def churn_travels_with_its_primary(p):
    start(p, "rubric,zoom-out")
    p.round_with("spec", {"rubric": [{"severity": "P1", "location": "a", "issue": "x"}], "zoom-out": []})
    p.gf("resolve", "spec", "rubric-1-1", "--as", "fix")
    p.gf("applied", "spec", "rubric-1-1")
    p.write("vibe/SPEC.md", "spec v2\n")
    p.round_with("spec", {"rubric": [{"severity": "P1", "location": "a", "issue": "fix broke it"}],
                          "zoom-out": [{"severity": "P1", "location": "a", "issue": "fix broke it too"}]})
    p.gf("link", "spec", "rubric-2-1", "--churn-of", "rubric-1-1")
    expect(p.gf("resolve", "spec", "rubric-2-1", "--as", "duplicate", "--of", "zoom-out-2-1")[0] != 0,
           "folding a churn finding is an answer, so it needs a person")
    p.gf("resolve", "spec", "rubric-2-1", "--as", "duplicate", "--of", "zoom-out-2-1", "--human")
    expect(p.gf("resolve", "spec", "zoom-out-2-1", "--as", "fix")[0] != 0,
           "the churn travels to the primary: a person answers that too")


def human_approval_of_unreviewed_text_is_marked(p):
    start(p, "rubric")
    p.round_with("spec", {"rubric": []})
    p.round_with("spec", {"rubric": []})
    p.write("vibe/SPEC.md", "spec v2\n")
    p.run(VS, "gate", "set", "spec", "--status", "approved", "--by", "human", "--report", "vibe/goldfish/spec")
    gates = json.loads((p.root / "vibe/.gates.json").read_text())
    expect(gates["spec"].get("reviewed") is False, "a person's approval of edited text is recorded as reviewed: false")


def small_project_converges_in_one_quiet_round(p):
    p.write("BRIEF.md", "# BRIEF\n> Created: 2026-10-30 via brainstorm: | Path: Personal | Complexity: S | Readiness: 100%\n")
    start(p, "rubric")
    p.round_with("spec", {"rubric": [{"severity": "P2", "location": "a", "issue": "nit"}]})
    p.gf("resolve", "spec", "rubric-1-1", "--as", "decline", "--note", "note only")
    expect(p.gf("status", "spec")[0] == 0, "S project: one clean round with no P0/P1 converges")
    p.write("vibe/SPEC.md", "spec v2\n")
    p.gf("init", "spec", "--doc", "vibe/SPEC.md", "--reviewers", "rubric")
    st = json.loads(p.gf("status", "spec", "--json")[1])
    expect(st["rounds_in_cycle"] == 0, "an edit after a one-round convergence starts a new cycle")
    p.round_with("spec", {"rubric": [{"severity": "P1", "location": "b", "issue": "gap"}]})
    p.gf("resolve", "spec", "rubric-2-1", "--as", "fix")
    p.gf("applied", "spec", "rubric-2-1")
    p.write("vibe/SPEC.md", "spec v3\n")
    p.round_with("spec", {"rubric": []})
    expect(p.gf("status", "spec")[0] == 0, "S project: a quiet round after a fixed round converges")


def bigger_or_thorough_needs_two_rounds(p):
    p.write("BRIEF.md", "# BRIEF\n## Complexity estimate\n**Size:** M\n")
    start(p, "rubric")
    p.round_with("spec", {"rubric": []})
    expect(p.gf("status", "spec")[0] == 2, "M project: one clean round is not enough")
    p.write("BRIEF.md", "# BRIEF\n**Size:** S\n")
    p.gf("init", "spec", "--doc", "vibe/SPEC.md", "--reviewers", "rubric", "--thorough")
    expect(p.gf("status", "spec")[0] == 2, "--thorough keeps two rounds on a small project")


def archive_resets_history(p):
    start(p, "rubric")
    p.round_with("spec", {"rubric": []})
    p.gf("archive", "spec")
    expect(not (p.root / "vibe/goldfish/spec").exists(), "archive moves the review aside")
    expect(any((p.root / "vibe/goldfish/archive").iterdir()), "the old review is kept under archive/")


def design_gate(p):
    (p.root / "vibe/design").mkdir()
    p.write("vibe/design/critique.md", "# c\n## MUST-FIX (1)\n- a\n")
    expect(p.run(VS, "gate", "set", "design", "--status", "approved", "--by", "agent-autonomous")[0] != 0,
           "an agent can't approve the design with MUST-FIX open")
    expect(p.run(VS, "gate", "set", "design", "--status", "approved", "--by", "agent-autonomous", "--backfill")[0] == 0,
           "backfill works for the design gate")


for fn in (converges_on_two_clean_rounds, isolation_must_be_recorded, incomplete_reviewer_is_not_clean,
           edits_reopen_a_converged_review, p2_edit_needs_another_round, rules_on_answers,
           relinking_and_churn, cap_can_be_raised, unfinished_round_blocks, duplicates, tool_lines_are_not_content, feature_bookkeeping_is_not_content,
           bookkeeping_rules_are_per_file, ledgers_from_v270_still_match, duplicate_loopholes,
           churn_travels_with_its_primary, human_approval_of_unreviewed_text_is_marked,
           small_project_converges_in_one_quiet_round, bigger_or_thorough_needs_two_rounds,
           archive_resets_history, design_gate):
    before = len(failures)
    scenario(fn)
    print(f"{'ok  ' if len(failures) == before else 'FAIL'} {fn.__name__}")

for f in failures:
    print(f"  ✗ {f}")
print("goldfish self-test:", "ALL PASS" if not failures else f"{len(failures)} failure(s)")
sys.exit(1 if failures else 0)
