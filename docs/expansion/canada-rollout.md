# Canada rollout plan

AIIO Canada is designed as a national research program with an Alberta pilot, not as an Alberta-specific dashboard. Expansion must preserve the same epistemic labels, geography identifiers, source lineage, unit separation and immutable release process.

## Expansion sequence

### Phase 0 — Alberta proof

- Complete the reproducible Alberta evidence, graph, scenario, power-overlay, workbook and web release.
- Validate the source adapter pattern against Statistics Canada and Alberta open data.
- Keep every pressure result explicitly uncalibrated until occupational and material-capacity denominators are defensibly estimated.

### Phase 1 — comparable provincial pilots

Add British Columbia, Ontario and Quebec because they provide contrasting power systems, construction markets and announced data-centre activity. Each province receives:

- a `PR_<code>` geography profile;
- an official-project adapter or documented manual-publication workflow;
- provincial construction-price and labour baselines;
- a power-planning source profile that remains separate from the CAD graph;
- a sealed province-specific scenario, graph-parameter set and release manifest.

Cross-province comparisons are prohibited until definitions, periods, units and project-stage classifications reconcile.

The current 13-geography, seven-domain availability and missingness contract is documented in [`canada-cross-domain-coverage.md`](canada-cross-domain-coverage.md) and reproduced by `npm run canada:coverage`.

**Current common-spine status:** quarterly job-vacancy and offered-wage
observations for the six graph-relevant occupations now cover every province and
territory under one deterministic adapter. This establishes a common labour
evidence structure, not comparable province-level model calibration. Smaller
jurisdictions have substantial unavailable, confidential or suppressed cells
that must remain visible.

The BCPI adapter selects the nine province-level geographies published in
Statistics Canada table 18-10-0289-01 for 16 specified building/component
combinations. It does not preserve the table's other building, division or CMA
series. Prince Edward Island and the territories are absent from this product
and remain explicit gaps. School is nested within the broader institutional
building category, so those two archetypes are related rather than disjoint
market totals. The index-point field is measured above the 2023 annual base
(index minus 100), not from the first quarter of 2023. These common cost indexes
are evidence baselines, not cross-province model calibration or AI-attributed
effects. Stable `PR_*` geography identifiers, rather than display labels, are
the cross-dataset join keys.

The first reference-class expansion run now preserves the four eligible public-
building composites for British Columbia, Ontario and Quebec. Each of the 12
province/asset reference series contains 38 quarterly observations from 2017 Q1
through 2026 Q2. Under the locked Alberta protocol this is not enough history:
all 60 one- through five-year horizon checks are `not_assessed`, and every
projection remains null. The program does not transfer Calgary or Edmonton
coefficients to fill this gap. Provincial Decision Mode therefore remains
blocked pending a separately justified shorter-history protocol or additional
eligible historical data.

### Phase 2 — national coverage

Extend the remaining evidence domains to every province and territory. Statistics Canada series provide the common national spine; provincial and municipal sources add project, procurement, utility and workforce detail. Missingness is published rather than silently imputed.

## Provincial adapter contract

Every adapter must produce stable normalized observations with:

- `source_id`, publisher, source URL, retrieved timestamp and content hash;
- `geography_id`, period start/end, value and unit;
- observed, inferred, assumed or scenario status;
- transformation version and quality flags;
- source vintage and revision relationship;
- public licence or reuse note.

## Infrastructure scope

The common public-delivery taxonomy covers hospitals, schools, government facilities, roads, rail, regulated utilities and municipal infrastructure. Provincial releases may add subtypes, but must map them back to the common taxonomy.

## National release gates

1. Source definitions and geography codes validate.
2. Raw retrievals and normalized outputs are content-hashed.
3. Graph units, signs, lags, absorption, retention and evidence grades validate.
4. Scenario decomposition reconciles and excludes non-modelled capex explicitly.
5. Power quantities remain in a separate MW/GWh overlay.
6. Golden runs and publication manifests reproduce from a clean commit.
7. Website, workbook and downloads consume the same release manifest.
8. An independent reviewer confirms that the public surface cannot reasonably be read as an empirical finding or forecast.

## Calibration roadmap

Calibration is a separate research stream. Candidate inputs include provincial construction employment and vacancy measures, apprenticeship completions, wage and hours data, building-construction price components, project schedules, utility queue information and procurement outcomes. Calibration may change parameter sets only through a reviewed versioned release; the weekly digest never changes model parameters automatically.

The Alberta public-building baseline is governed by the locked estimands,
rolling-origin validation and fail-closed publication rules in
[`docs/methodology/calibration-protocol.md`](../methodology/calibration-protocol.md).
Provincial expansion must rerun those gates rather than transfer an Alberta
coefficient. AI attribution remains a separate panel or event-study workstream.
