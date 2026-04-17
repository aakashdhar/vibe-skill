# DESIGN_PATTERNS.md

Cross-cutting design intelligence extracted from studying 55+ real products
in the awesome-design-md catalog. These patterns are what separates products
that feel considered from products that look generic.

Read by vibe-design during Step 3 when no DESIGN.md exists.
Read by vibe-design-md when generating a new DESIGN.md to validate quality.

---

## Pattern 1 — The colour restraint principle

**Observed in:** Vercel, Linear, Resend, Replicate, Ollama, xAI, Wise

The best products use far fewer colours than you think. Not because they're
boring — because restraint makes every colour meaningful.

**The pattern:**
1 brand colour + 1 near-black + 1 near-white + 2-3 neutral grays = complete system
Brand colour appears in: 1 primary CTA, 1 active/selected state, 1 accent element
Everything else is neutral. The brand colour pops because it has room to.

**Practical rule:**
Count how many distinct chromatic colours appear on any single page.
If the answer is more than 2 — remove colours until it is.
Neutrals (grays, off-whites, near-blacks) don't count.

**Anti-pattern:**
Primary + secondary + accent + 3 semantic colours + gradient backgrounds
= a design that looks like a colour palette instead of a product

---

## Pattern 2 — Weight contrast replaces size contrast

**Observed in:** Linear, Vercel, Stripe, Superhuman

The most sophisticated typographic hierarchies use weight variation more than
size variation. A 16px weight-600 label reads as more important than a 24px
weight-300 label. This is counter-intuitive but produces cleaner, more precise layouts.

**The pattern:**
- Body text: weight 400
- UI labels: weight 500
- Section headings: weight 600
- Hero headlines: weight 700-800
- Decorative/light text: weight 300

The *gap* between weights creates hierarchy.
A heading at 600 and body at 400 creates stronger hierarchy than
heading at 500 and body at 400.

**Linear's specific approach:**
Minimal size variation (12/14/16/20/32px — only 5 steps)
Weight varies dramatically (300 for secondary, 400 for body, 600 for emphasis)
The result: extremely precise, not loud

---

## Pattern 3 — Surface hierarchy without shadows

**Observed in:** Linear, Vercel, Notion, Mistral

Dark mode first products (and many light mode ones) create depth through
surface colour variation, not box-shadows. A sidebar at #1A1A1A on a
background of #0F0F0F creates hierarchy without any shadows.

**Light mode equivalent:**
background: #FAFAF8 (warm off-white, page background)
surface-1: #FFFFFF (cards, inputs — slightly brighter)
surface-2: #F2F0EB (secondary areas, hover states — slightly warmer)

The three layers are subtle but immediately readable.

**When to use shadows:**
Floating elements that sit above the page (dropdowns, tooltips, modals)
Interactive cards that need to communicate interactivity (hover lifts)
Never for static, non-interactive surfaces

---

## Pattern 4 — The editorial left anchor

**Observed in:** Notion, Sanity, Claude, many agency sites

Generic SaaS centers everything. Editorial design anchors to the left.

Left-anchored layouts:
- Feel like editorial/publishing (newspapers, magazines, serious software)
- Create implicit visual hierarchy (reading axis follows F-pattern)
- Allow text to breathe more naturally
- Are harder to get wrong (centering requires perfect line lengths)

**When to anchor left:**
- Hero headlines on marketing pages
- Feature descriptions (especially with visual on right)
- Any text block longer than 2 lines
- Navigation items

**When centering works:**
- Very short headlines (under 4 words) in section dividers
- Testimonial quotes (1-2 lines)
- Bottom-of-page CTAs in isolation

---

## Pattern 5 — Monospace as a design element

**Observed in:** Vercel, Resend, Replicate, Claude, VoltAgent

Monospace fonts aren't just for code. The best developer-tool sites use mono
for: metadata labels, statistics, version numbers, timestamps, technical identifiers,
navigation items (occasionally), section labels.

Mono at small size with letter-spacing: 0.04em creates visual texture
that signals "this is data" — distinct from prose without being loud.

**Specific uses:**
```
Version numbers: v1.4.2 — JetBrains Mono 12px weight 500
Timestamps: 2 hours ago — Mono 11px text-secondary
API endpoints: /api/brand-dna — Mono 13px on subtle bg
Statistics: 99.9% uptime — Mono 14px weight 600
Labels: BETA · NEW · DEPRECATED — Mono 10px uppercase tracking-wider
```

**Never use mono for:**
- Body copy longer than 2 sentences
- Marketing headlines
- Navigation labels (unless the whole product is terminal-aesthetic)

---

## Pattern 6 — Motion that earns its place

**Observed in:** Stripe, Framer, Raycast, Superhuman, Linear

The most effective motion in these products is almost imperceptible at normal use.
You notice it's missing when it's gone, but you never consciously notice it while using.

**The three legitimate uses:**
1. Confirm user input received (button press, form submit)
2. Explain spatial relationships (dropdown appears from button, modal closes)
3. Guide attention to what changed (new item appears, status updates)

**What the best products never do:**
- Animate on page load just to animate
- Add entrance animations to static content below the fold
- Use bounce/elastic easing on anything serious
- Animate more than one thing at a time

**Duration reference from studying real products:**
- Micro-interactions (button press, toggle): 100-150ms
- UI transitions (dropdown open, tab change): 150-250ms
- Layout changes (sidebar toggle, accordion): 200-300ms
- Page transitions: 200-350ms
- Scroll-triggered reveals: 400-600ms

Anything over 600ms feels slow. Anything under 100ms feels broken.

---

## Pattern 7 — The negative space signal

**Observed in:** Apple, Stripe, Superhuman, Vercel

The amount of whitespace around an element signals its importance.
More space = more important. This is consistent across every premium product.

A hero headline with 120px above and 80px below signals: this is the most
important thing on the page. Read this first.

A feature card with 24px padding signals: this is content to scan.

A legal footer link with 8px padding signals: this exists but doesn't demand attention.

**Practical rule:**
If something is important, give it more space than feels comfortable.
The instinct to fill space is almost always wrong.
When a design "feels empty" — that's often the design working correctly.

---

## Pattern 8 — Typography-first sections

**Observed in:** Linear (method page), Notion (home), Stripe (homepage)

The strongest sections in the best marketing sites are pure typography.
No images, no illustrations, no decorative elements. Just a massive headline
and a sentence of supporting copy.

These sections work because:
- They create rhythm — relief from image-heavy sections
- They force clarity — you can't hide behind visuals
- They age well — no stock photos to become dated
- They're memorable — you remember the words

**Identification:** A section where removing all non-text elements changes nothing
about the section's impact. That's a typography-first section done right.

---

## Pattern 9 — Consistent radius personality

**Observed in:** studying all 55 sites in the catalog

Border radius is one of the most opinionated design decisions in a product.
It communicates personality more than most teams realise.

| Radius | Personality | Example products |
|--------|------------|-----------------|
| 0px (sharp) | Serious, precise, technical | HashiCorp, some IBM surfaces |
| 2-4px (barely rounded) | Professional, minimal | Vercel, Linear |
| 6-8px (moderately rounded) | Balanced, accessible | Stripe, Supabase |
| 12-16px (clearly rounded) | Friendly, approachable | Notion, Zapier |
| 24px+ (very rounded) | Playful, consumer | Lovable, some Figma surfaces |
| Full/pill | Soft labels, tags, status indicators | Nearly universal |

**The rule:** Pick one radius for your product and use it everywhere.
Mixing sharp buttons with rounded cards is one of the most common design errors.

---

## Pattern 10 — Empty states that convert

**Observed in:** Linear, Notion, Superhuman

Most products have terrible empty states — a gray box with placeholder text.
The best products treat empty states as onboarding moments.

**Linear's empty state formula:**
1. Short, honest headline: "No issues in this project"
2. One-line reason or context: "Issues you create here will appear in this view"
3. Single action: "Create issue" button
No illustration. No decoration. Just clarity.

**Notion's formula:**
1. Icon (subtle, monochrome)
2. Headline that names exactly what's missing
3. Two-line explanation
4. One CTA button

**What both avoid:**
- Stock illustrations with people pointing at screens
- Long explanatory paragraphs
- Multiple CTAs competing for attention
- Apologetic copy ("Oops, nothing here yet...")

---

## Using these patterns with DESIGN.md

When vibe-design reads a DESIGN.md, these patterns provide the interpretive layer.
The DESIGN.md gives the tokens (what colours, what fonts, what sizes).
These patterns give the principles (how to use them, what they signal, what to avoid).

Together they produce output that matches the target product's aesthetic
rather than just matching its colours.

When vibe-design has no DESIGN.md, these patterns are the fallback —
the accumulated design intelligence that prevents generic defaults.
