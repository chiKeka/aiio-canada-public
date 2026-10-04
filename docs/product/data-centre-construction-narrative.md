# Canada data centres and Alberta construction capacity

Feasibility assessment, 5 September 2026. Existing evidence is a collection of
dated snapshots, not a refreshed census of projects as of today. New external
benchmarks below were reviewed for this assessment but have not been integrated
into the application model. No research or publication gates were changed.

## Assessment

We can produce a substantive presentation now about the identified Alberta
pipeline, construction resource intersections, observed workforce and cost
conditions, and potentially overlapping capital projects. A complete national
pipeline, trade-by-quarter demand forecast, contractor capacity estimate,
physical material requirements and quantified project delays require more data.

The central narrative is: data-centre development can concentrate demand for
specialist construction resources that other Alberta capital projects also need.
Timing, location, technical specification and available capacity determine the
exposure. Announced investment alone cannot quantify the resulting shortage.

## Proposed 12-slide narrative

| Slide | Claim and recommended visual | Evidence readiness |
| --- | --- | --- |
| 1. Canada's identified development pipeline | Map facilities and phases by province, stage, IT MW and expected delivery period; show coverage gaps | National project-by-project inventory incomplete; provincial power outlooks and municipal permit screens cannot substitute for a reconciled census |
| 2. Alberta's identified subset | Map and register of 19 core records; distinguish 15 proposed and 4 publisher-labelled under construction; show 3 enabling power projects separately | Existing Alberta Major Projects snapshot, 31 August 2026; records can represent phases or multi-location programmes, not 19 unique future campuses |
| 3. How much of the announcement is construction? | Cost-scope waterfall: IT/server equipment, facility works, utilities, land and professional costs | Seven core records report a partial $49.01B aggregate; do not apply construction shares before reconciling each project's cost scope and price basis |
| 4. Civil, electrical and mechanical scope | Work-package diagram and separate air/liquid-cooled benchmark bars | External indicative cost benchmark available; Alberta productivity and local scope adjustments remain missing |
| 5. When resources are needed | Quarterly construction phases, with distinct civil, electrical, mechanical and commissioning peaks | Only 3 of all 22 register records have both start and end years; trade-level dates are absent |
| 6. Alberta's workforce base | Six occupation bars; distinguish historical stock from current availability | 2021 Census employed stock available; provincial stock is not a count of available project workers |
| 7. Recruitment and contractor conditions | Vacancy/wage trends plus contractor capacity panel | Q1 2026 vacancies and offered wages available with suppression; firm headcount, backlog and dispatch availability missing |
| 8. Materials and equipment | Cost trend small multiples beside a procurement timeline | BCPI component bid-price changes available; concrete/steel quantities, equipment counts and supplier lead times missing |
| 9. Electricity, water and environmental constraints | Separate grid connection, cooling/water and emissions panels | Alberta power evidence available with quantity distinctions; project water, cooling and emissions specifications incomplete |
| 10. Where capital programmes intersect | Asset-class × trade matrix and geography/quarter overlap | Existing 541-record asset screen, with 166 records showing known schedule overlap with 2027–2036; overlap is not demonstrated competition |
| 11. Conditional demand and cascading effects | Staggered/base/concurrent scenarios, demand-to-capacity ratios and identified bottlenecks | Calculation architecture feasible; quantitative coefficients and current supply data needed; no calibrated AI-caused escalation or delay estimate |
| 12. Decisions and evidence priorities | Sequence major packages, validate supplier capacity, identify procurement windows and collect missing inputs | Actionable evidence programme; quantify benefits only after testing |

## Numbers already available

### Alberta register

- 22 AI-relevant records: 19 core data-centre records and 3 enabling power records.
- Core records: 15 proposed and 4 labelled Under Construction by the publisher.
- Seven core records have reported estimated costs totalling $49.01B; the other
  12 have unknown costs. This is a partial sum of estimates, not committed or
  forecast construction expenditure.
- Enabling power estimates total $6.40B across three records; keep this scope
  separate to avoid double counting development and generation announcements.
- Of all 22 records, 14 have at least one schedule year and only 3 have both.
- The reconstructed construction proxy has only one eligible costed project
  and six permit candidates. It is not a trade-demand forecast or a validated
  account of realized investment.

Sources: [announcement ledger](../../data/model-runs/alberta_ai_capex_announcement_ledger_v0.1.json),
[project register](../../data/processed/alberta_ai_projects.csv),
[reconstructed proxy](../../data/model-runs/ai_construction_proxy_alberta_v0.2.json).

### Workforce and recruitment

| Alberta occupation | Employed persons, May 2021 Census | Job vacancies, Q1 2026 |
| --- | ---: | ---: |
| Electricians, excluding industrial/power system | 13,375 | 460 |
| Industrial electricians | 4,175 | 80 |
| Power system electricians | 770 | Not published |
| Electrical power line and cable workers | 1,725 | Not published |
| Heating, refrigeration and air conditioning mechanics | 3,095 | 230 |
| Concrete finishers | 1,105 | Not published |

Published vacancy figures above carry Statistics Canada quality flag E. Missing
values are not zero. Census figures are rounded, from the long-form sample, and
refer to the pandemic-era reference week. They include the specified occupation
across industries; they are not exclusively new-construction workers. HVAC
mechanics do not represent the entire mechanical workforce.

The existing cross-vintage diagnostic gives HVAC 74.31 vacancies per 1,000
2021-employed persons and non-industrial electricians 34.39. These are screening
signals, not official vacancy rates or current capacity measures.

For this project, define labour density as trade employment per 1,000 construction
workers in a specified region, using compatible period and industry definitions.
Also show deployable trade-hours by quarter. Neither provincial headcount nor
workers per square kilometre adequately represents contractor availability.

Source: [labour diagnostic](../../data/model-runs/labour_recruitment_pressure_canada_v0.1.json).

### Shared construction price conditions

Industrial-factory BCPI proxy, Q2 2026 year-over-year contractor bid-price change:

| Component | Calgary | Edmonton |
| --- | ---: | ---: |
| Concrete | 4.11% | 5.24% |
| Structural steel framing | 7.30% | 10.44% |
| Electrical systems | 0.83% | 1.01% |
| HVAC | 10.06% | 10.05% |

This is a factory archetype, not a data-centre index. These figures describe
prices, not tonnes, cubic metres, equipment availability or AI-caused inflation.
Institutional/school and municipal depot archetypes are also available; the
factory series must not be silently substituted for them.

Source: [material cost screen](../../data/model-runs/bcpi_material_cost_screen_alberta_v0.1.json).

### Capital project intersection

The screen contains 179 school/postsecondary, 113 road/transit/airport, 95 health,
73 power-sector, 46 municipal water/resilience and 35 government/civic records.
Not all have verified public ownership or committed funding. Among 166 records
with a known overlap with 2027–2036, 92 have both reported costs and complete
schedules. Missing schedules must not be classified as no overlap.

Source: [public project exposure screen](../../data/model-runs/public_project_exposure_alberta_v0.1.json).

## Construction resource intersections to test

| Work package | Trades and suppliers to represent | Potential intersection with other capital work |
| --- | --- | --- |
| Site/civil/structural | Equipment operators, labourers, formwork carpenters, concrete finishers, ironworkers; aggregate, concrete, reinforcing and structural steel | Foundations, roads, water infrastructure, schools and hospitals |
| Electrical | Construction/industrial electricians, cable installers, controls and commissioning specialists; transformers, switchgear, UPS, generators and cable | Hospitals, transit, treatment plants, industrial facilities and electrification |
| Mechanical/cooling | HVAC mechanics, sheet metal workers, plumbers, pipefitters, welders, insulators and controls specialists; chillers, pumps, cooling equipment and piping | Hospital/school HVAC, industrial process work, district energy and water systems |
| Utility connections | Power-system electricians, line workers, civil crews and utility engineers | Grid upgrades and other industrial connections; connection-study scope must be verified |
| Environmental/site services | Environmental professionals and remediation/site-service contractors; water allocation, discharge, noise and emissions requirements | Permitting, enabling works and operating constraints; model separately from trade headcount |

This matrix is a proposed engineering classification, not evidence that every
project uses the same crews, suppliers, delivery window or procurement market.

## Additional benchmarks identified in this review

Turner & Townsend's 2025–2026 report gives indicative US construction allocations:

| Cost category | Air-cooled | Liquid-cooled |
| --- | ---: | ---: |
| General contractor preliminaries/fees | 10% | 10% |
| Core/shell/architectural | 14% | 9% |
| Mechanical including equipment | 22% | 33% |
| Electrical including equipment | 54% | 48% |

These are construction-cost shares, not labour shares. The benchmark excludes
active IT equipment, land, utility works, site works, abnormal groundworks and
professional fees. Do not apply it directly to broad investment announcements.
It needs separate Alberta validation and air/liquid cooling classification.

[Cost trends](https://reports.turnerandtownsend.com/data-centre-construction-cost-index-2025/data-centre-cost-trends)
and [methodology](https://reports.turnerandtownsend.com/data-centre-construction-cost-index-2025/methodology).

BuildForce's July 2026 Alberta outlook reports 196,700 construction tradespeople
in 2025 and forecasts non-residential employment up 15% by 2035 versus 2025.
It is a useful newer industry baseline, not directly interchangeable with the
six all-industry Census occupation counts. Obtain underlying trade forecasts
and determine which data-centre projects are already included before adding
incremental demand.

[BuildForce Alberta outlook](https://www.buildforce.ca/en/press-release/construction-activity-rises-in-alberta-to-2035-as-non-residential-growth-offsets-moderating-residential-demands/).

Statistics Canada's provincial input-output multipliers can support an aggregate
direct/indirect economic-demand cross-check. They do not replace project crew
schedules or measure spare contractor capacity.

[Provincial multipliers](https://www150.statcan.gc.ca/t1/tbl1/en/tv.action?pid=3610059501&request_locale=en).

## Minimum additional data, in priority order

1. **Reconciled national and Alberta phase register:** facility/phase identifiers,
   developer, coordinates, stage, FID/funding evidence, source/update date,
   start/finish dates, IT MW versus total facility/connection MW, cooling design,
   cost scope and price basis. Cross-check developers, municipalities and utilities.
   Separate operating capacity, expansion, proposed and cancelled/deferred phases.
2. **Construction quantities and labour conversion:** civil/electrical/mechanical
   estimates from completed comparable projects or quantity surveyors; local versus
   imported equipment, prefabrication, quantities, trade-hours per unit, contractor
   loaded labour rates, seasonal productivity and commissioning requirements.
   Separate off-site manufacturing labour from Alberta site labour.
3. **Current regional supply and existing demand:** employment/hours by expanded
   trade set, apprentices/completions, retirements, mobility, contractor headcount,
   backlog, tender participation and availability; BuildForce and official labour
   statistics plus contractor/association validation. Cover Calgary, Edmonton and
   relevant rural catchments and industrial maintenance/turnaround demand.
4. **Material and equipment capacity:** concrete cubic metres and plant/haul
   capacity, steel tonnage and fabrication slots, transformer/switchgear/chiller
   quantities, delivery quotations, booked orders, alternative suppliers and
   import exposure. BCPI remains a price context input.
5. **Competing project package schedules:** funded procurement dates, package
   values, trade/quantity demand and critical paths for priority public projects;
   confirm overlaps by resource, region and quarter, not broad whole-project dates.
6. **Environmental and utility specifications:** connection studies, on/off-site
   generation scope, cooling load and water balance, water source/allocation,
   discharge, operating profile, PUE/WUE assumptions and emissions factors.
   Keep construction embodied impacts separate from operating energy/water use.

## Quantification approach

For each phase, estimate package quantities and apply validated trade-hours per
unit. Allocate those hours to quarters using package schedules; sum by trade and
labour catchment. Divide period hours by stated productive hours per worker to
obtain period-average FTE equivalents. Peak concurrent headcount requires a
finer time profile; cumulative job-years are not peak workers or permanent jobs.

Where quantities are missing, a secondary estimating route is package cost ×
labour-cost fraction ÷ compatible fully loaded hourly cost. Never divide total
capex by an offered hourly wage. Use component-specific procurement/local labour
shares, rather than the current scenario's uniform local-capture assumption.

Compare total scheduled demand, including other construction and maintenance,
against deployable regional trade-hours. Model supply responses and alternative
sequences in addition to shortages. For materials compare period quantity orders
with available production/import/fabrication capacity and lead times.

This permits transparent conditional demand and exposure estimates without
waiting for causal identification. Predicting an Alberta project's cost premium
or delay requires additional calibrated market response evidence and its actual
procurement/critical-path constraints. The existing $50B graph's dimensionless
scores, assumed shares and absorption denominators cannot supply those units.

Recommended next deliverable: an evidence-led 12-slide baseline with source dates
and an appendix register, followed by a bottom-up phase/trade demand workbook.
Keep observed data, transferable benchmarks and explicit scenarios visually
distinct throughout.
