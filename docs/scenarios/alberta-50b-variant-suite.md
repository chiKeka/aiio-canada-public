# Alberta $50 billion scenario variant suite

## Decision purpose

The suite asks: **How does the timing and assumed local capture of a fixed CAD $50 billion Alberta AI-infrastructure program change the graph's structural pressure ordering?**

It turns the Alberta counterfactual into a controlled comparison. Each variant is a complete, versioned model run against the same graph. This is a stress-testing instrument for executive planning and research inspection, not a forecast or project cost estimator.

## Controlled variants

| Variant | Delivery window | First five years | Local capture | Deliberate change |
|---|---:|---:|---:|---|
| Staggered reference | 2027-2036 | 47.0% | 72% | Reference profile |
| Front-loaded | 2027-2036 | 67.0% | 72% | Timing concentration only |
| Constrained delivery | 2027-2041 | 29.5% | 72% | Timing extension only; annual share capped at 7.5% |
| High local capture | 2027-2036 | 47.0% | 90% | Local capture only |

All four cases hold total investment at CAD $50 billion in 2026 dollars, preserve the same component mix and normalization denominators, and pass only the 46% modelled construction share into the graph. The other 54% remains excluded. The constrained annual cap is a declared scenario rule, not an estimate of Alberta delivery capacity.

## Structural comparison

| Variant | Peak annual capex | Local modelled envelope | Top trade raw score (peak) | Hospital delivery-pressure raw score (peak) |
|---|---:|---:|---:|---:|
| Staggered reference | $7.00B | $16.56B | 0.62 (2034) | 0.44 (2035) |
| Front-loaded | $8.00B | $16.56B | 0.69 (2032) | 0.47 (2033) |
| Constrained delivery | $3.75B | $16.56B | 0.36 (2038) | 0.27 (2039) |
| High local capture | $7.00B | $20.70B | 0.77 (2034) | 0.55 (2035) |

Building electricians remain the highest-pressure trade in the four declared cases. Relative to the reference, front-loading moves their graph peak two years earlier and adds 0.07 to the raw structural score. Constrained delivery moves the peak four years later and reduces the raw score by 0.26. High local capture retains the reference timing and adds 0.15. These are dimensionless graph results; the differences are not percentage-point changes, wage inflation, labour deficits or delay duration.

## S3/PSPE role

The suite operationalizes the S3 framework's **Stress-Test Nodes/Ties** step. The graph maps the program and identifies candidate priority nodes; the variants perturb one declared dimension at a time to test where pressures concentrate and whether timing changes the priority sequence. The results are threshold probes for subsequent evidence collection and coordination, not empirical treatment effects. A policy threshold must eventually be supported by observed or simulated validation evidence before it can authorize action.

The minimum viable system therefore includes:

1. a versioned graph and scenario definition;
2. locked invariants across comparisons;
3. reproducible run receipts and content hashes;
4. explicit pressure paths and peak years;
5. a fail-closed publication boundary; and
6. independent power quantities that are never inferred from CAD capex.

## Reproducibility and validation

The contract is `data/model/alberta_50b_scenario_suite_contract_v0.1.json`; the comparison artifact is `data/model-runs/alberta_50b_scenario_suite_v0.1.json`. Run:

```bash
npm run model:variants
PYTHONPATH=research/src python3 -m unittest research/tests/test_scenario_suite.py -v
```

Validation rejects a changed investment total, currency, geography, modelled share, component mix, denominator set, undeclared timing/capture change, path escape or any prematurely authorized forecast, causal, project-cost/delay or power claim.

## Publication boundary

The variant suite supports comparative statements about the model's own structure. It does not authorize:

- a forecast of actual Alberta AI investment;
- an AI-attributable construction-cost effect;
- translation of a pressure score into dollars, escalation percentages or schedule delay;
- a measured regional local-capture rate;
- a capacity estimate from the constrained profile; or
- a power or transmission requirement inferred from capex.

