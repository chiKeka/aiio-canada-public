# Executive monthly cashflow scenario

This is an assumption-driven planning sensitivity, not validated proxy planning
or causal attribution. No empirical authorization flags are changed.

## Price basis and expenditure

The base budget excludes contingency and is stated in the entered price-basis
month. Prices in that month have index 1. Each subsequent month's assumed rate
compounds through the final delivery month, including pre-construction months.
The basis must precede or equal the January start of the selected project year.
This month-level convention does not distinguish within-month invoice dates.

The user selects even, front-loaded, back-loaded or mid-project-peak spending.
For N months, unnormalized weights are respectively 1, N-i, i+1 or
(i+1)(N-i), with zero-based i. Weights are normalized to sum to 1.
These profiles are explicit assumptions, not uploaded actual expenditure plans.

For month m, base spend B_m equals budget times its profile share. Baseline
escalation is B_m × (baseline index_m - 1); incremental scenario dollars are
B_m × (combined index_m - baseline index_m). Total scenario spend is the sum of
B_m × combined index_m, not the whole budget times the final index. The base,
baseline increment and AI scenario increment reconcile before display rounding.
Contingency is shown separately and is not assumed to cover this exposure.

## Monthly values and driver interpretation

Annual scenario activity is held constant within each scenario year, shifted by
the assumed lag. It is not observed monthly spending or a smooth interpolation.
Outside the declared annual scenario window, additional scenario flow is zero
by construction, not evidence of no future data-centre construction. Previously
accumulated price effects are retained. Annual baseline and AI peak assumptions
are converted to monthly rates; combined rate is their sum, matching the
existing scenario convention.

The selected month controls the spend readouts, MoM rate, driver labels and
decision-response context. Driver allocations use the stated 82% primary / 18%
secondary assumption and graph weights. They reconcile to the selected month's
AI rate increment. They do not decompose accumulated dollar exposure, which also
reflects earlier months. Upstream nodes are explanatory, not extra cost terms.

Low/high scenarios vary the AI rate only, not baseline uncertainty. They are not
probabilistic intervals. Mitigation timing and owners are suggested roles;
selections are session-local and never reduce estimates without benefit evidence.

## Safety and tests

Missing/invalid shared parameters preserve defaults; explicit zero is retained.
Profiles are included in shared URLs. Invalid dates or missing monthly price
levels withhold dollar results. A future calibrated artifact must match asset,
geography, price basis and delivery horizon and authorize combined costs before
it replaces the sandbox. Monthly driver effects remain withheld for that artifact
until separately supported; peak contributions are not relabelled as monthly.

`npm run test:planning` covers query defaults, date validation, allocation,
cashflow arithmetic, price-basis anchoring, profile sensitivity, zero shocks,
missing prices and driver reconciliation. It runs in the quality workflow.
