# Full-schedule proxy v0.2 and controlled comparison

The timing correction is implemented as a separate research proxy. It preserves
the full 2024–2026 project schedule and retains allocations beyond the data
window. The corrected combined model still performs worse than baseline-only,
so no validated estimate is authorized.

## What changed

The v0.1 reconstruction normalized its assumed project profile over the quarters
inside the output window, allocating the full CAD 750 million CAL-3 reported
budget by June 2026. Version 0.2 normalizes the same mathematical profile over
all 12 reported schedule quarters before selecting the output window.

| Assumed allocation before realization factors | CAD |
| --- | ---: |
| Full reported project budget | 750,000,000.00 |
| Through June 2026 | 652,739,251.04 |
| Retained for July–December 2026 | 97,260,748.96 |

A complete project-quarter ledger retains the final two quarters and any
pre-window allocations. It reconciles to the source budget to the cent. Integer
weights reproduce the original symmetric quadratic profile; largest-remainder
rounding conserves cents, with chronological tie-breaking. Changing the retained
window does not change allocations in overlapping quarters.

The aggregate CSV keeps the same 2017 Q1–2026 Q2 coverage and all original permit
amounts, counts, uncosted-project handling and realization factors. The six
permits remain included: draft maintenance classifications and proposed facility
links are not applied as exclusions or deduplication. No observed expenditure
is inferred from either the project ledger or the permit values.

## Frozen comparison

`data/model/full_schedule_proxy_comparison_contract_v0.2.json` was written before
building or evaluating v0.2. It pins the previous artifacts and declares four
arms: baseline-only, project-only, permit-only and combined. The combined arm is
the primary comparison against baseline; individual sources are diagnostics.
The existing test quarters, outcomes, geography/asset scope, ridge penalty,
training-only scaling, information lags and provisional acceptance criteria are
unchanged. Each arm has the same 48 asset rows in eight held-out quarters.

Prior v0.1 results were already known. Reusing these quarters is an exploratory
follow-up, not a fresh confirmatory test or external preregistration. No arm is
automatically selected based on the results. The original v0.1 CSV, panel,
benchmark contract, predictions and metrics remain intact.

## Results

MAE and RMSE are measured in BCPI year-over-year percentage points. Errors are
averaged within each market-quarter across assets, then across market-quarters,
as in the original protocol. Lower errors are better.

| Model | MAE | RMSE | MAE versus baseline |
| --- | ---: | ---: | ---: |
| Baseline-only | 0.81920 | 0.96808 | Reference |
| Project-only v0.2 | 0.82161 | 1.00447 | 0.29% worse |
| Permit-only | 0.83601 | 0.98577 | 2.05% worse |
| Combined v0.2 | 0.83843 | 1.02152 | 2.35% worse |
| Frozen combined v0.1 | 0.83944 | 1.02109 | 2.47% worse |

The correction reduces combined MAE by about 0.00101 percentage points, or
0.12% relative to v0.1, while combined RMSE increases slightly. It does not
deliver the required 5% MAE improvement over baseline. The combined model also
fails subgroup noninferiority: Calgary civic MAE is about 0.84303 versus 0.72976
for baseline. The project-only arm also fails that subgroup criterion.

The report retains every primary prediction, baseline reconciliation, subgroup
metric and all 27 declared component/realization/lag sensitivities. Eighteen
sensitivities can be evaluated; nine four-quarter-lag cases lack the required
training history at the first origin. These cases are explicitly insufficient
data; early folds are not dropped to improve results.

Project dollars occur in Calgary and permit dollars in Edmonton in this frozen
sample. The ablations reveal which source changes each market's fitted model;
they do not measure causal cost contributions or independently additive effects.
Repeated asset rows and overlapping YoY outcomes are not independent events.

## Remaining boundary and next work

Correcting arithmetic does not establish historical publication availability,
actual construction timing, AI specificity or predictive validity. Historical
vintages, independent permit/work-package review, individual-permit sensitivity,
predictive intervals, independent planning review and fresh prospective
validation remain outstanding. The baseline-only result is a comparison
reference, not an independently approved executive forecast.

The next research priority remains acquiring dated project and BCPI releases and
reviewing permit scope and linkage. Preserve this negative result instead of
tuning new settings on the same held-out quarters. The production application,
public research release and calibration gates are unchanged.

## Reproduction

Run in order:

```sh
npm run planning:proxy-v2
npm run planning:compare-v2
npm run research:test
```

Outputs:

- `data/processed/ai_construction_proxy_alberta_v0.2.csv`
- `data/processed/ai_construction_project_allocations_alberta_v0.2.csv`
- `data/model-runs/ai_construction_proxy_alberta_v0.2.json`
- `data/model-runs/full_schedule_proxy_comparison_v0.2.json`

Receipts bind source files, the frozen contract, output hashes and implementations.
Tests verify exact budget conservation, window-invariant allocations, unchanged
permit data, identical baseline predictions and folds, isolated source arms,
deterministic reconstruction, and rejection of invalid inputs or authorization.
Commands succeeding means the research run reproduced, not that a model passed
the predictive or publication gates.
