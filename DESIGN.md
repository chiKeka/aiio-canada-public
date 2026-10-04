# AIIO Canada — Design System

> Civic observatory on warm paper; infrastructure systems in a midnight command room.

**Theme:** light-first analytical product with a dark graph surface

AIIO Canada is a dual-use public research program and executive decision tool. The interface must let an Assistant Deputy Minister, Treasury Board analyst, infrastructure planner, researcher, or investor understand the current decision boundary in seconds and inspect the evidence in depth without changing products.

The visual system combines useful patterns identified through [Refero Styles](https://styles.refero.design/): the calm editorial restraint of Seline Analytics, Ventriloc's warm-paper data-observatory voice, Clearbit's surface-tint and hairline discipline, Together AI's research-console hierarchy, the focused mission-control structure of Harness.io, and the strict semantic use of bright data colours in Impilo. AIIO does not reproduce any one reference. Its own voice is public-sector, evidence-led, Canadian, and deliberately sober.

### Reference translation

| Reference pattern | AIIO translation | Boundary |
| --- | --- | --- |
| Quiet editorial analytics | Warm paper, light-weight display type, generous whitespace and hairline structure in Decision Mode | No borrowed brand palette, mascot or signature composition |
| Editorial data observatory | Monospace evidence labels and one restrained amber signal for unresolved gates | Amber must remain semantic, never ornamental |
| Research console | Compact methodological metadata, low-elevation category cards and explicit active/missing states in Research Mode | No decorative pastel dashboard wall; each surface must encode a research role |
| Mission-control surface | One midnight section for graph pathways and system propagation | Do not scatter dark cards through the briefing surface |
| Clinical semantic colour | Observed, inferred, assumed and scenario states retain distinct labels and tones | Colour never substitutes for status text |

## Product modes

### Decision Mode

The default working surface. It answers: “What can I use in a decision today, what is withheld, and what must be resolved before the next gate?”

- Warm paper canvas and white working cards.
- The project definition and decision boundary are visible in the first viewport.
- Results lead; method and source detail remain one step away.
- Withheld results are visible and explained, never replaced by a zero or a vague empty state.

### Research Mode

The public-method surface. It answers: “Where did this come from, how was it transformed, and what is still assumed?”

- Same light canvas and typography so the two modes feel like one product.
- More source IDs, dates, definitions, diagnostics, and reproducibility detail.
- The graph may use the dark command surface because relationships are easier to follow with luminous semantic strokes.

## Colour tokens

| Token | Value | Role |
| --- | --- | --- |
| Paper canvas | `#f7f6f1` | Page background; warm enough to read as a briefing surface |
| Paper raised | `#fbfaf5` | Low-elevation analytical panels |
| Pure white | `#ffffff` | Forms, focal result cards, selected controls |
| Hairline | `#d8dcd7` | Primary structural border |
| Ink | `#0d2b36` | Display text, strong labels, core navigation |
| Body | `#536764` | Explanatory text and secondary labels |
| Teal signal | `#145f59` | Primary action, observed evidence, active state |
| Teal wash | `#dceee8` | Selected controls and observed-evidence backgrounds |
| Cyan data | `#57c6c0` | Graph strokes and data emphasis on dark surfaces only |
| Steel inference | `#6b8798` | Inferred evidence and secondary series |
| Amber assumption | `#d66b35` | Assumed inputs, scenarios, unresolved caution |
| Amber wash | `#fff0e3` | Assumption and withheld-result backgrounds |
| Midnight canvas | `#081e28` | Dependency graph and system pathway surfaces |
| Midnight raised | `#103542` | Graph inspector and dark analytical cards |

### Semantic colour rules

- Teal means observed, available, or active. It is not decoration.
- Steel blue-grey means inferred or transformed evidence.
- Amber means assumed, scenario, withheld, or unresolved. Copy must say which.
- Cyan appears primarily on the dark graph surface and carries data/path meaning.
- Red is reserved for an actual error or failed system state, not ordinary uncertainty.
- Never use colour alone: every status also needs a text label.

## Typography

- **Interface and display:** Geist Sans, weights 400–600.
- **Data and provenance:** Geist Mono, weights 500–600.
- Display headings use light-to-medium weight, tight tracking, and short line lengths. Authority should come from clarity and scale, not boldness.
- Body copy defaults to 14–16px with generous line height. Dense provenance may use 10–12px monospace but must remain readable.
- Sentence case is standard. Uppercase is limited to short eyebrows, evidence labels, and source metadata.

### Type scale

| Role | Size | Weight | Line height |
| --- | --- | --- | --- |
| Display | `clamp(40px, 5vw, 76px)` | 400 | 0.98–1.05 |
| Page heading | `36–56px` | 400–500 | 1.04–1.1 |
| Section heading | `28–36px` | 500 | 1.12 |
| Card heading | `16–22px` | 500 | 1.25 |
| Body | `14–16px` | 400 | 1.55–1.75 |
| Evidence label | `10–11px` | 600 mono | 1.4 |

## Spacing and shape

- Base unit: `4px`.
- Main page width: `1440px` maximum.
- Reading width: `720–900px` depending on purpose.
- Page gutters: `20px` mobile, `32px` tablet, `48px` desktop.
- Section rhythm: `48–80px`.
- Card padding: `20–28px`.
- Card radius: `10–12px`.
- Pills: full radius, reserved for compact status, mode, or filter controls.
- Use hairline borders and surface tint as the main separators. Resting cards do not use decorative shadows; elevation is reserved for transient menus and overlays.

## Surface hierarchy

1. Paper canvas: the page and narrative context.
2. Paper raised: grouped analytical regions.
3. Pure white: project inputs, focal decisions, selected details.
4. Midnight canvas: dependency graph and system relationships.
5. Midnight raised: selected graph node, metrics, mechanism detail.

Do not scatter dark cards across the light workspace. The dark surface is a purposeful transition into the model’s system view.

## Core components

### Mode switch

A compact two-segment control labelled Decision and Research. The active segment uses teal fill; the inactive segment remains neutral. Mode changes the information hierarchy, not the underlying evidence.

### Decision signal rail

Four concise states shown near the top of Decision Mode:

1. Market context — available.
2. Baseline outlook — withheld when the forecast horizon gate fails.
3. AI cost increment — unquantified until calibration passes.
4. Graph pathways — inspectable, with assumption status shown.

This is an executive scan, not a KPI vanity strip. Never show a number where the model has withheld one.

### Evidence pill

Each evidence claim carries one of: `observed`, `inferred`, `assumed`, or `scenario`. Add `withheld` or `not assessed` in prose where applicable. The pill identifies epistemic status; it does not grade desirability.

### Decision boundary card

The most important result card. It states what the tool can and cannot support, the relevant date and release, and the next defensible action. When a value is withheld, the explanation and failed gate replace the value.

### Identification gate console

Research Mode shows the causal-estimation contract as a staged gate: treatment, outcome, controls, panel assembly, diagnostics and review. Available controls may be shown as ready, but they must never visually outweigh a missing authorizing treatment or outcome. A withheld effect is rendered as a deliberate publication state with null values—not as zero, an empty chart or a disabled forecast card.

### Dependency graph

The graph lives on the midnight canvas. Nodes use pale semantic fills for recognizability, active paths glow in cyan, inactive paths recede, and the selected-node inspector explains weights, lags, absorption, and evidence status. The accessible path list is always available.

### Charts and metrics

- Axes and units must be explicit.
- Show source date and geography near the chart.
- Use direct labels where possible.
- Tooltips add detail but must not contain the only explanation.
- Scenarios and observed series must never share an unlabeled visual treatment.

## Motion

- Motion is functional and brief: active-state transitions, graph selection, disclosure, and scroll-to-detail.
- No decorative ambient animation.
- Respect `prefers-reduced-motion`.
- A result must not depend on animation to become legible.

## Accessibility

- WCAG AA contrast minimum for text and interactive elements.
- Visible keyboard focus on every control.
- Minimum 40px target size for primary touch interactions when space permits.
- Every icon-only control needs an accessible name.
- Graph relationships require a text alternative.
- Status and evidence meaning must survive grayscale and screen readers.

## Do

- Put the decision boundary before supporting detail.
- Use realistic project language and dated public evidence.
- Let warm whitespace and hairlines create hierarchy.
- Reserve the strongest accent for the current action or selected evidence.
- Make “withheld,” “not assessed,” and “unknown” explicit product states.
- Keep source IDs, release versions, and evidence dates easy to find.

## Do not

- Do not present a dashboard wall of equally weighted cards.
- Do not use gradients, glassmorphism, or ornamental infrastructure illustrations.
- Do not imply precision with decorative gauges or percentages.
- Do not turn graph assumptions into forecast claims.
- Do not use generic green/red “good/bad” semantics for market pressure.
- Do not hide methodological caveats in a footer or tooltip.
- Do not copy a Refero reference’s brand palette, mascot, typography, or signature treatment.
