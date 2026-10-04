# Core data dictionary

This document defines the stable concepts shared by the database, analytical files, API, website and workbook. Machine-readable schemas will implement these concepts.

## Evidence status

| Status | Meaning |
|---|---|
| `observed` | Directly reported by an identified public source. |
| `corroborated` | Consistent observations from at least two independent sources. |
| `inferred` | Derived from observations using a disclosed transformation. |
| `assumed` | Chosen parameter with rationale and sensitivity range. |
| `scenario` | Counterfactual input or output; not a forecast or observation. |

## Source

Required fields: `source_id`, `title`, `publisher`, `canonical_url`, `source_type`, `geography`, `publication_date`, `retrieved_at`, `licence_note`, `access_method`, `content_hash`, `archive_path`, `status`.

## Observation

Required fields: `observation_id`, `indicator_id`, `value`, `unit`, `geography_id`, `period_start`, `period_end`, `source_id`, `evidence_status`, `transformation_id`, `quality_flags`, `release_id`.

`value` may be missing only when `quality_flags` explains the missingness or
suppression. A blank observed value must never be coerced to zero.

Province-preserving statistical extracts additionally retain the public source's
`geography_label` and `statcan_dguid`. The normalized `geography_id` uses the
`PR_<code>` convention. National totals, provincial estimates and subprovincial
regions are distinct records and cannot be substituted without an explicit
transformation.

## Workforce stock

Required fields: `observation_id`, `indicator_id`, `geography_id`, `geography_label`, `statcan_dguid`, `noc_code`, `occupation_label`, `trade_node_id`, `statistic`, `value`, `unit`, `period_start`, `period_end`, `release_date`, `source_id`, `evidence_status`, `transformation_id`, `quality_flags`, `coordinate`.

The first release uses 2021 Census employed-person counts for six NOC unit groups. A published Census zero filler is numeric zero with an explicit quality flag; it is distinct from an unpublished or suppressed value.

## Labour recruitment diagnostic

Required fields: `model_id`, `metric_id`, `geography_id`, `noc_code`, `vacancies`, `vacancy_period_end`, `workforce_stock`, `workforce_period_start`, `workforce_period_end`, `vacancies_per_1_000_2021_employed`, `availability`, `evidence_status`, `vacancy_quality_flags`, `workforce_quality_flags`.

The ratio is cross-vintage and inferred. It is not the Statistics Canada vacancy rate, a current workforce denominator or a measure of spare capacity. Null inputs remain null, and trade aggregates require complete component-NOC coverage.

## Claim

Required fields: `claim_id`, `claim_text`, `claim_type`, `geography_id`, `valid_from`, `valid_to`, `evidence_status`, `confidence`, `review_status`, `reviewer`, `release_id`.

## Project

Required fields: `project_id`, `name`, `project_class`, `sector`, `sponsor`, `geography_id`, `latitude`, `longitude`, `announced_capex`, `currency_year`, `stage`, `stage_probability`, `construction_start`, `construction_end`, `operating_start`, `power_mw`, `source_id`, `evidence_status`.

## Graph node

Required fields: `node_id`, `node_type`, `label`, `geography_id`, `unit`, `retention_low`, `retention_central`, `retention_high`, `valid_from`, `valid_to`, `evidence_status`, `source_id`, `author`, `version`, `release_id`.

## Graph edge

Required fields: `edge_id`, `source_node_id`, `target_node_id`, `mechanism`, `sign`, `weight_low`, `weight_central`, `weight_high`, `lag_periods`, `absorption`, `geography_id`, `source_id`, `assumption_id`, `evidence_status`, `confidence`, `author`, `version`, `release_id`.

## Scenario

Required fields: `scenario_id`, `parameter_set_id`, `name`, `description`, `geography_id`, `baseline_release_id`, `investment_total`, `currency_year`, `start_year`, `end_year`, `component_shares`, `local_capture_share`, `normalization_denominators`, `author`, `created_at`, `status`.

## Power overlay

Required fields: `overlay_id`, `parameter_set_id`, `geography_id`, `start_year`, `end_year`, `annual_commissioning_profile`, `it_load_mw_at_full_buildout`, `energy_pue`, `peak_to_it_factor`, `load_factor`, `grid_supply_share`, `peak_coincidence`, `planning_margin`, `evidence_status`.

Power overlays are independent scenario artifacts. `energy_pue` applies to annual energy; `peak_to_it_factor` applies to facility peak. Neither is derived from CAD capex.

## Material cost screen

Required fields: `geography_id`, `archetype`, `component`, `indicator_id`, `period_end`, `index_value`, `unit`, `quarter_over_quarter_percent_change`, `year_over_year_percent_change`, `source_id`, `source_evidence_status`, `change_evidence_status`, `quality_flags`.

The province-level BCPI normalization additionally retains `geography_label`
and `statcan_dguid`. Its coverage is the nine province series published in the
source table; missing jurisdictions are not filled with national or CMA values.

BCPI levels are observed; changes are inferred arithmetic transformations. Building archetypes are proxies and cannot be described as data-centre prices, physical availability, or AI-caused effects.

## Reference-class cost baseline

Required series fields: `indicator_id`, `geography_id`, `geography_label`,
`period_start`, `period_end`, `value`, `unit`, `source_id`, `evidence_status`,
`transformation_id`, `quality_flags`.

Required model fields: `model_id`, `input_sha256`, `as_of_date`,
`reference_class_results`, `horizon_status_counts`, `publication_authorization`,
`ai_attributable_increment`, `graph_role`, `limitations`.

Each horizon records the locked rolling-origin partition sizes, selected method,
validation errors, interval coverage, gate results and projected fields. A
`gate_failed` or `not_assessed` horizon has null projected values. Provincial
series remain distinct from CMA series; coefficients and model selections are
not transferred across geographies.

## Province-linked BCPI historical bridge

The province-linked research artifact uses the reference-class series schema
above. Official provincial observations retain `evidence_status=observed`.
Pre-2017 bridge rows require `evidence_status=inferred`, the reference CMA
`statcan_dguid`, `transformation_id`, and quality flags containing
`province_linked_cma_backcast` and
`not_official_provincial_observation`.

Required model additions: `backcast_id`, `source_input_manifest`,
`backcast_output_sha256`, `code_manifest`, `backcast_method`, and a
`publication_authorization` object that separately controls research display,
public projection, project-cost translation and AI attribution. Each diagnostic
requires province, named reference CMA, indicator, anchor quarter, scale
factor, overlap count, overlap MAPE, maximum absolute overlap error, backcast
count and pass/fail status.

The Alberta reference-cost independent-review package requires `package_id`,
`model_artifact_sha256`, a role-labelled and hash-locked `input_manifest`,
`facts_to_reconcile`, ten `required_criteria`, `reviewer_instructions`,
`test_commands`, `verdict_contract` and a false-valued `publication_boundary`.
A separate verdict must lock the exact package hash, identify the reviewer and
independence declaration, disposition every criterion and test, enumerate
findings, acknowledge the narrow claim boundary and return either `pass` with
`authorize_baseline_only` or `hold` with `withhold`. Validation of a verdict
does not itself edit a model artifact, governance gate or public release.

## Project historical-analog stress-test matrix

Required artifact fields: `model_id`, `source_id`, `input_sha256`,
`code_sha256`, `as_of_date`, `evidence_status`, `estimand`, `configuration`,
`publication_authorization`, `reference_class_results`,
`unsupported_asset_classes` and `limitations`.

Each reference-class result retains the asset and CMA mapping, unit, observation
coverage and a governed schedule grid. Required grid fields are
`start_lag_years`, `duration_years`, `profile_id`, `expenditure_schedule`,
`maximum_horizon_years`, `status`, origin counts and periods,
`schedule_weighted_factor` and `schedule_weighted_change_percent`. A missing
complete trajectory produces `not_assessed` with null summaries. Historical
factors are inferred transformations of observed BCPI paths; their budget
equivalents are scenario stress translations, not forecasts, probabilities,
recommended allowances or AI-attributable effects.

## Public-project exposure

Required fields: `project_id`, `asset_class`, `asset_class_evidence_status`, `sponsor_signal`, `sponsor_signal_evidence_status`, `estimated_cost_cad`, `start_year`, `end_year`, `schedule_overlap_status`, `overlap_years`, `annualized_cost_cad_if_complete`, `indicative_cost_allocated_to_window_cad`, `source_id`, `source_evidence_status`.

Incomplete schedules remain indeterminate unless a reported boundary proves they are outside the window. Asset and sponsor labels are inferences, not ownership findings.

## Power evidence screen

Required fields: `metric_id`, `period`, `value`, `unit`, `evidence_status`, `source_id`, `source_locator`. Requested, allocated, contracted, connected, peak, generation, and transmission quantities remain semantically distinct. The public screen does not publish a quotient across the differently dated request and contract records.

## Release

Required fields: `release_id`, `version`, `published_at`, `code_commit`, `dirty_worktree`, `input_manifest_hash`, `configuration_hash`, `model_version`, `engine_version`, `parameter_set_id`, `status`, `notes`.

## AI-attribution panel contract

Required contract fields: `contract_id`, `estimand_id`, `unit_of_analysis`,
`geography_level`, `frequency`, `design`, `treatment`, `outcomes`,
`data_domains`, `publication_authorization`.

Each data domain records `domain_id`, `role`, `status`, registry-bound
`source_ids`, `available_variables`, `missing_variables` and `limitation`.
Treatment authorizing measures are restricted to realized construction spend or
construction labour hours. Announcements, connection requests, forecasts,
scenarios and graph scores are prohibited. Cost and schedule effect fields remain
null in a readiness artifact; only a separately reviewed estimator run may
authorize them.

## AI-capex announcement ledger

Required artifact fields: `ledger_id`, `source_id`, `geography_id`,
`as_of_date`, `input_sha256`, `code_sha256`, `record_count`,
`coverage_summary`, `stage_counts`, `schedule_status_counts`,
`treatment_requirement_assessment`, `aggregation_controls`,
`publication_boundary`, `records` and `limitations`.

Each record preserves the publisher project identity, municipality, developer,
stage, reported estimated cost, schedule text and years, website, location
coverage and enabling-power capacity where present. It separately records the
inferred AI relevance and the treatment-screen status. Required authorizing
fields—`realized_construction_start_date`, `realized_construction_spend_cad`,
`authorizing_treatment_onset_available` and
`authorizing_treatment_dose_available`—remain null or false until verified
realized construction evidence exists. Missing reported estimates are not zero,
enabling power remains separate, and no probability or stage weighting is
permitted.

## AI-attribution acquisition preflight

The acquisition contract defines `candidate_regions`, `target_asset_classes`,
`evidence_receipts`, `acquisition_tasks` and `prohibited_shortcuts`. Every
receipt requires `receipt_id`, `domain_id`, `geography_ids`, `source_ids`,
`artifact_path`, `evidence_status`, `authorizing_status`,
`available_variables` and exact artifact `assertions`.

The preflight publishes `design_thresholds`, `candidate_scope`,
`current_eligibility`, `field_gap_summary`, `scope_coverage`, hash-locked
`evidence_receipts`, the `acquisition_queue`, `panel_assembly` and a fail-closed
`publication_boundary`. Candidate regions and fields are planning scope only;
eligible counts and assembled rows remain zero until authorizing evidence is
verified.

## Information-sector construction-capex screen

Required observation fields: `observation_id`, `geography_id`,
`geography_label`, `statcan_dguid`, `reference_year`,
`release_measure_status`, `value_millions_cad`, `value_cad`, `unit`,
`naics_code`, `naics_label`, `expenditure_category`,
`statcan_quality_symbol`, `quality_flag`, `source_id`,
`source_evidence_status`, `classification_evidence_status`, `treatment_role`
and `ai_construction_treatment_authorized`.

The screen selects NAICS 51 capital construction for Canada and all 13
provinces/territories. Values remain annual and publisher quality symbols are
preserved; suppressed values remain blank. NAICS 51 is a broad information and
cultural industry aggregate, so every row is a research-only contextual proxy
and `ai_construction_treatment_authorized` is false.

## CMA public-building reference cost panel

Required fields: `observation_id`, `indicator_id`, `geography_id`,
`geography_label`, `statcan_dguid`, `value`, `unit`, `period_start`,
`period_end`, `source_id`, `evidence_status`, `as_of_date`,
`transformation_id` and `quality_flags`.

The locked geography IDs are `CMA_933` (Vancouver), `CMA_535` (Toronto) and
`CMA_462` (Montréal). Each retains institutional, school, office and bus-depot
reference classes separately. CMA observations may not be recoded to `PR_*`
geographies or described as province-wide indexes.

## Regional building-investment control

Required fields: `observation_id`, `indicator_id`, `geography_label`,
`statcan_dguid`, `type_of_structure`, `investment_basis`, `value`, `unit`,
`geography_id`, `period_start`, `period_end`, `source_id`,
`source_evidence_status`, `evidence_status`, `transformation_id`,
`source_month_count`, `quality_flags`.

Each quarterly value requires three contiguous monthly source cells. Current and
constant dollars remain separate series. Province/territory and CMA identifiers
remain separate; named CMA parts are not silently merged. The quarterly sum is
inferred from observed monthly investment values and is a regional control only.

## Regional macro control panel

Required fields: `observation_id`, `indicator_id`, `indicator_label`,
`geography_id`, `geography_label`, `statcan_dguid`, `period_start`,
`period_end`, `value`, `unit`, `year_over_year_change_percent`, `source_id`,
`source_url`, `source_evidence_status`, `evidence_status`,
`transformation_id`, `aggregation_method`, `source_observation_count` and
`quality_flags`.

The panel keeps seven quarterly controls separate: all-items CPI, shelter CPI,
population, all-industry weekly earnings, construction weekly earnings, housing
starts and non-residential building investment. Monthly means, quarterly sums
and year-over-year changes are inferred transformations. No composite macro
pressure score, AI effect, scenario calibration or public-project cost
translation is authorized.

## Municipal data-centre permit proxy

Required fields: `permit_proxy_id`, `source_row_id`, `issue_date`, `issue_year`,
`job_category`, `building_type`, `work_type`, `classification`,
`candidate_status`, `matched_terms`,
`reported_estimated_construction_value_cad`, `construction_value_status`,
`floor_area_sq_ft`, `occupancy_granted_date`, `occupancy_date_status`,
`description_sha256`, `ai_specificity_status`,
`realized_construction_status`, `source_id`, `source_evidence_status`,
`classification_evidence_status`, `transformation_id`, `quality_flags`.

Permit issue date, category, type and reported values are observed source fields.
Keyword classification is inferred. Exact address, legal description,
coordinates, neighbourhood and job description are excluded from the processed
artifact. A reported construction value is a permit estimate, not realized
spend. An occupancy-granted date is a limited-coverage trend proxy, not legal
occupancy confirmation or verified construction completion.

## Audited public-project outcome reference

Required fields: `outcome_case_id`, `project_reference_id`,
`project_reference_id_status`, `project_name`, `geography_id`, `asset_class`,
`delivery_model`, `baseline_cost_cad`, `baseline_cost_approval_date`,
`baseline_cost_scope_id`, `baseline_price_basis_date`,
`latest_or_final_cost_cad`, `latest_or_final_cost_as_of_date`,
`latest_or_final_cost_status`, `cost_variance_cad`,
`cost_variance_percent`, `baseline_substantial_completion_date`,
`baseline_completion_precision`, `actual_substantial_completion_date`,
`actual_completion_precision`, `schedule_delay_days`,
`source_reported_schedule_delay`, `approved_change_history_complete`,
`cost_components`, `authorizing_field_status`, `source_id`, `source_locators`,
`quality_flags`.

Cost differences are calculated only when baseline and latest cost values share
the same declared scope. Day delays are calculated only when both planned and
actual completion dates have day precision. A source category in
`cost_components` is observed; its `graph_channel` is inferred. Named audited
reference cases do not become an outcome panel, and missing price-basis dates,
change histories or start dates remain null.

## Quebec authorized project revisions

The project-summary table requires `project_id`, `source_record_id`,
`project_name`, `geography_id`, `asset_class`, `stage_source_text`,
`planning_authorization_month`, `realization_authorization_month`,
`actual_completion_fiscal_year`, `cost_revision_event_count`,
`cost_revision_chain_reconciles`, `reported_current_authorized_cost_cad`,
`baseline_authorized_cost_cad`, `current_authorized_cost_cad`,
`authorized_cost_variance_cad`, `authorized_cost_variance_percent`,
`schedule_revision_event_count`, `schedule_revision_chain_reconciles`,
`reported_current_completion_month`, `baseline_completion_month`,
`current_completion_month`, `authorized_schedule_change_months`,
`stable_lifecycle_project_id`, `dashboard_lifecycle_history_published`,
publication flags, `source_id` and `quality_flags`.

The event table requires `revision_event_id`, `project_id`, `event_type`,
`effective_month`, `from_value`, `to_value`, `change_value`, `unit`,
`direction_source_text`, `arithmetic_reconciles`, `source_text_sha256`,
`source_id` and `evidence_status`. Cost values are CAD; completion changes are
calendar months. Source history text is not silently rewritten: every parsed
event carries a SHA-256 trace. A failed chain remains visible but cannot populate
the gated baseline/current comparison fields.

## Quebec milestone vintages and parser review

The milestone snapshot table requires `snapshot_date`, `vintage_index`,
`threshold_regime`, stable `project_id`, source identifiers and labels,
`asset_class`, observed stage and geography, current authorized cost, current
completion month, source-history hash, evidence status and source ID.

The lifecycle table requires first/last observed snapshots, milestone count,
latest-presence flag, pre/post-threshold flags, interval-disappearance and
reentry counts, adjacent-pair change diagnostics, a binary `presence_pattern`,
source ID and quality flags. Disappearance and reentry are observations across
the selected milestones, not inferred completion, cancellation or restart.

The parser-review CSV requires a deterministic `sample_id`, selection reasons,
source row locator, source file and history hashes, verbatim public history text,
parsed summary fields and event JSON, plus blank reviewer identity, date, status,
notes and reviewed-value fields. Blank reviewer fields are a release invariant
until a documented independent review is completed.

## Quebec complete-catalog transitions

The complete-catalog snapshot table extends the milestone schema with
`publisher_retirement_marker`, `publisher_complete_service_marker`,
`representation_type` and `representation_hash`. The lifecycle table records
69-position presence patterns, disappearance and reentry counts,
publisher-declared-retirement-backed disappearances, unclassified
disappearances and adjacent authorized-field change counts.

The transition table requires prior/current snapshot dates and project counts,
continuing, newly observed, disappeared and reentered ID counts, publisher-
declared retirement disappearances, unclassified disappearances, a threshold-
transition flag, source ID and evidence status. A publisher retirement marker is
an observed source statement, not an independently verified final outcome.

## Conventions

- Currency is CAD and carries a price year.
- Electrical power is MW; electrical energy is MWh or GWh. They are never interchangeable.
- Geography uses stable Statistics Canada identifiers where possible.
- Dates use ISO 8601. Retrieval timestamps use UTC.
- Missing, zero and not-applicable are distinct.
- Low, central and high values preserve declared structural cases; they are not called confidence or credible intervals without a fitted probability model.
