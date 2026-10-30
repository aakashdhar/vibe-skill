# DISPATCH.md

How the elephant starts the goldfish. Read before Step 3 of vibe-goldfish.

## The one rule

**A goldfish gets file paths, never explanations.** Its task names the documents, the
standards and the related files, and nothing else. Leave out all of these:

- a summary of the conversation, the brief, or "what we're building";
- why a section is written the way it is, or what the author meant;
- earlier findings, earlier answers, or what was fixed;
- hints such as "pay attention to X" or "this part is fine".

Each of those carries the author's context into the reviewer and makes it agree with the
author. If a reviewer needs a fact to judge the document, the document must contain that
fact. Add it to the document, not to the task.

## Starting each reviewer

One `Agent` call per reviewer, all sent **in the same message** so they run in parallel.
Never fork the conversation and never resume a reviewer from an earlier round: every
round gets brand-new subagents.

- `subagent_type`: `vibe-gf-<reviewer>` (e.g. `vibe-gf-comprehension`)
- `description`: `goldfish <reviewer> · <target>`
- `prompt`: exactly the template below, with absolute paths filled in.

```
Goldfish review. Follow your instructions.

Project root: <absolute project root>

Documents to review:
- <absolute path>
- <absolute path>

Standards:            (rubric reviewer only: omit this block for the others)
- <absolute path>

Related files you may read:
- <absolute path>     (or "none")
```

Nothing goes before or after the template.

## When the goldfish agents are not installed

Before the first dispatch, check that the agent files exist:

```bash
ls "$HOME/.claude/agents/"vibe-gf-*.md 2>/dev/null
```

- **All present** → dispatch as above. Record `goldfish.py isolation <target> full`.
- **Missing** (never installed, or installed in this session and Claude Code not yet
  restarted): tell the user once, in one line, that `scripts/sync-install.sh` installs
  them and a restart activates them. Then fall back for this review:
  `subagent_type: general-purpose`, with the prompt being the full text of the role file
  `$HOME/.claude/skills/vibe-goldfish/agents/vibe-gf-<reviewer>.md` (without its
  frontmatter) followed by the template. A general-purpose subagent still never sees this
  conversation, but it does load CLAUDE.md, so record
  `goldfish.py isolation <target> partial --note "agents not installed: CLAUDE.md visible to reviewers"`.
  The report shows this, and the user should know the review was weaker.
- **No `Agent` tool at all** (you are yourself a subagent, or the runtime has none):
  **do not review the document yourself.** A review in the author's own context is not a
  goldfish review. Return to the caller with "goldfish review not run: no subagent tool"
  and let it stop or ask a person.

## Collecting the results

Each reviewer ends with one fenced `json` block. For each reviewer:

1. Take the **last** ```json block in its reply and write it to
   `vibe/goldfish/<target>/round-<N>/<reviewer>.json` with the Write tool. Save it
   exactly as the reviewer wrote it. Never edit a reviewer's findings.
2. `goldfish.py ingest <target> --reviewer <reviewer> --file <that path>`. Ingest
   records nothing when the reviewer said `"status": "incomplete"` or left out
   `findings`, so the reviewer stays pending and can be retried.
3. If the reply has no JSON block, the JSON is invalid, or ingest refuses it (for
   example, an incomplete review), then **retry once** with a new subagent and the same
   template. If the retry also fails:
   `goldfish.py ingest <target> --reviewer <reviewer> --not-run --reason "<what happened>"`.
   A reviewer that did not run is never counted as "no findings". That round cannot be
   clean.

Don't paste reviewer replies into the conversation. The saved files and `goldfish.py
status` are the record. Show the user only the summary in vibe-goldfish Step 6.
