# SITE_TYPE_PLAYBOOK.md

Read during Step 3 of vibe-design, after ANTI_GENERIC.md. Concrete, *domain-diverse*
starting points. These are worlds to draw from — pick the closest by **domain ×
audience × emotion**, then derive palette/type per ANTI_GENERIC.md (do not copy a
palette verbatim). The point of this file is breadth: software is a few entries, not
the whole map.

**How to use:** identify the domain → pick the entry → adopt its *archetype and
structure* → derive the specific colours and fonts from the product. Never force a
non-software product into a software layout. Blend at most two.

---

## SOFTWARE

### Analytics / finance dashboard — Swiss / functional · emotion: clarity, trust
- Type: neutral grotesk (Söhne / Helvetica Now / Basis), mono for all numbers.
- Palette: **cool or true neutrals** (`#FBFBFD` / `#0E1116`), one signal hue (deep teal
  or ink blue — not default SaaS blue); semantic red/green only in data.
- Layout: real grid, dense but calm, typographic hierarchy, colour-coded dots not badges.
- Avoid: warm cream, decorative hero, marketing scroll-journey.

### Developer tool / docs — Technical · emotion: precision, respect
- Type: mono-forward (Berkeley/Commit/JetBrains Mono headings ok) + clean sans body.
- Palette: near-monochrome, `#FFFFFF`/`#0B0B0C`, one semantic accent.
- Layout: fixed text nav, 68–72ch reading width, code blocks dark in either theme, flat lists.
- Avoid: illustration, gradients, parallax.

### AI / B2B product — pick per feeling, NOT auto-editorial
- Calm/ops tool → Swiss. Consumer-facing/story-driven → Editorial. Dev-facing → Technical.
- Derive palette; avoid the purple/blue "AI" default and the orb/gradient hero entirely.

---

## CONSUMER & LIFESTYLE

### Kids / education (young) — Playful / toy · emotion: joy, safety
- Type: rounded (Fredoka / Baloo / Quicksand), chunky weights, big and friendly.
- Palette: **bright, multi-hue, saturated** (the restraint rule is relaxed here); high
  legibility; light background.
- Layout: big tap targets, generous spacing, characters/mascots, motion is springy/frequent.
- Avoid: tiny type, muted palettes, anything corporate, dark mode.

### Health / wellness / meditation — Soft / calm · emotion: reassurance, calm
- Type: soft humanist sans (Hanken Grotesk / Figtree), low contrast, roomy line height.
- Palette: desaturated cool or botanical (sage, soft blue, clay — *earned*, not reflex cream).
- Layout: lots of air, gentle curves, few elements per screen, slow motion.
- Avoid: clinical cyan, hard edges, dense dashboards, urgent reds.

### Fitness / sports / energy — Bold / maximalist or Cinematic · emotion: energy, drive
- Type: oversized condensed display (Druk / Monument), tight tracking.
- Palette: high-contrast, one electric hue; dark is legitimate here for intensity.
- Layout: full-bleed action imagery, big numbers, aggressive rhythm, kinetic motion.

### Fashion / beauty / luxury goods — Luxe / minimal · emotion: prestige, desire
- Type: high-contrast serif (Canela / GT Super / Bodoni) or refined sans, **small and airy**
  is often stronger than huge.
- Palette: deep neutral or off-white + one jewel/metallic accent; restraint.
- Layout: enormous negative space, full-bleed editorial photography, few words, slow fades.
- Avoid: 140px shouty hero, busy sections, saturated brights, cards.

### Food / restaurant / hospitality — Crafted / Organic · emotion: appetite, warmth
- Type: characterful serif or a display with personality + clean body.
- Palette: appetite-driven and *varied* — olive, tomato, aubergine, saffron, ink; warm
  neutrals are fine **here** because the domain earns them (not as a global default).
- Layout: photography-led, menu as a designed artifact, location/hours obvious, tactile texture.
- Avoid: SaaS hero, metrics rows, logo strips.

### E-commerce / retail — emotion: desire + confidence, low friction
- Archetype follows the brand (Luxe for premium, Playful for youth, Crafted for makers).
- Type/palette derived from the brand; product imagery is the hero, UI recedes.
- Layout: product-first grid, fast scan, trust cues near buy button, crisp PDP.
- Avoid: letting "design personality" fight the products; heavy motion on listings.

---

## BRAND, CREATIVE & CIVIC

### Agency / studio / portfolio — Brutalist or Editorial · emotion: confidence, taste
- Type: distinctive display (Clash / Syne / Space Grotesk) doing the heavy lifting.
- Palette: high-contrast; **dark is one option, not required** — a stark light brutalist
  site is equally strong. If dark, one luminous punch colour used sparingly.
- Layout: full-bleed work, massive type, asymmetry, hover reveals, rule-breaking grid.
- Avoid: the exact electric-yellow-on-near-black formula as a reflex — derive the accent.

### Editorial / media / blog — Editorial · emotion: authority, immersion
- Type: expressive serif display + readable serif/sans body; rotate beyond Fraunces.
- Palette: restrained, paper-like or crisp; one accent for links/marks.
- Layout: strong article typography, 65–75ch, generous rhythm, pull quotes, minimal chrome.

### Music / entertainment / events / gaming — Cinematic / Bold · emotion: hype, immersion
- Type: display sans, tight tracking, or period display for retro acts.
- Palette: **dark is genuinely at home here**; one or two luminous accents, gradients ok
  if intentional and modern.
- Layout: immersive full-screen, media-forward, kinetic transitions.

### Nonprofit / civic / government / education (institutional) — emotion: trust, access
- Type: clear, humanist, highly legible; accessibility is the aesthetic.
- Palette: calm, high-contrast for WCAG AAA where possible; institutional but human.
- Layout: information-first, plain-language, obvious actions, no dark patterns.
- Avoid: trendy low-contrast, decorative-over-clear, anything that reads "startup."

### Local / small business (dentist, salon, plumber, cafe) — Crafted / Soft · emotion: trust, approachability
- Type: friendly, legible; one characterful display for the name.
- Palette: derived from the real brand; warm or cool per the trade's feel.
- Layout: what a customer needs first — hours, location, book/call, services, photos.
- Avoid: SaaS marketing structure, jargon, giant abstract hero.

---

## When two worlds meet
A fintech *for teenagers* = Swiss trust structure + Playful palette/type energy.
A luxury *food* brand = Luxe restraint + Crafted warmth. Blend deliberately, name the
blend in the design contract, and keep one archetype dominant.

---

## Font loading (all types)
Prefer variable fonts, loaded locally (`next/font` / `@font-face`), never CDN links in
production (CLS + performance). Map to CSS variables:
```
--font-display, --font-body, --font-mono  →  tailwind fontFamily.{display,body,mono}
```
If a chosen face isn't freely licensable, substitute one of equal character from the
same mood group in ANTI_GENERIC.md — never silently fall back to Inter/Fraunces.
