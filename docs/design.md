# Design system — private press

Graphia is a small private press for documents. Warm paper, espresso ink, hairline
rules, folio numbers, and one electric registration mark. The landing page sells the
run; the converter is the desk where you start it.

The previous poolside arcade design is retired. Do not reintroduce the cabinet frame,
marquee bulbs, bubblegum accents, offset black shadows, Poppins, or the pool lane.

## Color

Balance by area: **70% sand, 25% espresso, 5% cobalt**. Cobalt is an action and state
color, never a section background.

| Token | Hex | Role |
| --- | --- | --- |
| `--sand-50` | `#FBF7F0` | Sheets, cards, inputs |
| `--sand-100` | `#F4ECDF` | Page canvas |
| `--sand-200` | `#EADFCD` | Footer, hover fill, tracks |
| `--sand-300` | `#DFD0BB` | Reserved surface step |
| `--espresso-900` | `#241B15` | Headings, dark bands |
| `--espresso-700` | `#3A2C22` | Reserved strong text |
| `--espresso-500` | `#6A5647` | Body and secondary text |
| `--muted-on-dark` | `#B9A896` | Secondary text on espresso |
| `--cobalt` | `#0047AB` | Primary action, focus, selected state |
| `--cobalt-deep` | `#003A8C` | Primary action hover |
| `--cobalt-light` | `#8FA6F2` | Accent text on espresso only |
| `--cobalt-tint` | `#E7EBF7` | Selected row, dropzone hover |
| `--line` | `#DCCDB6` | Decorative hairline |
| `--line-strong` | `#8A7663` | Control and input borders |
| `--brick` | `#8E3B2A` | Failures and destructive actions |
| `--brick-tint` | `#F3E4DE` | Failure alert fill |

Contrast checks at these values:

| Pair | Ratio |
| --- | --- |
| Espresso on sand | 14.4 |
| Muted text on sand | 5.9 |
| Cobalt on sand | 7.2 |
| Sand on cobalt | 7.9 |
| Muted sand on espresso | 7.3 |
| Cobalt light on espresso | 7.2 |
| Brick on sand | 6.4 |

Cobalt on espresso is only 2.0, so cobalt text is not used on dark bands. On espresso,
primary buttons keep a sand border and the accent appears as `--cobalt-light` or a
small mark.

## Type

**Manrope** is the only interface typeface, weights 400, 500, 600. Never use italics
and never go above semibold. **Geist Mono** appears only for the run number inside a
ticket; no mono labels, kickers, or timestamps.

Every text element uses one of these classes. They are defined once in
`client/app/globals.css` and applied in markup.

| Class | Size / line | Weight |
| --- | --- | --- |
| `heading-1` | 60 / 60 | 600 |
| `heading-2` | 48 / 48 | 600 |
| `heading-3` | 36 / 40 | 600 |
| `heading-4` | 30 / 36 | 600 |
| `heading-5` | 24 / 32 | 600 |
| `heading-6` | 20 / 28 | 600 |
| `title-1` | 20 / 28 | 500 |
| `title-2` | 18 / 28 | 500 |
| `title-3` | 16 / 24 | 500 |
| `title-4` | 14 / 20 | 500 |
| `body-1` | 16 / 24 | 600 |
| `body-2` | 16 / 24 | 500 |
| `body-3` | 16 / 24 | 400 |
| `body-4` | 14 / 20 | 600 |
| `body-5` | 14 / 20 | 500 |
| `body-6` | 14 / 20 | 400 |
| `caption-1` | 14 / 20 | 500 |
| `caption-2` | 14 / 20 | 400 |
| `caption-3` | 12 / 16 | 600, uppercase, `0.08em` |
| `caption-4` | 12 / 16 | 500 |
| `caption-5` | 12 / 16 | 400 |

Buttons use `Button-md` (16 / 24 semibold) by default, `Button-sm` for compact
navigation actions, and `Button-lg` for hero and final actions. Main buttons use 8px
vertical and 12px horizontal padding.

The hero heading is the only gradient in the product: espresso `#241B15` to
`#6A5647`, clipped to the text. Backgrounds stay flat.

## Spacing and radius

Only tokens: 2, 4, 8, 12, 16, 24, 32, 40, 48, 64, 80, 96. Radii: 2, 4, 6, 8, 12, 16,
full. Nested radii follow `outer − gap`; when the result is under 2, the inner shape
stays square.

## Layout

- Landing content: `min(1200px, 100% - 96px)`, 48px gutters below 1080, 32px below 560.
- App content: `min(1120px, 100% - 96px)`.
- Legal pages: 720px measure.
- Auth cards: 420px measure, 480px on tablet.
- The nav floats: sticky, 16px off the top, translucent sand with a 14px blur, 1px
  hairline, radius 16. It is never a flush full width bar.

## Landing page

`/` is public and uses the classic hero plus sections layout.

1. Floating nav: brand, four section links, sign in, one cobalt CTA.
2. Hero: eyebrow, 60px heading, subhead, primary CTA, text link, a guest link,
   three product facts.
3. Specimen sheet: a sample run ticket with crop marks, a perforation, a metadata
   grid, and a cobalt stamp. It is labelled as a sample.
4. Format matrix: ten rows, index, `DOCX → PDF` chips, description, accepted
   extensions. This replaces a three card feature grid.
5. Benefits: four numbered rows with hairlines.
6. Tagline reveal: full bleed espresso, two explicit lines, one word at a time.
7. How it works: three steps on a hairline rail.
8. Privacy: espresso band, copy plus a three node flow with cobalt arrows.
9. FAQ: eight native `details` items in two columns.
10. Final CTA: espresso band with a cobalt button.
11. Footer: sand 200, links, Iconscout credit, and retention line.

Section rules are hairlines that span the content width. Cards are only used for the
specimen, the upload panel, the ticket, and the action panel.

## App

- `/convert`: intro with three limits, a sheet style upload panel, grouped modes
  with radio semantics, a ready preview that names the input and output, a phase
  rail while the upload runs, and a three step footer.
- `/library`: every mode grouped by intent. Each row is a link into `/convert`
  with that mode selected. Loading uses mode shaped skeletons, errors offer a
  retry, and a guest line explains the download gate.
- `/conversions/[id]`: a ticket on sand 50 with a status chip, a metadata grid, a
  four pixel progress rule, a run state row, and a sticky collect panel. Elapsed
  time is printed in the foot while a run is live.
- Guest sessions show a dot and a `Sign in` action in the nav. A completed guest
  run replaces the download button with the sign in gate; the ticket is claimed
  by the account during login.
- `/login`, `/signup`, 404: split layout, espresso aside with facts, sand form card.
  Both auth pages offer `Continue as guest` under the SSO actions.
- `/privacy`, `/terms`: 720px reading measure with hairlines.

States are explicit: hover, `translateY(1px)` press, cobalt focus ring (sand on
espresso), loading skeletons, and inline errors. Destructive actions use a two step
confirm inside the panel, never `window.confirm`.

## Logo

The mark is the Unicons `file-graph` glyph by IconScout, used under the IconScout
Simple License:

- 32px espresso tile, radius 8, glyph in sand.
- A 6px cobalt registration square hangs off the top right corner.
- Wordmark `Graphia` in Manrope 600, 18px, with the caption `Document atelier`.
- On espresso surfaces the tile inverts to sand and the glyph to espresso; the
  registration square becomes `--cobalt-light`.

License text: `client/public/brand/LICENSE-unicons.txt`. Attribution appears in the
landing footer. Do not recolor the mark outside these two tones, rotate it, or use the
glyph as a decorative icon.

## Motion

Base curve `cubic-bezier(0.22, 1, 0.36, 1)`. Color and opacity shifts run 300ms,
layout and position 500ms, the tagline 600ms per word. Animate only transform and
opacity. The tagline uses one IntersectionObserver per word, with the final state
rendered immediately under `prefers-reduced-motion`. No scroll listeners.

The authored moment is the ticket stamp: when a run becomes ready, the status chip
stamps in with a short scale and rotation, and the progress rule fills to the end.
Supporting motion explains state rather than decorating it: mode rows and library
rows enter with a capped stagger, the selected check scales in, the dropzone shows
a single scan line while dragging, the phase rail advances through upload steps,
and live status dots pulse. Progress fills use `scaleX`, never width. Under
`prefers-reduced-motion` all delays and looping animations are removed; state
changes stay visible.

## Copy rules

- Sentence case for headings, buttons, and labels.
- No hyphens inside sentences; rewrite the phrase.
- No italics, no exclamation marks, no cute interjections.
- No orphaned words: `text-wrap: balance` on headings, `pretty` on body.
- Never invent customers, logos, prices, or statistics. Product facts come from the
  repository: 25 MB per file, ten modes, 24 hour retention, direct R2 upload.

## Do not

- Use a background gradient anywhere, including the tagline or footer.
- Border only one side of a card. Full borders or none; hairlines between rows are
  dividers, not card borders.
- Build three equal feature cards. Steps and format rows are lists, not cards.
- Add a second accent color. Cobalt is the only pop; failures use brick.
- Add mono labels. Geist Mono is limited to the ticket number.
