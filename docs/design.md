# Design system — poolside arcade

Graphia looks like a small arcade cabinet at the edge of a swimming pool: flat pool blue, arcade ink, bubblegum controls, chrome trim, and lane line progress.

Built against the `landing-page-design` skill (elayadesign/ai-design-skills), installed globally.

## Direction

- One primary action: convert one document.
- One visual world: poolside arcade, not a generic dark SaaS dashboard.
- Public landing page at `/`; authenticated converter at `/convert`.
- The cabinet is the app frame; the control deck is the form; the run ticket is the job.
- **Color balance:** about 70% pool blue, 25% arcade ink, 5% bubblegum. Pool blue owns the public surfaces, ink owns the structure and contrast sections, bubblegum is reserved for actions and state.

## Color

| Token | Value | Role |
|---|---|---|
| `--ink` | `#131209` | Page and cabinet background |
| `--ink-2` | `#181818` | Marquee, footer, panels |
| `--ink-3` | `#1F1F1F` | Cards and dropzone |
| `--ink-4` | `#272727` | Hover/selected surfaces |
| `--ink-5` | `#313131` | Borders and inactive controls |
| `--pool` | `#1FAAC4` | Hero screen, ticket, primary surface |
| `--pool-deep` | `#0F7C93` | Pool text on light surfaces |
| `--pool-soft` | `#A8ECF4` | Focus rings and subtle pool text |
| `--bubble` | `#F06BB1` | Primary action, active status, accents |
| `--bubble-deep` | `#D94A96` | Bubblegum hover and links |
| `--foam` | `#F6FBF7` | Light surfaces and text on ink |
| `--chrome` | `#6E8A92` | Cabinet trim |
| `--chrome-light` | `#C3D5D8` | Inner trim and input borders |
| `--muted` | `#9BB0B5` | Secondary text on ink |
| `--ink-muted` | `#2A3D41` | Secondary text on pool/foam |
| `--danger` | `#D9534F` | Fault state |

Surfaces are flat. The only gradient is the hero heading text rule from the skill.

## Type

- **Poppins** — the single interface typeface. Weights 400, 500, 600, 700.
- **Geist Mono** — allowed only for IDs, lane labels, status chips, and numeric metadata.
- No italics. No weights above bold.
- Sizes only from the Tailwind scale: 12, 14, 16, 18, 20, 24, 30, 36, 48, 60, 72, 96, 128.
- Headings use `text-wrap: balance`; body copy uses `text-wrap: pretty`.
- Hero and auth headings cap at 680px with intentional line breaks.

## Spacing and radius

Spacing is limited to the skill table: 0, 2, 4, 8, 12, 16, 24, 32, 40, 48, 64, 80, 96.

Radius is limited to 0, 2, 4, 6, 8, 12, 16, 24, full. Nested radii subtract the gap.

## Landing page

`/` is a public product page:

1. Sticky product nav with one primary action.
2. Pool blue hero with headline, subheadline, proof limits, and a product ticket preview.
3. Feature grid on pool blue.
4. Ink “How it works” lane with three steps.
5. Word by word tagline reveal on ink.
6. Pool blue FAQ.
7. Ink final CTA.
8. Ink footer with privacy and terms.

The converter lives at `/convert` and keeps the cabinet shell.

## Components

- **Cabinet** — chrome framed shell with marquee bar and bulb strip.
- **Control deck** — dark upload panel with a dashed pool dropzone.
- **Mode cards** — format pair chips (DOCX to PDF), selected with a bubblegum border.
- **Run ticket** — pool blue pass with status chip, metadata grid, lane meter.
- **Pool pass stub** — auth page membership card.
- **Lane meter** — queue, run, dry stops with a droplet marker.
- **Status chip** — queued, running, complete, failed, expired.

## Icons

Phosphor icons only. One stroke weight. Icons are decorative unless they carry an action; status always has a text label.

## Motion

- Base curve: `cubic-bezier(0.22, 1, 0.36, 1)`.
- Layout/position changes: 500ms.
- Color and opacity: 300ms.
- Only transform and opacity are animated.
- Marquee bulbs pulse; pool bubbles rise; droplet marker bobs while running; joystick wobbles while processing.
- The tagline section reveals word by word with one IntersectionObserver per word.
- Reduced motion shows final states immediately.

## Accessibility

- Skip link to `#main-content`.
- Visible focus ring on every interactive element.
- Status uses text plus color.
- 44px minimum button height.
- 390px layout checked for horizontal overflow.
- Legal links, branded 404, favicon, OG image, and metadata are present.
