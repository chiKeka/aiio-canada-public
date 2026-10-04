# Initial source register

This is the human-readable planning register. `data/registry/sources.json` is the
machine-readable authority for implemented and candidate adapters. URLs and
access methods must be revalidated at ingestion time.

| Domain | Candidate authoritative source | Intended variables | Geography/frequency | Adapter priority |
|---|---|---|---|---|
| AI/data-centre projects | Alberta Major Projects | Project, sponsor, value, location, stage, timing | Alberta; updated periodically | P0 |
| Public capital projects | Alberta Major Projects and provincial capital plans | Asset class, budget, location, schedule, stage | Alberta; periodic/annual | P0 |
| Construction prices | Statistics Canada table 18-10-0289-01, Building Construction Price Index | Quarterly non-residential price indices by CMA and building type | Selected CMAs; quarterly | P0 |
| Employment | Statistics Canada Labour Force Survey tables | Employment, unemployment, wages by occupation/industry | Provincial; monthly/annual | P0 |
| Vacancies | Statistics Canada Job Vacancy and Wage Survey tables | Vacancies, offered wages, vacancy rates | Provincial/economic region; quarterly | P0 |
| Trades pipeline | Alberta apprenticeship and industry training statistics | Registrations, completions, certificates by trade | Alberta; annual | P0 |
| Occupational outlook | Alberta occupational outlook | Supply/demand outlook and gap by occupation | Alberta; outlook vintages | P1 |
| Power forecast | Alberta Electric System Operator long-term outlook | Peak demand, energy, load scenarios, generation | Alberta; annual/periodic | P0 |
| Connection pipeline | AESO connection project lists and large-load updates | Queue/project, location, requested capacity, stage | Alberta; periodic | P0 |
| Transmission | AESO capability maps, needs documents and plans | Constraint zones, planned projects, timing, capacity where stated | Alberta; periodic | P1 |
| Energy/regulatory | Alberta Utilities Commission decisions and filings | Approved facilities, costs, conditions, schedules | Alberta; event-based | P1 |
| Industry structure | Statistics Canada supply-use tables | Industry commodity inputs and domestic/import shares | Canada/provinces; annual lag | P1 |
| Materials | Statistics Canada producer price and manufacturing tables | Steel, cement, electrical equipment and selected material proxies | Canada; monthly | P1 |
| Population/building demand | Statistics Canada demographics and provincial forecasts | Population and cohort demand drivers | Provincial/CMA; quarterly/annual | P2 |
| Regional macro controls | Statistics Canada tables 18-10-0004-01, 17-10-0009-01, 14-10-0223-01 and 34-10-0156-01 | CPI, population, weekly earnings and housing starts | Provinces/territories where published; monthly/quarterly | P1 |
| Procurement/schedules | Alberta Purchasing Connection and public tender portals | Tender volume, award timing, bid signals | Alberta/municipal; event-based | P2 |

## Causal-attribution feasibility sources

Additional sources are registered for the E2 identification workstream.
Statistics Canada table 34-10-0293-01 is now implemented as a content-hashed,
quarterly regional building-investment control across 13 provinces/territories
and 36 published CMAs or CMA parts. Three separately registered 2026-2027
CanadaBuys tender, award and contract-history files now feed a content-hashed,
fail-closed construction-procurement feasibility screen. It proves that tender,
award and contract dates can be partially linked while stable physical-project
IDs, CMA geography, independent estimates, complete approved changes, physical
completion and compliant bidder counts remain unavailable. The federal
proactive contract publication remains a candidate for amendment screening.
Edmonton's General Building Permits API now feeds a content-hashed,
field-minimized permit proxy: 85 broad keyword records resolve to 17 explicit
data-centre candidates, 62 generic server references and 6 excluded substring
false positives. None of the data-centre candidates contains an explicit AI
reference or an occupancy-granted trend date. No current source supplies the
combination of realized AI-construction spend or labour hours, independent
project estimate with price basis, complete approved changes, and actual project
completion required to authorize an AI-attributable effect. See
`docs/methodology/ai-attribution-identification.md` and
`docs/methodology/canadabuys-procurement-outcome-intake.md`.
The Edmonton permit implementation is documented in
`docs/methodology/edmonton-data-centre-permit-proxy.md`.

An explicit treatment-source feasibility contract now assesses eight plausible
public sources against seven non-substitutable authorizing gates. It adds the
Statistics Canada building-permit table, 2024 commercial-building energy survey
instrument and release, and annual CMA-industry employment table to the source
register. None passes every gate. The energy survey materially improves
operating-stock and power context because its questionnaire collects
data-centre type, floor area, critical IT load and design load, but its public
release does not expose construction dose. See
`docs/methodology/ai-attribution-treatment-source-feasibility.md`.

The Alberta Major Projects AI-relevant extract now also feeds a deterministic
announcement ledger. The 2026-08-31 snapshot contains 22 records and preserves
project stage, partial reported-estimated-cost coverage, schedule coverage and
source links. Ten records report $55.41 billion in estimated cost, split into
$49.01 billion of core facilities and $6.40 billion of enabling power. The sum
is incomplete and is not a commitment or realized-spending total. Four records
carry an `Under Construction` publisher stage, but none supplies a verified
realized construction-start date or realized regional-period spend. The ledger
therefore authorizes descriptive announcement tracking only. See
`docs/methodology/ai-capex-announcement-ledger.md`.

Four additional Statistics Canada sources now join the provincial building-
investment control in a common quarterly regional macro panel. It preserves
all-items and shelter CPI, population, all-industry and construction weekly
earnings, housing starts and non-residential building investment as seven
separate series. The panel covers 82 jurisdiction-indicator series from 2017 Q1
through the latest common quarter and deliberately does not publish a composite
score. See `docs/methodology/regional-macro-controls.md`.

The locked BCPI vintage now also supports a province-linked historical
research bridge for British Columbia, Ontario and Quebec. Official provincial
values remain untouched from 2017 Q1; earlier institutional, school and office
values are transparently inferred from Vancouver, Toronto and Montréal using a
single-level anchor and an overlap screen. The result is not an official
provincial series and remains outside Decision Mode. See
`docs/methodology/province-linked-bcpi-backcast.md`.

The same locked Calgary and Edmonton BCPI histories now feed a project-level
historical analog matrix. It applies declared annual expenditure shapes to
complete observed index trajectories and reports descriptive schedule-weighted
markers. Arithmetic budget equivalents are permitted only as clearly labelled
historical stress tests; future forecasts, probability intervals, recommended
allowances and AI-attributable increments remain prohibited. See
`docs/methodology/project-historical-analog-stress-test.md`.

The 2024 Ontario Auditor General performance audit is now a registered,
content-hash-locked outcome source. Its fail-closed intake preserves two named
completed projects: Lakeridge Gardens Long-Term Care Home and Highway 427
Expansion. It supplies one completed total-cost comparison, one estimated cost
still under dispute, two planned/actual substantial-completion comparisons and
source cost-component breakdowns. Only Highway 427 has day precision for both
substantial-completion dates. Neither case provides an estimate price-basis
date, complete approved-change history, publisher-stable project ID or reusable
regional panel, so the outcome domains remain missing for causal authorization.
See `docs/methodology/audited-project-outcome-references.md`.

## Implemented provincial public-project intake

Three official provincial inventories now share a source-preserving schema:

- British Columbia: the historical [Major Projects Inventory feature layer](https://catalogue.data.gov.bc.ca/dataset/ea4c0bdb-a63f-49a4-b14a-09c1560aad0b). The public inventory was discontinued after Q3 2025, while all retrieved feature `LAST_UPDATE` values report 2024-12-01. AIIO therefore treats the layer as historical and retains both vintage warnings.
- Ontario: [Ontario Builds: key infrastructure projects](https://data.ontario.ca/en/dataset/ontario-builds-key-infrastructure-projects), English all-project CSV dated 2026-06-12. The publisher calls this a sample of key projects; it is not treated as a complete capital plan. The source has no publisher project identifier, so AIIO derives a deterministic vintage-record hash and flags it.
- Quebec: the [public infrastructure project dashboard](https://www.tresor.gouv.qc.ca/infrastructures-publiques/tableau-de-bord), CSV dated 2026-08-20. Current coverage is limited to Plan québécois des infrastructures projects of at least $20 million; pre-November 2020 vintages used a $50 million threshold.

The Quebec dashboard's separate official field-description PDF is registered as
`QUEBEC_PQI_DATA_DICTIONARY` and hash-locked alongside the CSV. It defines
`no_projet` as a lifecycle-stable identifier, `cout_total` as total authorized
cost and `suivi_modifications` as authorized lifecycle changes with effective
dates. AIIO uses those definitions to build a research-only revision panel with
141 reconciled cost chains and 168 reconciled completion-month chains. The
official archive catalog is also registered and hash-locked. It inventories 69
CSV vintages. All 69 snapshot dates are now represented in a complete-catalog
panel with 1,122 stable project IDs and 43,044 project observations. One malformed
publisher CSV uses its official paired XLSX for the same date; the raw CSV is
still retained. Of 510 disappearance events, 291 follow publisher-declared
complete service and planned dashboard retirement while 219 remain unclassified.
The panel remains non-authorizing because those statements are not independently
audited final outcomes, authorized cost lacks estimate price-basis dates and
independent parser review is pending.

The normalized file retains publisher category, type, stage, location, funding signal, cost status and original schedule text. Asset classes are explicit inferences. British Columbia and Quebec costs are converted from millions of Canadian dollars; Ontario zero budget values are treated as unavailable because the dataset uses them as placeholders. Missing values remain null.

The intake is not yet a pooled exposure model. Source thresholds, completeness, vintages and schedule fields differ materially: Ontario and Quebec do not publish a comparable construction start period for most records. The machine report therefore sets `public_project_exposure_authorized` to `false` until a source-specific comparability design and schedule strategy pass review.

## Intake rule

Each adapter must capture the source metadata defined in the data dictionary, retain a raw-file hash, emit a schema validation report and document any suppression, revision or licensing limitation. Discovery sources can enter the digest but cannot directly calibrate a material model parameter without promotion through evidence review.

## Implemented labour spine

The pipeline normalizes quarterly rows from Statistics Canada table
14-10-0444-01 for NOC 72200, 72201, 72202, 72203, 72402 and 73100. These map to
the electrician, power-line, HVAC and concrete graph nodes. One Alberta extract
supports the pilot model and a second province-preserving extract covers all 13
provinces and territories. Canada totals and economic regions are excluded from
the provincial extract so they cannot silently substitute for local conditions.
Both extracts retain
the table's quality codes and include both job vacancies and average offered
hourly wages. Missing or suppressed values are represented as missing with an
explicit `value_missing_or_suppressed` flag—not as zero.

Job vacancies describe unmet demand, not the number of workers available.
Offered wages are posted offers, not realized earnings. Neither series directly
calibrates a graph edge or proves that a trade is constrained; they are observed
baseline signals for later calibration.

The full Statistics Canada ZIP is retained as a reproducible local cache because
its uncompressed table exceeds one gigabyte. Git versions the retrieval manifest,
content hash, deterministic adapter and normalized extracts instead of the
large provider file.

## Workforce-stock denominator

An intake test found that Statistics Canada table 14-10-0416-01 stops at broad
NOC groups such as 72 and 73. It is retained for later broad-group benchmarking,
but it is not used as a five-digit trade denominator.

The detailed source is 2021 Census table 98-10-0449-01. A selected-coordinate
Statistics Canada Web Data Service request retrieves employed persons for the six
graph-relevant NOC 2021 unit groups across all 13 provinces and territories. This
avoids downloading the full 1.8 GB cube while retaining the official dimension
metadata, request coordinates and raw responses. The counts describe the May
2–8, 2021 reference week, use the 25% long-form sample and are randomly rounded.

Employment is not spare capacity. Any vacancy-to-employment diagnostic must be
described as a recruitment-pressure signal, retain the Census and JVWS quality
flags, and avoid combining suppressed cells with zero. The two surveys also have
different reference periods and sampling designs. The five-year timing gap
between the 2021 Census stock and current vacancy observations must be shown. A
ratio is therefore an explicit analytical construction rather than a published
Statistics Canada measure, and it cannot be labelled a current vacancy rate.

## Implemented Alberta power evidence boundary

Three AESO sources are active: the September 2025 data-centre update, the June
2025 interim large-load announcement, and the current Large Load Projects page.
Their PDF or HTML responses and retrieval manifests are retained by content hash.

The PDF chart reports cumulative requested data-centre load; requests are not
contracts, forecasts, or realized demand. The current page reports executed
contracts under the 1,200 MW Phase 1 limit. AESO's statement that no new
transmission reinforcement was required is restricted to that interim scope and
cannot be generalized to the $50 billion counterfactual.

## Implemented provincial power-planning source contract

Five official Ontario, British Columbia and Quebec power-planning artifacts are
now registered, retrieved and content-hash locked. The Ontario 2026 Annual
Planning Outlook workbook supplies exact scenario energy, seasonal peak and
remaining-needs values; the associated demand module supplies data-centre
energy endpoints. Quebec's regulator-filed 2025 supply-plan update supplies
electricity-sales, winter-peak and data-centre peak forecasts, with a later
Hydro-Quebec announcement retained as a separate approximate outlook. The B.C.
public 2025 IRP summary supplies selected energy, generation and transmission
actions but no comparable numeric data-centre load path.

The normalized contract keeps energy, peak, remaining need and planned supply
action as separate quantities. It prohibits pooling Ontario data-centre TWh
with Quebec data-centre MW, or interpreting B.C. plan actions as spare capacity.
See `docs/methodology/provincial-power-planning-contract.md`.
