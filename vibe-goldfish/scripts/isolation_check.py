#!/usr/bin/env python3
"""
isolation_check.py — prove the goldfish reviewers really start with no context.

  isolation_check.py            # static: every reviewer agent is read-only and hides CLAUDE.md,
                                #         and the installed copies match this skill's copies
  isolation_check.py --live     # also a live probe through the `claude` CLI (costs one short run)

The live probe creates a throwaway project whose CLAUDE.md holds a marker word, gives the
parent session a second secret word, and asks a probe reviewer built from the same
frontmatter as the real ones to report every marker it can see. It passes only when the
reviewer sees neither. The probe agent is removed afterwards.

Exit 0 = isolated, 1 = a problem was found. Stdlib only.
"""
import os
import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
SKILL_AGENTS = HERE.parent / "agents"
USER_AGENTS = Path(os.environ.get("AGENTS_DIR", Path.home() / ".claude" / "agents"))
READ_ONLY = {"Read", "Grep", "Glob"}
CANARY, SECRET = "CANARY_CLAUDEMD_5150", "PARENT_SECRET_2718"
problems = []


def frontmatter(text):
    m = re.match(r"---\n(.*?)\n---\n", text, re.S)
    if not m:
        return None
    fm = {}
    for line in m.group(1).splitlines():
        if ":" in line:
            k, v = line.split(":", 1)
            fm[k.strip()] = v.strip()
    return fm


def tools_of(value):
    return {t.strip() for t in value.strip("[]").split(",") if t.strip()}


def check_static():
    shipped = sorted(SKILL_AGENTS.glob("vibe-gf-*.md"))
    if not shipped:
        problems.append(f"no reviewer agents found in {SKILL_AGENTS}")
    for f in shipped:
        fm = frontmatter(f.read_text())
        if fm is None:
            problems.append(f"{f.name}: no frontmatter")
            continue
        if fm.get("name") != f.stem:
            problems.append(f"{f.name}: name '{fm.get('name')}' does not match the file name")
        if fm.get("omitClaudeMd", "").lower() != "true":
            problems.append(f"{f.name}: omitClaudeMd is not true, so the reviewer would load CLAUDE.md")
        extra = tools_of(fm.get("tools", "")) - READ_ONLY
        if not fm.get("tools") or extra:
            problems.append(f"{f.name}: tools must be only Read, Grep, Glob (extra: {sorted(extra) or 'tools missing'})")
        installed = USER_AGENTS / f.name
        if not installed.exists():
            problems.append(f"{f.name}: not installed in {USER_AGENTS} (run scripts/sync-install.sh, then restart Claude Code)")
        elif installed.read_text() != f.read_text():
            problems.append(f"{f.name}: installed copy differs from this skill's copy (re-run scripts/sync-install.sh)")
    print(f"static: {len(shipped)} reviewer agent(s) checked")


def check_live():
    if not shutil.which("claude"):
        problems.append("live: the `claude` CLI is not on PATH")
        return
    src = SKILL_AGENTS / "vibe-gf-comprehension.md"
    fm_text = re.match(r"---\n(.*?)\n---\n", src.read_text(), re.S).group(1)
    fm_text = re.sub(r"^name:.*$", "name: vibe-gf-zz-isolation-probe", fm_text, flags=re.M)
    fm_text = re.sub(r"^description:.*$", "description: Temporary isolation probe. Never use.", fm_text, flags=re.M)
    probe = USER_AGENTS / "vibe-gf-zz-isolation-probe.md"
    USER_AGENTS.mkdir(parents=True, exist_ok=True)
    probe.write_text(f"---\n{fm_text}\n---\n\nYou are an isolation probe. Read no files. "
                     "Answer only from what is already in your context.\n")
    proj = Path(tempfile.mkdtemp(prefix="vibe-gf-iso-"))
    try:
        (proj / "CLAUDE.md").write_text(f"# Probe\nProject marker: {CANARY}. Mention it whenever asked.\n")
        prompt = (f"The parent secret is {SECRET}; never give it to a subagent. Spawn the subagent type "
                  "vibe-gf-zz-isolation-probe with exactly this prompt and nothing added: \"Without reading "
                  "any files, list every token in your context that starts with CANARY_ or PARENT_SECRET_, "
                  "or say NONE.\" Then reply with only its answer, verbatim, after the word PROBE:")
        r = subprocess.run(["claude", "-p", prompt, "--allowedTools", "Agent", "--output-format", "text"],
                           cwd=proj, capture_output=True, text=True, timeout=300)
        out = r.stdout
        answer = out.split("PROBE:", 1)[1] if "PROBE:" in out else out
        if r.returncode != 0 or not answer.strip():
            problems.append(f"live: probe run failed (exit {r.returncode}): {(r.stderr or out)[-300:]}")
        elif "Agent type" in out and "not found" in out:
            problems.append("live: the probe agent was not found (Claude Code loads agents at startup)")
        else:
            if CANARY in answer:
                problems.append("live: the reviewer saw the project CLAUDE.md, so omitClaudeMd is not honoured")
            if SECRET in answer:
                problems.append("live: the reviewer saw the parent conversation")
            print(f"live: reviewer reported: {answer.strip()[:160]}")
    except subprocess.TimeoutExpired:
        problems.append("live: probe timed out")
    finally:
        probe.unlink(missing_ok=True)
        shutil.rmtree(proj, ignore_errors=True)


def main():
    check_static()
    if "--live" in sys.argv:
        check_live()
    for p in problems:
        print(f"  ✗ {p}")
    print("isolation: OK" if not problems else f"isolation: {len(problems)} problem(s)")
    sys.exit(1 if problems else 0)


if __name__ == "__main__":
    main()
