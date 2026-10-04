# Alberta data-centre construction pressure: research and model requirements

Research date: 5 September 2026. Status: proposed requirements, not an implemented or calibrated forecast.

## Decision

Build a conditional construction-resource model now. Published estimating systems, workforce forecasts, capital plans and equipment lead times provide useful anchors. Missing project dates and quantities can be represented by explicit scenarios. Missing contractor availability can also be varied, but the resulting shortage must be identified as conditional on that assumed supply.

The narrative is: **Canada's identified pipeline → Alberta phases → timed construction packages → shared regional trades and suppliers → competing capital demand → conditional schedule and cost consequences.** The timing of package construction and procurement creates the intersection; the data-centre opening date is a scheduling anchor, not the date all pressure begins.

This specification extends the [existing presentation blueprint](../product/data-centre-construction-narrative.md). The [36-entry benchmark and assumptions register](construction-benchmark-register.json) distinguishes published observations, forecasts, transferable benchmarks, analyst assumptions and missing inputs. None of these entries has been promoted into application model parameters.

## What the research supports

| Input | Verified finding | Permitted use |
| --- | --- | --- |
| Electrical productivity | NECA publishes electrical installation labour units and condition categories; normal handling/layout/nonproductive allowances are included, supervision is excluded [NECA] | Quantity × authorized item-hours, with scope-specific adjustments; no invented universal hours/MW |
| Mechanical productivity | MCAA WebLEM supports component and work-activity estimating, including handling, joining and normal testing in applicable component units [MCAA] | Piping, HVAC and related mechanical take-offs; distinguish site assembly from shop fabrication |
| Civil estimating method | RSMeans' example uses six people for an eight-hour day and 30 small equipment pads: 48/30 = 1.6 crew-hours/pad [RSM] | Demonstrates auditable physical-unit conversion; this particular pad rate is not a large-foundation benchmark |
| Overtime | CII SD-98 studied 121 weeks on four industrial projects and reports 12% and 14% efficiency losses for the studied five- and six-day overtime schedules [CII] | Historical sensitivity references, not a penalty for an ordinary five-day week or an Alberta-calibrated coefficient |
| Recurring capital | Budget 2026 fully consolidated capital totals are $9.969B, $9.998B and $8.349B for FY2026–27 through FY2028–29; total $28.316B [AB_BUDGET] | Anchor a rolling public portfolio; these totals include multiple infrastructure types and non-site-labour costs |
| Updated capital | First-quarter update forecasts FY2026–27 capital at $10.687B [AB_Q1] | Replace the current-year budget anchor while retaining both vintages; later budget targets remain separately dated |
| Alberta labour outlook | BuildForce reports 196,700 construction tradespeople in 2025, non-residential employment growth of 15% to 2035, and a potential cumulative recruitment shortfall of 5,300 [BUILDFORCE] | Provincial context and supply-trajectory cross-check; neither idle capacity nor annual data-centre shortage |
| Industry employment | Job Bank reports 246,500 Alberta construction-industry workers in 2024 [JOBBANK] | Different population from construction trades; do not combine denominators |
| Supplier response | ISED reports a $410M Hitachi transformer expansion programme [ISED] | Evidence that supply can expand; investment dollars do not reveal uncommitted units available to Alberta |

The fiscal update reports a $717M increase; subtracting its rounded table endpoints gives $718M. Preserve the publisher's rounding and do not manufacture a balancing adjustment.

NECA, MCAA and RSMeans are credible routes to estimating inputs, but publicly accessible methodology is not the complete licensed item-rate library. The requirement is an authorized estimator export or a documented comparable-project take-off; no purchase or proprietary table reproduction was performed. RSMeans normal paid hours already include daily non-installation activities. Do not divide those hours by a second 60–65% tool-time allowance.

CII's companion review explicitly discusses weaknesses in historical overtime evidence [CII_REVIEW]. A 12% reduction in output per hour means an hours factor of 1/0.88 = 1.136, not 1.12. Weather, overtime, congestion and resource interruption may overlap; multiplying every available penalty would exaggerate effects.

### Usable equipment lead-time anchors

SourceBlue's Q2 2026 report supplies the following US national procurement ranges [SOURCEBLUE]. Use each equipment class separately.

| Equipment | Reported weeks |
| --- | ---: |
| Cooling towers | 6–19 |
| Air-cooled chillers | 3–49 |
| Water-cooled chillers | 12–60 |
| Air handling units | 8–78 |
| Generators | 28–66 |
| Low-voltage switchgear | 26–58 |
| Medium-voltage switchgear | 28–48 |
| UPS | 16–42 |

These ranges are scenario endpoints, not statistical confidence intervals or Alberta delivery promises. Confirm whether the clock starts at order, approved submittals or release to manufacture; record freight, installation and commissioning separately.

Wood Mackenzie's Q2 2025 US averages were 143 weeks for generator step-up transformers and 128 weeks for power transformers [WOODMAC]. They concern different products and dates from SourceBlue's switchgear ranges. Do not average these into a generic electrical lead time. New supplier slots and Canadian manufacturing expansions belong in supply-response scenarios.

## Functional requirements

### FR-01 — Reconcile projects, phases and evidence

Each record must include facility ID, phase ID, parent programme, province, labour catchment, stage, developer, source date, source URL, original reported dates, normalized dates and date precision. Preserve the existing Alberta register; extend Canada coverage without calling the known list a complete national census.

Separate operating facilities, extensions, proposed phases, funded/FID phases, construction and deferred/cancelled projects. Separate IT MW, total facility load and connection MW. Separate land, servers, building works, enabling utilities, generation, professional costs and tax; retain currency and price year. Prevent campus and phase costs or developer and utility announcements being counted twice.

The initial evidence boundary remains the dated existing register described in the presentation blueprint: 19 core Alberta records plus three enabling power records. New benchmarks do not refresh those project statuses.

### FR-02 — Infer schedules transparently

Use reported construction dates first. Otherwise work backward from each phase's target online date. For a year-only target, use 1 July as a computational midpoint and show ±6-month sensitivity.

Fallback field-construction durations are 18, 24 and 36 months, explicitly analyst-selected stress cases rather than validated Canadian averages. Include commissioning inside the duration. Use provisional commissioning windows of 2, 3 and 6 months respectively, also labelled assumptions. Procurement can begin before field construction.

Create overlapping package profiles: civil/site works early, structure following enabling works, electrical and mechanical installation during enclosure/fit-out, integrated commissioning late. Store normalized package weights that sum to one; retain material order/delivery profiles separately from labour profiles. Do not turn overlapping packages into a serial duration sum.

Do not retrospectively mark an unstarted proposal as constructed because back-calculation yields a past start. Flag infeasibility and run a forward-shifted scenario. Preserve both the published target and the calculated feasible completion. Choose proposed-project inclusion explicitly in scenarios; do not invent probabilities of delivery.

### FR-03 — Represent recurring competing capital

Use monthly calculations and quarterly/annual outputs. Default reporting windows are calendar 2027–2029, 2027–2031 and 2027–2036, with pre-2027 initialization and post-2036 tails retained. Alberta fiscal-year spending must be allocated to calendar periods explicitly; equal monthly allocation is a labelled fallback.

Use published annual cash spending envelopes for the funded period. Within each envelope:
- Allocate verified named projects and funded transfers once.
- Assign the remaining envelope to unnamed recurring work by asset type.
- Reconcile scope before interpreting a negative residual; do not silently clamp away an inconsistency.
- Keep private industrial, municipal own-source and utility spending outside the provincial envelope only where demonstrably additional.

Beyond the published plan, continue a constant-price annual capital envelope with -2%, 0% and +2% real growth sensitivities. Normalize the published anchor to a common price year before averaging. Future continuation is a scenario, not an appropriation.

Model annual cohorts lasting four to five years, as requested. Sum the resource demands of all active cohorts. Four- to five-year annual cohorts imply roughly four to five simultaneous cohorts in steady state. Initialize ongoing work before the reporting horizon. Calibrate starts and residual work to the spending envelope; do not add whole new cohort commitments on top of cash expenditures already representing those cohorts.

Include industrial maintenance, turnarounds, housing and other private construction in background labour demand where relevant. The public capital plan alone is not the full competitive market. Determine what data-centre work is already included in BuildForce/background forecasts before adding the incremental scenario.

### FR-04 — Convert construction scope into trade-hours and material quantities

Primary route, for project p, package k, trade r and period t:

`hours[p,k,r,t] = quantity[p,k] × paid_unit_hours[k,r] × incremental_conditions[p,k,r,t] × period_weight[p,k,r,t]`

Rates must specify physical unit, crew mix, normal allowances, supervision, shop/site boundary, location, source edition and estimator adjustment. Add genuinely excluded work separately. Unit conversions must be explicit.

Where take-offs are missing, use a separately labelled preliminary route:

`hours = scoped_package_cost × labour_cost_fraction / compatible_loaded_hourly_cost`

A cost share is not a labour fraction. Never divide total investment, including servers, by an advertised wage. Published construction-cost shares may help allocate compatible facility scope, but cannot yield hours without labour fractions and wage bases.

Track concrete m³, reinforcing and structural steel tonnes, cable length by specification, piping/duct quantities, transformer MVA and units, switchgear ratings/units, UPS power and redundancy, generators, and cooling duty/equipment. Do not infer all physical quantities from capex or IT MW without an explicit reference design.

Include equipment operators, labourers, carpenters, finishers, ironworkers, construction/industrial electricians, line workers, HVAC mechanics, sheet-metal workers, plumbers, pipefitters, welders, insulators and commissioning specialists. Avoid overlapping occupation definitions. Separate environmental/permitting professionals from these installation trades.

### FR-05 — Measure labour density and conditional capacity

Report trade employment per 1,000 construction workers only with compatible geography, period and industry scope. Keep all-industry occupational counts separate. Use Calgary, Edmonton and relevant rural/camp catchments; distinguish commuter mobility from relocation and specialized certifications.

Build deployable paid capacity from trade employment, construction participation, work calendar, mobility and contractor commitments. Starting calendar sensitivities are 1,760/1,840/2,000 hours per FTE-year (40 × 44/46/50 weeks), not observed productive tool-hours. Align seasonal capacity with the period and avoid deducting absences twice.

Use one consistent comparison:
`pressure_ratio = (background_hours + incremental_DC_hours) / total_deployable_hours`

Alternatively compare DC demand with residual capacity after background demand, but never subtract background from supply and also include it again in that ratio's numerator. Report unmet hours as conditional; unavailable supply inputs are null, not zero.

A provincial workforce stock, vacancy count or national capacity-utilization percentage cannot establish uncommitted Alberta electrical capacity. Contractor inputs should include trade-qualified headcount, location, committed hours/backlog, crew availability, apprentices and supervision constraints. Track bid participation and quoted mobilization dates as corroborating indicators.

BuildForce's forecast retirements and entrants are useful trajectories, but do not subtract retirements again from a workforce forecast that already includes them. Allow training, migration and supplier/contractor expansion responses. No response and responsive supply are separate scenarios.

### FR-06 — Test material and supplier intersections

For each relevant supplier market, capture production/fabrication capacity, booked orders, uncommitted slots, technical eligibility, project quantities, order-release dates, delivery estimates and logistics. Concrete requires plant and haul-radius analysis; steel requires fabricator slots; specialized equipment requires rating/configuration matches.

A published lead time is not an estimate of spare factory capacity. Until throughput data exist, report procurement schedule exposure, not a percentage supplier shortage. Model approved alternatives or early procurement only where technically plausible.

`delivery = approved_release_date + quoted_or_scenario_lead_time + separately_excluded_logistics`

Compare delivery with required-on-site dates. Account for predecessor works and float through the actual package network. Do not add all equipment delays together where procurement runs in parallel.

### FR-07 — Calculate conditional cascading delays and costs

Run paired cases with the same macroeconomic and capital assumptions: background without incremental DC work and background plus incremental DC work. Show only the difference attributable within the model to the incremental scenario. Keep already-embedded DC work in the background reconciliation.

Carry unserved hours forward. Allocate each trade's available period capacity among active packages; all allocations must sum to no more than capacity. Compare pro-rata allocation, protection of existing commitments and preferential DC recruitment as explicit assumptions. Recalculate resource demand when tasks shift; observe predecessor constraints and critical paths.

Cost effects apply to exposed remaining commitments and genuinely incremental prolongation:
`additional_escalation = uncommitted_exposed_cost × (price_index[shifted_purchase] / price_index[original_purchase] - 1)`

Add separately priced site overhead, overtime premiums and proven resequencing impacts without charging the same costs twice. Fixed-price contracts may shift exposure to contractors or change orders; they do not automatically reprice the owner's full contract.

An optional scarcity-price factor must remain an uncalibrated sensitivity until linked to compatible tender/availability evidence. Do not convert a demand/capacity ratio directly into a claimed empirical inflation rate.

Illustration only: $60M of uncommitted exposure delayed six months at an assumed 3.5% annual escalation incurs approximately $1.04M additional escalation. It is not a forecast for an Alberta project. A whole-project factor must weight exposed packages and retain spent/fixed amounts; do not compound against the entire announced investment.

### FR-08 — Explain scenarios and publish traceable outputs

Separate three labels in every screen/export:
1. Estimated demand: sourced quantities or stated assumptions converted into hours and materials.
2. Conditional capacity gap: demand relative to stated workforce/supplier capacity.
3. Conditional consequence: schedule/cost effects under resource allocation, procurement and price assumptions.

Provide staggered, reference and concentrated starts; 3/5/10-year horizons; static and responsive supply; and one-at-a-time sensitivity. Do not imply these are probability percentiles. Show observed, inferred and missing inputs, source dates, scope, exclusions and sensitivity drivers.

Outputs: trade-hours by quarter, average period FTE, cumulative job-years, explicitly modelled peak concurrency, physical material demand, equipment order windows, unmet hours/backlogs, delayed packages and incremental exposed cost. Construction jobs, permanent operating jobs, job-years and peak workers must remain distinct.

Map intersections with hospitals/schools (electrical and cooling), roads/water (civil), and utilities/industry (electrical, piping and commissioning) at resource × catchment × time level. A whole-project date overlap is only a screening signal.

Track water allocation, electrical connection, cooling design, emissions/permit dependencies and environmental enabling works as separate constraints. Neither lead times nor labour benchmarks quantify operating water, grid or emissions impacts without project-specific technical inputs.

## Input contract and acceptance criteria

Every parameter needs: ID, value or range, unit, geography, applicable scope, observation period, publication/retrieval date where available, URL/document locator, extraction artifact, evidence class, assumption owner, review status and allowed use. Store reported value separately from transformations. A model run must record immutable input versions and selected assumptions.

Before publication:
- Reconcile unique phases and funding transfers; show missing coverage.
- Preserve total package hours, quantities and costs when schedules shift; retain horizon tails.
- Verify monthly weights sum to one and simultaneous cohorts add.
- Verify a zero-incremental-DC case produces zero incremental effects.
- Verify allocations respect trade capacity and package precedence.
- Verify unknown supply yields no purported measured shortage.
- Verify cost escalation applies only to stated exposure and time shift.
- Verify hours/FTE denominators use the same paid-hour basis.
- Verify package/crew boundaries prevent duplicate normal allowances and off-site labour.
- Require supplier product, geography, date and start-of-clock labels.
- Compare any modelled aggregate job-years with published macro benchmarks only after reconciling direct/indirect, sector and time scopes.
- Label all inferred starts, durations, capacity fractions and price-response assumptions in slides and exports.

## Build sequence and remaining inputs

**First build:** phase reconciliation; inferred schedule engine; funded-envelope plus recurring-cohort generator; versioned assumptions; demand-only outputs with low/reference/high quantities. This is actionable without waiting for measured contractor capacity.

**Second build:** authorized NECA/MCAA/RSMeans estimator inputs or comparable completed-project take-offs; trade and regional supply scenarios; supplier lead-time integration; paired background/DC comparisons.

**Third build:** resource-constrained package scheduling and exposed-cost calculations; replace assumed capacity with contractor and supplier observations; assemble the 12-slide narrative with source notes and sensitivity charts.

Highest-value remaining collection is targeted: reference designs and quantities for air/liquid cooling, item-level paid labour units, trade-by-region available hours/backlog, actual supplier quotations and slots, named capital package schedules, and a reconciled Canada-wide pipeline. Unknowns do not prevent scenario calculations, but remain material to local point estimates.

## Independent triangulation

Firecrawl was the primary discovery/extraction route. Grok CLI independently checked suppliers, schedules and recurring investment; Claude CLI independently checked labour estimating and productivity. Their outputs were treated as leads, not citations.

Accepted after checking original publishers: NECA/MCAA/RSMeans methods; BuildForce outlook; latest SourceBlue ranges; CII SD-98 study findings; Wood Mackenzie transformer data; Alberta budget and its first-quarter update; ISED expansion.

Corrections/exclusions:
- Use the latest Q2 2026 SourceBlue equipment classes instead of mixing older Q1 2025 ranges.
- Use 143 weeks for the cited GSU observation, not the secondary 144-week figure.
- Sum active cohort demands; reject a proposed maximum-of-cohorts calculation and arbitrary portfolio peak factors.
- Reject unsupported universal winter penalties, regional labour-index adders, congestion thresholds and detailed overtime curves supplied by CLI review.
- CII's verified source is SD-98 (1994), not the inconsistent report identifier/date in the CLI response.
- Do not turn cost location indices into physical productivity multipliers or paid hours into tool-time twice.
- Exclude a proposed transformer capacity-tripling figure: the checked ISED release supports investment expansion, not that output coefficient.
- Use SourceBlue's equipment lead times; its landing-page versus PDF historical index extraction differed, so no historical index series was adopted.

No application changes, deployment, external messages, purchases or evidence-gate promotions were made.

## Sources

- **[NECA]** [NECA source](https://www.necanet.org/education/publications/neca-manual-of-labor-units-(mlu)). 2023–2024 edition described. Electrical installation labour units; normal allowances included; supervision excluded.
- **[MCAA]** [MCAA source](https://www.mcaa.org/resources/weblem/). Undated public product guidance. Mechanical component/activity hours; unit-level data needs authorized access.
- **[RSM]** [RSM source](https://www.rsmeans.com/resources/what-is-construction-estimating). Undated public estimating example. Six-person crew, 30 equipment pads/day, 1.6 paid crew-hours/pad; assembly-specific.
- **[CII]** [CII source](https://www.construction-institute.org/effects-of-scheduled-overtime-on-labor-productivity-a-quantitative-analysis). 1994-08-01. SD-98; 121 weeks across four industrial projects; historical overtime study.
- **[CII_REVIEW]** [CII_REVIEW source](https://www.construction-institute.org/effects-of-scheduled-overtime-on-labor-productivity-a-literature-review-and-analysis). 1990-11-01. SD-60; limitations of historical overtime datasets.
- **[AB_BUDGET]** [AB_BUDGET source](https://open.alberta.ca/dataset/3393a7b5-07bf-4b9f-8aaf-a6d89273297b/resource/58a8d024-398f-482e-b1c2-81a754a97253/download/budget-2026-fiscal-plan-2026-29.pdf). Budget 2026; FY2026–27 through FY2028–29. Fully consolidated capital plan; broad infrastructure, not exclusively ICI or labour.
- **[AB_Q1]** [AB_Q1 source](https://open.alberta.ca/dataset/9c81a5a7-cdf1-49ad-a923-d1ecb42944e4/resource/eaeb7a75-0c9f-4964-be53-0f1cc889ffab/download/tbf-2026-27-first-quarter-fiscal-update-economic-statement.pdf). 2026–27 first-quarter fiscal update. Current-year capital forecast revision; preserve original budget vintage.
- **[BUILDFORCE]** [BUILDFORCE source](https://www.buildforce.ca/en/press-release/construction-activity-rises-in-alberta-to-2035-as-non-residential-growth-offsets-moderating-residential-demands/). 2026-07-20; 2025 base to 2035. Alberta construction trades and forecast; not spare headcount.
- **[JOBBANK]** [JOBBANK source](https://www.jobbank.gc.ca/trend-analysis/job-market-reports/alberta/sectoral-profile-construction). Modified 2025-12-01; 2024 annual and March 2025 observations. All construction-industry occupations, not the same universe as BuildForce trades.
- **[SOURCEBLUE]** [SOURCEBLUE source](https://sourceblue.com/equipment-cost-index/q2-2026-cost-index-report); [underlying report](https://sourceblue.blob.core.windows.net/qa-sourceblue/uploads/media/1786376580684-59991e4c8f932e82.pdf). Q2 2026; landing page 2026-08-05. US national equipment procurement ranges; not Alberta vendor commitments.
- **[WOODMAC]** [WOODMAC source](https://www.woodmac.com/news/opinion/mind-the-gap-tackling-supply-chain-challenges-in-the-electric-td-sector/). 2025-10-15; Q2 2025 observations. US electrical T&D equipment; distinguish GSU from other transformers.
- **[ISED]** [ISED source](https://www.canada.ca/en/innovation-science-economic-development/news/2025/09/government-of-canada-expands-investment-in-critical-clean-technology-manufacturing-and-clean-energy.html). 2025-09-29. Canadian transformer manufacturing expansion announcement; no annual available-unit capacity.
- **[STATCAN_CAPACITY]** [STATCAN_CAPACITY source](https://www.statcan.gc.ca/o1/en/plus/6596-construction-sector-not-operating-full-capacity-here-are-some-data-could-explain-why). 2024-07-04; Q1–Q2 2024. National construction capacity/obstacles context; not Alberta trade availability.

