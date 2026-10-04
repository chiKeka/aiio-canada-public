# Refero-inspired design direction

Status: adopted for the local AIIO Canada interface on 2026-08-31.

Sources of inspiration: [Refero Styles](https://styles.refero.design/), its [Seline Analytics](https://styles.refero.design/style/7967c6d9-e50c-42b5-b4d1-74003ba41781), [Ventriloc](https://styles.refero.design/style/f99aca3e-5289-4595-a7cc-77a72052f4b8), and [Decide AI](https://styles.refero.design/style/5d9e1cc2-4b81-40fe-aa92-640f2e1d7420) references. This is a translation of general design patterns, not a copy of Refero or any referenced brand or asset.

The 2026-09-01 product pass also reviewed [Together AI](https://styles.refero.design/style/461da0f0-fde6-46bc-8137-7eca006260a8), [Visitors](https://styles.refero.design/style/e7876363-181a-44a9-9e5c-2255cf98aea5), [Ui](https://styles.refero.design/style/0fd67ec5-7e9c-4ca9-b368-5d9c7388477a), [Harness.io](https://styles.refero.design/style/6f3652cf-583f-411d-a117-3a03f6342917), and [Impilo](https://styles.refero.design/style/b44b0bb2-4ba3-4599-9706-3c3e0c8c2522). Their compact command navigation, restrained instrument surfaces, clinical data accents, and research-console labelling informed the interface; AIIO retains its own teal, paper and warning semantics.

## Product expression

AIIO should feel like a quiet analyst's desk built for consequential public decisions: calm, precise, dated, and inspectable. The product surface is the proof. Decorative marketing treatments should never compete with evidence status, uncertainty, or the project decision.

The two interface modes now use distinct but related visual voices:

- Decision Mode is the warm-paper executive briefing: quiet, legible and oriented around a project decision.
- Research Mode is the dark observatory console: instrument-like, explicitly exploratory and oriented around mechanisms, evidence gates and model state.

## Adopted principles

- Use a warm paper canvas and white working surfaces.
- Use a geometric sans-serif throughout, with regular-weight display type and tight tracking.
- Let hairline borders provide most of the structure; reserve meaningful elevation for the primary interactive workbench.
- Use deep teal as the single brand/action accent.
- Keep amber and rust only for analytical warnings, assumptions, and negative movements.
- Use compact pill controls for modes, branches, evidence classes, and dated states.
- Use dark, inverted analytical surfaces for the Research Mode header, framing question and graph; return to warm paper for long-form methodology and tables.
- Reserve mint in Research Mode for active-state and signal punctuation. It must not replace amber/rust warning semantics.
- Prefer generous section rhythm around dense, compact evidence cards.
- Use subtle category-tinted panels only when the tint encodes an evidence
  domain; never use pastel colour as decoration or to imply a positive result.

## AIIO-specific constraints

- Evidence classes retain distinct treatments because their meaning is more important than strict monochrome restraint.
- Warning colour cannot imply a quantified cost impact.
- Scenario controls must remain labelled as counterfactual and uncalibrated.
- No decorative illustration, stock photography, or borrowed brand asset is needed; the decision brief, graph, and evidence panels are the visual product.
- Accessibility, dated provenance, and the observed/inferred/assumed/scenario boundary outrank visual novelty.

## Component rules

- Canvas: warm off-white.
- Cards: white or near-white, 1px warm-grey border, 16px radius.
- Inputs: muted paper fill at rest, white on hover/focus, with visible teal focus treatment.
- Primary action: deep teal filled pill; use sparingly.
- Secondary action: white or transparent pill with a hairline border.
- Research canvas: near-black with white type, mint signal punctuation and sharp-edged light instrument cards.
- Research actions: white or transparent pills; mint denotes active research state, not a positive finding.
- Display headings: regular weight, tight tracking, short line length.
- Metadata: compact mono, uppercase only for short labels.
- Shadows: one soft workbench elevation; otherwise rely on borders.
- Focus: visible teal outline on all interactive controls.

## Rejected patterns

- Copying Refero or Seline names, layouts, copy, mascots, screenshots, or assets.
- Generic glassmorphism, gradients, heavy shadows, or colourful dashboard chrome.
- Hiding methodological caveats to make the product appear more certain.
- Turning the executive workspace into a promotional landing page.
