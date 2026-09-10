# ANTI_GENERIC.md

Read in full during Step 3 of vibe-design, before committing to a design direction.
Beautiful, *fitting* design sells and engages — this file exists to make the design
specific to **this** product, not a house style stamped onto every project.

---

## Two enemies, not one

**Enemy 1 — the SaaS generic** (Claude's training-data default):
navy/indigo sidebar + white cards with `shadow-md rounded-lg`, blue-500 buttons,
Inter everywhere, 8px radius on all, stacked 80px sections, centered hero with two CTAs.

**Enemy 2 — the "anti-generic" generic** (the *new* cliché — just as tired):
- **Warm cream `#faf...` + terracotta/rust/amber** as the go-to light palette. It is
  now its own template. Ban it as a default.
- The **Fraunces / DM Serif + DM Sans + JetBrains Mono** reflex. These are fine fonts,
  but reaching for them every time is the same failure as always reaching for Inter.
- **Dark mode as a shortcut to "premium."** Dark is a *choice for specific domains*,
  not a default and not a substitute for taste. Most consumer products should be light.
- The **140px editorial serif hero + parallax** applied to everything, including
  products that are not magazines or agencies.
- **"SaaS-shaped" layouts on non-SaaS products** — a bakery, a kids' app, a law firm,
  a game, a fashion label do not want a 100vh hero, a logo strip, and a metrics row.

If the output could be re-skinned for a different company in a different industry
without changing the structure, it has failed. **Both** enemies produce that.

---

## The core principle: derive, don't default

The design language is **derived from the product**, along three axes. Answer these
from BRIEF.md / SPEC.md / the request *before* choosing a single font or colour:

1. **Domain** — what world is this in? (finance, healthcare, food, fashion, kids,
   music, developer tools, civic/gov, luxury goods, fitness, gaming, education…)
2. **Audience** — who uses it, and what do they find credible / delightful?
   (a surgeon, a teenager, a CFO, a parent, a designer, a retiree…)
3. **Emotion** — the one feeling it should evoke in 3 seconds
   (trust, joy, calm, energy, prestige, safety, nostalgia, awe, playfulness, focus…).

Domain × audience × emotion → an **aesthetic archetype** (below) → concrete type,
colour, layout, and motion. Every choice traces back to this. If you can't say
*why* a choice fits the domain/audience/emotion, it's a default — kill it.

---

## Aesthetic archetypes — pick the one that fits (not always the same one)

Twelve starting worlds. Pick the one the product actually lives in; blend at most two.
None of these is the "right" one — the point is *variety matched to domain*.

| Archetype | Feels like | Fits | Type character | Colour character |
|-----------|-----------|------|----------------|------------------|
| **Editorial** | a considered magazine | media, essays, some B2B | expressive serif + clean sans | restrained, 1 accent |
| **Swiss / functional** | precise, gridded, calm | finance, analytics, enterprise | neutral grotesk, tight grid | near-mono + 1 signal |
| **Brutalist / raw** | confident, unpolished | agencies, music, streetwear | heavy grotesk, system mono | high-contrast mono + shock accent |
| **Playful / toy** | fun, rounded, alive | kids, consumer social, games | rounded sans, chunky weights | bright, multi-hue, saturated |
| **Luxe / minimal** | expensive, quiet, sparse | luxury goods, hospitality, beauty | high-contrast serif or refined sans, lots of air | deep neutral + metallic/jewel accent |
| **Organic / natural** | warm, human, earthy | food, wellness, sustainability, craft | humanist serif/sans, soft curves | earth/botanical tones (this is where cream *may* belong — earned, not default) |
| **Retro / nostalgic** | a specific era | entertainment, food, indie brands | period-authentic display | period palette (70s, 90s, Y2K…) |
| **Technical / precise** | built by engineers | dev tools, infra, security | mono-forward, monospace headings ok | minimal, near-monochrome, semantic only |
| **Cinematic / dark** | dramatic, immersive | gaming, film, crypto, nightlife | display sans, tight tracking | true dark, one luminous accent |
| **Soft / calm** | gentle, safe, reassuring | health, meditation, finance-for-humans, kids' health | soft humanist sans, low contrast | desaturated, cool or pastel |
| **Bold / maximalist** | loud, memorable, dense | events, fashion drops, campaigns | oversized display, clashing pairs | vivid, multiple chromatic colours (rule below is relaxed here) |
| **Crafted / handmade** | tactile, artisanal | makers, local business, food | characterful serif, hand elements | ink-and-paper, muted, textured |

**Choosing rules:**
- Default consumer/lifestyle products to a **light** archetype unless the domain is
  genuinely nocturnal/dramatic (gaming, film, nightlife, some crypto). Don't reach for dark.
- Match the archetype to the *audience's* taste, not the designer's. A children's
  maths app is Playful, never Swiss. A private bank is Luxe or Swiss, never Playful.
- SaaS/software is **not automatically Editorial or Brutalist** — a calm analytics
  tool may be Swiss; a health app may be Soft. Let the domain decide.

---

## Colour — a derivation method, not a formula

There is **no default palette.** Build one per project:

**Step A — Light or dark?** Decide from domain, not habit.
- Light by default for: consumer, commerce, health, finance-for-humans, education,
  food, most marketing. Reading and trust favour light.
- Dark only when the domain is dramatic/immersive (gaming, film, music, nightlife,
  some developer/crypto) — or when you genuinely offer both and dark is the hero.
- Never pick dark because it "looks premium." Prove it fits.

**Step B — The primary hue comes from meaning.** Map the domain/emotion to a hue,
then pick a *specific, slightly unexpected* shade — not the category default:
- trust/finance → often blue, so go adjacent: deep teal, ink navy, slate green.
- health/calm → sage, eucalyptus, soft blue — not clinical cyan.
- food/warmth → yes, warm tones exist here, but vary: tomato, saffron, olive,
  aubergine — **not reflexively terracotta**.
- energy/youth → coral, electric blue, lime, magenta.
- luxury → deep jewel (emerald, oxblood, sapphire) or near-black + one metallic.
- The category default (blue fintech, green eco, purple AI) is the thing to *avoid*.

**Step C — Neutrals match the hue's temperature — not always warm cream.**
- Warm hue → warm neutrals. **Cool hue → cool/true-gray neutrals.** A cool teal brand
  on `#faf...` cream reads muddy. Pick neutrals in the same temperature family.
- Near-white options: cool `#FBFBFD`, true `#FFFFFF` (fine for clinical/luxe), warm
  `#FAF8F4` (only when the archetype is Organic/Crafted). Rotate — cream is one option, not the answer.
- Near-black text: warm `#1A1814`, cool `#0E1116`, or true-ish `#111` — pick to match.

**Step D — Restraint, with one exception.** One dominant chromatic colour, everything
else neutral — *except* Playful and Bold/Maximalist archetypes, which legitimately use
multiple saturated hues. Use `color-mix()` / OKLCH to derive tints so the palette is coherent.

**Never (all archetypes):** brand→brand-light background gradients; 2019 multi-colour
hero gradients; pure-black-on-pure-white unless deliberate; the category-default hue as primary.

---

## Type — choose for character, and rotate

Match typeface *personality* to the archetype and emotion. Do **not** reach for the
same families every time. Below is a broad palette organized by mood — treat it as a
starting set to draw from and go beyond, not a canonical list.

- **Editorial serifs:** Fraunces, Freight, Newsreader, Spectral, Lora, GT Sectra,
  Canela, Tiempos — *rotate*; Fraunces is not the default.
- **Luxe / high-contrast serifs:** Cormorant, Playfair, Bodoni, Didot, GT Super.
- **Humanist / warm serifs & sans:** Source Serif, Besley; Söhne, Inter Tight,
  Hanken Grotesk, Figtree.
- **Neutral / Swiss grotesks:** Neue Haas / Helvetica Now, Söhne, Suisse, Aeonik,
  ABC Diatype, Basis Grotesque.
- **Distinctive / brutalist display:** Syne, Space Grotesk, Clash Display, Unbounded,
  Monument Extended, Druk.
- **Rounded / playful:** Poppins-round, Quicksand, Baloo, Fredoka, Nunito, Sharp Grotesk Rounded.
- **Mono (as texture, not just code):** Berkeley Mono, JetBrains Mono, IBM Plex Mono,
  Space Mono, Commit Mono — *rotate*.

**Rules:**
- Display ≠ body typeface. Pairing creates hierarchy.
- Weight contrast is the design: headline 700–900 vs caption 300–400.
- Sizing serves the archetype — a Luxe hero may be *small and airy*, not 140px. Don't
  auto-scale every hero to 96–140px; that's a SaaS-editorial tic.
- Licensing/loading: prefer variable fonts; load locally (`next/font` / `@font-face`),
  never CDN links in production (CLS + perf). If a listed face isn't freely available,
  substitute one of equal character from the same mood group.

---

## Layout & motion — fit the archetype

- **Don't default every project to the marketing scroll-journey.** An app's home is a
  workspace; a shop's home is products; a kids' app is a playful launchpad. Structure
  follows what the user came to do.
- Grid discipline for functional/Swiss; asymmetry and rule-breaking for Editorial/Brutalist;
  generous negative space for Luxe; density and delight for Playful.
- **Motion is library-agnostic.** Prefer CSS transitions/animations and the View
  Transitions API for most work; reach for a motion library (Framer Motion, Motion One,
  GSAP) only when the interaction needs it. Match motion energy to the archetype
  (Luxe = slow and few; Playful = springy and frequent; Swiss = minimal). Always honour
  `prefers-reduced-motion`.

---

## The quality check

Before submitting, ask — and actually look at a rendered screenshot (see SKILL Step 6):

1. **Domain test** — could this be re-skinned for a company in a *different industry*
   with no structural change? If yes → too generic. It must look like it belongs to
   THIS domain and audience.
2. **Not-cream, not-dark-by-default test** — did the palette get *derived* (Steps A–C)
   or did it fall back to warm cream / dark-for-premium? If the latter → redo it.
3. **Not-the-same-fonts test** — are these typefaces chosen for this archetype, or the
   reflex Fraunces/DM-Sans pairing again? Justify the pairing from the emotion.
4. **Removal test** — cover the logo. Can you still tell what this is for?
5. **Bold-and-fitting test** — there's one choice a stranger might question, *and* it's
   right for the audience (bold ≠ random; a private bank being loud is wrong, not brave).
6. **Motion + typography tests** — does it feel alive at the archetype's energy level,
   and does the type carry character with images covered?

If any fail — it's not done. Go back to domain × audience × emotion and re-derive.
