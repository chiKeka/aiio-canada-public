# Historical construction-cost envelope

## Decision question

Before a validated forecast or AI-attributable effect exists, what can an executive learn from the realized history of the closest available public construction-price reference class?

The historical envelope is an interim decision-support layer. It summarizes what Statistics Canada Building Construction Price Index (BCPI) model-building indexes actually did across previous one- through five-year windows in Calgary and Edmonton. It does not forecast the next window, price a project or estimate an AI premium.

## Estimand

For reference index value \(I_t\) and horizon \(h\) quarters, each realized cumulative change is:

```text
change(t, h) = (I[t] / I[t-h] - 1) × 100
```

For each asset proxy, metro and horizon, the pipeline calculates every available quarterly-origin window and reports the minimum, p10, p25, median, p75, p90 and maximum realized cumulative changes. It also reports the latest realized window, its descriptive rank among prior windows, the number of overlapping windows and the number of non-overlapping windows spanned by the history.

The median annualized value is the compound annual rate implied by the historical median cumulative change. It is descriptive arithmetic, not an estimated future growth rate.

## Reference-class mapping

| Product asset | BCPI model-building reference | Status |
|---|---|---|
| Hospital or health facility | Institutional buildings division composite | Proxy |
| School | School division composite | Direct for schools; proxy for post-secondary |
| Government administrative facility | Office building division composite | Proxy for administrative buildings only |
| Municipal operations facility | Bus depot with maintenance and repair facilities | Proxy with limited history |
| Roads, water/resilience and regulated utilities | None | Not assessed |

Calgary and Edmonton are separate market references. No metro average is substituted for a province-wide value.

## Interpretation status

A horizon is labelled `historical_context_available` only when the series spans at least eight non-overlapping windows of that length. Shorter histories are labelled `limited_history_only`. Quantiles still use all overlapping quarterly-origin windows to show the observed distribution, but those windows are serially dependent and must not be treated as independent draws.

For the long-running institutional, school and office references, history begins in 1981. The bus-depot series begins in 2017, so its four- and five-year summaries remain limited-history context.

## Publication boundary

The artifact authorizes publication of deterministic historical summaries. It does not authorize:

- a future BCPI projection;
- a confidence, prediction or probability interval;
- multiplication of the selected project's estimate by a historical marker;
- a schedule-weighted project cost;
- an AI-attributable cost or schedule effect;
- a road, water, transmission, distribution or generation cost proxy; or
- substitution for a professional estimate and risk analysis.

The existing held-out baseline forecast remains separately gated. Failed four- and five-year forecast results stay null; the historical envelope does not override or relax that validation.

## Reproducibility

The generated artifact is `data/model-runs/alberta_bcpi_historical_envelope_v0.1.json`. Run:

```bash
npm run cost:historical-envelope
PYTHONPATH=research/src python3 -m unittest research/tests/test_historical_envelope.py -v
```

The artifact locks both the normalized BCPI input hash and the implementation hash. Tests cover deterministic regeneration, constant-growth identities, quantile ordering, missing-quarter rejection, reference-class coverage and fail-closed authorization fields.
