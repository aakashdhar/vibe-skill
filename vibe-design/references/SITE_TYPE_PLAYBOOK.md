# SITE_TYPE_PLAYBOOK.md

Read during Step 3 of vibe-design after ANTI_GENERIC.md.
Concrete design decisions for the most common site types.
Pick the closest match, adapt to the project's brand and DESIGN_SYSTEM.md.

---

## How to use this file

1. Identify the site type from SPEC.md and the design request
2. Read the corresponding section fully
3. Commit to the design language described
4. Adapt it to the specific brand colour and typography from DESIGN_SYSTEM.md
5. Never blend two site type playbooks — pick one, go all the way

---

## Site type 1 — AI / SaaS product (the Brandbot type)

**The problem:** Every AI SaaS looks the same. Dark mode, purple/blue gradient,
floating orbs or abstract network graphs, Inter font, "the future of X" headline.

**The direction — editorial meets technical:**
Think: a well-designed magazine that happens to be about software.
Strong typographic hierarchy. Clear information architecture.
One unexpected visual element rather than abstract decoration.

**Typography:**
```
Display: Fraunces Variable (serif with optical size axis, dramatic at large sizes)
         OR Playfair Display (classic, editorial weight)
Body:    DM Sans (modern, neutral, pairs well with serif display)
Mono:    JetBrains Mono (for metrics, data points, technical labels)

Hero headline: 128px, weight 800, tracking -0.04em, line-height 0.92
Section headline: 56px, weight 700, tracking -0.02em
Body: 18px, weight 400, line-height 1.7
Labels/meta: JetBrains Mono 12px, weight 500, tracking 0.08em, uppercase
```

**Colour:**
```css
/* Light mode — warm and considered, not cold tech */
--brand: [one colour — e.g. #B45309 amber, #166534 forest, #7C3AED violet];
--surface: #FAFAF8;
--surface-2: #F2F0EB;
--text: #1C1917;
--text-secondary: #78716C;
--border: #E7E5E4;

/* Accent — brand colour at 15% opacity for subtle backgrounds */
--brand-subtle: color-mix(in srgb, var(--brand) 15%, transparent);
```

**Layout:**
- Hero: full viewport, headline left-anchored, 3-column grid, visual element in right 2 columns
- Features: alternating left/right image-text layout (not a 3-column icon grid)
- Metrics: large mono numbers, minimal labels, no card containers
- CTA section: full-width with brand colour background, large headline, single button

**Key component — the hero:**
```tsx
<section className="min-h-screen grid grid-cols-12 items-center px-8 gap-8">
  <div className="col-span-7">
    {/* Label in mono above headline */}
    <span className="font-mono text-xs tracking-widest uppercase text-[--brand]">
      Intelligent content engine
    </span>
    {/* Massive serif headline */}
    <h1 className="font-display text-[clamp(64px,8vw,140px)] font-bold
                   leading-[0.92] tracking-[-0.04em] mt-6 text-[--text]">
      Content that<br/>
      <em className="font-light italic">sounds like</em><br/>
      you.
    </h1>
    {/* Single CTA */}
    <motion.button whileHover={{ scale: 1.02 }} whileTap={{ scale: 0.97 }}
      className="mt-12 px-8 py-4 bg-[--brand] text-white font-medium
                 text-lg tracking-[-0.01em] rounded-none"> {/* No radius */}
      Start free →
    </motion.button>
  </div>
  <div className="col-span-5">
    {/* Product visual or abstract element — NOT a stock photo */}
  </div>
</section>
```

**What to avoid for this site type:**
- Animated gradient hero background
- Abstract floating orbs or particles
- Three equal-weight feature cards in a row
- Dark mode as default (save it for the product itself)

---

## Site type 2 — Agency / Studio / BetaCraft type

**The direction — bold, opinionated, proves expertise through design:**
This site IS the product demonstration.
If it looks generic, the agency looks generic.

**Typography:**
```
Display: Syne (geometric grotesque, very distinctive at large sizes)
         OR Space Grotesk (modern, slightly quirky)
Body:    Inter (here it's okay — the display font does the heavy lifting)
Mono:    IBM Plex Mono (for technical details, process steps)

Hero headline: clamp(80px, 12vw, 180px), weight 800, tracking -0.06em
Process numbers: 200px, weight 800, opacity 0.08 (background decorative)
Body: 16px, weight 400, line-height 1.7
```

**Colour:**
```css
/* Near-monochrome with one unexpected accent */
--surface: #0F0F0F;        /* almost black, not pure black */
--surface-2: #1A1A1A;      /* card backgrounds */
--text: #F5F5F3;           /* warm near-white */
--text-secondary: #8A8A88;
--brand: #E8FF47;          /* electric yellow — one punch of colour */
--border: rgba(255,255,255,0.08);
```

**Layout:**
- Full dark. Brand colour appears ONLY in CTAs, hover states, and one graphic element
- Process section: numbered with massive background numbers, text overlay
- Work/portfolio: full-bleed images, no cards, hover reveals details
- About: one large photo, text wrapped around it or offset
- Services: large type list, each item is a full row with hover animation

**The brand colour technique:**
```tsx
/* The brand colour appears as a punch — not a background */
<h1 className="text-[--text]">
  We build digital products that{' '}
  <span className="text-[--brand]">actually work</span>
</h1>

/* On hover, elements reveal the brand colour */
<div className="group cursor-pointer">
  <div className="h-px bg-[--border] group-hover:bg-[--brand] transition-colors duration-300" />
  <h3 className="text-[--text-secondary] group-hover:text-[--text] transition-colors">
    Service name
  </h3>
</div>
```

---

## Site type 3 — Marketing / Landing (generic product)

**The direction — conversion-focused but not template-looking:**
Clear hierarchy. Strong social proof. Obvious CTA.
But with typographic personality and considered spacing.

**Typography:**
```
Display: Bricolage Grotesque (expressive, variable weight)
         OR Cabinet Grotesk (editorial feel)
Body:    Outfit (clean, modern, readable)

Hero: clamp(52px, 6vw, 96px), weight 800, tracking -0.03em
Sub-headline: 20px, weight 400, line-height 1.6, max-width 540px
```

**Layout — the scroll journey:**
1. Hero: full viewport, headline + CTA, product screenshot or visual below fold
2. Social proof: logo strip, minimal, black and white, no cards
3. Problem: large type, emotional, 2-column layout
4. Solution: feature-by-feature with alternating visuals
5. Metrics: 3 large numbers, mono font, minimal labels
6. Testimonials: 2 large quotes, full name + photo, NOT a 3-col grid
7. CTA: full-width brand colour section, one headline, one button

**The metrics section (not cards):**
```tsx
<section className="py-32 px-8">
  <div className="grid grid-cols-3 divide-x divide-[--border]">
    {[
      { value: "10x", label: "faster than manual research" },
      { value: "94%", label: "brand voice accuracy score" },
      { value: "2min", label: "from URL to published article" },
    ].map(({ value, label }) => (
      <div className="px-12 py-8">
        <div className="font-mono text-[80px] font-bold leading-none text-[--brand]">
          {value}
        </div>
        <div className="text-[--text-secondary] mt-3 text-lg">{label}</div>
      </div>
    ))}
  </div>
</section>
```

---

## Site type 4 — Developer tool / Documentation

**The direction — precision, clarity, respects the reader's intelligence:**
No decoration. Every element earns its place.
The typography IS the design.

**Typography:**
```
Display: Berkeley Mono (mono for headlines — unexpected, very developer)
         OR Geist (Vercel's typeface, modern, clean)
Body:    Geist or Inter
Code:    Geist Mono

Headlines: mono for all levels — unconventional, immediately signals technical
Body: 17px, line-height 1.8, max-width 68ch
```

**Colour:**
```css
/* Minimal — almost no colour */
--surface: #FFFFFF;
--text: #111111;
--text-secondary: #666666;
--brand: #000000; /* black IS the brand colour here */
--code-bg: #F6F6F6;
--border: #E5E5E5;
/* One semantic colour: green for success, nothing else */
```

**Layout:**
- Left navigation: 240px fixed, no icons (just text)
- Content: 720px max-width, generous line height
- Code blocks: always dark, even in light mode
- No cards — flat lists and clear headings

---

## Animation defaults by site type

| Site type | Hero | Scroll reveals | Hover | Transitions |
|-----------|------|---------------|-------|-------------|
| AI/SaaS | Parallax bg, text fade-in | staggered fadeUp | lift + shadow | page fade |
| Agency/Studio | Bold slide-in left | line drawing, reveal | colour change | wipe transition |
| Marketing | Scale + fade | staggered by section | scale 1.02 | fade |
| Developer tool | Minimal — text cursor blink | simple opacity | underline | none |

---

## Font loading — always use next/font or @font-face

```typescript
// Next.js — preferred
import { Fraunces, DM_Sans, JetBrains_Mono } from 'next/font/google'

const fraunces = Fraunces({
  subsets: ['latin'],
  axes: ['opsz', 'SOFT', 'WONK'], // variable font axes
  variable: '--font-display',
})

const dmSans = DM_Sans({
  subsets: ['latin'],
  variable: '--font-body',
})

// Then in tailwind.config.js
fontFamily: {
  display: ['var(--font-display)', 'serif'],
  body: ['var(--font-body)', 'sans-serif'],
  mono: ['var(--font-mono)', 'monospace'],
}
```

Never use CDN font links for production. Always local load via next/font or @font-face.
Font loading is a performance issue — and a CLS issue on first load.
