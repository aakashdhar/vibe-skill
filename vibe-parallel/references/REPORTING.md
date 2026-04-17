# REPORTING.md

Read during Step 6 and Step 7 of vibe-parallel.
How to parse structured subagent completion reports,
determine task states ([x] / [~] / [!]),
extract diagnostic information for targeted retries,
and compute wave cost annotations.

---

## Completion report format

Every subagent outputs this report when done:

```
TASK_COMPLETE: TASK-003
STATUS: DONE
FILES_MODIFIED: src/agents/scout_agent.py, src/tools/tavily.py
FILES_CREATED: none
TESTS_PASSED: 4/4
CRITERIA:
  [x] ScoutAgent returns top 5 competitors
  [x] Results written to Supabase immediately
  [x] Rate limiter applied between requests
  [ ] Error handling for Tavily timeout — NOT MET: Tavily mock not available in test env
CODEBASE_UPDATE: YES: updated Agents section with ScoutAgent constructor params
BLOCKERS: none
RATIONALE_ADDED: YES: added WHY comment at line 12 explaining directory-first approach
ERROR_IF_FAILED: none
```

---

## Parsing the completion report

```python
import re

def parse_completion_report(raw_output, task_id):
    """
    Extracts structured data from a subagent completion report.
    Handles malformed output gracefully.
    """
    # Find the report block — look for TASK_COMPLETE marker
    report_start = raw_output.find(f"TASK_COMPLETE: {task_id}")
    if report_start == -1:
        # Report not found — treat as FAILED
        return {
            "task_id": task_id,
            "status": "FAILED",
            "parse_error": True,
            "raw": raw_output[-2000:],  # last 2000 chars for diagnosis
            "state": "!"
        }

    report = raw_output[report_start:]

    def extract_field(key, text):
        match = re.search(rf"^{key}:\s*(.+)$", text, re.MULTILINE)
        return match.group(1).strip() if match else ""

    def extract_criteria(text):
        criteria = []
        in_criteria = False
        for line in text.split("\n"):
            if line.startswith("CRITERIA:"):
                in_criteria = True
                continue
            if in_criteria:
                if line.startswith("  ["):
                    met = line.strip().startswith("[x]")
                    text_part = re.sub(r"^\[.\]\s*", "", line.strip())
                    note = ""
                    if " — NOT MET:" in text_part:
                        parts = text_part.split(" — NOT MET:")
                        text_part = parts[0].strip()
                        note = parts[1].strip() if len(parts) > 1 else ""
                    criteria.append({
                        "text": text_part,
                        "met": met,
                        "note": note
                    })
                elif line and not line.startswith(" "):
                    in_criteria = False
        return criteria

    status = extract_field("STATUS", report)
    files_modified = [f.strip() for f in extract_field("FILES_MODIFIED", report).split(",")
                      if f.strip() and f.strip() != "none"]
    files_created = [f.strip() for f in extract_field("FILES_CREATED", report).split(",")
                     if f.strip() and f.strip() != "none"]
    tests_raw = extract_field("TESTS_PASSED", report)
    codebase_update = extract_field("CODEBASE_UPDATE", report)
    blockers = extract_field("BLOCKERS", report)
    rationale_added = extract_field("RATIONALE_ADDED", report)
    error = extract_field("ERROR_IF_FAILED", report)
    criteria = extract_criteria(report)

    # Parse test count
    tests_passed = tests_total = 0
    if "/" in tests_raw:
        parts = tests_raw.split("/")
        try:
            tests_passed = int(parts[0])
            tests_total = int(parts[1])
        except ValueError:
            pass

    # Determine task state
    unmet_criteria = [c for c in criteria if not c["met"]]
    tests_all_pass = tests_passed == tests_total if tests_total > 0 else True

    if status == "DONE" and not unmet_criteria and tests_all_pass:
        state = "x"          # [x] complete
    elif status == "FAILED" or (tests_total > 0 and not tests_all_pass and not unmet_criteria):
        state = "!"          # [!] failed
    else:
        state = "~"          # [~] partial

    return {
        "task_id":        task_id,
        "status":         status,
        "state":          state,
        "files_modified": files_modified,
        "files_created":  files_created,
        "tests_passed":   tests_passed,
        "tests_total":    tests_total,
        "criteria":       criteria,
        "unmet_criteria": unmet_criteria,
        "codebase_update": codebase_update,
        "blockers":       blockers,
        "rationale_added": rationale_added,
        "error":          error,
        "parse_error":    False
    }
```

---

## Task state rules

```python
def determine_state(report):
    """
    [x] COMPLETE:
        STATUS=DONE AND all criteria met AND all tests pass

    [~] PARTIAL (passes warnings downstream, does not block):
        STATUS=PARTIAL
        OR: STATUS=DONE but some criteria not met
        OR: tests pass but criteria have unverifiable items

    [!] FAILED (stops the wave after diagnostic retry):
        STATUS=FAILED
        OR: tests failed (tests_passed < tests_total, total > 0)
        OR: parse error (report not found in output)
        OR: second retry also fails
    """
    if report["parse_error"]:
        return "!"
    if report["status"] == "FAILED":
        return "!"
    if report["tests_total"] > 0 and report["tests_passed"] < report["tests_total"]:
        return "!"
    if report["unmet_criteria"]:
        return "~"
    return "x"
```

---

## Partial task warning format

When a task completes as [~], downstream tasks receive this warning:

```python
def format_partial_warning(report):
    lines = [f"⚠️ UPSTREAM WARNING from {report['task_id']}:"]
    for c in report["unmet_criteria"]:
        lines.append(f"   Criterion not met: {c['text']}")
        if c["note"]:
            lines.append(f"   Reason: {c['note']}")
    if report["blockers"] and report["blockers"] != "none":
        lines.append(f"   Blocker: {report['blockers']}")
    lines.append(
        f"   Action: verify this does not affect your task "
        f"before marking yourself done."
    )
    return "\n".join(lines)
```

---

## Diagnostic retry

On first [!] failure, build a targeted retry prompt rather than
resending the same prompt verbatim.

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

def build_diagnostic_retry(task, failure_report, original_prompt):
    error = failure_report.get("error", "") or failure_report.get("raw", "")

    # Find matching error pattern
    cause = "Unknown failure — review the error output carefully"
    approach = "Re-read the task requirements and try again with fresh context"

    for pattern_def in COMMON_ERROR_PATTERNS:
        if re.search(pattern_def["pattern"], error, re.IGNORECASE):
            cause = pattern_def["cause"]
            approach = pattern_def["approach"]
            break

    retry_prompt = f"""RETRY — {task['id']} (attempt 2 of 2)

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
SONNET_INPUT_COST_PER_M = 3.0    # $3.00 per million input tokens (Sonnet 4.6)
SONNET_OUTPUT_COST_PER_M = 15.0  # $15.00 per million output tokens

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
