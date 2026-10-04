# Provincial BCPI evidence gate — 2026-08-31

## Decision

**GO.** The nine-province Statistics Canada Building Construction Price Index
material spine is suitable for publication as a common evidence baseline. It is
not a calibrated cross-province model and does not attribute price change to AI.

## Independent review

Grok CLI independently inspected the source ZIP, adapter, processed CSV, screen
CSV and JSON. It reproduced the normalized CSV byte-for-byte and matched all 144
quarter-over-quarter and year-over-year calculations.

Verified source:

- Statistics Canada table 18-10-0289-01 ZIP
- SHA-256: `d0d11fda82bf37c3720d159c1d441bc1f15abd73ba9b7d9e750f4b1929b26612`
- Retrieval date: 2026-08-31

Verified scope:

- 5,472 normalized observations
- nine published provinces
- 16 selected building/component combinations
- 38 complete quarters from 2017-Q1 through 2026-Q2
- 144 aligned latest-period screen observations
- no Canada, CMA, Prince Edward Island or territory rows
- no missing or suppressed values in this vintage

## Conditions identified and cleared

1. The adapter now fails closed when the source's known province coverage differs
   from the nine-province allowlist.
2. Quarter-over-quarter change now date-matches the previous calendar quarter;
   a gap produces a missing change and explicit quality flag.
3. `index_points_above_2023_annual_base` now states the correct index-minus-100
   interpretation.
4. Display labels normalize non-breaking spaces; stable `PR_*` identifiers remain
   the documented join key.
5. Limitations disclose that School is nested within Institutional buildings
   `[62213]` and that province and CMA products are not interchangeable.
6. Golden hash, row-count, period, indicator and geography tests lock the committed
   vintage and generated artifacts.

## Public interpretation guardrails

- Factory is a proxy archetype, not a data-centre construction index.
- BCPI is a contractor bid-price index, not a commodity price, quantity,
  lead-time or capacity series.
- Side-by-side provincial values are evidence baselines, not calibrated
  comparability or AI-attributed impacts.
- Prince Edward Island and the territories remain visible coverage gaps and are
  never imputed.
