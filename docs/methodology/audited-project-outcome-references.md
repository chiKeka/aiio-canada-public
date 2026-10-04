# Audited public-project outcome reference cases

## Purpose

This intake preserves named estimate-to-latest-cost and planned-to-actual
schedule evidence from the Ontario Auditor General's 2024 performance audit,
[Procurement and Delivery of Selected Infrastructure Projects](https://www.auditor.on.ca/en/content/annualreports/audits/en2024/AR-PA_infrastructureON_en24.html).
It improves the Observatory's outcome-field discovery and reference-case layer.
It does not authorize the AI-attributable effect.

The pipeline inputs and outputs are:

- `data/raw/oago_selected_infrastructure_projects_2024/2026-09-01_88cdf8a0966d.pdf`;
- `data/manual/oago_selected_infrastructure_outcomes_2024.json`;
- `data/processed/oago_audited_project_outcomes.csv`; and
- `data/model-runs/oago_audited_project_outcomes_v0.1.json`.

Run the transformation with `npm run outcomes:audit:normalize`.

## Source and review contract

The official PDF is retained with its retrieval manifest and SHA-256 content
hash. The manual extract records report-page and PDF-page locators. During every
normalization run, machine-readable text anchors are checked against the
supplied hash-locked PDF. Pages 35–37, 45–46, 74 and 77 were also rendered and
visually inspected.

The current review state is
`primary_visual_review_complete_pending_independent_review`. The normalized
reference cases therefore remain non-publishable program inputs even though the
underlying audit is public and independent. This state is distinct from an
independent review of AIIO's transcription, scope choices and calculations.

## Named-case result

| Project | Cost comparison | Schedule comparison | Boundary |
| --- | --- | --- | --- |
| Lakeridge Gardens Long-Term Care Home | October 2020 Stage 2 total-project budget of $179.6M to completed total-project cost of $229.0M; inferred difference $49.4M or 27.51%, consistent with the audit's rounded 27% | December 2021 planned substantial completion to 2022-02-23 actual; source reports one month late | Month/day precision is mixed, so AIIO does not calculate delay days. Price-basis date and complete change history are missing. |
| Highway 427 Expansion | Audit comparator of $660.0M, inferred from the published $616M fixed-price contract plus $44M contingency, to $757.8M estimated total; inferred difference $97.8M or 14.82%, consistent with the audit's rounded 15% | 2020-09-30 planned substantial completion to 2021-09-09 actual; inferred 344 calendar days, while the source reports one year | Final cost was disputed and not finalized. Price-basis date, complete change history and baseline start are missing. |

All currency values are nominal CAD as published. The Highway 427 $1.57B
Treasury Board budget is not used in the $757.8M comparison because the audit
states that the larger approval includes property, Infrastructure Ontario fees
and other costs. Scope-inconsistent values are not silently combined.

## Cost-component bridge to the graph

The audit also publishes actual or estimated cost components. AIIO retains the
source categories and separately applies an inferred graph-channel label. For
Lakeridge Gardens, the $198.5M construction-manager total includes $37.7M of
mechanical/electrical work and $34.9M of construction materials. For Highway
427, the $757.8M estimate separates structures, road accessories, subsurface
work, pavement, financing, maintenance, change orders and the disputed
arbitration award.

These components are valuable for defining which public-project cost accounts
could overlap with data-centre labour, materials or enabling infrastructure.
They are not AI effects, model weights or transferable cost shares. Lakeridge's
$198.5M component total also has a narrower scope than the $229M completed total
project cost and remains explicitly separate.

## Publication boundary

The intake deliberately reports:

```text
public-project cost outcome panel: not authorized
public-project schedule outcome panel: not authorized
AI-attributable cost or schedule effect: not authorized
```

Promotion requires publisher-stable project identifiers or a reviewed linkage,
price-basis reconciliation, complete approved-change histories, consistent
asset reference classes, reusable region-period coverage and the realized
AI-construction treatment required by the locked identification protocol. Two
audited examples strengthen the evidence architecture; they do not constitute
an estimation panel.
