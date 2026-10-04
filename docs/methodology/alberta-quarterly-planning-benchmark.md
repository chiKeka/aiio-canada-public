# Alberta quarterly planning benchmark

The first frozen exploratory benchmark does **not** support promoting the
reconstructed AI-construction proxy into executive planning estimates. Mean
absolute error rises from 0.8192 to 0.8394 BCPI year-over-year percentage points
when the proxy is added, a 2.47% deterioration. The primary run also fails the
subgroup noninferiority criterion. This is a retrospective prediction experiment,
not an estimate of AI's effect on prices.

## Frozen scope and design

`data/model/alberta_quarterly_planning_benchmark_contract_v0.1.json` was written
before executing the benchmark. It pins input hashes, scope, model settings,
test quarters and provisional research tolerances. It is not an independently
approved or externally preregistered protocol. Changing it requires a new
version; do not select settings after inspecting these results.

The outcome is quarterly BCPI year-over-year percentage change for Calgary and
Edmonton, mapped to health, education and civic assets. It is a market-price
proxy. There is no CAD conversion, monthly interpolation, project-cost forecast,
or schedule-delay prediction. The source BCPI index supplies the price basis;
the modeled outcome is a dimensionless percentage change.

The eight contiguous test quarters are 2024 Q2 through 2026 Q1. Each forecast
origin is the preceding quarter. To allow for reporting delay, predictors and
the latest training outcome stop two quarters before the target. This is a
conservative information lag assumption, not proof that each historical input
was available at that time. All markets and assets share each target-quarter
fold. Each market/asset model is fitted separately with at least 20 training
quarters. Model fitting and feature scaling use training observations only.

The baseline is ridge regression on an intercept and lagged BCPI YoY change.
The augmented model adds `log1p(reconstructed proxy CAD / 1 billion)` at the same
information lag. Both use a fixed ridge penalty of 1, training-only mean and
population standard deviation, and an unpenalized intercept. Neither model uses
contemporaneous target-quarter investment, macro controls or realized outcomes.

The primary specification uses central exposure and a two-quarter information
lag. Low/central/high exposure and three-/four-quarter lags are declared
sensitivity cases; none is selected as a replacement primary model.

## Results and effective evidence

| Metric | Baseline only | Proxy augmented |
| --- | ---: | ---: |
| MAE, percentage points | 0.8192 | 0.8394 |
| RMSE, percentage points | 0.9681 | 1.0211 |

Errors are averaged over assets within each market-quarter, then equally over
market-quarters. This represents equal asset weights, not additional independent
evidence. The 48 asset rows represent 16 market-quarter cells in eight quarters.
Health and education reuse the same price series in each market; the six scoped
series contain only four distinct outcome trajectories. YoY changes also share
overlapping periods. No significance test treats these rows as independent.

The provisional gates require eight test quarters, MAE at most 2 percentage
points, at least 5% improvement over baseline, and no subgroup MAE more than
10% above baseline. Only test length and absolute MAE pass. Calgary civic MAE
rises from about 0.730 to 0.830, failing the subgroup criterion.

All evaluable exposure/lag sensitivities also worsen aggregate MAE. Four-quarter
lag cases lack the required training history at the first locked origin; they
are reported as insufficient data instead of silently dropping early folds.

The source reconstruction contains one costed project and six permit candidates.
These are source records, not seven verified independent events. Project/permit
linkage and overlap remain unresolved. The protocol requires at least ten
independently linked events; that criterion remains unassessed.

## Why estimates remain withheld

This is latest-vintage pseudo-out-of-sample evaluation. The 2026 reconstruction
uses retrospectively reported project costs and schedules. Its historical
quarter labels do not establish what a forecaster knew at each origin. Lagging
those labels and isolating training folds cannot remove that vintage look-ahead.

Predictive intervals are withheld. The contract specifies 90% nominal coverage,
at least 80% empirical coverage, mean width at most 8 percentage points, and
eight prior out-of-sample calibration quarters. No interval implementation has
yet met that protocol. Low/high exposure assumptions are not predictive bounds.

Point-in-time source vintages, independently linked events, overlap bounds,
leave-one-project/source-out experiments and an independent planning-review
receipt remain necessary. No check count, error threshold or benchmark receipt
automatically authorizes a model. The existing public planning-validation
checklist and website calibration gates are unchanged.

The next experiment should address timing and record linkage before adding
model complexity. Preserve this unsuccessful primary result as the benchmark
against which a separately versioned future specification is compared.

## Reproduction

Run `npm run planning:benchmark`. It verifies the frozen panel and its source
hashes, runs the time-blocked fits, and writes
`data/model-runs/alberta_quarterly_planning_benchmark_v0.1.json` with every
prediction, cutoff, subgroup metric, sensitivity result and implementation hash.
`npm run research:test` includes deterministic reproduction, future-data
isolation, constant-exposure behavior, training minimums and authorization
guardrails. A successful command means the diagnostic reproduced; it does not
mean that the proxy passed validation.
