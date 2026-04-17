# ANTI_GENERIC.md

Read in full during Step 3 of vibe-design before committing to any design direction.
This file is the difference between a design that looks like every other SaaS dashboard
and one that someone screenshots and sends to their team.

---

## The problem this file solves

Claude's training data is dominated by generic SaaS UIs.
Left to its own defaults it produces:
- Navy/indigo sidebar + white main content area
- Cards with `shadow-md` and `rounded-lg` on white backgrounds
- Blue primary buttons (`blue-500` / `indigo-600`)
- Inter or system-ui for everything
- 8px border radius on everything
- Flat sections stacked vertically with 80px padding between them
- Hero with centered headline, subheading, two CTAs, stock photo or abstract gradient blob

This is not a design. It is the statistical average of 10,000 SaaS landing pages.
The agent must be stopped from producing this before a single line of code is written.

---

## Step 0 — Kill the defaults before starting

Before choosing anything, explicitly reject these patterns for this session:

**Typography defaults to kill:**
- Inter as the primary typeface — it's fine, it's everywhere, it signals nothing
- System-ui / -apple-system — invisible, generic, zero personality
- Single font for everything — display and body should never be the same typeface
- Font weight 400 for headlines — headlines should be extreme: 100 or 800+, not 400

**Colour defaults to kill:**
- blue-500, indigo-600, violet-500 as primary — the three colours of generic SaaS
- bg-white + text-gray-900 as the base — technically correct, aesthetically dead
- Evenly distributed palette (primary + secondary + accent + neutral all at similar saturation)
- Gray-100 section backgrounds — the most overused "separation" technique in existence
- Default Tailwind colours directly in JSX — always define named tokens

**Layout defaults to kill:**
- Centered content column with max-w-7xl mx-auto padding on both sides on every section
- Cards as the primary content container — not every piece of content needs a card
- 12 equal columns with content always in the middle 8 — asymmetry is interesting
- Same vertical rhythm on every section — variety creates breathing room and emphasis
- Horizontal rule separators between sections — use space, not lines

**Component defaults to kill:**
- Pill badges in brand colour for labels — use mono type instead
- Icon + heading + body text stacked vertically for feature lists — find a different form
- Testimonial cards in a 3-column grid — everyone does this
- Pricing cards with a "most popular" highlight — everyone does this too
- Footer with 4 columns of links — try something different

---

## The design vocabulary for this framework

### Typography system

**Display headlines:** Dramatic, opinionated, makes a statement
- Use variable fonts with extreme weight shifts — `font-weight: 800` to `100` within one typeface
- OR use a display serif (Playfair Display, DM Serif Display, Cormorant, Freight Display)
  paired with a clean geometric sans (DM Sans, Geist, Outfit, Plus Jakarta Sans)
- Headlines at 96px–160px on desktop for hero. Not 48px. Not 64px. Go bigger.
- Tight tracking on large display text: `letter-spacing: -0.04em` to `-0.06em`
- Never center-align large headlines on marketing pages — left-align reads stronger
- Line height on display: 0.9–1.0 (tighter than you think)

**Body text:** Readable, restrained, serves the headline
- Generous line height: 1.6–1.8
- Max width: 65ch — never wider, readability drops
- Size: 17px–19px on desktop — slightly larger than default feels considered
- Weight: 400 for body, 500 for UI labels, never 600+ for paragraphs

**Mono as a design element:**
- Use mono (`JetBrains Mono`, `Fira Code`, `IBM Plex Mono`) for labels, metadata,
  version numbers, category tags, technical details
- NOT for code only — mono at small size with tracking creates visual texture
- Example: a feature label in mono caps at 11px tracking-widest feels editorial

**Weight contrast:**
- Headlines at 800+ weight, captions at 300 — the gap is the design
- Never have all text at similar weight — contrast creates hierarchy

---

### Colour system

**One dominant brand colour, everything else neutral:**

```css
/* The formula */
--color-brand: [single colour — could be unusual: terracotta, forest green, warm amber, deep plum];
--color-brand-subtle: [brand at 10% opacity — used for subtle backgrounds];
--color-brand-text: [brand darkened for text use — maintains contrast];

/* Neutrals — NOT gray-100/200/300 */
--color-surface: #fafaf8;   /* warm off-white, not pure white */
--color-surface-2: #f2f0ec; /* warm light gray — section backgrounds */
--color-text: #1a1814;      /* warm near-black, not #000000 or gray-900 */
--color-text-secondary: #6b6560; /* warm mid-gray for secondary text */
--color-border: #e5e0d8;    /* warm light border */
```

**Brand colour selection rules:**
- Pick one colour that's slightly unexpected for the category
- Security SaaS? Not blue — try deep amber or slate green
- Analytics? Not green — try warm coral or indigo
- The brand colour should appear sparingly — in CTAs, accents, highlights
- Everything else is neutral — the brand colour pops because it has room to breathe

**Never:**
- Gradient from brand to brand-light as a background — overused
- Multi-colour gradients as hero backgrounds — 2019 called
- Pure black (#000000) or pure white (#ffffff) as surface/text — use near-black, near-white
- More than one chromatic colour in the palette — neutrals don't count

---

### Layout system — judgement-based

**For marketing/landing pages:**

The goal is a sense of journey — each section has a distinct character.
One section is dense with information. The next breathes. The next is typographic.
Rhythm matters more than consistency.

Principles:
- Hero: full viewport height, massive type, one dominant visual element
- Don't center everything — left-anchored content with asymmetric right-side element
- Let text break out of the grid occasionally — a headline that runs edge to edge
- Use negative space as a design element, not just padding
- Feature sections: try a 2-column layout where text is 40% and visual is 60%
- Never stack identical-height sections with identical padding — vary the rhythm

**For product/dashboard UIs:**

Swiss grid discipline with typographic hierarchy doing the heavy lifting.
- Strong left rail — not a sidebar, a navigation column with a specific character
- Content area with clear typographic hierarchy — H1 → H2 → body, all consistent
- Tables and data: mono for numbers, extreme precision in alignment
- Status indicators: colour-coded dots, not badges and cards

**Asymmetry techniques:**
```
// Good — headline breaks the grid
<section className="grid grid-cols-12">
  <div className="col-span-8 col-start-1">
    <h1 className="text-[120px] font-[800] leading-[0.95] tracking-[-0.04em]">
      Headline that commands attention
    </h1>
  </div>
  <div className="col-span-4 col-start-9 self-end pb-8">
    <p>Supporting text positioned at the bottom right, creating tension</p>
  </div>
</section>

// Bad — everything centered in the same column
<section className="max-w-4xl mx-auto text-center">
  <h1>Headline</h1>
  <p>Subheading</p>
  <Button>CTA</Button>
</section>
```

---

### Animation system — Framer Motion

All motion in this framework uses Framer Motion. Never use `transition-all`.

**Core animation philosophy:**
Motion should feel purposeful and slightly surprising.
Not every element needs animation. But when something moves, it should feel alive.

**Standard animation tokens:**
```typescript
// Entrance animations — elements appearing
export const fadeUp = {
  initial: { opacity: 0, y: 24 },
  animate: { opacity: 1, y: 0 },
  transition: { duration: 0.5, ease: [0.25, 0.46, 0.45, 0.94] }
}

// Stagger for list items
export const staggerContainer = {
  animate: { transition: { staggerChildren: 0.08 } }
}

// Scale entrance — for cards and modals
export const scaleIn = {
  initial: { opacity: 0, scale: 0.96 },
  animate: { opacity: 1, scale: 1 },
  transition: { duration: 0.4, ease: [0.34, 1.56, 0.64, 1] } // spring
}

// Hover lift — for interactive cards
export const hoverLift = {
  whileHover: { y: -4, transition: { duration: 0.2 } }
}
```

**Scroll-triggered reveals:**
```typescript
import { useInView } from 'framer-motion'

// Use for any section that enters the viewport
const ref = useRef(null)
const isInView = useInView(ref, { once: true, margin: "-100px" })

<motion.div
  ref={ref}
  initial={{ opacity: 0, y: 40 }}
  animate={isInView ? { opacity: 1, y: 0 } : { opacity: 0, y: 40 }}
  transition={{ duration: 0.6, ease: [0.25, 0.46, 0.45, 0.94] }}
/>
```

**Parallax on hero sections:**
```typescript
import { useScroll, useTransform } from 'framer-motion'

const { scrollY } = useScroll()
const y = useTransform(scrollY, [0, 500], [0, -150]) // background moves slower
const opacity = useTransform(scrollY, [0, 300], [1, 0]) // text fades as scrolled

<motion.div style={{ y }} className="absolute inset-0 bg-[image]" />
<motion.h1 style={{ opacity }} className="relative">Headline</motion.h1>
```

**Cursor-following effects:**
```typescript
import { useMotionValue, useSpring } from 'framer-motion'

const mouseX = useMotionValue(0)
const mouseY = useMotionValue(0)
const smoothX = useSpring(mouseX, { stiffness: 100, damping: 30 })
const smoothY = useSpring(mouseY, { stiffness: 100, damping: 30 })

// Attach to container mousemove
// Use for: spotlight effects, magnetic buttons, floating decorative elements
```

**Micro-interactions — every interactive element:**
```typescript
// Button — tactile press feeling
<motion.button
  whileHover={{ scale: 1.02 }}
  whileTap={{ scale: 0.97 }}
  transition={{ type: "spring", stiffness: 400, damping: 25 }}
/>

// Link — subtle underline grow
// Use CSS: after pseudo-element width: 0 → 100% on hover with transition

// Input focus — border brightens, slight scale
// Use Framer layoutId for shared element transitions between states

// Card hover — shadow deepens, slight lift
<motion.div whileHover={{ y: -4, boxShadow: "0 20px 60px rgba(0,0,0,0.12)" }} />
```

**Page transitions:**
```typescript
// Wrap pages in AnimatePresence
// Simple fade works beautifully — don't over-engineer
<AnimatePresence mode="wait">
  <motion.div
    key={router.route}
    initial={{ opacity: 0 }}
    animate={{ opacity: 1 }}
    exit={{ opacity: 0 }}
    transition={{ duration: 0.25 }}
  />
</AnimatePresence>
```

**Motion rules:**
- Duration: 200ms for micro-interactions, 400–600ms for layout transitions
- Never use `ease-in` alone — always `ease-in-out` or custom cubic-bezier
- Spring physics for UI interactions (`type: "spring"`) — feels alive
- Cubic-bezier for scroll-triggered animations — more controlled
- Never animate more than 2 properties simultaneously on the same element
- `will-change: transform` on elements that animate — performance
- Reduced motion: always wrap in `useReducedMotion()` check

---

### Surface and depth system

**Layers:**
```css
/* Not flat. Not cards-on-white. Depth through colour and blur. */

/* Layer 0 — page background */
background: #fafaf8; /* warm off-white */

/* Layer 1 — content surface */
background: #ffffff;
box-shadow: 0 1px 3px rgba(0,0,0,0.04), 0 4px 16px rgba(0,0,0,0.06);

/* Layer 2 — elevated card */
background: #ffffff;
box-shadow: 0 4px 24px rgba(0,0,0,0.08), 0 1px 4px rgba(0,0,0,0.04);

/* Layer 3 — modal / floating panel */
background: rgba(255,255,255,0.9);
backdrop-filter: blur(20px) saturate(180%);
box-shadow: 0 20px 60px rgba(0,0,0,0.12), 0 4px 16px rgba(0,0,0,0.08);
```

**Texture:**
```css
/* Subtle grain texture — adds warmth and craftsmanship */
.grain {
  position: relative;
}
.grain::after {
  content: '';
  position: absolute;
  inset: 0;
  background-image: url("data:image/svg+xml,..."); /* SVG noise pattern */
  opacity: 0.03;
  pointer-events: none;
}

/* Or use CSS gradient noise */
background-image: 
  url("data:image/svg+xml,%3Csvg viewBox='0 0 256 256' xmlns='http://www.w3.org/2000/svg'%3E%3Cfilter id='noise'%3E%3CfeTurbulence type='fractalNoise' baseFrequency='0.9' numOctaves='4' stitchTiles='stitch'/%3E%3C/filter%3E%3Crect width='100%25' height='100%25' filter='url(%23noise)' opacity='1'/%3E%3C/svg%3E"),
  linear-gradient(to bottom, var(--color-surface), var(--color-surface));
```

---

## Site-type design rules

**Marketing / Landing page:**
- Hero takes 100vh. Full stop.
- Headline is 96px minimum on desktop. Closer to 140px is better.
- One CTA in the hero. Never two equal-weight CTAs fighting for attention.
- Scroll-triggered animations on every section reveal
- Parallax on the hero background element
- Social proof: numbers in giant type, not cards
- Footer: minimal, typographic, not a sitemap

**Product dashboard:**
- Navigation: narrow, dark, typographic. Not a wide sidebar with icons + labels.
- Data: mono font for all numbers. Always.
- Status: colour dots, not badges with background fill
- Empty states: illustrated or typographic, never a gray box with placeholder text
- Micro-interactions on every data point — hover reveals detail

**Documentation / Content:**
- Reading width: 680px maximum
- Large, generous line height (1.8)
- Code blocks: dark surface, always, even on light pages
- Navigation: sticky left rail, current item is obvious
- No decorative images — type and structure do all the work

---

## The quality check

Before submitting any design, ask:

1. **The screenshot test** — if you screenshot this and show it to a designer,
   would they say "nice" or "another SaaS dashboard"?

2. **The removal test** — if you remove the brand name, can you still tell
   what company/product this is for? If the answer is no — it's too generic.

3. **The bold choice test** — what is the one thing in this design that
   someone might push back on? If the answer is nothing — it's not bold enough.
   Good design always makes at least one choice that requires defending.

4. **The motion test** — does the page feel alive? Click something. Hover something.
   Scroll down. Is there a moment of delight anywhere?

5. **The typography test** — cover the images. Does the page still have character
   from type alone? If not — the typography is not doing its job.

If any of these fail — the design is not done. Go back.
