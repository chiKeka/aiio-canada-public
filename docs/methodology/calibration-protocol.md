# AIIO calibration and forecasting protocol

## Decision question

For a public infrastructure project with a stated geography, asset class, price
basis and delivery window, what market-wide construction-price escalation is a
reasonable planning baseline, and what additional cost or schedule effect can
be attributed to an AI-infrastructure scenario?

AIIO answers those as two separate estimands. It does not convert a graph score
into a cost percentage.

## Estimands

### E1 — market reference-index baseline

The first estimand is the cumulative percentage change in a Statistics Canada
Building Construction Price Index (BCPI) reference series from the latest
observed quarter to a stated future horizon. It estimates a contractor
bid-price reference path for a model building. It is not a forecast of the
realized cost of a particular project.

For Alberta v0.1 the eligible reference classes are:

| Public asset decision | BCPI reference class | Mapping note | Geography |
| --- | --- | --- | --- |
| Health facility | Institutional buildings division composite | Institutional aggregate; hospital proxy | Calgary and Edmonton CMA |
| School or post-secondary facility | School division composite | Direct for schools; proxy for post-secondary | Calgary and Edmonton CMA |
| Government administrative facility | Office building division composite | Administrative-office proxy only | Calgary and Edmonton CMA |
| Municipal operations facility | Bus depot with maintenance and repair facilities division composite | Municipal-operations building proxy | Calgary and Edmonton CMA |

Road, rail, airport, water, wastewater, grid and other non-building projects are
`not_assessed` until an appropriate public reference series and validation
protocol are added. Calgary and Edmonton results are not province-wide
substitutes.

The British Columbia, Ontario and Quebec expansion uses the same four reference
classes and preserves province-level `PR_*` identifiers. The current Statistics
Canada provincial series begin in 2017. With 38 observations, they do not supply
the predeclared calibration and validation partitions: the available rolling
origins range from 15 at one year to zero at five years, before the required
15/10 partition split. All 60 provincial horizons are therefore
`not_assessed`. No Alberta model selection, error band or coefficient is
transferred to another province.

A separate city-market expansion preserves Vancouver, Toronto and Montréal CMA
identifiers. The institutional, school and office series contain 182 quarters
from 1981 Q1 through 2026 Q2, while the bus-depot series begin in 2017. The
unchanged locked protocol produces 9 gate-passing, 36 gate-failed and 15
not-assessed horizons. All nine passes are Vancouver results. Every result
remains withheld pending independent modelling review, and no CMA result is
relabeled as province-wide evidence. See
`docs/methodology/cma-reference-cost-expansion.md`.

### E2 — AI-attributable incremental effect

The second estimand is the difference between the public-project outcome under
an explicit AI-infrastructure scenario and the otherwise-equivalent outcome
without that scenario. Outcomes may eventually include a cost-index increment,
schedule delay, bid participation or procurement timing.

E2 is currently `not_calibrated`. No current dataset supplies a defensible
historical treatment measure, counterfactual, project price basis and realized
outcome panel at the required resolution. The Alberta Major Projects inventory
is an exposure and schedule screen, not an outcomes dataset.

### E3 — mechanism and exposure ranking

The graph estimates neither E1 nor E2. It is a structural analysis layer that
traces an explicit scenario shock through labour, material, utility and delivery
paths. Its current outputs rank pathways and timing under declared assumptions.
They remain dimensionless diagnostics until edge-level empirical calibration
passes a separate gate.

## Baseline model candidates

Each eligible BCPI series is ordered quarterly and checked for duplicate,
missing, non-positive or non-contiguous observations. Two deliberately simple
candidates are evaluated:

1. `flat_index`: the latest index level remains unchanged;
2. `median_recent_yoy_drift`: the median annual log change observed in the
   trailing 20 quarters is compounded to the forecast horizon.

The lookback, candidates, tie rule, horizons and gates are fixed in code before
the current result is inspected. A drift model must improve calibration-period
mean absolute percentage error by more than 0.10 percentage points to displace
the flat benchmark.

## Rolling-origin validation

For each one- through five-year horizon, the pipeline constructs rolling-origin
forecasts using only observations available at each origin. At most the latest
40 eligible origins are retained so evaluation reflects a reasonably current
market regime without discarding multiple cycles.

The earlier half is the calibration partition. It selects the candidate and
provides the empirical 10th and 90th percentiles of percentage forecast error.
The later half is a locked validation partition. It assesses the already-chosen
candidate and the resulting empirical interval. Production intervals apply the
calibration error quantiles to the current point projection; they are empirical
error bands, not confidence intervals or probability guarantees.

A horizon passes only when all of these conditions hold:

- at least 15 calibration origins and 10 validation origins exist;
- validation mean absolute percentage error is no more than 15%;
- absolute validation mean percentage error is no more than 10%;
- validation error is no more than 2 percentage points worse than the flat
  benchmark; and
- calibration-derived interval coverage on the validation partition is at
  least 60%.

Failure produces `gate_failed` and null public projection values. Insufficient
history produces `not_assessed`. The pipeline never fills a failed value with a
different model after looking at the outcome.

## Translating an index path to a project decision

A current-price project estimate may be multiplied by a reference-index factor
only when its estimate date and price basis are known. Applying an end-horizon
factor to the entire project budget would wrongly assume all expenditure occurs
at the end. A schedule-weighted project baseline additionally requires a
declared cash-flow or expenditure profile. Until that component exists, AIIO
publishes the index path and cumulative change, not a total project-cost
forecast.

The baseline and AI increment must always be rendered as:

```text
market reference-index baseline: observed-series projection or not assessed
AI-attributable increment: calibrated estimate or calibration pending
graph pathways: structural diagnostic, shown separately
```

No interface may add the graph score to E1, multiply E1 by a graph score, or
describe their juxtaposition as E2.

## Identification roadmap for the AI increment

Calibration of E2 requires a versioned panel with, at minimum:

- project-level estimate dates, price bases, tender or award values, approved
  changes, completion dates and asset reference classes;
- annual or quarterly AI/data-centre construction activity measured as realized
  spend, labour hours, permits or installed capacity rather than announcements;
- local labour, wage, vacancy, contractor-capacity and material-price measures;
- grid construction and large-load connection activity; and
- regional macro controls and comparable regions with different exposure.

The preferred design is a preregistered regional panel or event-study with
staggered exposure, fixed-effects controls, pre-trend and placebo tests, and
leave-one-region/event-out sensitivity. If parallel-trend and overlap conditions
do not hold, the output remains descriptive. A synthetic-control or matched
reference-class design may be used for a small number of large shocks, but it
must preserve the same temporal holdout and negative-control discipline.

The graph may route an externally estimated, unit-bearing channel effect only
after that effect is independently identified. Graph edge weights cannot be
back-solved from a single scenario to create the appearance of calibration.

## PSPE-derived validation discipline

AIIO carries forward the dissertation program's strongest methodological
lessons while not claiming its incomplete layers as inherited capability:

- lock the protocol, cohort, thresholds and artifact versions before outcome
  inspection;
- freeze defects and disclose dispositions rather than silently repairing a
  method after seeing its results;
- separate diagnostic usefulness from prediction and causal identification;
- use temporal splits, fixed rules, alternative specifications and
  leave-one-unit-out checks;
- treat mechanism taxonomies as overlays unless coding reliability is
  demonstrated; and
- do not use conserved cascade mass as an origin ranking in a row-normalized
  graph.

The conceptual PSPE blend of model and reference-class probabilities is not
used here because a dimensionless graph score and a BCPI change are not
unit-compatible. AIIO instead keeps the reference baseline, empirical increment
and mechanism graph modular.

## Frozen artifacts and release states

Every calibration run records the input hash, code revision, series identifier,
geography, observation window, horizons, model candidates, selected method,
partition sizes, validation metrics, gate results and limitations. The public
release state is one of:

- `not_assessed` — no eligible reference class or too little history;
- `baseline_only` — E1 passed, E2 remains null;
- `calibrated_increment` — E1 and an independently reviewed E2 both passed; or
- `withheld` — a previously available output failed a current integrity or
  validation gate.

Promotion to `calibrated_increment` requires an independent modelling review,
reproducible release build and explicit publication approval. Weekly evidence
digests may propose new inputs but never change model parameters automatically.
No gate-passing E1 value enters Decision Mode until the same independent review
has also authorized the baseline artifact for public use.
