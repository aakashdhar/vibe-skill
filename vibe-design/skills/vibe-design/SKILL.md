---
name: vibe-design
description: >
  Frontend design workflow that produces non-generic, editorial-quality UI.
  Immediately invokes the frontend-design skill for aesthetic direction before
  any code is written. Enforces a written design contract that is re-read before
  every single component — not once and forgotten. Creates separate files per
  page and component, never monolithic output. Reads DESIGN.md if present for
  exact brand tokens. Reads ANTI_GENERIC.md to kill SaaS dashboard defaults.
  Reads SITE_TYPE_PLAYBOOK.md for site-type-specific vocabulary.
  Triggers on "design:" prefix, "style this", "make this look better",
  "redesign this page", "the UI needs work", "can you polish",
  "do a design pass", "it looks too plain", "it looks generic",
  "it looks like a saas dashboard", "make separate pages".
  Always use when the goal is visual — aesthetics, layout, feel, interactions.
  Never use for logic, data, tests, or spec changes.
---

# Vibe Design Skill

Handles all visual styling for a vibe project.
Invokes frontend-design first. Commits to a design contract.
Re-reads that contract before every component. Creates separate files.

**The separation of concerns:**
- **vibe agent** — spec compliance, data flow, logic, tests, docs
- **vibe-design** — aesthetics, layout, feel, interactions, visual polish

---

## CRITICAL: How this skill works

The reason AI design tools produce generic output is that they commit to a
direction once and then forget it during implementation.

This skill works differently:
1. **frontend-design is invoked first** — before reading any project files
2. **A design contract is written** — specific, named, irreversible choices
3. **The contract is re-read before every single component** — not once, every time
4. **Each page gets its own file** — never one monolithic output

If you find yourself about to write a white card with shadow-md — stop.
Re-read the design contract. If the contract says "no cards" — no cards.

---

## Step 1 — Invoke frontend-design IMMEDIATELY

Before reading project files. Before understanding the request.
Before doing anything else.

Read `~/.claude/skills/frontend-design/SKILL.md` in full right now.

This is not optional. This is not "if installed." This is the first action.

The frontend-design skill gives you:
- The instruction to commit to an EXTREME aesthetic direction
- The anti-generic typography, colour, and motion principles
- The mindset: make it UNFORGETTABLE, not safe

If the file is not found at `~/.claude/skills/frontend-design/SKILL.md`:
Check `~/.claude/skills/public/frontend-design/SKILL.md`.
If neither exists — proceed, but the output quality will be lower.

**After reading frontend-design — internalise this:**
> "I will commit to a bold, specific aesthetic direction.
> I will not produce a SaaS dashboard.
> I will not use Inter, blue-500, shadow-md, or centered columns.
> Every component will reflect the committed direction."

---

## Step 2 — Read project context and DESIGN.md

Read in this order:

**First — check for DESIGN.md (highest priority):**
```bash
ls DESIGN.md 2>/dev/null && echo "DESIGN.MD EXISTS" || echo "NO DESIGN.MD"
cat DESIGN.md 2>/dev/null
```

If DESIGN.md exists — its tokens are the law. Exact hex values. Exact font names.
Exact shadow formulas. Do not approximate. Do not substitute.
DESIGN.md overrides DESIGN_SYSTEM.md where they conflict.

**Then read project files:**
1. `vibe/CODEBASE.md` — stack, component library, file paths
2. `vibe/SPEC.md` — UI specification, screens, components
3. `vibe/DESIGN_SYSTEM.md` — existing tokens
4. `CLAUDE.md` — code style, naming conventions

Extract:
- Styling approach: Tailwind / CSS Modules / styled-components / vanilla CSS
- Framework: React / Vue / Next.js / vanilla — determines animation library
- Platform: mobile-first or desktop
- Pages and screens that need design work

---

## Step 3 — Write the design contract

This is the most important step. Do not rush it.

Read `references/ANTI_GENERIC.md` in full.
Read `references/SITE_TYPE_PLAYBOOK.md` — find the matching site type.

Then write the design contract. This is a concrete, named document.

```
═══════════════════════════════════════════════════════════
DESIGN CONTRACT — [Project name] — [date]
═══════════════════════════════════════════════════════════

SITE TYPE: [AI/SaaS / Agency / Marketing / Developer tool / Dashboard]

ONE BOLD CHOICE: [Name it explicitly — this is non-negotiable]
Examples:
  "Headlines are Fraunces 120px+ left-anchored — never centered"
  "No cards anywhere — all content is in full-width rows"
  "Brand colour appears in exactly 3 places — nowhere else"
  "Navigation is 32px tall, text only, no icons"

TYPOGRAPHY CONTRACT:
  Display font: [exact name — NOT Inter, NOT system-ui]
  Body font: [exact name]
  Mono font: [exact name — for labels, data, metadata]
  Display size: [clamp(72px, 9vw, 140px) or specific px]
  Display weight: [800 or 700 — not 400, not 500]
  Display tracking: [-0.04em or tighter]
  Body size: [17px or 18px]
  Body line-height: [1.7]

COLOUR CONTRACT:
  Surface: [warm off-white hex — NOT #ffffff]
  Text: [warm near-black hex — NOT #000 or gray-900]
  Brand accent: [one colour only — NOT blue-500 or indigo-600]
  Brand appears on: [list exactly where]
  Brand does NOT appear on: [everything else]

MOTION CONTRACT:
  Library: [Framer Motion | CSS + IntersectionObserver | Vue Transition]
  Hero: [specific animation]
  Sections: [scroll-triggered reveal approach]
  Interactions: [hover/tap approach]

FILE STRUCTURE:
  [Every file to be created — one page per file, one component family per file]

BANNED FOR THIS PROJECT:
  ❌ Inter as display font
  ❌ blue-500 / indigo-600 / violet-500 as primary colour
  ❌ white card with shadow-md
  ❌ Centered hero headline
  ❌ 3-column icon feature grid
  ❌ Gray-100 section backgrounds
  [add project-specific bans here]
═══════════════════════════════════════════════════════════
```

**Save the contract:**
```bash
mkdir -p vibe/design
# Write contract to file — this gets re-read before every component
```

Save as `vibe/design/CONTRACT.md`.

**Present to user:**
> "Design contract written.
> Bold choice: [state it clearly]
> This will look like: [one sentence description]
> Files to create: [N files — list them]
> Proceeding."

Wait for approval only if 3+ components. Otherwise proceed immediately.

---

## Step 4 — Establish file structure BEFORE writing any code

**Rule: one file per page, one file per component family. Always.**

Never put multiple pages in one file.
Never create a single wireframe.html or index.html with everything.

If the user asks for a wireframe.html — respond:
> "I create separate files per page for maintainability and because
> vibe-design produces production files, not wireframes.
> File structure: [list from contract]. Starting with [first page]."

Create the structure:
```bash
mkdir -p src/pages src/components src/lib src/styles

# Create animation tokens file FIRST — everything imports from here
# Write src/lib/animations.ts with tokens from ANTI_GENERIC.md

# Create CSS tokens file with values from the contract
# Write src/styles/tokens.css with all CSS custom properties

# Announce
echo "Structure created. Building [N] files:"
echo "[list all files from contract]"
echo "Starting with [first file]."
```

---

## Step 5 — Implement — one file at a time

### MANDATORY before each file: Re-read the design contract

```bash
cat vibe/design/CONTRACT.md
```

Then ask: does my plan for this component implement the bold choice?
State out loud:
> "Building [filename]. Bold choice implementation: [how this component shows it].
> Using [display font] at [size]. Brand colour on [what, if anything]."

If you cannot answer how this component implements the bold choice — redesign
the approach until you can.

### Write the implementation

For each component:
1. Implement the design
2. Cover all states: default, hover, active, focus, disabled, loading, empty
3. Mobile-first if project is mobile-first

### Per-component self-check (mandatory before moving to next file):

- [ ] Bold choice is visible and intentional in this component
- [ ] Display font used for headlines — NOT Inter, NOT system fonts
- [ ] Brand colour appears only where the contract specifies
- [ ] Animation imported from `src/lib/animations.ts` — not inline
- [ ] No pattern from the BANNED LIST is present
- [ ] This component could not be mistaken for a generic SaaS dashboard

If any check fails — fix before moving to the next file.

### Stack-specific guidance

**React + Tailwind + Framer Motion:**
```typescript
// Tokens in tailwind.config.js, not hardcoded
// All animations from src/lib/animations.ts
// next/font for font loading
// motion.div with variants from animations.ts
```

**React + CSS Modules + Framer Motion:**
```typescript
// CSS custom properties in tokens.css
// BEM class names in .module.css
// Framer Motion for all transitions
```

**Vue 3:**
```typescript
// CSS custom properties globally
// Vue Transition + CSS @keyframes
// IntersectionObserver for scroll reveals
// No Framer Motion (React only)
```

**Vanilla HTML + CSS + JS:**
```javascript
// CSS custom properties at :root
// IntersectionObserver for scroll triggers
// CSS @keyframes with animation-delay for stagger
// No dependencies required
```

---

## Step 6 — Full consistency check after all files

After all files written:

**Typography:**
- [ ] Display font is the font from the contract — everywhere
- [ ] No Inter as display font unless it IS in the contract
- [ ] Mono font used for labels, metadata, numbers

**Colour:**
- [ ] Brand colour in ONLY the places the contract specifies
- [ ] Surface is warm off-white, NOT #ffffff
- [ ] Text is warm near-black, NOT gray-900 or #000000
- [ ] No blue-500, indigo-600 anywhere

**Motion:**
- [ ] All animations from animations.ts
- [ ] `prefers-reduced-motion` handled

**Layout:**
- [ ] The bold choice is visible on the page
- [ ] No centered hero headline (unless contract says so)
- [ ] No 3-column icon grid
- [ ] No white cards with shadow-md (unless in contract)

**Files:**
- [ ] Every page is a separate file
- [ ] No monolithic output

---

## Step 7 — Update docs and commit

Update `vibe/DESIGN_SYSTEM.md` with the design contract as the direction section.
Update `vibe/TASKS.md` with what was built.

```bash
git add src/ vibe/
git commit -m "design([scope]): [bold choice] — [files created]"
```

Signal done:
```
✅ Design complete — [scope]
   [One sentence: what it looks like]
   Bold choice: [restate]
   Files: [N files created — list them]
   Contract: vibe/design/CONTRACT.md
```

---

## Non-negotiable rules

**frontend-design is read in Step 1. No exceptions.**

**The design contract is written before any code. No exceptions.**

**The contract is re-read before each file. No exceptions.**

**One file per page. One file per component family. No exceptions.**

**Generic is failure.** A SaaS dashboard means the skill failed.
Not played it safe — failed. Retry from Step 3.
