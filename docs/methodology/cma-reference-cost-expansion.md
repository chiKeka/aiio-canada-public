# Vancouver, Toronto and Montréal reference-cost expansion

## Decision question

Can AIIO extend its public-building market reference-index baseline beyond
Alberta without transferring Calgary or Edmonton coefficients or presenting a
province-wide index as local project evidence?

The current Statistics Canada Building Construction Price Index cube supports
a city-market answer for Vancouver, Toronto and Montréal. It does not resolve
the separate province-level history limitation.

## Locked scope

The deterministic adapter selects three Statistics Canada CMA geographies:

| Geography ID | Publisher geography | DGUID |
| --- | --- | --- |
| `CMA_933` | Vancouver, British Columbia | `2021S0503933` |
| `CMA_535` | Toronto, Ontario | `2021S0503535` |
| `CMA_462` | Montréal, Quebec | `2021S0503462` |

Each geography retains the four public-building reference classes already
mapped in the Alberta protocol: institutional buildings, schools, offices and
bus depots with maintenance and repair facilities. No province, Canada total
or other CMA may enter this artifact implicitly.

The institutional, school and office series contain 182 contiguous quarterly
observations from 1981 Q1 through 2026 Q2. The bus-depot series contain 38
observations from 2017 Q1 through 2026 Q2. The complete normalized panel has
1,752 observations and no missing values.

## Validation result

The run applies the unchanged Alberta v0.1 rolling-origin protocol: the same
candidate methods, 20-quarter lookback, calibration/validation split and five
predeclared gates. It does not tune thresholds after seeing CMA results.

Across 12 reference series and five horizons, the current run produces:

| Status | Horizons |
| --- | ---: |
| `gate_passed` | 9 |
| `gate_failed` | 36 |
| `not_assessed` | 15 |

All nine gate-passing horizons are Vancouver reference classes. Toronto and
Montréal do not pass any horizon under the locked protocol. The three
bus-depot series are not assessed because their 2017-onward histories cannot
satisfy the required rolling-origin partitions.

This asymmetry is a result, not a reason to weaken the protocol. A
`baseline_only` artifact means at least one individual horizon passed; it does
not authorize the whole city, asset class or country.

## Publication boundary

Every result remains withheld pending independent modelling review. Even an
independently authorized CMA projection would be a market reference-index path
for a model building, not:

- a province-wide construction forecast;
- an AI-attributable increment;
- a project budget allowance without a known estimate price basis and
  expenditure profile; or
- evidence for road, rail, water, wastewater or power infrastructure.

The province-level BCPI artifact remains separate and null. AIIO does not
replace a short provincial series with a CMA series or relabel the CMA result as
provincial evidence.

## Reproducibility

Run:

```bash
npm run bcpi:normalize:reference-cmas
npm run cost:baseline:cmas
```

The normalized CSV is reproducible from the content-hashed Statistics Canada
ZIP. The baseline artifact records the CSV hash and a combined code manifest
covering both the common calibration engine and the CMA-specific wrapper.
Tests reject source-schema drift, missing or suppressed selected values,
geography/reference-class coverage changes and premature publication.
