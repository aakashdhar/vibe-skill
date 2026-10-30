#!/usr/bin/env python3
"""
vibe-skill self-linter — catches the classes of defect the blind audits kept finding,
so they can't silently return. Zero dependencies (stdlib only).

Checks, per vibe-*/ skill:
  1. Dangling `references/NAME.md` — a SKILL.md cites a same-skill reference that
     doesn't exist (cross-skill `other-skill/references/x.md` paths are ignored).
  2. Duplicate step headings — `## Step N` / `## Stage N` appearing twice in one file.
  3. Stale model IDs — claude-*-4-6 / sonnet-4-6 etc. outside an explicit
     "older/legacy/pinned" line.
  4. Python under scripts/ must byte-compile.
  6. Settings read by grepping CLAUDE.md (`grep "VIBE_MODE" CLAUDE.md`) — must use
     vibe_state.py mode, which honours env overrides.
  7. SKILL.md description longer than 1024 characters (warning).
Goldfish (vibe-goldfish):
  8. every reviewer agent is read-only (Read/Grep/Glob) with omitClaudeMd: true, and its
     name matches its file; every reviewer named in PRESETS.md has an agent file.
Repo-level:
  5. README skill count matches the number of vibe-*/ directories.

Exit code: 0 = clean, 1 = issues found. Run from the repo root:  python3 scripts/lint.py
"""
import re, sys, py_compile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
issues = []
def add(sev, where, msg): issues.append((sev, where, msg))

skill_dirs = sorted(p for p in ROOT.glob("vibe-*") if p.is_dir())

STALE = re.compile(r"claude-(?:opus|sonnet|haiku)-4-6|claude-sonnet-4-6|claude-3-", re.I)
STALE_OK = re.compile(r"older|legacy|pinned|deprecated|do not use|only for", re.I)

for sd in skill_dirs:
    for md in sd.rglob("*.md"):
        text = md.read_text(errors="ignore")
        rel = md.relative_to(ROOT)

        # 1. dangling same-skill references
        for m in re.finditer(r"`?references/([A-Za-z0-9_/]+\.md)`?", text):
            ref = m.group(1)
            # ignore cross-skill qualified paths like vibe-x/references/y.md
            line_start = text.rfind("\n", 0, m.start()) + 1
            prefix = text[line_start:m.start()]
            if prefix.rstrip().endswith("/") or "vibe-" in prefix[-20:]:
                continue
            if not (sd / "references" / ref).exists():
                # tolerate a cross-skill mention elsewhere in the repo
                if not list(ROOT.glob(f"vibe-*/references/{ref}")):
                    add("ERROR", rel, f"dangling reference: references/{ref} not found")

        # 2. duplicate step/stage headings — match the FULL label token so
        # intentional sub-steps (10B, 0.5, 2P/2C, 1A/1B/1C) are distinct, and only
        # a genuinely repeated label (e.g. two "Step 13") is flagged. Strip fenced
        # code blocks first — example docs inside ``` fences carry their own headings.
        no_fences = re.sub(r"```.*?```", "", text, flags=re.S)
        heads = re.findall(r"^##\s+(Step|Stage)\s+([0-9]+(?:\.[0-9]+)?[A-Za-z]?)\b", no_fences, re.M)
        seen = {}
        for kind, tok in heads:
            seen[(kind, tok)] = seen.get((kind, tok), 0) + 1
        for (kind, tok), c in seen.items():
            if c > 1:
                add("ERROR", rel, f"duplicate heading: '## {kind} {tok}' appears {c}×")

        # 3. stale model ids
        for i, line in enumerate(text.splitlines(), 1):
            if STALE.search(line) and not STALE_OK.search(line):
                add("WARN", f"{rel}:{i}", f"possible stale model id: {line.strip()[:80]}")

    # 6. CLAUDE.md mode grep
    for md in sd.rglob("*.md"):
        for i, line in enumerate(md.read_text(errors="ignore").splitlines(), 1):
            if re.search(r"grep\s+[\"']?VIBE_MODE", line) and "CLAUDE.md" in line:
                add("ERROR", f"{md.relative_to(ROOT)}:{i}", "reads VIBE_MODE by grepping CLAUDE.md — use vibe_state.py mode")

    # 7. description length (folded YAML: the indented lines after `description:`)
    sk = sd / "SKILL.md"
    if sk.exists():
        fm = re.match(r"---\n(.*?)\n---", sk.read_text(), re.S)
        out, on = [], False
        for l in (fm.group(1).splitlines() if fm else []):
            if l.startswith("description:"):
                on, rest = True, l.split(":", 1)[1].strip()
                if rest not in (">", ">-", "|", "|-", ""):
                    out.append(rest)
            elif on and l[:1] in (" ", "\t"):
                out.append(l.strip())
            elif on:
                break
        desc = " ".join(out)
        if len(desc) > 1024:
            add("WARN", sk.relative_to(ROOT), f"description is {len(desc)} chars (limit 1024)")

    # 4. scripts compile
    for py in sd.rglob("*.py"):
        try:
            py_compile.compile(str(py), doraise=True)
        except py_compile.PyCompileError as e:
            add("ERROR", py.relative_to(ROOT), f"does not compile: {e.msg.splitlines()[-1][:80]}")

# 8. goldfish reviewer agents
gf = ROOT / "vibe-goldfish"
if gf.exists():
    agents = {f.stem: f for f in (gf / "agents").glob("vibe-gf-*.md")}
    for name, f in agents.items():
        fm = re.match(r"---\n(.*?)\n---", f.read_text(), re.S)
        rel = f.relative_to(ROOT)
        if not fm:
            add("ERROR", rel, "agent has no frontmatter"); continue
        head = fm.group(1)
        if not re.search(r"^name:\s*" + re.escape(name) + r"\s*$", head, re.M):
            add("ERROR", rel, "agent name does not match its file name")
        if not re.search(r"^omitClaudeMd:\s*true\s*$", head, re.M):
            add("ERROR", rel, "reviewer must set omitClaudeMd: true (zero context)")
        t = re.search(r"^tools:\s*\[?(.*?)\]?\s*$", head, re.M)
        tools = {x.strip() for x in (t.group(1).split(",") if t else []) if x.strip()}
        if not tools or tools - {"Read", "Grep", "Glob"}:
            add("ERROR", rel, f"reviewer tools must be only Read, Grep, Glob (got {sorted(tools) or 'none'})")
    presets = gf / "references" / "PRESETS.md"
    if presets.exists():
        for row in presets.read_text().splitlines():
            if not row.startswith("| `"):
                continue
            cells = [c.strip() for c in row.split("|")]
            if len(cells) > 4:
                for r in re.split(r"\s*·\s*", cells[4]):
                    r = re.sub(r"[¹²³]", "", r).strip()
                    if r and f"vibe-gf-{r}" not in agents:
                        add("ERROR", "vibe-goldfish/references/PRESETS.md", f"reviewer '{r}' has no agent file vibe-gf-{r}.md")

# also lint repo-level scripts/
for py in (ROOT / "scripts").glob("*.py"):
    if py.name == "lint.py":
        continue
    try:
        py_compile.compile(str(py), doraise=True)
    except py_compile.PyCompileError as e:
        add("ERROR", py.relative_to(ROOT), f"does not compile: {e.msg.splitlines()[-1][:80]}")

# 5. README skill count
readme = ROOT / "README.md"
if readme.exists():
    m = re.search(r"framework of (\d+) .*skills", readme.read_text())
    if m and int(m.group(1)) != len(skill_dirs):
        add("ERROR", "README.md", f"claims {m.group(1)} skills but there are {len(skill_dirs)} vibe-*/ dirs")

errors = [i for i in issues if i[0] == "ERROR"]
warns  = [i for i in issues if i[0] == "WARN"]
for sev, where, msg in errors + warns:
    print(f"  {sev}  {where}: {msg}")
print(f"\nvibe-skill lint: {len(skill_dirs)} skills · {len(errors)} error(s) · {len(warns)} warning(s)")
sys.exit(1 if errors else 0)
