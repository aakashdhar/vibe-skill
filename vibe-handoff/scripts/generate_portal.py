#!/usr/bin/env python3
"""
vibe-handoff portal generator
Reads all .md files in a handoff folder and generates index.html
Clean, client-readable, light mode — optimised for sharing with non-technical stakeholders.
Zero dependencies — pure Python stdlib.

Usage:
  python3 generate_portal.py [handoff-folder-path]
  If no path given, searches for the most recent vibe/handoff/* folder.
"""

import re, sys, webbrowser
from pathlib import Path
from datetime import datetime


# ─── DOCUMENT METADATA ───────────────────────────────────────────────────────

# Maps filename → (display title, short description, audience)
DOC_META = {
    # client mode
    "DELIVERY.md":           ("Project Delivery",        "What was built and key decisions",           "client"),
    "FEATURES.md":           ("Feature Walkthrough",     "Screen-by-screen guide to everything built", "client"),
    "KNOWN_ISSUES.md":       ("Known Issues",            "Limitations, bugs, and technical debt",      "client"),
    "CREDENTIALS.md":        ("Credentials & Access",    "Placeholder list — fill before sharing",     "client"),
    "SUPPORT.md":            ("Support & Escalation",    "How to get help when things break",          "client"),
    "ROADMAP.md":            ("Roadmap",                 "What was deferred and what comes next",      "client"),
    "SIGN_OFF_CHECKLIST.md": ("Sign-Off Checklist",      "Work through this on the sign-off call",     "client"),
    # milestone mode
    "PHASE_DELIVERY.md":     ("Phase Delivery",          "What was built this phase",                  "milestone"),
    "PHASE_SIGN_OFF.md":     ("Phase Sign-Off",          "Checklist for this milestone",               "milestone"),
    "NEXT_PHASE.md":         ("Next Phase",              "What's coming and what to expect",           "milestone"),
    # dev mode
    "ONBOARDING.md":         ("Onboarding Guide",        "Start here — full environment setup",        "dev"),
    "ARCHITECTURE_GUIDE.md": ("Architecture Guide",      "How the system works and why",               "dev"),
    "ACTIVE_CONTEXT.md":     ("Active Context",          "Where we are and what's in progress",        "dev"),
    "GOTCHAS.md":            ("Gotchas",                 "Tribal knowledge and things that bite",      "dev"),
    # internal mode
    "CONTEXT_DUMP.md":       ("Context Dump",            "Complete brain dump from outgoing dev",      "internal"),
    "ACTIVE_TASKS.md":       ("Active Tasks",            "Exactly where to pick up",                   "internal"),
    "DECISIONS_LOG.md":      ("Decisions Log",           "Recent decisions with reasoning",            "internal"),
    "OPEN_QUESTIONS.md":     ("Open Questions",          "Unresolved items needing attention",         "internal"),
    # maintenance mode
    "SYSTEM_OVERVIEW.md":    ("System Overview",         "What runs where, how it fits together",      "maintenance"),
    "RUNBOOK.md":            ("Runbook",                 "Common operations, deployments, rollbacks",  "maintenance"),
    "MONITORING.md":         ("Monitoring",              "What to watch, alerts, thresholds",          "maintenance"),
    "ESCALATION.md":         ("Escalation",              "When to call BetaCraft, what to send",       "maintenance"),
}

# Preferred display order per mode
DOC_ORDER = {
    "client":      ["DELIVERY.md","FEATURES.md","KNOWN_ISSUES.md","ROADMAP.md","CREDENTIALS.md","SUPPORT.md","SIGN_OFF_CHECKLIST.md"],
    "milestone":   ["PHASE_DELIVERY.md","KNOWN_ISSUES.md","PHASE_SIGN_OFF.md","NEXT_PHASE.md"],
    "dev":         ["ONBOARDING.md","ARCHITECTURE_GUIDE.md","ACTIVE_CONTEXT.md","GOTCHAS.md","CREDENTIALS.md"],
    "internal":    ["CONTEXT_DUMP.md","ACTIVE_TASKS.md","DECISIONS_LOG.md","OPEN_QUESTIONS.md"],
    "maintenance": ["SYSTEM_OVERVIEW.md","RUNBOOK.md","MONITORING.md","KNOWN_ISSUES.md","CREDENTIALS.md","ARCHITECTURE_GUIDE.md","ESCALATION.md"],
}

# Warn before sharing these in client packages
INTERNAL_ONLY = {"CONTEXT_DUMP.md","GOTCHAS.md","OPEN_QUESTIONS.md","ACTIVE_TASKS.md"}


# ─── PATH HELPERS ────────────────────────────────────────────────────────────

def find_handoff_folder(given_path=None):
    if given_path:
        p = Path(given_path)
        if p.exists() and p.is_dir():
            return p
        print(f"ERROR: path not found: {given_path}")
        sys.exit(1)

    # Search from cwd upward for vibe/handoff/
    cwd = Path.cwd()
    for root in [cwd, *cwd.parents]:
        handoff_root = root / "vibe" / "handoff"
        if handoff_root.exists():
            # Find most recently modified subfolder
            folders = [f for f in handoff_root.iterdir() if f.is_dir() and not f.name.startswith(".")]
            if folders:
                return max(folders, key=lambda f: f.stat().st_mtime)

    print("ERROR: No vibe/handoff/ folder found. Run from inside a vibe-* project.")
    sys.exit(1)


def detect_mode(folder_name):
    name = folder_name.lower()
    for mode in ["client","milestone","dev","internal","maintenance"]:
        if mode in name:
            return mode
    return "client"


def load_docs(folder, mode):
    """Load all .md files in folder, sorted by preferred order."""
    order = DOC_ORDER.get(mode, [])
    found = {f.name: f for f in folder.glob("*.md")}

    # Ordered first, then any extras alphabetically
    result = []
    for name in order:
        if name in found:
            result.append(found[name])
    for name, path in sorted(found.items()):
        if path not in result:
            result.append(path)
    return result


# ─── MINIMAL MD → HTML ───────────────────────────────────────────────────────

def md_to_html(text):
    """Convert markdown to HTML. Handles headings, bold/italic, lists, tables, code, checkboxes, hr."""
    lines = text.split("\n")
    out = []
    in_ul = False
    in_ol = False
    in_table = False
    table_rows = []
    in_pre = False
    pre_buf = []

    def flush_list():
        nonlocal in_ul, in_ol
        if in_ul: out.append("</ul>"); in_ul = False
        if in_ol: out.append("</ol>"); in_ol = False

    def flush_table():
        nonlocal in_table, table_rows
        if not table_rows: return
        html = '<table class="md-table"><thead><tr>'
        for cell in table_rows[0]:
            html += f"<th>{cell.strip()}</th>"
        html += "</tr></thead><tbody>"
        for row in table_rows[2:]:
            html += "<tr>" + "".join(f"<td>{c.strip()}</td>" for c in row) + "</tr>"
        html += "</tbody></table>"
        out.append(html)
        in_table = False
        table_rows.clear()

    def inline(s):
        # Checkboxes
        s = re.sub(r'\[x\]', '<span class="cb-done">✓</span>', s, flags=re.I)
        s = re.sub(r'\[ \]', '<span class="cb-empty"></span>', s)
        # Code inline
        s = re.sub(r'`([^`]+)`', r'<code>\1</code>', s)
        # Bold + italic
        s = re.sub(r'\*\*\*(.+?)\*\*\*', r'<strong><em>\1</em></strong>', s)
        s = re.sub(r'\*\*(.+?)\*\*', r'<strong>\1</strong>', s)
        s = re.sub(r'\*(.+?)\*', r'<em>\1</em>', s)
        # Links
        s = re.sub(r'\[([^\]]+)\]\(([^)]+)\)', r'<a href="\2" target="_blank">\1</a>', s)
        return s

    i = 0
    while i < len(lines):
        line = lines[i]

        # Fenced code block
        if line.strip().startswith("```"):
            if in_pre:
                out.append("<br>".join(pre_buf) + "</code></pre>")
                pre_buf = []
                in_pre = False
            else:
                flush_list(); flush_table()
                lang = line.strip()[3:].strip()
                out.append(f'<pre class="code-block"><code class="lang-{lang}">')
                in_pre = True
            i += 1
            continue

        if in_pre:
            pre_buf.append(line.replace("&","&amp;").replace("<","&lt;").replace(">","&gt;"))
            i += 1
            continue

        # Table row
        if "|" in line and line.strip().startswith("|"):
            flush_list()
            if not in_table:
                in_table = True
            row = [c for c in line.split("|")[1:-1]]
            table_rows.append(row)
            i += 1
            continue
        else:
            if in_table:
                flush_table()

        # HR
        if re.match(r'^[-*_]{3,}\s*$', line.strip()):
            flush_list()
            out.append('<hr class="md-hr">')
            i += 1
            continue

        # Headings
        m = re.match(r'^(#{1,4})\s+(.+)', line)
        if m:
            flush_list()
            level = len(m.group(1))
            tag = f"h{min(level+1, 4)}"
            cls = f"md-h{level}"
            out.append(f'<{tag} class="{cls}">{inline(m.group(2))}</{tag}>')
            i += 1
            continue

        # Blockquote
        if line.startswith(">"):
            flush_list()
            content = line.lstrip("> ").strip()
            out.append(f'<blockquote class="md-quote">{inline(content)}</blockquote>')
            i += 1
            continue

        # Unordered list
        m = re.match(r'^(\s*)[*\-+]\s+(.+)', line)
        if m:
            if not in_ul:
                flush_list()
                out.append("<ul>")
                in_ul = True
            content = inline(m.group(2))
            out.append(f"<li>{content}</li>")
            i += 1
            continue

        # Ordered list
        m = re.match(r'^(\s*)\d+\.\s+(.+)', line)
        if m:
            if not in_ol:
                flush_list()
                out.append("<ol>")
                in_ol = True
            out.append(f"<li>{inline(m.group(2))}</li>")
            i += 1
            continue

        # Paragraph / blank
        flush_list()
        stripped = line.strip()
        if not stripped:
            out.append("")
        else:
            out.append(f"<p>{inline(stripped)}</p>")
        i += 1

    flush_list()
    flush_table()
    if in_pre:
        out.append("<br>".join(pre_buf) + "</code></pre>")

    return "\n".join(out)


# ─── CSS ─────────────────────────────────────────────────────────────────────

CSS = """
*,*::before,*::after{box-sizing:border-box;margin:0;padding:0}
:root{
  --paper:#faf8f4;--paper2:#f4f1eb;--paper3:#ede9e1;
  --ink:#1a1710;--ink2:#3d3a33;--ink3:#7a756a;--ink4:#b0aa9e;
  --accent:#b0412e;--accent2:#8c3122;--gold:#c9922a;--rule:#ddd8cf;
  --serif:'Cormorant Garamond',Georgia,serif;
  --sans:'DM Sans',system-ui,sans-serif;
  --mono:'DM Mono',monospace;
}
html{background:var(--paper);color:var(--ink);font-family:var(--sans);font-size:16px;line-height:1.7;scroll-behavior:smooth}
body{display:flex;min-height:100vh}

/* SIDEBAR */
.sidebar{
  position:fixed;top:0;left:0;bottom:0;width:240px;
  background:var(--ink);padding:0;display:flex;flex-direction:column;
  z-index:100;overflow-y:auto;flex-shrink:0;
}
.sidebar-brand{padding:32px 24px 28px;border-bottom:1px solid rgba(255,255,255,0.08)}
.brand-name{font-family:var(--serif);font-size:20px;font-weight:500;color:#fff;letter-spacing:0.02em;line-height:1.2}
.brand-label{font-size:10px;letter-spacing:0.16em;text-transform:uppercase;color:rgba(255,255,255,0.35);margin-top:5px;font-family:var(--sans)}
.brand-date{font-size:11px;color:rgba(255,255,255,0.25);margin-top:3px;font-family:var(--mono)}
.sidebar-nav{flex:1;padding:16px 12px}
.nav-group{margin-bottom:4px}
.nav-group-label{font-size:9px;letter-spacing:0.18em;text-transform:uppercase;color:rgba(255,255,255,0.25);padding:10px 14px 5px;font-family:var(--sans);font-weight:500}
.nav-link{
  display:flex;align-items:center;gap:10px;padding:9px 14px;
  color:rgba(255,255,255,0.5);text-decoration:none;font-size:13px;
  border-radius:6px;border-left:2px solid transparent;
  transition:all 0.14s;font-family:var(--sans);line-height:1.3;
}
.nav-link:hover{color:#fff;background:rgba(255,255,255,0.07)}
.nav-link.active{color:#fff;background:rgba(255,255,255,0.09);border-left-color:var(--accent)}
.nav-num{font-family:var(--mono);font-size:10px;color:rgba(255,255,255,0.2);flex-shrink:0;width:18px}
.sidebar-foot{padding:20px 24px;border-top:1px solid rgba(255,255,255,0.08);font-size:11px;color:rgba(255,255,255,0.2);font-family:var(--mono);line-height:1.6}

/* TOPBAR */
.topbar{
  position:fixed;top:0;left:240px;right:0;height:44px;
  background:rgba(250,248,244,0.95);backdrop-filter:blur(8px);
  border-bottom:1px solid var(--rule);z-index:90;
  display:flex;align-items:center;justify-content:space-between;
  padding:0 48px;
}
.topbar-left{font-family:var(--mono);font-size:11px;color:var(--ink4)}
.topbar-right{display:flex;gap:10px}
.topbar-btn{
  font-family:var(--sans);font-size:11px;color:var(--accent);
  text-decoration:none;border:1px solid var(--accent);
  padding:4px 12px;background:none;cursor:pointer;
  transition:all 0.12s;letter-spacing:0.03em;
}
.topbar-btn:hover{background:var(--accent);color:#fff}

/* MAIN */
.main{margin-left:240px;padding-top:44px;flex:1;min-width:0}

/* HERO */
.hero{
  background:var(--ink);padding:72px 64px 64px;position:relative;overflow:hidden;
}
.hero::before{
  content:'';position:absolute;top:-80px;right:-80px;width:360px;height:360px;
  background:radial-gradient(circle,rgba(176,65,46,0.22) 0%,transparent 68%);
  pointer-events:none;
}
.hero::after{
  content:'';position:absolute;bottom:0;left:0;right:0;height:1px;
  background:linear-gradient(90deg,var(--accent),transparent 55%);
}
.hero-tag{font-size:10px;letter-spacing:0.18em;text-transform:uppercase;color:var(--accent);font-family:var(--sans);margin-bottom:18px;font-weight:500}
.hero-title{font-family:var(--serif);font-size:60px;font-weight:300;color:#fff;line-height:1.05;letter-spacing:-0.01em}
.hero-title em{font-style:italic;color:rgba(255,255,255,0.5)}
.hero-desc{font-size:15px;color:rgba(255,255,255,0.42);margin-top:16px;max-width:540px;line-height:1.65;font-family:var(--sans)}
.hero-meta{display:flex;gap:28px;margin-top:36px;padding-top:28px;border-top:1px solid rgba(255,255,255,0.08)}
.meta-item{}
.meta-label{font-size:10px;letter-spacing:0.14em;text-transform:uppercase;color:rgba(255,255,255,0.28);font-family:var(--sans)}
.meta-value{font-size:14px;color:rgba(255,255,255,0.65);margin-top:4px;font-family:var(--sans)}

/* DOC INDEX */
.doc-index{padding:40px 64px;background:var(--paper2);border-bottom:1px solid var(--rule)}
.index-label{font-size:10px;letter-spacing:0.16em;text-transform:uppercase;color:var(--ink3);margin-bottom:16px;font-family:var(--sans);font-weight:500}
.index-grid{display:grid;gap:1px;background:var(--rule);border:1px solid var(--rule)}
.index-item{
  background:var(--paper);padding:18px 20px;
  text-decoration:none;transition:background 0.12s;display:block;
}
.index-item:hover{background:var(--paper2)}
.index-num{font-family:var(--mono);font-size:10px;color:var(--ink4);margin-bottom:6px;letter-spacing:0.08em}
.index-title{font-family:var(--serif);font-size:15px;color:var(--ink);font-weight:500;line-height:1.3}
.index-desc{font-size:12px;color:var(--ink3);margin-top:3px;line-height:1.4}

/* SECTIONS */
.doc-section{padding:64px;border-bottom:1px solid var(--rule);scroll-margin-top:60px}
.doc-section:last-child{border-bottom:none}
.doc-section.alt{background:var(--paper2)}
.sec-tag{
  font-size:10px;letter-spacing:0.16em;text-transform:uppercase;
  color:var(--accent);font-family:var(--sans);font-weight:500;
  margin-bottom:10px;display:flex;align-items:center;gap:8px;
}
.sec-tag::after{content:'';width:32px;height:1px;background:var(--accent);opacity:0.4}
.sec-title{
  font-family:var(--serif);font-size:42px;font-weight:400;
  color:var(--ink);line-height:1.1;letter-spacing:-0.01em;margin-bottom:36px;
}
.sec-title em{font-style:italic;color:var(--ink3)}
.doc-body{max-width:760px}

/* MD CONTENT STYLES */
.md-h1{font-family:var(--serif);font-size:34px;font-weight:400;color:var(--ink);margin:40px 0 16px;line-height:1.15}
.md-h2{font-family:var(--serif);font-size:24px;font-weight:500;color:var(--ink);margin:36px 0 14px;padding-bottom:10px;border-bottom:1.5px solid var(--accent)}
.md-h3{font-family:var(--serif);font-size:19px;font-weight:500;color:var(--ink);margin:28px 0 10px}
.md-h4{font-family:var(--sans);font-size:13px;font-weight:500;color:var(--ink);margin:22px 0 8px;letter-spacing:0.06em;text-transform:uppercase}
.doc-body p{font-size:15px;color:var(--ink2);line-height:1.85;margin-bottom:16px}
.doc-body p:last-child{margin-bottom:0}
.doc-body p strong{color:var(--ink);font-weight:500}
.doc-body ul,.doc-body ol{margin:12px 0 16px 20px}
.doc-body li{font-size:15px;color:var(--ink2);line-height:1.75;margin-bottom:6px}
.doc-body li strong{color:var(--ink);font-weight:500}
.doc-body blockquote,.md-quote{
  border-left:3px solid var(--gold);padding:12px 18px;
  margin:18px 0;background:var(--paper2);font-size:14px;color:var(--ink3);
  font-family:var(--sans);line-height:1.65;
}
code{font-family:var(--mono);font-size:12.5px;background:var(--paper3);padding:1px 6px;border:1px solid var(--rule);color:var(--accent2)}
.code-block{
  background:var(--ink);padding:20px 24px;margin:18px 0;overflow-x:auto;
  border-radius:2px;
}
.code-block code{background:none;border:none;color:rgba(255,255,255,0.8);font-size:13px;padding:0}
.md-hr{border:none;border-top:1px solid var(--rule);margin:32px 0}
.md-table{width:100%;border-collapse:collapse;margin:16px 0;font-size:14px}
.md-table th{text-align:left;padding:9px 14px;font-size:10px;letter-spacing:0.1em;text-transform:uppercase;color:var(--ink3);background:var(--paper3);border-bottom:2px solid var(--rule);font-weight:400;font-family:var(--sans)}
.md-table td{padding:10px 14px;border-bottom:1px solid var(--rule);color:var(--ink2);vertical-align:top;line-height:1.55}
.md-table td:first-child{font-family:var(--mono);font-size:12px;color:var(--accent2)}
.md-table tr:last-child td{border-bottom:none}
.md-table tr:hover td{background:var(--paper2)}
.cb-done{
  display:inline-flex;align-items:center;justify-content:center;
  width:16px;height:16px;background:var(--ink);color:#fff;
  font-size:10px;font-weight:700;margin-right:6px;flex-shrink:0;
}
.cb-empty{
  display:inline-block;width:16px;height:16px;
  border:1.5px solid var(--ink4);margin-right:6px;flex-shrink:0;vertical-align:middle;
}
.doc-body li:has(.cb-empty),.doc-body li:has(.cb-done){
  list-style:none;display:flex;align-items:flex-start;margin-left:-20px;padding-left:0;
}

/* WARN BOX */
.warn-box{
  background:#fff8f0;border:1px solid #f0c080;border-left:4px solid var(--gold);
  padding:14px 18px;margin-bottom:24px;font-size:14px;color:#5a3a00;
  line-height:1.65;font-family:var(--sans);
}

/* PRINT */
@media print{
  .sidebar,.topbar{display:none}
  .main{margin-left:0;padding-top:0}
  .doc-section{padding:40px;page-break-inside:avoid}
  .doc-section+.doc-section{page-break-before:always}
  .hero{padding:48px 40px}
}
"""


# ─── HTML ASSEMBLY ────────────────────────────────────────────────────────────

def doc_anchor(filename):
    return filename.replace(".","_").lower()

def nav_group_label(mode):
    return {
        "client":      "Client Package",
        "milestone":   "Milestone Package",
        "dev":         "Developer Package",
        "internal":    "Internal Package",
        "maintenance": "Maintenance Package",
    }.get(mode, "Documents")

def generate_html(docs, folder, mode, project_name, generated_at):
    folder_date = folder.name
    doc_count   = len(docs)
    has_credentials = any(d.name == "CREDENTIALS.md" for d in docs)

    # Build nav items
    nav_items_html = ""
    for i, doc in enumerate(docs):
        meta  = DOC_META.get(doc.name, (doc.stem.replace("_"," ").title(), "", ""))
        title = meta[0]
        anch  = doc_anchor(doc.name)
        nav_items_html += f'<a href="#{anch}" class="nav-link" data-section="{anch}"><span class="nav-num">{i+1:02d}</span>{title}</a>\n'

    # Build doc index grid (max 4 cols)
    cols = min(4, doc_count) if doc_count >= 4 else doc_count
    index_items_html = ""
    for i, doc in enumerate(docs):
        meta  = DOC_META.get(doc.name, (doc.stem.replace("_"," ").title(), "", ""))
        title, desc = meta[0], meta[1]
        anch  = doc_anchor(doc.name)
        index_items_html += f'''
      <a href="#{anch}" class="index-item">
        <div class="index-num">{i+1:02d}</div>
        <div class="index-title">{title}</div>
        <div class="index-desc">{desc}</div>
      </a>'''

    # Build document sections
    sections_html = ""
    for i, doc in enumerate(docs):
        meta  = DOC_META.get(doc.name, (doc.stem.replace("_"," ").title(), "", ""))
        title = meta[0]
        anch  = doc_anchor(doc.name)
        alt   = " alt" if i % 2 == 1 else ""

        raw  = doc.read_text(encoding="utf-8")
        # Strip the H1 title line (already shown as section title)
        raw  = re.sub(r'^# .+\n', '', raw, count=1).lstrip("\n")
        # Strip blockquote "Prepared by" lines at top
        raw  = re.sub(r'^> Prepared by:.+\n', '', raw, flags=re.M)
        body = md_to_html(raw)

        # Add credentials warning
        warn = ""
        if doc.name == "CREDENTIALS.md":
            warn = '<div class="warn-box">⚠ This document contains placeholder names only. Fill in actual values from your password manager before sharing. Never commit actual credentials to the repository.</div>'

        # Parts title for sign-off — keep as-is (MD renders them)
        tag_num = f"{i+1:02d} · {meta[1][:30] if meta[1] else doc.stem}"

        # Split title for italic second word effect
        words = title.split()
        if len(words) >= 2:
            display_title = f"{words[0]}<br><em>{' '.join(words[1:])}</em>"
        else:
            display_title = title

        sections_html += f"""
  <section id="{anch}" class="doc-section{alt}">
    <div class="sec-tag">{i+1:02d} · {title}</div>
    <h2 class="sec-title">{display_title}</h2>
    {warn}
    <div class="doc-body">{body}</div>
  </section>"""

    # Action notes
    action_notes = ""
    if has_credentials:
        action_notes = "Before sharing: fill in CREDENTIALS.md values"

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>{project_name} — Handoff Package</title>
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Cormorant+Garamond:ital,wght@0,300;0,400;0,500;1,300;1,400&family=DM+Sans:ital,opsz,wght@0,9..40,300;0,9..40,400;0,9..40,500;1,9..40,300&family=DM+Mono:wght@400;500&display=swap" rel="stylesheet">
<style>{CSS}</style>
</head>
<body>

<aside class="sidebar">
  <div class="sidebar-brand">
    <div class="brand-name">{project_name}</div>
    <div class="brand-label">{nav_group_label(mode)}</div>
    <div class="brand-date">{generated_at}</div>
  </div>
  <nav class="sidebar-nav">
    <div class="nav-group">
      <div class="nav-group-label">{nav_group_label(mode)}</div>
      {nav_items_html}
    </div>
  </nav>
  <div class="sidebar-foot">Prepared by BetaCraft</div>
</aside>

<div class="topbar">
  <div class="topbar-left">{project_name} · {mode.title()} Handoff · {generated_at}</div>
  <div class="topbar-right">
    {"<span style='font-size:11px;color:#b0412e;font-family:var(--mono)'>⚠ Fill CREDENTIALS.md before sharing</span>" if has_credentials else ""}
    <button class="topbar-btn" onclick="window.print()">Print / Save PDF</button>
  </div>
</div>

<main class="main">

  <div class="hero">
    <div class="hero-tag">{mode.title()} Handoff Package</div>
    <h1 class="hero-title">{project_name}</h1>
    <p class="hero-desc">{doc_count} document{'s' if doc_count != 1 else ''} · {mode.title()} package · Prepared by BetaCraft</p>
    <div class="hero-meta">
      <div class="meta-item">
        <div class="meta-label">Package</div>
        <div class="meta-value">{nav_group_label(mode)}</div>
      </div>
      <div class="meta-item">
        <div class="meta-label">Documents</div>
        <div class="meta-value">{doc_count} files</div>
      </div>
      <div class="meta-item">
        <div class="meta-label">Generated</div>
        <div class="meta-value">{generated_at}</div>
      </div>
      {"<div class='meta-item'><div class='meta-label'>Action required</div><div class='meta-value' style='color:#b0412e'>Fill CREDENTIALS.md before sharing</div></div>" if has_credentials else ""}
    </div>
  </div>

  <div class="doc-index">
    <div class="index-label">Contents</div>
    <div class="index-grid" style="grid-template-columns:repeat({cols},1fr)">
      {index_items_html}
    </div>
  </div>

  {sections_html}

</main>

<script>
const links = document.querySelectorAll('.nav-link[data-section]');
const sections = document.querySelectorAll('.doc-section[id]');
const obs = new IntersectionObserver(entries => {{
  entries.forEach(e => {{
    if (e.isIntersecting) {{
      links.forEach(l => l.classList.toggle('active', l.dataset.section === e.target.id));
    }}
  }});
}}, {{ rootMargin: '-15% 0px -70% 0px' }});
sections.forEach(s => obs.observe(s));
</script>
</body>
</html>"""


# ─── MAIN ─────────────────────────────────────────────────────────────────────

def main():
    given = sys.argv[1] if len(sys.argv) > 1 else None
    folder = find_handoff_folder(given)
    mode   = detect_mode(folder.name)
    docs   = load_docs(folder, mode)

    if not docs:
        print(f"ERROR: No .md files found in {folder}")
        sys.exit(1)

    # Project name from parent directory or DELIVERY.md first line
    project_name = folder.parent.parent.parent.name
    delivery = folder / "DELIVERY.md"
    if delivery.exists():
        first_line = delivery.read_text(encoding="utf-8").split("\n")[0]
        m = re.match(r'^#\s+(.+?)\s*[—–-]', first_line)
        if m:
            project_name = m.group(1).strip()

    generated_at = datetime.now().strftime("%b %d, %Y")
    out_path = folder / "index.html"

    html = generate_html(docs, folder, mode, project_name, generated_at)
    out_path.write_text(html, encoding="utf-8")

    print(f"✅  Portal generated: {out_path}")
    print(f"    Project : {project_name}")
    print(f"    Mode    : {mode}")
    print(f"    Docs    : {len(docs)} files")
    for d in docs:
        flag = " ⚠ fill values before sharing" if d.name == "CREDENTIALS.md" else ""
        print(f"    · {d.name}{flag}")

    try:
        webbrowser.open(out_path.as_uri())
        print("    Opening in browser...")
    except Exception:
        print(f"    Open manually: {out_path}")


if __name__ == "__main__":
    main()
