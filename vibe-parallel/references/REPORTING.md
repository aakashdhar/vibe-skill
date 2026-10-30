# REPORTING.md

Read during Step 6 and Step 7 of vibe-parallel.
How to parse structured subagent completion reports,
determine task states ([x] / [~] / [!]),
extract diagnostic information for targeted retries,
and compute wave cost annotations.

---

## Completion report format (structured JSON)

Current models produce reliable structured output — instruct each subagent to end
its turn with a single fenced `json` block matching the schema below. This
replaces the old free-text `TASK_COMPLETE:` block that had to be scraped with
regex (and failed a whole task whenever the format drifted). Where the runtime
supports a schema-validated output / tool call, bind this schema with
`strict: true` so the shape is guaranteed.

**Schema** (all keys required; `files_*` are arrays, empty when none):

```json
{
  "task_id": "TASK-003",
  "status": "DONE",
  "files_modified": ["src/agents/scout_agent.py", "src/tools/tavily.py"],
  "files_created": [],
  "tests": { "passed": 4, "total": 4, "expected_failing": [] },
  "criteria": [
    { "text": "ScoutAgent returns top 5 competitors", "met": true, "note": "" },
    { "text": "Error handling for Tavily timeout", "met": false,
      "note": "Tavily mock not available in test env" }
  ],
  "codebase_update": "updated Agents section with ScoutAgent constructor params",
  "blockers": [],
  "rationale_added": "WHY comment at line 12 explaining directory-first approach",
  "decisions": [
    { "title": "Validate ATS payloads with Zod",
      "why": "untrusted input; Zod already a dep via tRPC; hand-written guards drift",
      "touches": "shared/schemas/ats.ts, src/tools/tavily.py" }
  ],
  "error": null
}
```

`status` is one of `DONE` | `PARTIAL` | `FAILED`.

`tests` counts every test the subagent ran: `total` includes all of them, `passed` only
the green ones. `expected_failing` lists the ids (`<test file::test name>`) of tests that
fail **on purpose**. Only a task whose block declares `- **Expect:** red: <test file::test name>`
(vibe-fix-bug's regression-test task) may use it: the new regression test must fail on the
unfixed code, so it is counted in `total`, not in `passed`, and listed here by exactly
the id declared on that line. Any other id here counts as an ordinary failing test. Every
other task reports `"expected_failing": []`.

The subagent must NOT write the
main-session-owned files itself — `codebase_update` / `rationale_added` / `decisions`
describe deltas for the main session to apply after the wave.

`decisions` is an array (empty when none) of **meaningful** implementation decisions made
while building the task — hard-to-reverse choices, picks among real alternatives
(library / pattern / data-model / API shape), or anything that would surprise a future
reader. Routine work → `[]`. The main session promotes these into
`vibe/IMPLEMENTATION_LOG.md` after the wave (see WAVE step below); the subagent never
writes that file itself.

---

## Parsing the completion report

Parse the JSON block; only fall back to the legacy text parser if no JSON is
found (older subagents). A schema-valid JSON report removes the `parse_error →
auto-FAILED` failure class entirely.

```python
import json, re

def parse_completion_report(raw_output, task_id, expect_red=None):
    # expect_red: the declared test id(s) from the task block's `- **Expect:** red: ...`
    # line (task["expect_red"]), or None when the task has no such line.
    data = _extract_json_report(raw_output, task_id)
    if data is None:
        data = _parse_legacy_text_report(raw_output, task_id)   # fallback
    if data is None:
        return {"task_id": task_id, "status": "FAILED", "parse_error": True,
                "raw": raw_output[-2000:], "state": "!"}
    return _finalize(data, task_id, expect_red)

def _extract_json_report(raw_output, task_id):
    # Prefer a fenced ```json block; else the last {...} object in the output.
    blocks = re.findall(r"```json\s*(\{.*?\})\s*```", raw_output, re.DOTALL)
    if not blocks:
        blocks = re.findall(r"(\{(?:[^{}]|\{[^{}]*\})*\})", raw_output, re.DOTALL)
    for block in reversed(blocks):
        try:
            d = json.loads(block)
        except json.JSONDecodeError:
            continue
        if d.get("task_id") == task_id or "status" in d:
            return d
    return None

def _declared_red(expect_red):
    """The test id(s) declared on the task's `Expect: red:` line, as a list."""
    if not expect_red:
        return []
    return [expect_red] if isinstance(expect_red, str) else list(expect_red)

def tests_ok(passed, total, expected_failing, expect_red):
    """Failing tests are a failure UNLESS every failing test is listed in
    expected_failing AND each listed id is a test declared on the task's
    `Expect: red:` line. expect_red is that declared id (or a list of ids), or None.
    A task that does not declare `Expect: red` can never use expected_failing. An
    `Expect: red` task must actually have its declared tests failing (all green =
    bug not reproduced). Shared by _finalize(), determine_state() and SKILL.md
    parse_completion(): one rule, one count."""
    declared = _declared_red(expect_red)
    if expected_failing and not declared:
        return False
    failing = max(total - passed, 0)
    if declared:
        # The declared regression test MUST fail on the unfixed code. A report where
        # nothing failed means the bug was not reproduced: not done. A listed id that
        # is not the declared test is an ordinary failing test. Ids are counted once:
        # listing the declared id twice cannot hide an unrelated failing test.
        listed = set(expected_failing)
        return (failing >= 1 and len(listed) == len(expected_failing)
                and failing == len(listed) and listed <= set(declared))
    return failing == 0

def _finalize(d, task_id, expect_red=None):
    tests = d.get("tests") or {}
    passed, total = int(tests.get("passed", 0)), int(tests.get("total", 0))
    expected = list(tests.get("expected_failing") or [])
    criteria = d.get("criteria", []) or []
    unmet = [c for c in criteria if not c.get("met", False)]
    ok = tests_ok(passed, total, expected, expect_red)
    status = (d.get("status") or "").upper()

    # Same rule as determine_state() below — keep the two in lockstep.
    if status == "FAILED" or not ok:
        state = "!"          # failing tests are a failure, whatever the criteria say
                             # (except the declared expected-red tests, see tests_ok)
    elif status == "DONE" and not unmet:
        state = "x"
    else:
        state = "~"          # PARTIAL, or DONE with unmet criteria

    files = lambda k: [f for f in (d.get(k) or []) if f and f != "none"]
    return {
        "task_id": task_id, "status": status, "state": state,
        "files_modified": files("files_modified"),
        "files_created":  files("files_created"),
        "tests_passed": passed, "tests_total": total,
        "expected_failing": expected, "expect_red": expect_red,
        "criteria": criteria, "unmet_criteria": unmet,
        "codebase_update": d.get("codebase_update") or "",
        "blockers": d.get("blockers") or [],
        "rationale_added": d.get("rationale_added") or "",
        "decisions": d.get("decisions") or [],
        "error": d.get("error"),
        "parse_error": False,
    }
```

> `_parse_legacy_text_report` is the pre-JSON regex parser (kept only for
> backward compatibility with the old `TASK_COMPLETE:` text format); new
> subagent prompts should always request the JSON schema above.

---

## Task state rules

```python
def determine_state(report):
    """
    [x] COMPLETE:
        STATUS=DONE AND all criteria met AND all tests pass
        (or the only failing tests are the task's declared expected-red tests:
         the task has `Expect: red: <id>` and lists exactly that id in
         tests.expected_failing)

    [~] PARTIAL (treated like a failure for retry; never unlocks dependents):
        STATUS=PARTIAL
        OR: STATUS=DONE but some criteria not met
        OR: tests pass but criteria have unverifiable items
        → diagnostic retry once (attempt 2). Still [~] or [!] after it → [!], STOP.

    [!] FAILED (diagnostic retry once, then STOP for a person):
        STATUS=FAILED
        OR: tests failed (see tests_ok: expected-red tests excepted)
        OR: parse error (report not found in output)
        OR: the retry (attempt 2) ends [~] or [!] again
    """
    if report["parse_error"]:
        return "!"
    if report["status"] == "FAILED":
        return "!"
    if not tests_ok(report["tests_passed"], report["tests_total"],
                    report["expected_failing"], report["expect_red"]):
        return "!"
    if report["status"] != "DONE" or report["unmet_criteria"]:
        return "~"           # PARTIAL, or DONE with unmet criteria
    return "x"
```

---

## Partial task warning format

A `[~]` task never unlocks its dependents: they wait for it to become `[x]`. This
warning is used only inside the task's own retry prompt (what the first attempt left
unmet) and in the stop report when the retry also ends `[~]`:

```python
def format_partial_warning(report):
    lines = [f"⚠️ PARTIAL RESULT from {report['task_id']}:"]
    for c in report["unmet_criteria"]:
        lines.append(f"   Criterion not met: {c['text']}")
        if c["note"]:
            lines.append(f"   Reason: {c['note']}")
    if report["blockers"] and report["blockers"] != "none":
        lines.append(f"   Blocker: {report['blockers']}")
    lines.append(
        f"   Action: meet these criteria in the retry, "
        f"without undoing what already works."
    )
    return "\n".join(lines)
```

---

## Diagnostic retry

On a first `[!]` or `[~]` result, build a targeted retry prompt rather than
resending the same prompt verbatim. Before dispatching it, count the attempt on disk:

```bash
VS="$HOME/.claude/skills/vibe-mode/scripts/vibe_state.py"
python3 "$VS" attempt [TASK-ID]     # prints "attempt [TASK-ID]: 2 of 2"; exit 1 = budget spent
```

Exit 1 means the budget (2) is already spent: do not dispatch. Mark the task `[!]` and
STOP (`run-state set --status needs_human --reason "[TASK-ID] failed after retry: <root cause>"`).
The `attempt` number in the prompt header is the one that command printed, never a
number kept in memory.

```python
COMMON_ERROR_PATTERNS = [
    {
        "pattern":   r"ModuleNotFoundError|ImportError|Cannot find module",
        "cause":     "Import path is incorrect or module not yet created",
        "approach":  "Check the exact import path. If importing a file from Wave 1, "
                     "verify it was created by checking with ls. Use the graph imports "
                     "as the canonical import path."
    },
    {
        "pattern":   r"TypeError: .* is not a function|AttributeError",
        "cause":     "Method signature mismatch — function called with wrong args or doesn't exist yet",
        "approach":  "Read the actual file before calling. Don't assume the interface — verify it."
    },
    {
        "pattern":   r"ENOENT|FileNotFoundError|no such file",
        "cause":     "File referenced in task doesn't exist yet",
        "approach":  "Create the file before using it. Check if a parent directory needs creating."
    },
    {
        "pattern":   r"AssertionError|FAIL|Expected .* to",
        "cause":     "Test assertion failed — implementation doesn't match expected behaviour",
        "approach":  "Read the test carefully. Implement exactly what the test expects, "
                     "not what you think it should do."
        # Never used for an `Expect: red` task: see build_diagnostic_retry().
    },
    {
        "pattern":   r"SyntaxError|unexpected token|ParseError",
        "cause":     "Syntax error in generated code",
        "approach":  "Review the generated code carefully. Run a syntax check before submitting."
    },
    {
        "pattern":   r"TypeScript|TS\d{4}|type error",
        "cause":     "TypeScript type mismatch",
        "approach":  "Check the type definitions. Import types explicitly. "
                     "Don't use 'any' — resolve the actual type."
    },
]

def build_diagnostic_retry(task, failure_report, original_prompt, attempt, budget=2):
    # attempt / budget: from the line `vibe_state.py attempt [TASK-ID]` printed.
    error = failure_report.get("error", "") or failure_report.get("raw", "")
    if not error and failure_report.get("state") == "~":
        error = format_partial_warning(failure_report)   # PARTIAL: the unmet criteria

    # Find matching error pattern
    cause = "Unknown failure — review the error output carefully"
    approach = "Re-read the task requirements and try again with fresh context"

    for pattern_def in COMMON_ERROR_PATTERNS:
        if re.search(pattern_def["pattern"], error, re.IGNORECASE):
            cause = pattern_def["cause"]
            approach = pattern_def["approach"]
            break

    if task.get("expect_red"):
        # The regression test must stay red: this task never writes the fix.
        cause = cause if "assertion" not in cause.lower() else \
            "The regression test failed for the wrong reason, or a test outside expected_failing failed"
        approach = ("This task writes a test that must FAIL on the unfixed code. Do not touch "
                    "non-test files and do not write the fix. Make sure the test fails for the "
                    "bug's reason, every other test passes, and the red test is listed in "
                    "tests.expected_failing.")

    retry_prompt = f"""RETRY — {task['id']} (attempt {attempt} of {budget})

Your previous attempt failed:
  Error: {error[:500] if error else 'No error captured — check output'}
  Most likely cause: {cause}

Approach for this retry:
  {approach}

Additional context from failure analysis:
"""

    # Add specific hints based on what was partially done
    files_modified = failure_report.get("files_modified", [])
    if files_modified:
        retry_prompt += f"  Files you already modified: {', '.join(files_modified)}\n"
        retry_prompt += "  Review these files — they may need to be corrected, not rewritten.\n"

    criteria_met = [c for c in failure_report.get("criteria", []) if c["met"]]
    if criteria_met:
        retry_prompt += f"  Criteria already passing:\n"
        for c in criteria_met:
            retry_prompt += f"    [x] {c['text']}\n"
        retry_prompt += "  Focus only on the unmet criteria — don't undo what works.\n"

    retry_prompt += f"""
{original_prompt}
"""

    return retry_prompt
```

---

## Wave cost annotation

After wave completes, compute cost annotation for the progress log.

```python
# Source of truth: vibe-cost/references/PRICING.md. Defaults to the build-loop
# workhorse (claude-sonnet-5). If subagents ran on a different tier, use that
# model's row from PRICING.md instead of these two constants.
SONNET_INPUT_COST_PER_M = 2.0    # claude-sonnet-5 input ($/MTok)
SONNET_OUTPUT_COST_PER_M = 10.0  # claude-sonnet-5 output ($/MTok)

def compute_wave_cost(reports, wave_tasks, use_graph):
    """
    Estimate wave cost from completion reports.
    Token counts are estimates — not exact Claude API figures.
    """
    # Input: context slice or CODEBASE.md per subagent
    # Output: code written + completion report
    from references.SUBAGENT_CONTEXT import estimate_subagent_tokens

    total_input_tokens = 0
    total_output_tokens = 0

    for task in wave_tasks:
        input_tok = estimate_subagent_tokens(task, use_graph)
        # Output estimate: ~500 tokens per file created/modified + 300 for report
        report = next((r for r in reports if r["task_id"] == task["id"]), {})
        output_files = len(report.get("files_modified", [])) + len(report.get("files_created", []))
        output_tok = output_files * 500 + 300
        total_input_tokens += input_tok
        total_output_tokens += output_tok

    input_cost = total_input_tokens / 1_000_000 * SONNET_INPUT_COST_PER_M
    output_cost = total_output_tokens / 1_000_000 * SONNET_OUTPUT_COST_PER_M
    total_cost = input_cost + output_cost

    # What would sequential cost? Same but without graph slicing benefit
    sequential_input = sum(
        estimate_subagent_tokens(t, use_graph=False) for t in wave_tasks
    )
    sequential_cost = (
        sequential_input / 1_000_000 * SONNET_INPUT_COST_PER_M
        + total_output_tokens / 1_000_000 * SONNET_OUTPUT_COST_PER_M
    )

    return {
        "input_tokens":    total_input_tokens,
        "output_tokens":   total_output_tokens,
        "cost_usd":        round(total_cost, 4),
        "sequential_usd":  round(sequential_cost, 4),
        "saving_usd":      round(sequential_cost - total_cost, 4),
        "context_mode":    "graph-aware" if use_graph else "full CODEBASE.md"
    }
```

---

## CODEBASE.md batch update format

After wave completes, the main session writes CODEBASE.md once.
Collect all reports first, then write:

```python
def generate_codebase_updates(reports):
    """
    Collects CODEBASE.md update descriptions from all completion reports.
    Returns a structured list for the main session to apply.
    """
    updates = []
    for report in reports:
        if report.get("codebase_update", "").upper().startswith("YES"):
            desc = report["codebase_update"][4:].strip()  # strip "YES:" prefix
            updates.append({
                "task_id":       report["task_id"],
                "files_created": report.get("files_created", []),
                "files_modified": report.get("files_modified", []),
                "description":   desc
            })

    if not updates:
        return None

    return updates

# Main session applies these as a batch:
# - New files → add to relevant CODEBASE.md section
# - Modified files → update existing entries
# - One git commit for all CODEBASE.md changes from the wave
```

---

## Progress log update format

```python
def update_progress_log(wave_num, wave_name, reports, cost_annotation, duration_seconds):
    tasks_complete = sum(1 for r in reports if r["state"] == "x")
    tasks_partial = sum(1 for r in reports if r["state"] == "~")
    tasks_failed = sum(1 for r in reports if r["state"] == "!")

    STATE_EMOJI = {"x": "✅ complete", "~": "🟡 partial", "!": "❌ failed"}

    rows = []
    for r in reports:
        emoji = STATE_EMOJI.get(r["state"], "❓")
        rows.append(
            f"| {r['task_id']} | {r.get('size', '?')} | {emoji} | — | — | — |"
        )

    unmet_section = ""
    for r in reports:
        if r["unmet_criteria"]:
            for c in r["unmet_criteria"]:
                unmet_section += f"- {r['task_id']}: {c['text']}"
                if c.get("note"):
                    unmet_section += f" — {c['note']}"
                unmet_section += "\n"

    all_files = []
    for r in reports:
        all_files.extend(r.get("files_modified", []))
        all_files.extend(r.get("files_created", []))

    mins = duration_seconds // 60
    secs = duration_seconds % 60

    return f"""# Wave {wave_num} — {wave_name}
Duration: {mins}m {secs}s

## Tasks
| ID | Size | Status | Started | Completed | Duration |
|----|------|--------|---------|-----------|----------|
{chr(10).join(rows)}

## Summary
Complete: {tasks_complete} · Partial: {tasks_partial} · Failed: {tasks_failed}

{"## Unmet criteria" + chr(10) + unmet_section if unmet_section else ""}

## Files modified this wave
{chr(10).join(f"  {f}" for f in sorted(set(all_files))) if all_files else "  none"}

## Cost
Subagent input tokens: ~{cost_annotation['input_tokens']:,}
Subagent output tokens: ~{cost_annotation['output_tokens']:,}
Wave cost: ~${cost_annotation['cost_usd']}
Context mode: {cost_annotation['context_mode']}
{f"Saving vs no-graph: ~${cost_annotation['saving_usd']}" if cost_annotation['saving_usd'] > 0 else ""}
"""
```
