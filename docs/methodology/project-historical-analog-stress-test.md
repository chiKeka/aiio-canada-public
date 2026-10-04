# Project historical-analog stress test

## Decision question

If a public project follows a declared annual expenditure shape, how would its
price-basis estimate translate under coherent construction-price paths that
actually occurred in the selected Alberta market?

This layer supports budget-risk discussion while the forward reference forecast
and AI-attributable increment remain withheld. It is a historical what-if, not a
prediction, probability distribution, recommended contingency or estimate of an
AI premium.

## Inputs

The engine uses the content-hashed Statistics Canada Building Construction Price
Index series already normalized for Calgary and Edmonton. The user supplies:

- a supported public-building reference class and Alberta CMA;
- an estimate stated in the latest BCPI price basis, excluding future escalation;
- a start lag in whole years from the June 2026 index origin;
- a one- through ten-year delivery duration; and
- an `even`, `front_loaded` or `back_loaded` annual expenditure shape.

Road, water, wastewater, resilience, generation, transmission and distribution
projects remain unsupported. Building indexes are not silently substituted for
those asset classes.

## Coherent-path calculation

For historical origin quarter \(t\), expenditure horizon \(h_i\), annual share
\(w_i\) and index \(I\), the schedule-weighted analog factor is:

```text
F(t) = Σᵢ wᵢ × I[t + 4hᵢ] / I[t]
```

The same historical origin supplies every expenditure year. This preserves the
observed relationship among years and avoids assembling an impossible trajectory
from independently selected one-, two- and five-year quantiles.

The artifact summarizes the resulting origin-level factors using minimum, p10,
p25, median, p75, p90 and maximum markers. Budget equivalents are simple
`price_basis_estimate × factor` translations. They appear in Decision Mode only
after the user confirms the estimate's basis and absence of embedded escalation.

## Expenditure shapes

- `even`: equal shares in every expenditure year;
- `front_loaded`: linearly declining shares from the first to last year; and
- `back_loaded`: linearly increasing shares from the first to last year.

These are declared stress-test shapes, not inferred cash-flow forecasts. The
interface displays the selected rule and lets the user compare profiles.

## Interpretation status

Every quarterly origin with a complete future trajectory contributes an
overlapping historical analog. Because adjacent origins share observations, they
are serially dependent. A row is `historical_context_available` only when the
underlying history spans at least eight non-overlapping maximum-horizon windows;
otherwise it is `limited_history_only`. A schedule without even one complete
trajectory is `not_assessed` and contains null factors.

## Publication boundary

The artifact authorizes the transparent historical stress test and its arithmetic
budget equivalent. It does not authorize:

- a future BCPI projection or probability interval;
- a recommended escalation allowance or contingency;
- a forecast of realized total project cost;
- an AI-attributable cost or schedule increment;
- addition of graph pressure scores to the historical markers; or
- replacement of a professional cost estimate and project risk analysis.

The graph remains useful for identifying channels to investigate—trades,
materials, grid dependencies and delivery bottlenecks—but it supplies no scalar
uplift to this calculation.

## Reproducibility

The generated artifact is
`data/model-runs/alberta_project_historical_analog_matrix_v0.1.json`. Run:

```bash
npm run cost:historical-analogs
PYTHONPATH=research/src python3 -m unittest research/tests/test_historical_analog.py -v
```

The artifact locks the normalized BCPI input and implementation hashes. Tests
cover exact constant-growth identities, expenditure-shape ordering, committed
artifact regeneration, source drift, missing-quarter rejection and fail-closed
publication fields.
