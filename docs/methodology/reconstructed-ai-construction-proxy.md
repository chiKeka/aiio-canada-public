# Reconstructed AI-construction exposure proxy

## Analytical role

This proxy supports exploratory association and sensitivity analysis when quarterly realized private-project spending or labour hours are not publicly disclosed. It never replaces the locked authorizing treatment in the causal E2 estimand.

The reconstruction combines two independently visible components: reported-cost data-centre projects currently classified by the publisher as under construction, and City of Edmonton permits whose public descriptions explicitly use a controlled data-centre term. Proposed projects, announcements, requested electricity load and scenario expenditure are excluded.

## Reconstruction

For a costed project with reported start and end years, total reported cost is distributed across quarters using a normalized symmetric construction profile. Low, central and high realization shares of 45%, 65% and 80% are applied. These shares are assumptions, not measurements.

Non-demolition permit estimates are assigned to their issue quarter. Low, central and high realization shares of 35%, 60% and 85% are applied. Permit and project components remain separately reported because public identifiers do not allow reliable deduplication.

Projects missing either cost or a complete schedule contribute activity counts only. No dollar value is imputed. Comparison-market exposure is recorded as not observed rather than zero.

## Interpretation

The output is a reconstruction of possible construction intensity. It is not realized capital expenditure, labour hours, physical completion, or proof that a facility serves AI workloads. Results using this proxy must be described as associations and accompanied by all three uncertainty cases.

The first association diagnostic differences Calgary and Edmonton market-level BCPI changes, controls for their non-residential investment difference, and includes asset fixed effects. It cannot establish a causal counterfactual and cannot populate the executive calibrated forecast.
