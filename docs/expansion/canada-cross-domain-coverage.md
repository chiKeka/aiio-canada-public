# Canada cross-domain evidence coverage

The Canada expansion begins with an explicit coverage contract, not a province ranking. The generated matrix records whether each province or territory currently has public evidence in seven domains: labour, materials, building investment, regional macro controls, public-project inventories, power planning, and information-sector construction capex.

## Interpretation

- `available` means the current source package contains a usable observation or inventory for that geography.
- `available_with_missingness` means the domain is present but published values are incomplete or suppressed.
- `not_available` means the current pipeline has no qualifying source for that geography. The pipeline does not impute the gap.

Availability is not comparability. Public-project inventories use different source scopes and thresholds; power quantities differ by unit, horizon, scenario, and system boundary; broad information-sector capex is not an AI construction treatment. The artifact therefore prohibits cross-province performance comparisons, province-specific model calibration, and AI-attributable claims.

## Current footprint

Labour and building-investment evidence cover all 13 provinces and territories. Provincial material observations cover nine provinces. Public-project and power-planning inventories currently cover Alberta, British Columbia, Ontario, and Quebec. The regional macro panel and information-sector capex screen preserve their published gaps and suppression.

## Reproduction

Run `npm run canada:coverage`. The report at `data/model-runs/canada_cross_domain_coverage_v0.1.json` hash-locks every input and is validated by the program-readiness audit.
