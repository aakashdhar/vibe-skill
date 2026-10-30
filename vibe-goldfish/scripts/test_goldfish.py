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
    p.gf("init", "spec", "--doc", "vibe/SPEC.md", "--reviewers", "rubric", "--max-rounds", "7")
    p.gf("init", "spec", "--doc", "vibe/SPEC.md", "--reviewers", "rubric")
    expect(p.gf("round", "spec")[0] == 0, "a raised cap survives a plain re-init")


def unfinished_round_blocks(p):
    start(p)
    p.gf("round", "spec")
    p.gf("ingest", "spec", "--reviewer", "rubric", "--file", p.findings("e.json", []))
    expect(p.gf("round", "spec")[0] != 0, "a round with a pending reviewer must be finished first")


def design_gate(p):
    (p.root / "vibe/design").mkdir()
    p.write("vibe/design/critique.md", "# c\n## MUST-FIX (1)\n- a\n")
    expect(p.run(VS, "gate", "set", "design", "--status", "approved", "--by", "agent-autonomous")[0] != 0,
           "an agent can't approve the design with MUST-FIX open")
    expect(p.run(VS, "gate", "set", "design", "--status", "approved", "--by", "agent-autonomous", "--backfill")[0] == 0,
           "backfill works for the design gate")


for fn in (converges_on_two_clean_rounds, isolation_must_be_recorded, incomplete_reviewer_is_not_clean,
           edits_reopen_a_converged_review, p2_edit_needs_another_round, rules_on_answers,
           relinking_and_churn, cap_can_be_raised, unfinished_round_blocks, design_gate):
    before = len(failures)
    scenario(fn)
    print(f"{'ok  ' if len(failures) == before else 'FAIL'} {fn.__name__}")

for f in failures:
    print(f"  ✗ {f}")
print("goldfish self-test:", "ALL PASS" if not failures else f"{len(failures)} failure(s)")
sys.exit(1 if failures else 0)
