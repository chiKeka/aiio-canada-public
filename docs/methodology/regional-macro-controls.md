# Regional macro control panel

Status: implemented descriptive control panel; not an AI-effect estimate or
project-cost translation.

## Purpose

The panel provides a dated, Canada-ready view of regional conditions that may
confound or contextualize construction-market analysis. It keeps household
prices, population, payroll earnings, housing activity and non-residential
building investment as separate indicators. It does not collapse them into a
single “macro pressure” score.

## Public inputs

| Indicator family | Statistics Canada source | Published frequency | Coverage used |
|---|---|---|---|
| All-items and shelter CPI | Table 18-10-0004-01 | Monthly | Ten provinces |
| Population estimates | Table 17-10-0009-01 | Quarterly | Thirteen provinces and territories |
| Average weekly earnings | Table 14-10-0223-01 | Monthly, seasonally adjusted | Thirteen provinces and territories |
| Housing starts | Table 34-10-0156-01 | Monthly SAAR | Ten provinces |
| Non-residential building investment | Table 34-10-0293-01 | Monthly, seasonally adjusted current dollars | Thirteen provinces and territories |

Every source archive and retrieval manifest is content-hashed. The earnings
selection uses the industrial aggregate excluding unclassified businesses and
Construction [23]. Housing values are published with a thousands scalar and
are converted to units before aggregation.

## Transformation

The artifact begins in 2017 Q1 and ends at the latest quarter common to all
seven indicators. Monthly CPI, earnings and housing-start values are arithmetic
means of exactly three contiguous monthly cells. Building investment is the sum
of exactly three monthly current-dollar values from the separately governed
investment-control artifact. Population remains the published quarterly point
estimate.

For each jurisdiction-indicator series, the pipeline calculates a deterministic
year-over-year percentage change when both current and prior-year values are
published and the prior value is non-zero. Blank or suppressed inputs remain
blank; they are never converted to zero. Source quality symbols are retained in
`quality_flags`.

## Output contract

The long-form panel is
`data/processed/regional_macro_controls_canada.csv`. Its receipt is
`data/model-runs/regional_macro_controls_canada_v0.1.json`. The current artifact
contains 3,116 quarterly cells: 82 jurisdiction-indicator series, seven metrics,
13 jurisdictions and 38 common quarters through 2026 Q2.

Required fields are `observation_id`, `indicator_id`, `indicator_label`,
`geography_id`, `geography_label`, `statcan_dguid`, `period_start`,
`period_end`, `value`, `unit`, `year_over_year_change_percent`, `source_id`,
`source_url`, `source_evidence_status`, `evidence_status`,
`transformation_id`, `aggregation_method`, `source_observation_count` and
`quality_flags`.

## Interpretation boundary

- The panel describes regional context; it does not identify an
  AI-attributable macroeconomic effect.
- CPI is a household-consumption price index, not a construction bid-price
  index.
- Payroll earnings are not occupation-specific offered wages, labour
  availability or proof of wage causation.
- Housing starts are an activity measure at a seasonally adjusted annual rate,
  not housing affordability or worker-accommodation capacity.
- Population is a demand and denominator control, not construction capacity.
- Non-residential building investment excludes engineering construction and is
  not a public-project outcome.
- Territorial CPI and housing-start values are unavailable in the selected
  tables and are not filled from capital-city or national proxies.
- No metric may calibrate the scenario, change a graph weight, generate a
  project contingency or authorize a cost or schedule effect without a separate
  preregistered and independently reviewed model.

