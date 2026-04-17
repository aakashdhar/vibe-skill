---
name: vibe-design-md
description: >
  Generates a DESIGN.md file for any website URL or fetches a pre-built one
  from the awesome-design-md collection (55+ sites). DESIGN.md captures the
  complete design system of a real product — exact hex/oklch values, font
  families, spacing scales, shadow formulas, component states, do's and don'ts
  — in a format vibe-design reads to produce pixel-accurate matching UI.
  Two modes: fetch a pre-built DESIGN.md from the catalog by site name
  (instant, exact tokens), or generate one from any URL by reading the site's
  CSS and visual language (works on any site, ~2 min).
  Output always saved to project root as DESIGN.md.
  Triggers on "design-md:", "generate a design system for", "extract design
  tokens from", "make it look like [brand]", "get the design system for",
  "fetch DESIGN.md for", "create DESIGN.md from".
  After output: vibe-design reads DESIGN.md automatically in Step 2.
---

# Vibe Design MD Skill

Captures the visual language of any real website into a DESIGN.md file.
vibe-design reads this file at session start to produce UI that matches
the target product's aesthetic — exact tokens, not approximations.

Two modes. Same output. Always `DESIGN.md` in the project root.

---

## Mode A — Catalog fetch (instant)

**When:** User names a site that exists in the catalog
**How:** Download the pre-built DESIGN.md from awesome-design-md
**Accuracy:** High — tokens extracted directly from real CSS
**Time:** ~5 seconds

**Triggers:**
```
design-md: stripe
design-md: linear
design-md: notion
make it look like Vercel
get the design system for Supabase
```

Read `references/CATALOG.md` to check if the site is in the collection.
If found → fetch and save.
If not found → offer Mode B or suggest closest match from catalog.

---

## Mode B — URL generation (any site)

**When:** User provides a URL not in the catalog
**How:** Fetch the site, extract design tokens from CSS and visual inspection
**Accuracy:** Good — based on computed styles and visual analysis
**Time:** ~2 minutes

**Triggers:**
```
design-md: https://linear.app
design-md: https://resend.com
extract design tokens from https://raycast.com
```

---

## Step 0 — Parse the request

Determine mode:

```
Input contains "http" or "https" → Mode B (URL generation)
Input contains a known site name → Mode A (catalog fetch)
Input is ambiguous → check CATALOG.md first, ask if not found
```

**If ambiguous — ask once, concisely:**
> "Is this [site name] in the catalog (instant) or a URL I should visit and extract?"

---

## Step 1A — Catalog fetch (Mode A)

Read `references/CATALOG.md` to find the exact slug and fetch URL.

```bash
# Fetch from awesome-design-md
curl -fsSL "https://raw.githubusercontent.com/VoltAgent/awesome-design-md/main/design-md/[SLUG]/DESIGN.md" \
  -o DESIGN.md

# Verify download succeeded
if [ -f DESIGN.md ] && [ -s DESIGN.md ]; then
  echo "✅ DESIGN.md downloaded — $(wc -l < DESIGN.md) lines"
  head -20 DESIGN.md
else
  echo "❌ Download failed — falling back to Mode B"
fi
```

If download succeeds → jump to Step 3.
If download fails → fall back to Mode B automatically, tell user.

---

## Step 1B — URL fetch and CSS extraction (Mode B)

**Fetch the target site:**
```bash
# Fetch the page HTML
curl -fsSL "[URL]" -o /tmp/design_target.html 2>/dev/null

# Check if fetch succeeded
wc -c /tmp/design_target.html
```

**Extract what you need from the HTML:**

Read `/tmp/design_target.html` and extract:

1. **Font references** — `<link>` tags with Google Fonts or font CDN URLs, `@font-face` declarations
2. **CSS custom properties** — any `:root { --variable: value }` declarations
3. **Inline styles and classes** — colour values, font sizes, spacing patterns
4. **Meta information** — `<title>`, og:description, brand name

**Inspect visually** (from HTML structure and class names):
- What's the dominant colour? (look for background, button, link colours)
- What font families appear in font links?
- What's the general density? (sparse whitespace vs data-dense)
- What's the layout approach? (centered column, full-width, asymmetric?)
- Dark or light mode primary?

If the site requires JavaScript to render (SPA):
> "This site is JavaScript-rendered — I can see the HTML shell but not computed styles.
> I'll generate DESIGN.md based on visible static content and inferred patterns.
> For higher accuracy, share a screenshot or the site's public style guide URL."
Proceed with what's available. Flag inferred values explicitly.

---

## Step 2 — Generate the DESIGN.md

Read `references/DESIGN_MD_FORMAT.md` for the exact 9-section structure.

Fill each section from extracted data. Be precise — exact values, not descriptions.

**Section 1 — Visual Theme & Atmosphere**
2-3 sentences: what does this design feel like? What's the mood, density, philosophy?
Example: "Linear uses extreme restraint — near-monochrome surfaces, tight typography,
and generous whitespace to create a sense of precision and focus. Every element
earns its place. Nothing is decorative."

**Section 2 — Color Palette & Roles**
Every colour with: semantic name, exact hex (and oklch if extractable), functional role.
```markdown
| Token | Hex | OKLCH | Role |
|-------|-----|-------|------|
| --color-bg | #FFFFFF | oklch(100% 0 0) | Page background |
| --color-text | #0F0F0F | oklch(6% 0 0) | Primary text |
| --color-brand | #5E6AD2 | oklch(50% 0.12 265) | Linear purple — CTAs, links, active states |
| --color-surface | #F7F8F9 | oklch(97% 0.005 240) | Card and sidebar backgrounds |
| --color-border | #E5E7EB | oklch(91% 0.006 240) | Dividers, input borders |
```

Minimum 6 colours. Include the brand accent even if subtle.

**Section 3 — Typography Rules**
Font families (exact names as they appear in CSS/font links).
Full hierarchy table:
```markdown
| Role | Font | Size | Weight | Line height | Tracking |
|------|------|------|--------|------------|---------|
| Display | [font] | [px/rem] | [number] | [value] | [em] |
| H1 | [font] | [px] | [number] | [value] | [em] |
| H2 | [font] | [px] | [number] | [value] | [em] |
| Body | [font] | [px] | [number] | [value] | [em] |
| Caption | [font] | [px] | [number] | [value] | [em] |
| Mono | [font] | [px] | [number] | [value] | [em] |
```

**Section 4 — Component Styling**
Buttons, cards, inputs, navigation — with exact values for all states.
```markdown
### Button (Primary)
- Background: [colour token]
- Text: [colour token]
- Border radius: [px]
- Padding: [px × px]
- Font: [weight, size]
- Hover: background [value], transition [duration ease]
- Active: background [value], scale [value]
- Disabled: opacity [value]
- Focus: outline [colour] [width] offset [value]
```

**Section 5 — Layout Principles**
Spacing scale (e.g. 4px base, multiples), max-widths, grid, whitespace philosophy.

**Section 6 — Depth & Elevation**
Shadow system with exact `box-shadow` values for each elevation level.
```
Level 0 — flat: no shadow
Level 1 — card: 0 1px 3px rgba(0,0,0,0.08), 0 1px 2px rgba(0,0,0,0.04)
Level 2 — dropdown: 0 4px 16px rgba(0,0,0,0.12), 0 1px 4px rgba(0,0,0,0.06)
Level 3 — modal: 0 20px 60px rgba(0,0,0,0.16), 0 4px 16px rgba(0,0,0,0.08)
```

**Section 7 — Do's and Don'ts**
5-8 specific guardrails for this design language.
Example for Linear:
```
✅ DO: Use weight contrast (300 vs 600) for hierarchy, not size alone
✅ DO: Keep interactive elements subtle — hover should feel discovered, not announced
❌ DON'T: Use colour to convey information (colourblind-safe by design)
❌ DON'T: Add decorative elements — if it doesn't help users, remove it
❌ DON'T: Use more than 2 font weights in any single view
```

**Section 8 — Responsive Behaviour**
Key breakpoints, how navigation collapses, touch target sizes, what changes on mobile.

**Section 9 — Agent Prompt Guide**
3 ready-to-use prompts for common UI tasks in this style.
```
"Build a dashboard sidebar using the Linear DESIGN.md.
 Navigation items: text-only, no icons, active state uses --color-brand background at 8% opacity."

"Create a data table using Linear tokens.
 Headers: --color-text-secondary, 12px, weight 500, uppercase, tracking 0.04em.
 Rows: 1px --color-border bottom, hover --color-surface background."

"Design an empty state using Linear's minimalist approach.
 Short headline, one-line description, single CTA. No illustrations."
```

---

## Step 3 — Save and validate

```bash
# Save to project root
# (already there from curl in Mode A, or write from generation in Mode B)

# Validate it has content
LINES=$(wc -l < DESIGN.md)
SECTIONS=$(grep -c "^## " DESIGN.md)

echo "DESIGN.md: $LINES lines, $SECTIONS sections"

if [ $SECTIONS -lt 7 ]; then
  echo "⚠️ Missing sections — expected 9, found $SECTIONS"
fi
```

---

## Step 4 — Tell the user

```
✅ DESIGN.md ready — [Site name]
   [Mode A: "Downloaded from awesome-design-md catalog" /
    Mode B: "Generated from [URL]"]

Design language:
  [One sentence from Section 1]

Key tokens:
  Brand: [colour name + hex]
  Type: [display font] + [body font]
  Surface: [bg colour]

How to use:
  vibe-design reads DESIGN.md automatically.
  Trigger a design pass: design: [what to style]

[If Mode B — inferred values:]
  ⚠️ [N] values were inferred (marked with * in DESIGN.md).
  Verify against the live site before production use.
```

---

## Step 5 — Offer to update DESIGN_SYSTEM.md

If `vibe/DESIGN_SYSTEM.md` exists:
> "DESIGN.md is ready. Should I also update vibe/DESIGN_SYSTEM.md to use
> these tokens as the project's design system? This would make all future
> design passes use [site name]'s visual language by default."

Wait for answer. If yes — update DESIGN_SYSTEM.md with the key tokens.
If no — leave as is. DESIGN.md will still be read by vibe-design.

---

## Absolute rules

**Never fabricate token values.**
If a colour can't be extracted, write `[EXTRACT FROM SITE]` as the value.
Inferred values are marked with `*` and flagged in the Step 4 summary.

**DESIGN.md always goes in the project root.**
Not in vibe/, not in src/. Root only.
vibe-design checks `./DESIGN.md` — nowhere else.

**Mode B accuracy is honest.**
JS-rendered sites will have incomplete token extraction.
Always flag what was inferred vs extracted.
Never present an inferred value as definitive.

**One DESIGN.md per project at a time.**
If DESIGN.md already exists, show a diff of what would change:
> "DESIGN.md already exists ([current site name]).
> Replace with [new site]? Or save as DESIGN_[site].md for reference?"
Wait for answer.
