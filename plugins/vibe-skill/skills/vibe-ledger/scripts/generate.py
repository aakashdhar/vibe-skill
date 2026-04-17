#!/usr/bin/env python3
"""
vibe-ledger generator v1.1
Reads vibe/cost/history.json + vibe/cost/summary.json
Generates vibe/cost/ledger/index.html
Zero dependencies — pure Python stdlib.
"""

import json, os, sys, webbrowser
from pathlib import Path
from datetime import datetime
from collections import defaultdict


# ─── DATA LOADING ────────────────────────────────────────────────────────────

def find_project_root():
    cwd = Path.cwd()
    for path in [cwd, *cwd.parents]:
        if (path / "vibe" / "cost" / "history.json").exists():
            return path
    return None

def load_history(root):
    with open(root / "vibe" / "cost" / "history.json") as f:
        return json.load(f)

def load_summary(root):
    p = root / "vibe" / "cost" / "summary.json"
    if not p.exists():
        return {}
    try:
        raw = p.read_text(encoding="utf-8")
        return json.loads(raw)
    except Exception:
        return {}


# ─── METRICS ─────────────────────────────────────────────────────────────────

def compute_metrics(sessions, summary):
    all_tasks = []
    for s in sessions:
        for tid, t in s.get("task_breakdown", {}).items():
            all_tasks.append({
                "id": tid, "session": s["session_id"],
                "phase": s.get("phase", ""), "size": t.get("size", "M"),
                "cost": t.get("cost_usd", 0), "input": t.get("input_tokens", 0),
                "output": t.get("output_tokens", 0), "note": t.get("note", ""),
            })

    total_cost   = sum(s["cost_usd"] for s in sessions)
    total_input  = sum(s["input_tokens"] for s in sessions)
    total_output = sum(s["output_tokens"] for s in sessions)
    total_tasks  = sum(s["tasks_completed"] for s in sessions)
    total_tokens = total_input + total_output
    n_sessions   = len(sessions)

    s_tasks = [t for t in all_tasks if t["size"] == "S"]
    m_tasks = [t for t in all_tasks if t["size"] == "M"]
    l_tasks = [t for t in all_tasks if t["size"] == "L"]

    avg_s = sum(t["cost"] for t in s_tasks) / len(s_tasks) if s_tasks else 0
    avg_m = sum(t["cost"] for t in m_tasks) / len(m_tasks) if m_tasks else 0
    avg_l = sum(t["cost"] for t in l_tasks) / len(l_tasks) if l_tasks else 0
    avg_task = total_cost / total_tasks if total_tasks else 0

    day_totals = defaultdict(lambda: {"cost": 0, "sessions": 0, "tasks": 0, "phases": []})
    for s in sessions:
        d = s.get("date", "unknown")
        day_totals[d]["cost"]     += s["cost_usd"]
        day_totals[d]["sessions"] += 1
        day_totals[d]["tasks"]    += s["tasks_completed"]
        day_totals[d]["phases"].append(s.get("phase", ""))

    peak     = max(sessions, key=lambda x: x["cost_usd"])
    cheapest = min(sessions, key=lambda x: x["cost_usd"])
    top_tasks = sorted(all_tasks, key=lambda x: x["cost"], reverse=True)[:5]

    all_patterns  = [p for s in sessions for p in s.get("patterns_detected", [])]
    clean_sessions = sum(1 for s in sessions if not s.get("patterns_detected"))

    dates = sorted(set(s.get("date", "") for s in sessions))
    if len(dates) == 1:
        date_range = datetime.strptime(dates[0], "%Y-%m-%d").strftime("%b %d, %Y")
    elif len(dates) > 1:
        d1 = datetime.strptime(dates[0],  "%Y-%m-%d").strftime("%b %d")
        d2 = datetime.strptime(dates[-1], "%Y-%m-%d").strftime("%b %d, %Y")
        date_range = f"{d1} – {d2}"
    else:
        date_range = "unknown"

    max_cost  = max(s["cost_usd"] for s in sessions)
    dot_value = max_cost / 7

    def session_dots(cost, s):
        filled = min(7, round(cost / dot_value)) if dot_value > 0 else 0
        patterns = s.get("patterns_detected", [])
        if s["session_id"] == peak["session_id"]:
            colour = "#ff4060"
        elif "CP-03" in patterns:
            colour = "#ffb800"
        elif "review" in s.get("phase", "").lower():
            colour = "#00cfff"
        else:
            colour = "#39ff14"
        return filled, 7 - filled, colour

    tasks_remaining = summary.get("tasks_remaining") or 8
    pct_complete    = summary.get("build_progress_pct") or (total_tasks / (total_tasks + tasks_remaining) * 100)
    remaining_low   = avg_task * tasks_remaining * 0.85
    remaining_high  = avg_task * tasks_remaining * 1.20

    return {
        "total_cost": total_cost, "total_input": total_input, "total_output": total_output,
        "total_tokens": total_tokens, "total_tasks": total_tasks, "n_sessions": n_sessions,
        "avg_task": avg_task, "avg_s": avg_s, "avg_m": avg_m, "avg_l": avg_l,
        "count_s": len(s_tasks), "count_m": len(m_tasks), "count_l": len(l_tasks),
        "total_s": sum(t["cost"] for t in s_tasks),
        "total_m": sum(t["cost"] for t in m_tasks),
        "total_l": sum(t["cost"] for t in l_tasks),
        "io_ratio": total_input / total_output if total_output else 0,
        "output_per_dollar": total_output / total_cost if total_cost else 0,
        "tokens_per_task": total_tokens / total_tasks if total_tasks else 0,
        "peak": peak, "cheapest": cheapest, "top_tasks": top_tasks,
        "all_patterns": all_patterns, "clean_sessions": clean_sessions,
        "day_totals": dict(day_totals), "date_range": date_range,
        "pct_complete": pct_complete, "tasks_remaining": tasks_remaining,
        "remaining_low": remaining_low, "remaining_high": remaining_high,
        "forecast_low": total_cost + remaining_low,
        "forecast_high": total_cost + remaining_high,
        "dot_value": dot_value, "session_dots_fn": session_dots,
        "input_pct": (total_input / total_tokens * 100) if total_tokens else 0,
        "output_pct": (total_output / total_tokens * 100) if total_tokens else 0,
        # Rich fields from summary.json
        "at_a_glance":          summary.get("at_a_glance", ""),
        "session_narratives":   summary.get("session_narratives", {}),
        "phase_summary":        summary.get("phase_summary", []),
        "feature_costs":        summary.get("feature_costs", {}),
        "summary_recs":         summary.get("recommendations", []),
        "forecast_narrative":   summary.get("forecast_narrative", ""),
    }


# ─── HTML HELPERS ─────────────────────────────────────────────────────────────

def blocks(filled_n, colour, total=52):
    return (f'<span style="font-family:\'VT323\',monospace;font-size:15px;letter-spacing:0;color:{colour}">'
            + "█" * filled_n + "</span>"
            + f'<span style="font-family:\'VT323\',monospace;font-size:15px;letter-spacing:0;color:#363c5a">'
            + "░" * (total - filled_n) + "</span>")

def bar(pct, colour, total=52):
    return blocks(round(pct / 100 * total), colour, total)

def dot_row(filled, empty, colour):
    d = ""
    for _ in range(filled):
        d += f'<div style="width:10px;height:10px;background:{colour};display:inline-block;margin-right:3px"></div>'
    for _ in range(empty):
        d += '<div style="width:10px;height:10px;background:#363c5a;display:inline-block;margin-right:3px"></div>'
    return d

def flag(text, col, border, bg):
    return (f'<span style="display:inline-block;font-size:12px;padding:1px 7px;letter-spacing:1px;'
            f'border:1px solid {border};margin-left:6px;vertical-align:middle;'
            f'color:{col};background:{bg}">{text}</span>')

def fmt_date(iso):
    try:
        return datetime.strptime(iso, "%Y-%m-%d").strftime("%b %d")
    except Exception:
        return iso


# ─── SECTION RENDERERS ────────────────────────────────────────────────────────

def render_at_a_glance(m):
    if m["at_a_glance"]:
        return m["at_a_glance"]
    peak_ppt = m["peak"]["cost_usd"] / m["peak"]["tasks_completed"] if m["peak"]["tasks_completed"] else 0
    vs_avg   = "right at" if abs(peak_ppt - m["avg_task"]) < 0.03 else ("above" if peak_ppt > m["avg_task"] else "below")
    days     = len(m["day_totals"])
    return (
        f"You've spent <strong>${m['total_cost']:.2f}</strong> across "
        f"<strong>{m['n_sessions']} sessions</strong> over {days} day{'s' if days > 1 else ''}. "
        f"Your average cost per task is <strong>${m['avg_task']:.2f}</strong> — "
        f"small tasks run ${m['avg_s']:.2f}, medium ${m['avg_m']:.2f}, and large ${m['avg_l']:.2f}. "
        f"The most expensive session was <strong>{m['peak'].get('phase', m['peak']['session_id'])}</strong> "
        f"at <strong>${m['peak']['cost_usd']:.2f}</strong> for {m['peak']['tasks_completed']} tasks — "
        f"${peak_ppt:.2f} per task, {vs_avg} your project average.<br><br>"
        f"At this pace the full project will cost between "
        f"<span class=\"warn\"><strong>${m['forecast_low']:.2f} and ${m['forecast_high']:.2f}</strong></span>."
    )


def render_day_by_day(m):
    days = sorted(m["day_totals"].items())
    max_c = max(d["cost"] for d in m["day_totals"].values()) if m["day_totals"] else 1
    html  = ""
    for date, data in days:
        label  = datetime.strptime(date, "%Y-%m-%d").strftime("%B %d, %Y") if "-" in date else date
        colour = "#ffb800" if data["cost"] == max_c else "#39ff14"
        pct    = data["cost"] / max_c * 100
        phases = " · ".join(set(p.split("—")[0].strip() for p in data["phases"] if p))[:60]
        html  += f"""
        <div style="margin-bottom:14px">
          <div style="display:flex;justify-content:space-between;font-size:16px;margin-bottom:4px">
            <span style="color:#dde4f4">{label}</span><span style="color:{colour}">${data['cost']:.2f}</span>
          </div>
          {bar(pct, colour, 48)}
          <div style="font-size:14px;color:#7a88aa;margin-top:3px">{data['sessions']} session{'s' if data['sessions']!=1 else ''} · {data['tasks']} tasks · {phases}</div>
        </div>"""
    return html


def render_session_rows(sessions, m):
    rows = ""
    for s in reversed(sessions):
        filled, empty, colour = m["session_dots_fn"](s["cost_usd"], s)
        cost_cls = {"#ff4060":"cr","#ffb800":"ca","#00cfff":"cb","#39ff14":"cg"}.get(colour,"cg")
        peak_badge = flag("peak","#ff4060","#880022","rgba(255,64,96,0.07)") if s["session_id"]==m["peak"]["session_id"] else ""
        sid_short  = s["session_id"].split("-")[-1].upper()
        narrative  = m["session_narratives"].get(s["session_id"], "")
        nar_row    = (f'<tr><td colspan="5" style="padding:2px 12px 10px;font-size:15px;'
                      f'color:#7a88aa;line-height:1.6;border-bottom:1px solid var(--line)">'
                      f'{narrative}</td></tr>') if narrative else ""
        rows += f"""
          <tr>
            <td style="color:#7a88aa;font-size:14px">{sid_short} · {fmt_date(s.get('date',''))}</td>
            <td style="color:#dde4f4">{s.get('phase', s['session_id'])}{peak_badge}</td>
            <td style="color:#7a88aa">{s['tasks_completed']} tasks</td>
            <td>{dot_row(filled, empty, colour)}</td>
            <td style="text-align:right" class="{cost_cls}">${s['cost_usd']:.2f}</td>
          </tr>{nar_row}"""
    return rows


def render_top_tasks(m):
    size_css = {"S":"cs","M":"cm","L":"cl"}
    rows = ""
    for t in m["top_tasks"]:
        css  = size_css.get(t["size"], "cm")
        note = (f' <span style="font-size:12px;color:#ffb800">[{t["note"][:40]}]</span>') if t.get("note") else ""
        rows += f"""
          <tr>
            <td style="color:#00ffee;font-size:15px">{t['id']}</td>
            <td style="color:#dde4f4">{t['phase']}{note}</td>
            <td><span style="display:inline-block;padding:1px 6px;font-size:14px;border:1px solid;letter-spacing:1px" class="{css}">{t['size']}</span></td>
            <td style="text-align:right;color:#ffb800">${t['cost']:.2f}</td>
            <td style="text-align:right;color:#7a88aa">{t['input']:,}</td>
            <td style="text-align:right;color:#39ff14">{t['output']:,}</td>
          </tr>"""
    return rows


def render_feature_costs(m):
    fc = m["feature_costs"]
    if not fc:
        return ""

    # Normalise — vibe-cost may write a list of {label, cost} dicts instead of a plain dict
    if isinstance(fc, list):
        try:
            fc = {item.get("label", item.get("name", str(i))): float(item.get("cost", item.get("cost_usd", 0)))
                  for i, item in enumerate(fc)}
        except Exception:
            return ""

    # Ensure all values are floats (dollar signs in values from bad JSON encoding)
    clean = {}
    for k, v in fc.items():
        try:
            clean[k] = float(str(v).replace("$", "").replace(",", "").strip())
        except Exception:
            pass
    fc = clean
    if not fc:
        return ""

    max_c        = max(fc.values())
    rows         = ""
    sorted_items = sorted(fc.items(), key=lambda x: x[1], reverse=True)
    for i, (label, cost) in enumerate(sorted_items):
        pct    = cost / m["total_cost"] * 100 if m["total_cost"] else 0
        colour = "#ffb800" if i == 0 else ("#39ff14" if i < 3 else "#7a88aa")
        rows  += f"""
  <div style="display:grid;grid-template-columns:220px 1fr 110px;align-items:center;gap:14px;padding:11px 16px;border-bottom:1px solid var(--line)">
    <div style="font-size:16px;color:#dde4f4">{label}</div>
    {bar(cost / max_c * 100, colour, 48)}
    <div style="text-align:right;font-size:18px;color:{colour}">${cost:.2f} <span style="font-size:13px;color:#7a88aa">{pct:.0f}%</span></div>
  </div>"""
    return f"""
<div style="font-size:12px;color:#39ff14;letter-spacing:3px;padding:9px 0 4px;display:flex;align-items:center;gap:8px;margin-bottom:0">
  <span style="flex:1;height:1px;background:var(--green2);opacity:0.35;display:block"></span>WHERE DID THE ${m['total_cost']:.2f} GO?<span style="flex:1;height:1px;background:var(--green2);opacity:0.35;display:block"></span>
</div>
<div style="background:var(--bg2);border:2px solid var(--line2);margin-bottom:5px">
  <div style="background:var(--bg3);border-bottom:2px solid var(--line2);padding:6px 14px;font-size:12px;color:var(--dim);letter-spacing:3px">COST BY FEATURE AREA</div>
  {rows}
</div>"""


def render_phase_summary(m):
    phases = m["phase_summary"]
    if not phases:
        return ""
    max_c = max((p.get("cost_usd", 0) for p in phases), default=1)
    rows  = ""
    for p in phases:
        st     = p.get("status", "not_started")
        s_col  = {"complete":"#39ff14","active":"#ffb800","not_started":"#7a88aa"}.get(st,"#7a88aa")
        s_lbl  = {"complete":"✓ done","active":"▶ active","not_started":"⬜ next"}.get(st,"—")
        cost   = p.get("cost_usd", 0)
        tasks  = p.get("tasks") or p.get("task_count") or p.get("tasks_completed") or 0
        b_col  = "#39ff14" if st == "complete" else "#ffb800"
        pct    = cost / max_c * 100 if max_c else 0
        rows  += f"""
        <tr>
          <td style="color:#dde4f4">{p.get('phase','')}</td>
          <td style="color:#7a88aa">{p.get('sessions',0)}</td>
          <td style="color:#7a88aa">{tasks}</td>
          <td style="color:#ffb800">${cost:.2f}</td>
          <td>{bar(pct, b_col, 28)}</td>
          <td style="color:{s_col}">{s_lbl}</td>
        </tr>"""
    return f"""
<div style="font-size:12px;color:#39ff14;letter-spacing:3px;padding:9px 0 4px;display:flex;align-items:center;gap:8px;margin-bottom:0">
  <span style="flex:1;height:1px;background:var(--green2);opacity:0.35;display:block"></span>PHASE BREAKDOWN<span style="flex:1;height:1px;background:var(--green2);opacity:0.35;display:block"></span>
</div>
<div style="background:var(--bg2);border:2px solid var(--line2);margin-bottom:5px">
  <table style="width:100%;border-collapse:collapse;font-size:16px">
    <thead><tr>
      <th style="font-size:12px;color:var(--dim);letter-spacing:2px;text-align:left;padding:6px 12px;border-bottom:2px solid var(--line2);background:var(--bg3);font-weight:400">Phase</th>
      <th style="font-size:12px;color:var(--dim);letter-spacing:2px;text-align:left;padding:6px 12px;border-bottom:2px solid var(--line2);background:var(--bg3);font-weight:400;width:60px">Sessions</th>
      <th style="font-size:12px;color:var(--dim);letter-spacing:2px;text-align:left;padding:6px 12px;border-bottom:2px solid var(--line2);background:var(--bg3);font-weight:400;width:60px">Tasks</th>
      <th style="font-size:12px;color:var(--dim);letter-spacing:2px;text-align:left;padding:6px 12px;border-bottom:2px solid var(--line2);background:var(--bg3);font-weight:400;width:80px">Cost</th>
      <th style="font-size:12px;color:var(--dim);letter-spacing:2px;text-align:left;padding:6px 12px;border-bottom:2px solid var(--line2);background:var(--bg3);font-weight:400">Burn</th>
      <th style="font-size:12px;color:var(--dim);letter-spacing:2px;text-align:left;padding:6px 12px;border-bottom:2px solid var(--line2);background:var(--bg3);font-weight:400;width:80px">Status</th>
    </tr></thead>
    <tbody>{rows}</tbody>
  </table>
</div>"""


def render_advice(m):
    SEV = {
        "ok":   ("2px solid #2bc010","rgba(57,255,20,0.07)","#2bc010","#39ff14","✓"),
        "warn": ("2px solid #cc9200","rgba(255,184,0,0.07)", "#cc9200","#ffb800","!"),
        "fix":  ("2px solid #880022","rgba(255,64,96,0.07)", "#880022","#ff4060","!!"),
    }
    html = ""

    # Use summary recommendations if present
    if m["summary_recs"]:
        for rec in m["summary_recs"]:
            bd,bg,bc,tc,ic = SEV.get(rec.get("severity","warn"), SEV["warn"])
            html += f"""
    <div style="border:{bd};background:{bg};margin-bottom:4px">
      <div style="display:flex;align-items:center;gap:12px;padding:8px 14px;border-bottom:1px solid {bc};font-size:16px">
        <span style="font-size:20px;width:26px;text-align:center;color:{tc}">{ic}</span>
        <span style="color:#dde4f4;flex:1">{rec.get('title','')}</span>
        <span style="font-size:13px;letter-spacing:1px;color:{tc}">{rec.get('saving','')}</span>
      </div>
      <div style="padding:10px 14px 12px 52px;font-size:16px;color:#7a88aa;line-height:1.7">{rec.get('body','')}</div>
    </div>"""
        return html

    # Fallback generic advice
    html += f"""
    <div style="border:2px solid #2bc010;background:rgba(57,255,20,0.07);margin-bottom:4px">
      <div style="display:flex;align-items:center;gap:12px;padding:8px 14px;border-bottom:1px solid #2bc010;font-size:16px">
        <span style="font-size:20px;width:26px;text-align:center;color:#39ff14">✓</span>
        <span style="color:#dde4f4;flex:1">Costs are healthy — your average of ${m['avg_task']:.2f} per task is solid</span>
        <span style="font-size:13px;letter-spacing:1px;color:#39ff14">on track</span>
      </div>
      <div style="padding:10px 14px 12px 52px;font-size:16px;color:#7a88aa;line-height:1.7">
        No session spiked unexpectedly. Your peak was <strong style="color:#dde4f4">{m['peak'].get('phase','peak session')}</strong>
        at <strong style="color:#dde4f4">${m['peak']['cost_usd']:.2f}</strong> for {m['peak']['tasks_completed']} tasks.
        Project is <strong style="color:#39ff14">{m['pct_complete']:.0f}% complete</strong> and tracking well.
      </div>
    </div>"""

    if "CP-01" in m["all_patterns"] or m["total_input"] / m["n_sessions"] > 100000:
        avg_in = m["total_input"] / m["n_sessions"] / 1000
        html += f"""
    <div style="border:2px solid #cc9200;background:rgba(255,184,0,0.07);margin-bottom:4px">
      <div style="display:flex;align-items:center;gap:12px;padding:8px 14px;border-bottom:1px solid #cc9200;font-size:16px">
        <span style="font-size:20px;width:26px;text-align:center;color:#ffb800">!</span>
        <span style="color:#dde4f4;flex:1">Claude re-reads the same project files from scratch every session</span>
        <span style="font-size:13px;letter-spacing:1px;color:#ffb800">save ~$0.10/session</span>
      </div>
      <div style="padding:10px 14px 12px 52px;font-size:16px;color:#7a88aa;line-height:1.7">
        Every session starts with roughly <strong style="color:#dde4f4">{avg_in:.0f}K tokens</strong> of reading overhead — your main project files loaded before any task runs.
        Splitting the codebase file by domain means each task loads only the half it needs. Est. saving: <strong style="color:#ffb800">~$0.08–0.12/session</strong>.
      </div>
    </div>"""

    html += """
    <div style="border:2px solid #cc9200;background:rgba(255,184,0,0.07);margin-bottom:4px">
      <div style="display:flex;align-items:center;gap:12px;padding:8px 14px;border-bottom:1px solid #cc9200;font-size:16px">
        <span style="font-size:20px;width:26px;text-align:center;color:#ffb800">!</span>
        <span style="color:#dde4f4;flex:1">Claude isn't reusing work between sessions — paying full price every time</span>
        <span style="font-size:13px;letter-spacing:1px;color:#ffb800">save 40–70% on reading</span>
      </div>
      <div style="padding:10px 14px 12px 52px;font-size:16px;color:#7a88aa;line-height:1.7">
        Claude has a built-in feature called <strong style="color:#dde4f4">prompt caching</strong> — unchanged files reused at 90% lower cost.
        Current cache saves: <strong style="color:#ff4060">$0.00</strong>. Most likely cause: CLAUDE.md is modified mid-session, resetting the cache each time.
        Keep the main instruction file stable during a session.
      </div>
    </div>"""

    if "CP-03" in m["all_patterns"]:
        html += """
    <div style="border:2px solid #2bc010;background:rgba(57,255,20,0.07);margin-bottom:4px">
      <div style="display:flex;align-items:center;gap:12px;padding:8px 14px;border-bottom:1px solid #2bc010;font-size:16px">
        <span style="font-size:20px;width:26px;text-align:center;color:#39ff14">✓</span>
        <span style="color:#dde4f4;flex:1">The output-heavy session was a one-time cost — future updates are cheap</span>
        <span style="font-size:13px;letter-spacing:1px;color:#39ff14">save ~$0.55/update</span>
      </div>
      <div style="padding:10px 14px 12px 52px;font-size:16px;color:#7a88aa;line-height:1.7">
        That session generated large files from scratch — a one-time build cost. Future incremental updates
        only re-process changed files, typically <strong style="color:#dde4f4">$0.04–0.08 each</strong>. Already sunk.
      </div>
    </div>"""

    return html


def render_forecast(m):
    if m["forecast_narrative"]:
        return m["forecast_narrative"]
    return (
        f"Based on your average of <strong style=\"color:#ffb800\">${m['avg_task']:.2f} per task</strong>, "
        f"the remaining <strong style=\"color:#ffb800\">{m['tasks_remaining']} tasks</strong> will likely cost "
        f"<strong style=\"color:#ffb800\">${m['remaining_low']:.2f}–${m['remaining_high']:.2f}</strong>. "
        f"That puts the total project between "
        f"<strong style=\"color:#ffb800\">${m['forecast_low']:.2f} and ${m['forecast_high']:.2f}</strong>. "
        f"Fixing the caching issue before your next session could save an additional "
        f"<strong style=\"color:#39ff14\">$0.20–0.40</strong> off that estimate."
    )


# ─── CSS ─────────────────────────────────────────────────────────────────────

CSS = """
@import url('https://fonts.googleapis.com/css2?family=VT323&family=Share+Tech+Mono&display=swap');
*,*::before,*::after{box-sizing:border-box;margin:0;padding:0}
:root{
  --bg:#1c2030;--bg2:#242840;--bg3:#2e3452;
  --line:#363c5a;--line2:#464e70;
  --green:#39ff14;--green2:#2bc010;--green-dim:rgba(57,255,20,0.07);
  --amber:#ffb800;--amber2:#cc9200;--amber-dim:rgba(255,184,0,0.07);
  --red:#ff4060;--red-dim:rgba(255,64,96,0.07);
  --blue:#00cfff;--blue-dim:rgba(0,207,255,0.05);
  --white:#dde4f4;--dim:#7a88aa;
  --font:'VT323','Share Tech Mono',monospace;
}
html{background:var(--bg);color:var(--white);font-family:var(--font);font-size:17px;line-height:1.5;overflow-x:hidden}
body{background:repeating-linear-gradient(0deg,rgba(57,255,20,0.012) 0px,rgba(57,255,20,0.012) 1px,transparent 1px,transparent 3px),var(--bg);min-height:100vh;overflow-x:hidden}
body::after{content:'';position:fixed;inset:0;pointer-events:none;z-index:9999;
  background:repeating-linear-gradient(0deg,transparent,transparent 2px,rgba(0,0,0,0.09) 2px,rgba(0,0,0,0.09) 3px)}
.shell{max-width:1280px;margin:0 auto;padding:20px 28px 64px}
.cg{color:var(--green)}.ca{color:var(--amber)}.cb{color:var(--blue)}.cr{color:var(--red)}.cd{color:var(--dim)}.cc{color:#00ffee}
.glow-g{text-shadow:0 0 10px var(--green),0 0 24px var(--green2)}
.glow-a{text-shadow:0 0 10px var(--amber),0 0 24px var(--amber2)}
.cur{display:inline-block;width:11px;height:19px;background:var(--green);box-shadow:0 0 8px var(--green);animation:blink 1s step-end infinite;vertical-align:middle}
@keyframes blink{50%{opacity:0}}
.prompt{font-size:15px;color:var(--dim);padding:0 0 10px;letter-spacing:1px}
.sym{color:var(--green)}.cmd{color:#00ffee}
.hdr{border:2px solid var(--green);box-shadow:0 0 20px rgba(57,255,20,0.14),inset 0 0 20px rgba(57,255,20,0.03);background:var(--bg2);padding:16px 22px;margin-bottom:5px;position:relative}
.hdr::before{content:'';position:absolute;top:0;left:0;right:0;height:2px;background:linear-gradient(90deg,transparent,var(--green),transparent);box-shadow:0 0 8px var(--green)}
.hdr-top{display:flex;align-items:flex-start;justify-content:space-between;margin-bottom:12px}
.ttl{font-size:50px;color:var(--green);letter-spacing:5px;text-shadow:0 0 12px var(--green),0 0 36px var(--green2),3px 3px 0 var(--green2);line-height:1}
.ttl em{color:var(--amber);font-style:normal;text-shadow:0 0 12px var(--amber),0 0 36px var(--amber2),3px 3px 0 var(--amber2)}
.ttl-sub{font-size:15px;color:var(--dim);letter-spacing:3px;margin-top:5px}
.total-lbl{font-size:12px;color:var(--dim);letter-spacing:3px;text-align:right}
.total-num{font-size:62px;color:var(--amber);letter-spacing:2px;line-height:1;text-shadow:0 0 14px var(--amber),0 0 36px var(--amber2),3px 3px 0 var(--amber2);text-align:right}
.total-sub{font-size:13px;color:var(--dim);letter-spacing:2px;text-align:right}
.rule{border:none;border-top:1px solid var(--green2);box-shadow:0 0 5px var(--green2);margin:10px 0 9px}
.meta{display:flex;gap:0;flex-wrap:wrap;font-size:15px}
.hm{padding:0 16px 0 0;margin-right:16px;border-right:1px solid var(--line2);color:var(--dim)}
.hm:last-child{border-right:none}.hm span{color:var(--white)}
.s6{display:grid;grid-template-columns:repeat(6,1fr);gap:5px;margin-bottom:5px}
.sc{background:var(--bg2);border:2px solid var(--line);padding:12px 14px}
.sl{font-size:12px;color:var(--dim);letter-spacing:2px;margin-bottom:4px}
.sv{font-size:30px;line-height:1;letter-spacing:0.5px}
.ss{font-size:13px;color:var(--dim);margin-top:3px;line-height:1.3}
.sum{background:var(--bg2);border:2px solid var(--line2);padding:18px 20px;margin-bottom:5px}
.sec{font-size:12px;color:var(--dim);letter-spacing:3px;border-bottom:1px solid var(--line);padding-bottom:7px;margin-bottom:13px}
.bt{font-size:18px;color:var(--white);line-height:1.8;letter-spacing:0.2px}
.bt strong{color:var(--amber)}.bt .good{color:var(--green)}.bt .warn{color:var(--amber)}
.g2{display:grid;grid-template-columns:1fr 1fr;gap:5px;margin-bottom:5px}
.g32{display:grid;grid-template-columns:3fr 2fr;gap:5px;margin-bottom:5px}
.pb2{background:var(--bg2);border:2px solid var(--line2)}
.pb2.gb{border-color:var(--green2);box-shadow:0 0 8px rgba(57,255,20,0.08)}
.pb2.ab{border-color:var(--amber2);box-shadow:0 0 8px rgba(255,184,0,0.08)}
.pb2.bb{border-color:#006688}
.ph{background:var(--bg3);border-bottom:2px solid var(--line2);padding:6px 14px;font-size:12px;color:var(--dim);letter-spacing:3px;display:flex;justify-content:space-between;align-items:center}
.ph.g{color:var(--green);border-bottom-color:var(--green2);background:rgba(57,255,20,0.04)}
.ph.a{color:var(--amber);border-bottom-color:var(--amber2);background:rgba(255,184,0,0.04)}
.ph.b{color:var(--blue);border-bottom-color:#006688}
.pb{padding:13px 14px}
.tt{width:100%;border-collapse:collapse;font-size:16px}
.tt th{font-size:12px;color:var(--dim);letter-spacing:2px;text-align:left;padding:6px 12px;border-bottom:2px solid var(--line2);background:var(--bg3);font-weight:400}
.tt td{padding:8px 12px;border-bottom:1px solid var(--line);vertical-align:middle}
.tt tr:last-child td{border-bottom:none}
.tt tr:hover td{background:var(--bg3)}
.cs{color:var(--green);border-color:var(--green2);background:var(--green-dim)}
.cm{color:var(--blue);border-color:#006688;background:var(--blue-dim)}
.cl{color:var(--amber);border-color:var(--amber2);background:var(--amber-dim)}
.div{font-size:12px;color:var(--green2);letter-spacing:3px;padding:9px 0 4px;display:flex;align-items:center;gap:8px;margin-bottom:0}
.div::before,.div::after{content:'';flex:1;height:1px;background:var(--green2);opacity:0.35}
.footer{margin-top:20px;border-top:2px solid var(--green2);box-shadow:0 -1px 8px rgba(57,255,20,0.07);padding-top:10px;display:flex;justify-content:space-between;font-size:13px;color:var(--dim);letter-spacing:1px}
"""


# ─── HTML ASSEMBLY ────────────────────────────────────────────────────────────

def generate_html(sessions, m, project_name, generated_at):
    at_glance    = render_at_a_glance(m)
    day_section  = render_day_by_day(m)
    sess_rows    = render_session_rows(sessions, m)
    task_rows    = render_top_tasks(m)
    advice       = render_advice(m)
    feature_sec  = render_feature_costs(m)
    phase_sec    = render_phase_summary(m)
    forecast     = render_forecast(m)

    i_bar = bar(m["input_pct"],  "#00cfff", 52)
    o_bar = bar(m["output_pct"], "#39ff14", 52)
    s_bar = bar(m["total_s"] / m["total_cost"] * 100 if m["total_cost"] else 0, "#39ff14", 48)
    mb    = bar(m["total_m"] / m["total_cost"] * 100 if m["total_cost"] else 0, "#00cfff", 48)
    l_bar = bar(m["total_l"] / m["total_cost"] * 100 if m["total_cost"] else 0, "#ffb800", 48)

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>vibe-ledger · {project_name}</title>
<style>{CSS}</style>
</head>
<body>
<div class="shell">

<div class="prompt"><span class="sym">~/{project_name} $</span><span class="cmd"> cost:</span> generate ledger<span class="cur"></span></div>

<div class="hdr">
  <div class="hdr-top">
    <div>
      <div class="ttl">VIBE-<em>LEDGER</em></div>
      <div class="ttl-sub">{project_name.upper()} &nbsp;·&nbsp; FULL PROJECT COST REPORT &nbsp;·&nbsp; ALL SESSIONS</div>
    </div>
    <div>
      <div class="total-lbl">TOTAL SPENT SO FAR</div>
      <div class="total-num glow-a">${m['total_cost']:.2f}</div>
      <div class="total-sub">estimate &nbsp;±25%</div>
    </div>
  </div>
  <hr class="rule">
  <div class="meta">
    <div class="hm">Sessions <span>{m['n_sessions']}</span></div>
    <div class="hm">Tasks done <span>{m['total_tasks']}</span></div>
    <div class="hm">Dates <span>{m['date_range']}</span></div>
    <div class="hm">Tokens processed <span>{m['total_tokens']:,}</span></div>
    <div class="hm">Clean sessions <span class="cg">{m['clean_sessions']} / {m['n_sessions']}</span></div>
    <div class="hm">Build progress <span class="cg">{m['pct_complete']:.0f}% complete</span></div>
  </div>
</div>

<div class="s6">
  <div class="sc" style="border-color:var(--amber2)">
    <div class="sl">AVG COST / TASK</div><div class="sv ca">${m['avg_task']:.2f}</div>
    <div class="ss">across all {m['total_tasks']} tasks</div>
  </div>
  <div class="sc" style="border-color:var(--green2)">
    <div class="sl">SMALL TASK AVG</div><div class="sv cg">${m['avg_s']:.2f}</div>
    <div class="ss">{m['count_s']} small tasks done</div>
  </div>
  <div class="sc" style="border-color:#006688">
    <div class="sl">MEDIUM TASK AVG</div><div class="sv cb">${m['avg_m']:.2f}</div>
    <div class="ss">{m['count_m']} medium tasks done</div>
  </div>
  <div class="sc" style="border-color:var(--amber2)">
    <div class="sl">LARGE TASK AVG</div><div class="sv ca">${m['avg_l']:.2f}</div>
    <div class="ss">{m['count_l']} large tasks done</div>
  </div>
  <div class="sc" style="border-color:var(--green2)">
    <div class="sl">PEAK SESSION</div><div class="sv ca">${m['peak']['cost_usd']:.2f}</div>
    <div class="ss">{m['peak']['tasks_completed']} tasks · {m['peak']['session_id']}</div>
  </div>
  <div class="sc" style="border-color:#880022">
    <div class="sl">CACHE SAVINGS</div><div class="sv cr">$0.00</div>
    <div class="ss">potential: unlock caching</div>
  </div>
</div>

<div class="sum">
  <div class="sec">AT A GLANCE</div>
  <div class="bt">{at_glance}</div>
</div>

<div class="g2">
  <div class="pb2 gb">
    <div class="ph g">DAY BY DAY</div>
    <div class="pb">{day_section}</div>
  </div>
  <div class="pb2 ab">
    <div class="ph a">TASK SIZE BREAKDOWN</div>
    <div class="pb">
      <div style="margin-bottom:12px">
        <div style="display:flex;justify-content:space-between;font-size:16px;margin-bottom:4px">
          <span style="color:#dde4f4">Small tasks <span style="color:#7a88aa;font-size:14px">(quick fixes, config)</span></span>
          <span style="color:#39ff14">${m['total_s']:.2f}</span>
        </div>
        {s_bar}
        <div style="font-size:14px;color:#7a88aa;margin-top:2px">{m['count_s']} tasks · ${m['avg_s']:.2f} avg · {m['total_s']/m['total_cost']*100:.0f}% of spend</div>
      </div>
      <div style="margin-bottom:12px">
        <div style="display:flex;justify-content:space-between;font-size:16px;margin-bottom:4px">
          <span style="color:#dde4f4">Medium tasks <span style="color:#7a88aa;font-size:14px">(features, screens)</span></span>
          <span style="color:#00cfff">${m['total_m']:.2f}</span>
        </div>
        {mb}
        <div style="font-size:14px;color:#7a88aa;margin-top:2px">{m['count_m']} tasks · ${m['avg_m']:.2f} avg · {m['total_m']/m['total_cost']*100:.0f}% of spend</div>
      </div>
      <div>
        <div style="display:flex;justify-content:space-between;font-size:16px;margin-bottom:4px">
          <span style="color:#dde4f4">Large tasks <span style="color:#7a88aa;font-size:14px">(complex features)</span></span>
          <span style="color:#ffb800">${m['total_l']:.2f}</span>
        </div>
        {l_bar}
        <div style="font-size:14px;color:#7a88aa;margin-top:2px">{m['count_l']} tasks · ${m['avg_l']:.2f} avg · {m['total_l']/m['total_cost']*100:.0f}% of spend</div>
      </div>
    </div>
  </div>
</div>

<div class="g32">
  <div class="pb2 gb">
    <div class="ph g">SESSION BURN</div>
    <div style="padding:0">
      <table class="tt">
        <thead><tr>
          <th style="width:110px">Session</th><th>What happened</th>
          <th style="width:80px">Tasks</th><th style="width:120px">Cost indicator</th>
          <th style="text-align:right;width:70px">Cost</th>
        </tr></thead>
        <tbody>{sess_rows}</tbody>
      </table>
      <div style="padding:8px 14px;border-top:1px solid var(--line);font-size:14px;color:#7a88aa">
        Each dot ≈ ${m['dot_value']:.2f} &nbsp;·&nbsp; 7 filled = peak &nbsp;·&nbsp;
        <span style="color:#39ff14">Green</span> on track &nbsp;
        <span style="color:#ff4060">Red</span> peak &nbsp;
        <span style="color:#ffb800">Amber</span> output-heavy &nbsp;
        <span style="color:#00cfff">Blue</span> review
      </div>
    </div>
  </div>

  <div style="display:flex;flex-direction:column;gap:5px">
    <div class="pb2 bb">
      <div class="ph b">HOW TOKENS WERE USED</div>
      <div class="pb">
        <div style="font-size:16px;color:#7a88aa;margin-bottom:12px;line-height:1.6">
          Claude processed <strong style="color:#dde4f4">{m['total_tokens']:,} tokens</strong> in total.
        </div>
        <div style="margin-bottom:10px">
          <div style="display:flex;justify-content:space-between;font-size:16px;margin-bottom:3px">
            <span style="color:#dde4f4">Reading (input)</span><span style="color:#00cfff">{m['total_input']:,} &nbsp; {m['input_pct']:.0f}%</span>
          </div>
          {i_bar}
          <div style="font-size:13px;color:#7a88aa;margin-top:2px">Cost of Claude reading your code and docs — ${m['total_cost']*0.9:.2f} of ${m['total_cost']:.2f}</div>
        </div>
        <div style="margin-bottom:10px">
          <div style="display:flex;justify-content:space-between;font-size:16px;margin-bottom:3px">
            <span style="color:#dde4f4">Writing (output)</span><span style="color:#39ff14">{m['total_output']:,} &nbsp; {m['output_pct']:.0f}%</span>
          </div>
          {o_bar}
          <div style="font-size:13px;color:#7a88aa;margin-top:2px">Cost of Claude writing code and plans — ${m['total_cost']*0.1:.2f} of ${m['total_cost']:.2f}</div>
        </div>
        <div>
          <div style="display:flex;justify-content:space-between;font-size:16px;margin-bottom:3px">
            <span style="color:#ff4060">Reused from cache</span><span style="color:#ff4060">0 &nbsp; 0%</span>
          </div>
          <span style="font-family:'VT323',monospace;font-size:15px;letter-spacing:0;color:#363c5a">{'░'*52}</span>
          <div style="font-size:13px;color:#ff4060;margin-top:2px">Nothing reused — paying full price every session</div>
        </div>
      </div>
    </div>
    <div class="pb2 ab">
      <div class="ph a">EFFICIENCY METRICS</div>
      <div class="pb" style="font-size:16px">
        <div style="display:flex;justify-content:space-between;padding:5px 0;border-bottom:1px solid var(--line)">
          <span style="color:#7a88aa">Tokens per task</span><span style="color:#dde4f4">~{m['tokens_per_task']:,.0f}</span>
        </div>
        <div style="display:flex;justify-content:space-between;padding:5px 0;border-bottom:1px solid var(--line)">
          <span style="color:#7a88aa">Read-to-write ratio</span>
          <span style="color:#dde4f4">{m['io_ratio']:.0f}:1 <span style="font-size:13px;color:#7a88aa">(under 10:1 is healthy)</span></span>
        </div>
        <div style="display:flex;justify-content:space-between;padding:5px 0;border-bottom:1px solid var(--line)">
          <span style="color:#7a88aa">Code written per $1</span><span style="color:#39ff14">~{m['output_per_dollar']:,.0f} tokens</span>
        </div>
        <div style="display:flex;justify-content:space-between;padding:5px 0;border-bottom:1px solid var(--line)">
          <span style="color:#7a88aa">Cheapest session</span>
          <span style="color:#39ff14">{m['cheapest']['session_id']} · ${m['cheapest']['cost_usd']:.2f}</span>
        </div>
        <div style="display:flex;justify-content:space-between;padding:5px 0">
          <span style="color:#7a88aa">Patterns detected</span>
          <span style="color:{'#ff4060' if m['all_patterns'] else '#39ff14'}">{', '.join(set(m['all_patterns'])) if m['all_patterns'] else 'none'}</span>
        </div>
      </div>
    </div>
  </div>
</div>

{phase_sec}
{feature_sec}

<div class="div">MOST EXPENSIVE TASKS</div>
<div class="pb2" style="margin-bottom:5px">
  <table class="tt">
    <thead><tr>
      <th>Task</th><th>Phase</th><th>Size</th>
      <th style="text-align:right">Cost</th>
      <th style="text-align:right">Tokens read</th>
      <th style="text-align:right">Tokens written</th>
    </tr></thead>
    <tbody>{task_rows}</tbody>
  </table>
</div>

<div class="div">WHAT YOU COULD DO DIFFERENTLY</div>
{advice}

<div class="pb2 ab" style="margin-bottom:5px">
  <div class="ph a">WHAT'S LEFT AND WHAT IT WILL COST</div>
  <div class="pb">
    <div style="font-size:18px;color:#dde4f4;line-height:1.8">{forecast}</div>
  </div>
</div>

<div class="footer">
  <div>
    <div class="cmd">~/{project_name} $ cost: generate ledger</div>
    <div style="margin-top:4px">Regenerate any time &nbsp;·&nbsp; Precise mode: <span class="cmd">cost: [paste /cost output]</span></div>
  </div>
  <div style="text-align:right">
    <div>vibe-ledger v1.1 &nbsp;·&nbsp; BetaCraft</div>
    <div>Generated {generated_at}</div>
    <div style="color:#7a88aa">vibe/cost/history.json &nbsp;·&nbsp; {m['n_sessions']} sessions</div>
  </div>
</div>

</div>
</body>
</html>"""


# ─── MAIN ─────────────────────────────────────────────────────────────────────

def main():
    root = find_project_root()
    if not root:
        print("ERROR: vibe/cost/history.json not found in current or parent directories.")
        print("Make sure you're inside a vibe-* project and have run cost: at least once.")
        sys.exit(1)

    sessions = load_history(root)
    if not sessions:
        print("ERROR: history.json is empty — run cost: after at least one session first.")
        sys.exit(1)

    summary      = load_summary(root)
    m            = compute_metrics(sessions, summary)
    project_name = summary.get("project_name") or root.name
    generated_at = datetime.now().strftime("%b %d %Y, %H:%M")

    try:
        html = generate_html(sessions, m, project_name, generated_at)
    except Exception as e:
        print(f"⚠  summary.json caused an error ({e}) — regenerating without it")
        m    = compute_metrics(sessions, {})
        html = generate_html(sessions, m, project_name, generated_at)

    out_dir = root / "vibe" / "cost" / "ledger"
    out_dir.mkdir(parents=True, exist_ok=True)
    out_path = out_dir / "index.html"
    out_path.write_text(generate_html(sessions, m, project_name, generated_at), encoding="utf-8")

    print(f"✅  vibe-ledger generated: {out_path}")
    print(f"    Project : {project_name}")
    print(f"    Sessions: {m['n_sessions']}  ·  Tasks: {m['total_tasks']}  ·  Total: ${m['total_cost']:.2f}")
    has_summary = bool(summary)
    print(f"    Summary : {'summary.json loaded ✓' if has_summary else 'no summary.json — using computed fallbacks'}")

    try:
        webbrowser.open(out_path.as_uri())
        print("    Opening in browser...")
    except Exception:
        print(f"    Open manually: {out_path}")


if __name__ == "__main__":
    main()
