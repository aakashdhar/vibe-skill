# WAVE_BUILDER.md

Read during Step 2 of vibe-parallel.
Full dependency wave construction algorithm including
write-write conflict detection, read-write conflict detection,
and size-aware wave splitting.

---

## Pass 1 — Standard dependency resolution

```python
def build_waves(tasks):
    """
    tasks: list of task dicts with id, dependencies, touches, reads, size
    Returns: list of waves, each wave a list of task IDs
    """
    completed = set()   # tasks already [x] in task file
    pending = {t["id"]: t for t in tasks if t["status"] == "[ ]"}
    waves = []

    while pending:
        # Find tasks whose dependencies are all in completed
        wave = []
        for tid, task in pending.items():
            deps = task.get("dependencies", [])
            if all(d in completed for d in deps):
                wave.append(tid)

        if not wave:
            # Circular dependency or unresolvable — surface to user
            remaining = list(pending.keys())
            raise ValueError(
                f"Cannot resolve dependencies for: {remaining}. "
                f"Check for circular dependencies in the task file."
            )

        waves.append(wave)
        for tid in wave:
            completed.add(tid)
            del pending[tid]

    return waves
```

---

## Pass 2 — Write-write conflict detection

Two tasks write the same file → they cannot run in the same wave.
The second task (alphabetically later ID) moves to the next wave.

```python
APPEND_ONLY_FILES = {
    "vibe/CODEBASE.md",
    "vibe/DECISIONS.md",
    "vibe/TASKS.md",
    "CLAUDE.md",
}

def resolve_write_conflicts(waves, tasks_by_id):
    resolved = []

    for wave_idx, wave in enumerate(waves):
        file_to_writer = {}    # file → first task to claim it
        deferred = []          # tasks bumped to next wave

        # Sort wave by task ID for deterministic conflict resolution
        wave_sorted = sorted(wave)

        for tid in wave_sorted:
            task = tasks_by_id[tid]
            conflict = False
            for f in task.get("touches", []):
                if f in APPEND_ONLY_FILES:
                    continue   # safe to write concurrently
                if f in file_to_writer:
                    # Conflict — this task loses, moves to next wave
                    deferred.append(tid)
                    conflict = True
                    break
            if not conflict:
                for f in task.get("touches", []):
                    if f not in APPEND_ONLY_FILES:
                        file_to_writer[f] = tid

        clean_wave = [tid for tid in wave_sorted if tid not in deferred]
        resolved.append(clean_wave)

        if deferred:
            # Inject deferred tasks at the front of the next wave
            if wave_idx + 1 < len(waves):
                waves[wave_idx + 1] = deferred + waves[wave_idx + 1]
            else:
                waves.append(deferred)

    return resolved
```

**Log conflict resolutions for the plan display:**
```
Conflict resolved: TASK-004 moved to Wave 2
  Reason: write conflict on src/models/brand_dna.py
  Writer in Wave 1: TASK-001
```

---

## Pass 3 — Read-write conflict detection

Task A writes a file. Task B reads that same file.
If both are in the same wave — Task B needs Task A's output.
Task B must move to the next wave.

This catches:
- Task B extends a base class Task A is creating
- Task B uses a schema Task A is defining
- Task B imports a utility Task A is writing
- Task B tests a file Task A is implementing

```python
def resolve_read_write_conflicts(waves, tasks_by_id):
    resolved = []

    for wave_idx, wave in enumerate(waves):
        # Build map of files being written this wave
        written_this_wave = {}   # file → writing task ID
        for tid in wave:
            task = tasks_by_id[tid]
            for f in task.get("touches", []):
                if f not in APPEND_ONLY_FILES:
                    written_this_wave[f] = tid

        deferred = []
        for tid in wave:
            task = tasks_by_id[tid]
            conflict = False
            for f in task.get("reads", []):
                if f in written_this_wave and written_this_wave[f] != tid:
                    # Task reads a file another task in the same wave writes
                    deferred.append(tid)
                    conflict = True
                    break
            if conflict:
                wave.remove(tid)

        resolved.append(wave)

        if deferred:
            if wave_idx + 1 < len(waves):
                waves[wave_idx + 1] = deferred + waves[wave_idx + 1]
            else:
                waves.append(deferred)

    return resolved
```

**Log read-write conflict resolutions:**
```
Read-write conflict: TASK-003 moved to Wave 2
  Reason: TASK-003 reads src/agents/base_agent.py
          which TASK-001 is writing in Wave 1
  TASK-003 needs TASK-001's output to proceed
```

---

## Pass 4 — Size-aware wave splitting

**The problem:**
Wave 1 has: TASK-001 (L), TASK-002 (S), TASK-003 (S)
Wave 2 has: TASK-004 (depends on TASK-002), TASK-005 (depends on TASK-001)

Without splitting: Wave 2 waits for ALL of Wave 1 to finish.
TASK-004 is blocked by TASK-001 (L) even though it only depends on TASK-002 (S).

**The solution:**
TASK-004 can run alongside TASK-001 (L) — it doesn't depend on it.
Promote TASK-004 to a "fast lane" that runs with the Wave 1 L task.

```python
def apply_size_aware_splitting(waves, tasks_by_id):
    """
    For each wave containing an L task alongside S/M tasks:
    Find Wave N+1 tasks that depend ONLY on S/M tasks from Wave N (not the L task).
    Promote those tasks to run alongside the L task in Wave N's "fast lane".
    """
    result = []

    for wave_idx, wave in enumerate(waves):
        # Find L tasks and S/M tasks in this wave
        l_tasks = [tid for tid in wave if tasks_by_id[tid].get("size") == "L"]
        sm_tasks = [tid for tid in wave if tasks_by_id[tid].get("size") in ("S", "M")]

        if not l_tasks or not sm_tasks:
            # No splitting opportunity
            result.append({"main": wave, "fast_lane": []})
            continue

        l_task_set = set(l_tasks)

        # Look at the next wave — can any tasks be promoted?
        if wave_idx + 1 >= len(waves):
            result.append({"main": wave, "fast_lane": []})
            continue

        next_wave = waves[wave_idx + 1]
        fast_lane = []
        still_next = []

        for next_tid in next_wave:
            next_task = tasks_by_id[next_tid]
            deps = set(next_task.get("dependencies", []))

            # Does this task depend on any L task from current wave?
            depends_on_l = bool(deps & l_task_set)

            # Does it conflict with L task files?
            l_files = set()
            for l_tid in l_tasks:
                l_files.update(tasks_by_id[l_tid].get("touches", []))
            conflicts_with_l = bool(
                set(next_task.get("touches", [])) & l_files
            )

            if not depends_on_l and not conflicts_with_l:
                # Safe to promote to fast lane
                fast_lane.append(next_tid)
            else:
                still_next.append(next_tid)

        result.append({"main": wave, "fast_lane": fast_lane})

        # Update next wave to only contain non-promoted tasks
        waves[wave_idx + 1] = still_next

    return result
```

**Resulting wave structure with fast lane:**

```
Wave 1 main:       TASK-001 (L) · TASK-002 (S) · TASK-003 (S)
Wave 1 fast lane:  TASK-004 (S) — promoted from Wave 2
                   (runs alongside L task after TASK-002 and TASK-003 complete)
Wave 2:            TASK-005 (M) — still depends on L task
```

**Execution order with fast lane:**
1. Dispatch Wave 1 main tasks (TASK-001 L, TASK-002 S, TASK-003 S) simultaneously
2. TASK-002 and TASK-003 complete quickly (S tasks)
3. Immediately dispatch fast lane (TASK-004) — don't wait for TASK-001
4. TASK-001 completes (L task, slower)
5. After TASK-001 AND TASK-004 both complete → dispatch Wave 2 (TASK-005)

**Plan display for fast lane:**
```
Wave 1 — 3 tasks run simultaneously:
  · TASK-001 (L) — [description]
  · TASK-002 (S) — [description]
  · TASK-003 (S) — [description]

  Fast lane — unlocks when TASK-002 and TASK-003 complete:
  · TASK-004 (S) — [description]  ← runs alongside TASK-001

Wave 2 — unlocks when Wave 1 + fast lane both complete:
  · TASK-005 (M) — [description]
```

---

## Complete wave building pipeline

```python
def build_all_waves(tasks):
    tasks_by_id = {t["id"]: t for t in tasks}

    # Pass 1: standard deps
    waves = build_waves(tasks)

    # Pass 2: write-write conflicts
    waves = resolve_write_conflicts(waves, tasks_by_id)

    # Pass 3: read-write conflicts
    waves = resolve_read_write_conflicts(waves, tasks_by_id)

    # Pass 4: size-aware splitting
    waves_with_fast_lanes = apply_size_aware_splitting(waves, tasks_by_id)

    return waves_with_fast_lanes, tasks_by_id
```

---

## Time estimate calculation

```python
SIZE_HOURS = {"S": 1.5, "M": 3.0, "L": 5.0}

def estimate_time(waves_with_fast_lanes, tasks_by_id):
    sequential_total = sum(
        SIZE_HOURS[t.get("size", "M")]
        for t in tasks_by_id.values()
    )

    parallel_total = 0
    for wave in waves_with_fast_lanes:
        main_tasks = wave["main"]
        fast_lane = wave["fast_lane"]

        if not main_tasks:
            continue

        # Wave duration = slowest task in main + fast lane
        # Fast lane runs after S/M complete, alongside L
        l_tasks = [t for t in main_tasks if tasks_by_id[t].get("size") == "L"]
        sm_tasks = [t for t in main_tasks if tasks_by_id[t].get("size") in ("S", "M")]

        sm_max = max((SIZE_HOURS[tasks_by_id[t].get("size","M")] for t in sm_tasks), default=0)
        l_max = max((SIZE_HOURS[tasks_by_id[t].get("size","M")] for t in l_tasks), default=0)
        fl_max = max((SIZE_HOURS[tasks_by_id[t].get("size","M")] for t in fast_lane), default=0)

        # S/M tasks finish first, then fast lane and L run in parallel
        wave_duration = max(l_max, sm_max + fl_max)
        parallel_total += wave_duration

    saving = sequential_total - parallel_total
    pct = int((saving / sequential_total * 100)) if sequential_total else 0

    return {
        "sequential_hours": round(sequential_total, 1),
        "parallel_hours": round(parallel_total, 1),
        "saving_hours": round(saving, 1),
        "saving_pct": pct
    }
```
