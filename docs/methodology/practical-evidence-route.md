# Practical evidence route

This pipeline operationalizes the shortest public-data route toward an
AI-infrastructure attribution study without relabelling proxies as realized
construction or authorized revisions as final outcomes.

It runs three parallel evidence tracks:

1. A quarterly Calgary–Edmonton construction-activity proxy reconstructed from
   costed under-construction projects and explicit data-centre permits. Values
   are sensitivity cases, not observed spending.
2. A prospective snapshot of hospital, education and civic projects from the
   Alberta, BC, Ontario and Quebec inventories. Stable source identifiers allow later
   snapshots to be reconciled into stage, estimate and schedule changes.
3. A preregistered narrow outcome: quarterly publisher-authorized cost and
   completion-plan revisions. This is analytically distinct from final cost
   outturn and actual delay.

The released baseline covers 3,970 target projects in four provinces. The
reconstructed treatment track has positive activity in two Alberta CMAs. The
revision outcome remains Quebec-only, so neither the narrow estimand nor the
original realized-treatment estimand is authorized.

Each weekly evidence run rebuilds the current view, quarterly revision cells,
coverage checks, input hashes and research-surface receipt. The next official
snapshot becomes evidence only after stable-ID reconciliation; a page update by
itself is not interpreted as a project change.

Causal attribution authorization requires a second revision region, at least two asset classes,
eight pre-event and four post-event quarters, treated/control common support,
price-basis reconciliation for CAD outcomes, placebo and negative-control
tests, leave-one-out sensitivity, and independent parser and modelling review.

## Separate public-proxy planning validation

Public-only is a source constraint, not a claim of predictive or causal validity.
The weekly practical-route report now contains `proxy_planning_validation` with
three distinct claim levels: observed evidence, proxy planning, and causal
attribution. Assumption-driven scenarios remain available during validation.
The causal identification requirements above do **not** gate noncausal planning.
Private realized expenditure or labour hours are **not** prerequisites for the
proxy route; public milestones, permits and appropriately scoped price indices
can support its validation.

The current proxy passes lineage reconciliation and ordered sensitivity-case
checks (2 of 7 checks). This is a checklist, not a confidence score. It does not
pass predictive validation: coverage, timing, held-out performance, overlap and
independent review remain unassessed. In-sample association coefficients are
not substituted for a validated executive estimate. Low/high assumptions are
not probabilistic prediction intervals.

### Practical work queue

The first frozen Alberta quarterly benchmark is now implemented as a separate
research artifact. Its proxy-augmented model worsens held-out MAE by 2.47%;
validation remains withheld. See [the benchmark protocol and findings](alberta-quarterly-planning-benchmark.md).
The following items remain the full validation program; completing this
retrospective experiment does not complete the seven-check planning assessment.

The subsequent [vintage and linkage audit](vintage-linkage-audit.md) inventories
the pinned local archives, reviews all six included permit scopes, and documents
the schedule denominator correction needed for a separately versioned proxy.

That correction and the predeclared source comparisons are now implemented in
[proxy v0.2](full-schedule-proxy-comparison.md). Combined MAE remains 2.35% worse
than baseline-only on the reused test quarters; all estimate gates remain closed.

[Historical snapshot intake](historical-snapshot-intake.md) now provides immutable
capture registration, conservative as-of selection and a source/origin acquisition
queue. The registered current captures do not fill the historical evidence gap.

The [historical acquisition and review](historical-evidence-acquisition.md)
now preserves eight dated BCPI releases, a predecessor asset extract, a CAL-3
publication timeline and all six permit reviews. Detailed historical coverage
remains incomplete, so a benchmark replay is withheld.

1. Freeze a scope-specific validation contract before fitting: geography, asset,
   price basis, outcome, prediction horizon, minimum independent events and
   tolerances for predictive error, interval coverage and subgroup performance.
   Start with quarterly market-price planning in the observed Alberta markets;
   do not silently transfer it to monthly project costs or schedule delay.
2. Benchmark proxy-enhanced predictions against a baseline-only model using
   rolling origins and held-out contiguous quarters. Fit preprocessing only on
   training data. Shared market-quarter observations stay in the same fold;
   report effective independent events, not just asset-row counts.
3. Test alternative timing/realization profiles, record linkage or explicit
   overlap bounds, and leave-one-project/source-out sensitivity. Reconcile any
   baseline/increment decomposition to avoid counting the same pressure twice.
4. Publish validation metrics and limitations. Accept a separate independent
   planning-review receipt bound to the frozen model, inputs, domain and horizon.
   Passing may authorize **noncausal proxy-based planning estimates** only.

No automatic promotion is implemented from checklist scores. Future promotion
requires machine-verified validation receipts and a scope-specific review, not
flipping a flag or relaxing the existing causal gate. The current assessment is
an operational gap inventory, not evidence that these remaining experiments
have been performed.

## Immutable observations and Alberta review intake

`project_longitudinal.py` retains content-addressed normalized project snapshots
and reconciles official source record IDs, independently for each inventory.
Snapshot rows retain their source observation dates; the weekly run date is only
the report build date. An unchanged fetch, including one whose verification date
advances, cannot create a new observation. Costs, stages, schedules, names and
asset classifications are compared only across stable IDs. Same-vintage field
conflicts are ineligible for dated revision analysis. Disappearance is a catalog
coverage event and never implies completion. Every cost revision still requires
scope and price-basis review; authorized estimates are not final outturns.

The October 3 Alberta public export was successfully captured and hashed using
the existing source adapter. The review candidate in
`data/review-candidates/alberta-projects-2026-10-03/intake.json` contains 971
normalized inventory records and 77 target-project inventory events relative to
the August 31 released baseline. This includes appearances and absences, not 77
cost revisions. Capture dates establish when inventory fields were observed;
they do not establish the effective date of an estimate or milestone change.
The candidate does not replace any released data or authorize causal claims.
Review must establish source-scope continuity, cost basis and project milestones.
Raw Alberta CSV redistribution remains excluded by the existing repository rule;
the versioned acquisition receipt binds the locally retained raw content.

Reproduce the intake with the existing capture (or fetch through the established
Alberta adapter first):

```sh
PYTHONPATH=research/src python3 research/scripts/project_vintage_intake.py \
  --raw data/raw/alberta_major_projects/2026-10-03_effcef27c3b1.csv \
  --manifest data/raw/alberta_major_projects/2026-10-03_effcef27c3b1.csv.manifest.json \
  --output data/review-candidates/alberta-projects-2026-10-03
```

The longitudinal report links the existing Quebec comparator archive by hash.
Its 69 dated official snapshots supply stable-ID transitions, while its explicit
threshold, retirement, missing price-basis and final-outcome limitations remain
binding. Alberta still lacks a reviewed longitudinal outcome series and dated
actual completion/outturn evidence. Two inventory captures and the comparator
framework do not resolve that empirical gap or establish AI attribution.
