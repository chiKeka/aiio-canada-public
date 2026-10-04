# AI-attribution panel acquisition preflight

## Purpose

The preflight converts the E2 causal-identification contract into an operational
data-acquisition queue. It answers a narrower question than the estimator:
**what exact evidence must exist before AIIO may assemble a
region-quarter-asset-class panel?**

The machine contract is
`data/model/ai_attribution_panel_acquisition_contract_v0.1.json`; the current
hash-locked run is
`data/model-runs/ai_attribution_panel_preflight_v0.1.json`.

## Candidate scope is not eligibility

The declared pilot scope contains five candidate CMAs:

- Calgary and Edmonton as potential treated regions;
- Vancouver, Toronto and Montréal as potential comparison regions; and
- health facilities, schools/postsecondary and government/civic facilities as
  the first three public asset classes.

Those counts meet the *planned scope* minima of two treated regions, three
controls per cohort and two asset classes. They do not meet the evidence gates.
At present there are zero authorizing treated regions, zero eligible comparison
regions, zero eligible asset classes and zero assembled panel rows.

## Evidence receipts

Eleven receipts bind the preflight to current model artifacts and registered public
sources. They cover the Alberta announcement ledger, Edmonton permits, the
Statistics Canada information-sector capex proxy, the eight-source public
treatment-feasibility screen, CanadaBuys cost and
procurement feasibility, Ontario audited cost/schedule references, Quebec cost
and schedule candidates, and the Canada building-investment control panel.

Each receipt records:

- its locked domain or outcome;
- geography and source IDs;
- the artifact path and SHA-256 hash;
- candidate variables;
- exact assertions against the artifact; and
- a non-authorizing or control-only status.

An assertion failure, unknown source, path escape, missing artifact or attempted
authorization fails the build.

## Field-complete acquisition queue

The locked E2 design contains 27 authorizing field instances across four scopes:

| Priority | Scope | Required field instances | Current status |
| --- | --- | ---: | --- |
| P0 | Realized AI-construction dose | 2 | No public source currently supplies quarterly realized spend or data-centre construction labour hours for two reconciled regions |
| P0 | Public-project cost outturn | 9 | Price basis, complete changes, final outturn and multi-region comparability remain missing |
| P0 | Public-project physical schedule | 9 | Versioned baseline plus actual start/completion dates remain missing across regions |
| P1 | Procurement competition | 7 | Stable project linkage, CMA geography and compliant bidder count do not coexist |

Every locked field is assigned to exactly one acquisition task. “Covered by a
task” means the gap is explicit; it does not mean the field is available.

## S3/PSPE relationship

S3/PSPE identifies missing high-consequence nodes and ties in the program
ecosystem. Here it helps prioritize the realized treatment node, the
estimate-to-outturn and baseline-to-actual outcome nodes, and the geography ties
needed to connect them. It does not fill those fields, create a counterfactual
or authorize an effect.

## Fail-closed boundary

The preflight may publish candidate scope and evidence gaps. It may not:

- treat announcements, requested/contracted MW or permit values as realized
  dose;
- treat authorized revisions or catalog disappearances as final outturns;
- create panel rows with missing authorizing fields;
- run cohort, pre-trend, placebo or leave-one-out diagnostics; or
- publish AI-attributable cost escalation or schedule delay.

All effect fields therefore remain null—not zero.

## Reproduction

```bash
npm run attribution:readiness
npm run attribution:treatment-sources
npm run attribution:preflight
PYTHONPATH=research/src python3 -m unittest research/tests/test_panel_preflight.py research/tests/test_treatment_source_feasibility.py -v
npm run program:audit
```
