# AIIO Canada product framing

## Product promise

AIIO Canada helps a public-sector decision maker answer:

> For this infrastructure project, what cost and schedule pressures should I
> prepare for as AI infrastructure builds out, what is driving them, and what
> decisions can I take now?

Decision Mode and Research Mode are two interfaces over the same evidence,
graph and release artifacts. Changing modes changes language and depth, never
the underlying numbers or evidence status.

## Primary user

The primary user is an Assistant Deputy Minister, Treasury Board analyst,
capital-planning executive or infrastructure investor reviewing a proposed or
active public project. They need a decision brief in minutes and an auditable
explanation when challenged.

## Decision Mode journey

1. Define the project: asset class, geography, current estimate, start year and
   delivery duration.
2. Read the decision headline: what can be stated now, what cannot yet be
   quantified, and which project years intersect the scenario pressure window.
3. Inspect drivers without mixing units:
   - observed construction-cost movement;
   - observed labour-market availability and wages;
   - scenario trade and material pressure;
   - grid and utility enabling constraints;
   - dated regional macroeconomic context, kept separate from any future
     AI-attributable spillover estimate.
4. Open the dependency graph to see the exact paths, lags, evidence grades and
   sticky points behind the brief.
5. Review practical decision triggers: procurement timing, market sounding,
   utility coordination, packaging strategy and contingency review dates.
6. Switch to Research Mode for sources, assumptions, methods, limitations,
   version history and downloadable artifacts.
7. Print an executive decision record that preserves the configured project,
   dated observed signals, scenario boundary, explicit unknowns, decision gates,
   release identity and source IDs on one auditable briefing surface.

## Output contract

Every executive result must include:

- the project definition and analysis date;
- a baseline cost signal clearly separated from any AI increment;
- an AI scenario pressure diagnostic clearly separated from observed evidence;
- the leading labour, material, utility and schedule paths;
- confidence and data-coverage statements;
- sources and release version;
- decision triggers and mitigations;
- explicit unknowns.

The printable decision record is a point-in-time briefing artifact, not a
model export or new evidence product. It repeats the same release-bound values
and fail-closed language already visible in Decision Mode. Printing cannot
unlock withheld fields, alter assumptions or authorize publication.

## Calibration guardrail

The current graph ranks structural pressure pathways but is not calibrated to
dollars, escalation percentages, worker shortages or delay days. Until the
cost-translation layer passes a reviewed calibration gate, Decision Mode must
show “calibration pending” for AI-attributable project cost escalation. It may
show observed BCPI change and scenario pressure scores side by side, but it may
not add, multiply or otherwise fuse them into a forecast.

## Project reference-cost contract

When a reference-class baseline is independently authorized, Decision Mode may
translate it to a schedule-weighted current-price equivalent only when the user
supplies:

- an estimate value and exact price-basis quarter;
- a supported asset class and CMA reference geography; and
- positive annual expenditure shares that sum to one.

Each expenditure year is escalated separately and then recombined. The tool
must not apply the end-year index to the full project estimate. If any required
horizon failed validation, the price basis cannot be reconciled, the reference
class is unsupported, or independent review is incomplete, the entire project
baseline remains null. This market reference calculation never contains the AI
increment and never uses a graph pressure score.

The independent-review packet is visible as governance evidence, not as a
projection. It must lock the exact model artifact, implementation, tests and
claim-boundary documents. A separate verdict must disposition all ten required
criteria and may recommend only `authorize_baseline_only`; verdict validation
does not edit the model artifact, governance state or public release. A
prepared packet, an authenticated reviewer tool or a prose approval cannot
unlock Decision Mode.

The British Columbia, Ontario and Quebec province-linked historical bridge is
also Research Mode evidence only. Its pre-2017 values are inferred from named
CMA reference markets and may support validation research, but they must not be
shown as official provincial observations or used for a project-cost result
until the backcast and modelling review gate is independently passed.

## Historical-path project stress test

While the forward reference forecast is withheld, Decision Mode may translate a
user-entered estimate under coherent historical Alberta BCPI trajectories. The
user must select a supported building class and CMA, declare a start year,
duration and annual expenditure shape, and confirm that the estimate is in the
June 2026 price basis with no future escalation already embedded.

The display reports historical p10, median and p90 schedule-weighted markers and
their arithmetic budget equivalents. These are explicitly labelled as a
historical-path stress test. They are not probabilities, forecast bounds,
recommended contingencies or an AI increment. The graph may identify diligence
channels beside the result but must never supply a multiplier or be added to the
historical marker.

## AI-capex announcement evidence

Evidence Mode exposes the hash-locked Alberta AI-capex announcement ledger. It
reports record counts, partial known estimated cost, publisher stage and
schedule/source completeness. Core data-centre estimates remain separate from
enabling-power estimates. The ledger applies no stage probability and displays
zero authorizing treatment records because publisher stage and estimated cost
do not establish realized construction onset or regional-period spend.

## Analysis channels

The product distinguishes five channels:

1. Direct construction competition: trades, equipment and materials shared by
   data centres and public projects.
2. Grid enabling work: power-line trades, grid equipment, interconnection and
   transmission or distribution dependencies.
3. Delivery capacity: procurement packaging, contractor capacity, sequencing
   and schedule spillovers.
4. Regional macro demand: the product now displays separate dated controls for
   wages, housing activity, population, consumer prices and non-residential
   investment. These are descriptive context only; the AI-attributable
   spillover channel remains uncalibrated and is not quantified in the graph.
5. Public fiscal response: an enabling-asset accounting ledger identifies
   incremental scope, baseline work and payer allocation. Capital-plan
   reprioritization and causal public budget pressure remain unquantified.

## Product success criteria

- An executive can configure a project and understand the decision boundary in
  under three minutes.
- Every number is traceable to a source or a sealed scenario assumption.
- The interface never presents a scenario score as a percent, probability,
  forecast or measured effect.
- A researcher can reproduce the same result from the release artifacts.
- The graph reveals why a driver matters and which evidence or calibration gap
  would most improve the decision.


## Enabling infrastructure and cost incidence

`data/scenarios/alberta_enabling_infrastructure_v0.1.json` links potential
transmission, substation, roads and water scope to the counterfactual AI program.
These are diligence placeholders, not observed assets or commitments. Their
costs, timing, funding and CAPEX membership are unknown; payer allocation is
100% explicitly unknown. No incremental public cost can be inferred from them.
The existing 8% grid-and-generation share is a $4 billion component **within**
the $50 billion scenario, not an additional public infrastructure estimate.

`lib/enabling-infrastructure.ts` validates this contract and reconciles scoped
cost ranges in 2026 CAD. Each shared asset has one stable row and may link to
multiple AI phases. Rows distinguish incremental, baseline or unknown scope,
already-funded versus uncommitted or unknown funding, observed versus scenario
cost evidence, and start/end timing. A sourced cost estimate alone establishes
neither AI incrementality nor a funding commitment. Observed costs require
observed source evidence; assumption ranges retain their scenario label.

Payer shares must sum to one across developer, utility, ratepayer, government
and unknown. Utility and ratepayer shares describe mutually exclusive ultimate
incidence, avoiding a second count of utility expenditure recovered from bills.
Payer allocation does not create a government commitment. Baseline scope is
excluded from incremental cost. Incremental assets already inside AI CAPEX are
reconciled against their component budget and are never added again. Only
explicitly excluded incremental assets add to the program range. Unknown
membership, scope or cost withholds the combined total; a known subtotal is
never a complete fiscal estimate. Invalid allocations, duplicate assets,
unknown phase links, unsupported observed costs and component-budget overruns
fail closed.

This ledger is an accounting and evidence contract, not a calibrated fiscal
forecast. Analyst fixture tests verify arithmetic but do not validate empirical
costs, induced scope, incidence or public commitments. Project-specific enabling
scope, official cost bases, baseline funding and ultimate payer evidence are
required before a defensible Alberta fiscal assessment can be made. The public
hospital/school/road resource-competition calculation must consume incremental
packages only after this scope reconciliation; it must not consume the ledger's
unknown placeholders as measured construction demand.
