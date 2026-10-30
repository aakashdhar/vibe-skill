# RESOLVE.md

How the elephant answers goldfish findings. Read before Step 5 of vibe-goldfish.

You wrote the document under review, so you will want to defend it. **Wanting to contest
a finding is not evidence.** The rules below exist because the author is the worst judge
of whether the author was clear.

## First, link repeats

For every finding from round 2 onward, check whether it raises the same problem, at the
same place, as a finding from an earlier round (`goldfish.py status <target> --json`
lists them; the round files hold the text). If it does:

```bash
goldfish.py link <target> <new-id> --reraise-of <old-id>
```

- Old one **settled** (contested, declined, accepted, rejected) → the script settles the
  repeat automatically. A settled question is not reopened.
- Old one **fixed** → the fix did not hold. The new finding stays open; answer it again.

If a new finding sits exactly where a fix from the previous round went in, and undoing
that fix would make it go away, it is **churn**:

```bash
goldfish.py link <target> <new-id> --churn-of <old-id>
```

Churn always goes to a person (see Step 6 of the skill). Don't try to fix your way out of
it, because that is how a review loops forever.

## Then give every open finding exactly one answer

| Answer | When | Command |
|---|---|---|
| **fix** | The finding is right, or you can't prove it wrong from the files. This is the default. | `resolve <target> <id> --as fix --note "<the exact edit>"` |
| **contest** | The finding is wrong **and** a file the reviewer could read proves it. | `resolve <target> <id> --as contest --evidence "<file:line, quoted>"` |
| **escalate** | You believe it is wrong, but the proof is only in your head or in this conversation (a client call, a decision nobody wrote down). A person decides. | `resolve <target> <id> --as escalate --note "<your position, one or two lines>"` |
| **decline** | A P2 you choose not to act on. Only P2. | `resolve <target> <id> --as decline --note "<why>"` |

Hard rules, enforced by `goldfish.py`:

- **Never contest a comprehension finding.** If a careful reader misunderstood, the
  document must say more, so fix it.
- **Never change a severity.** If you think a P1 is really a P2, escalate it with that as
  your position.
- **A contest needs evidence the reviewer could have read.** "We discussed this" is an
  escalation, not a contest.
- **Don't add context just to satisfy a reviewer.** When the proof for an escalation is
  missing from the document, ask whether the document *should* say it. If it should, the
  answer is **fix**: write it into the document. If it shouldn't (it really is outside
  the document's job), escalate.

## Writing the fixes

Make each fix the smallest edit that resolves the finding, in the document itself.
Every edit, a P2 fix included, means the next round reviews new text, and the review
can only converge on two clean rounds of the same text.
Don't rewrite whole sections, and don't "improve" things no finding asked about: every
extra change is new material the next round must review, and the most common source of
churn. After editing:

```bash
goldfish.py applied <target> <id> [<id> ...]
```

## The elephant-only check

Before the next round, do the one check no goldfish can do: compare the document with
**what the user told you in this conversation**. Is anything they asked for missing? Did
any fix just made contradict something they said? A goldfish only has the files, so this
check is yours. Anything you find, write into the document and say so in the Step 6
summary. Don't grade the document against the reviewers' standards yourself: the session
that wrote it agrees with it.
