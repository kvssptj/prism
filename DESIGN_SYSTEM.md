# The Curated Sanctuary — Design System
### PRISM Design Language

---

## Philosophy

The Curated Sanctuary is a design philosophy, not just a component library. It treats digital interfaces as curated spaces — places of focus, calm, and deliberate craft. The aesthetic rejects the frantic density of standard SaaS and reaches instead toward the editorial warmth of a premium print publication.

Three ideas anchor every decision:

- **The Tactile Manuscript** — interactions should feel like handling high-quality paper. Deliberate, smooth, layered.
- **Ma (間)** — the Japanese concept of negative space as an active element. Space is not absence; it is rhythm, focus, and breathing room.
- **Hygge** — the Danish pursuit of soulful warmth. The interface should feel human-centric and welcoming, never cold or sterile.

> **The north star question:** *Does this element feel like it has been carefully chosen for a physical manuscript, or does it feel like a placeholder in a generic template?*

---

## Palette — Deep Forest

All colors are defined as CSS custom properties on `:root`.

### Raw tokens

| Token | Value | Role |
|-------|-------|------|
| `--canvas` | `#F9F7F2` | Page background — warm cardstock with noise texture |
| `--forest` | `#0B2B1B` | Deepest surface — sidebar, primary buttons |
| `--forest-1` | `#0E3322` | Forest hover state |
| `--forest-2` | `#153E2B` | Forest active / pressed |
| `--forest-3` | `#1F4C37` | Forest selected highlight |
| `--moss` | `#6B8E23` | Accent — active states, focus rings, growth indicators |
| `--moss-soft` | `#8AA94B` | Lighter moss for secondary accents |
| `--moss-deep` | `#53701A` | Moss on light surfaces |
| `--moss-wash` | `#EEF1E0` | Moss tint for backgrounds |
| `--ink` | `#1A231D` | Primary text — pressed ink quality |
| `--ink-2` | `#3A4640` | Secondary text |
| `--ink-3` | `#5C6A61` | Tertiary text, labels |
| `--ink-4` | `#8B9288` | Muted / placeholder text |
| `--cream` | `#EFE7D4` | Raised surface — cards, panels |
| `--cream-2` | `#F2EBDA` | Slightly lighter raised surface |
| `--parchment` | `#E4DAC4` | Sunken / input surface |
| `--sage` | `#A8B89C` | Border accents, secondary highlights |
| `--sage-wash` | `#E6EBDF` | Sage tint |
| `--clay` | `#C96F3E` | Warm accent (use sparingly) |
| `--clay-soft` | `#E3946C` | Clay hover |
| `--clay-deep` | `#A85628` | Clay on light backgrounds |
| `--clay-wash` | `#F5E4D8` | Clay tint |
| `--warm-100–700` | — | Neutral warm scale for utility surfaces |

### Semantic aliases

These are the tokens components should reference. Never use raw tokens in component styles.

| Semantic token | Maps to | Use |
|---------------|---------|-----|
| `--bg` | `--canvas` | Page background |
| `--bg-raised` | `--cream` | Card / panel surfaces |
| `--bg-sunken` | `--parchment` | Input backgrounds |
| `--fg-1` | `--ink` | Primary text |
| `--fg-2` | `--ink-2` | Secondary text |
| `--fg-3` | `--ink-3` | Labels, captions |
| `--fg-muted` | `--ink-4` | Placeholder, disabled text |
| `--fg-on-forest` | `#E8E3D3` | Text on forest-colored surfaces |
| `--fg-on-forest-2` | `#AAB5A6` | Secondary text on forest surfaces |
| `--accent` | `--moss` | Interactive accent |
| `--border` | `rgba(26,35,29,0.08)` | Default border |
| `--border-strong` | `rgba(26,35,29,0.16)` | Emphasized border |
| `--border-on-forest` | `rgba(232,227,211,0.12)` | Border on forest surfaces |

### Usage principles

- Never use pure black (`#000`) or pure white (`#fff`) — use ink and canvas.
- All shadows use `rgba(11, 43, 27, ...)` — green-tinted, not grey, so even elevation carries warmth.
- Clay is a secondary accent. Use only when a warm highlight is needed that is distinct from moss.

---

## Typography

Three typefaces. Each has a precise role and must not be used interchangeably.

| Token | Family | Fallbacks | Role |
|-------|--------|-----------|------|
| `--font-serif` | Newsreader | Iowan Old Style, Hoefler Text, Georgia | Headings, titles, editorial body, inner thoughts |
| `--font-sans` | Instrument Sans | Inter, system-ui | All UI chrome — labels, buttons, metadata, body copy |
| `--font-mono` | JetBrains Mono | SF Mono, Menlo, Consolas | Code, technical strings |

### Scale in use

| Element | Font | Size | Weight | Notes |
|---------|------|------|--------|-------|
| Scenario title | serif | 18px | 400 | `letter-spacing: -0.01em` |
| Panel body text | sans | 14px | 400 | `line-height: 1.7` |
| Inner thought | serif | 13px | 400 | `font-style: italic` |
| Tag label | sans | 10px | 500 | `text-transform: uppercase`, `letter-spacing: 0.08em` |
| Button | sans | 12–13px | 500 | `letter-spacing: 0.005em` |
| Section header | sans | 11px | 500 | `text-transform: uppercase`, `letter-spacing: 0.08em` |
| Meta / caption | sans | 11–12px | 400 | `color: --fg-3` |

### Principles

- Line heights are generous: `1.65` for body, `1.7` for reading text, `1.4` for tight labels.
- Serif is the emotional register. Use it for content users read; sans for UI they interact with.
- Never track (letter-space) serif type wider — let it breathe naturally.

---

## Spacing & Layout

Built on an **8px base grid**. All spacing values are multiples of 4 or 8.

| Scale | Value | Common use |
|-------|-------|------------|
| 4px | `0.25rem` | Tight gap between inline elements |
| 6px | `0.375rem` | Chip gap, icon-to-label |
| 8px | `0.5rem` | Component internal padding (small) |
| 10px | `0.625rem` | Chip padding, row gap |
| 12px | `0.75rem` | Card internal padding (compact) |
| 16px | `1rem` | Standard internal padding |
| 20px | `1.25rem` | Panel padding |
| 24px | `1.5rem` | Card padding |
| 28px | `1.75rem` | Page-level content padding |

**Negative space is not waste.** The layout should feel like content placed on a desk rather than text packed into a box.

---

## Border Radius — The Arboreal Grid

Radius increases with depth and softness. Deeper, more modal elements are rounder; sharp, inline elements are tighter.

| Token | Value | Use |
|-------|-------|-----|
| `--radius-xs` | `4px` | Tiny UI elements, tags |
| `--radius-sm` | `8px` | Buttons, inputs, chips |
| `--radius-md` | `10px` | Secondary cards |
| `--radius-lg` | `16px` | Primary cards, panels |
| `--radius-xl` | `20px` | Chat bar, floating containers |
| `--radius-full` | `999px` | Pills, full-round chips |

---

## Shadows — Warm Elevation

All shadows are forest-tinted (`rgba(11, 43, 27, ...)`), never neutral grey. This ensures even drop shadows carry the warmth of the palette.

| Token | Value | Use |
|-------|-------|-----|
| `--shadow-leaf` | `0 1px 2px …0.06, 0 2px 4px …0.04` | Subtle lift — chips, small buttons |
| `--shadow-page` | `0 2px 4px …0.04, 0 12px 24px …0.06` | Card elevation |
| `--shadow-stack` | `0 4px 8px …0.06, 0 32px 48px …0.10` | Floating panels, dropdowns |
| `--shadow-inset-press` | `inset 0 2px 4px …0.12` | Pressed / active button state |
| `--shadow-inset-field` | `inset 0 1px 2px …0.06` | Input fields — sunken, tactile |

Inset shadows on inputs create the "pressed paper" effect. Never use flat or purely coloured backgrounds for inputs — the inset shadow is required.

---

## Motion — Weighted Growth

Animations should feel like organic growth, not mechanical transitions. Slow, purposeful, and weighted.

| Token | Value | Use |
|-------|-------|-----|
| `--ease-quint` | `cubic-bezier(0.83, 0, 0.17, 1)` | Standard transitions (hover states, toggles) |
| `--ease-out-quint` | `cubic-bezier(0.22, 1, 0.36, 1)` | Entrance animations (elements arriving) |
| `--duration-micro` | `200ms` | Hover, focus, colour transitions |
| `--duration-std` | `400ms` | Layout changes, panel opens |
| `--duration-reveal` | `700ms` | Full content reveals |

### Keyframes in use

**`panelIn`** — perspective cards entering the split view:
```css
from { opacity: 0; transform: scale(0.97) translateY(8px); transform-origin: top left; }
to   { opacity: 1; transform: scale(1) translateY(0); }
```
The slight scale-up from `0.97` creates an "unrolling" quality — the card grows into place.

**`messageIn`** — dialogue turns arriving:
```css
from { opacity: 0; transform: translateY(6px); }
to   { opacity: 1; transform: translateY(0); }
```

### Principles

- No instantaneous state changes. Even a colour swap should use `transition: 200ms`.
- Avoid bounce easings — they break the calm.
- Stagger entrance animations when multiple elements arrive together (e.g., `animation-delay` per panel index × 150ms).

---

## Components

### Surface hierarchy

Three levels of surface, always expressed through the palette:

| Level | Background | Shadow | Radius |
|-------|-----------|--------|--------|
| Page | `--canvas` + noise texture | — | — |
| Raised (cards, panels) | `--cream` | `--shadow-page` | `--radius-lg` |
| Sunken (inputs, tags) | `--parchment` | `--shadow-inset-field` | `--radius-sm` |
| Floating (dropdowns, tooltips) | `--canvas` | `--shadow-stack` | `--radius-lg` |
| Dark (sidebar, primary buttons) | `--forest` | `--shadow-leaf` | `--radius-sm` |

### Buttons

Three variants, each with a distinct weight:

| Variant | Background | Border | Use |
|---------|-----------|--------|-----|
| Primary | `--forest` | none | The single most important action |
| Secondary | `--cream` | `--border-strong` | Supporting actions |
| Ghost pill | transparent | `--border-strong` | Filters, toggles, chips |

Active/pressed state always uses `--shadow-inset-press` — the "ink soaking in" effect.

### Inputs

- Background: `--parchment` (sunken)
- Border: `--border-strong` at rest; `--moss` on focus
- Focus ring: `box-shadow: 0 0 0 3px --moss-wash` (soft glow, not harsh outline)
- Placeholder: `--fg-muted`

### Persona chips / pills

- Deselected: `--canvas` background, `--border-strong` border, `--fg-2` text
- Selected: `--forest` background, no border, `--fg-on-forest` text
- The dot indicator on selected state uses `rgba(232,227,211,0.5)` — not pure white

### Panels (perspective cards)

- Left border accent: `3px solid var(--panel-color)` — the persona's identity colour
- Background: `--cream`
- Internal tag block: `--parchment` background — sunken within the raised card, creating a third depth layer

### Tooltips

- Background: `--forest`
- Text: `--fg-on-forest`
- No arrow. Appears `8px` below trigger. Opacity transition at `--duration-micro`.

---

## Iconography

- Stroke-based SVG only. Fill icons are not used.
- `stroke-width: 2` as the standard weight; `stroke-linecap: round` where applicable.
- Size: `14px` for toolbar/UI icons, `16px` for send/action icons, `48px` for empty state illustrations.
- Icons inherit `currentColor` — never hardcoded colour values.

---

## The Noise Texture

The canvas background includes a subtle SVG noise filter layered over `#F9F7F2`. This is non-negotiable — it is what separates the surface from feeling like a flat digital render and gives it the warm cardstock quality central to the Tactile Manuscript principle.

```css
background-image: url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='180' height='180'%3E%3Cfilter id='n'%3E%3CfeTurbulence type='fractalNoise' baseFrequency='0.9' numOctaves='2' stitchTiles='stitch'/%3E%3CfeColorMatrix values='0 0 0 0 0.10  0 0 0 0 0.17  0 0 0 0 0.11  0 0 0 0.035 0'/%3E%3C/filter%3E%3Crect width='100%25' height='100%25' filter='url(%23n)'/%3E%3C/svg%3E");
background-repeat: repeat;
```

The `FeColorMatrix` values are tuned to the forest palette — the noise itself has a faint green tint.

---

## Do / Don't

| Do | Don't |
|----|-------|
| Use serif for editorial content and inner states | Use serif for buttons, labels, or data |
| Use inset shadows on all input fields | Use flat backgrounds for inputs |
| Let negative space breathe | Fill every gap with content or decoration |
| Animate at `400ms` with quint easing | Use linear or bounce easing |
| Use forest-tinted shadows | Use neutral grey shadows |
| Use `--moss` for focus states | Use blue for focus rings |
| Layer surfaces (page → raised → sunken) | Use a single flat background level |
| Stagger entrance animations | Animate all elements simultaneously |
