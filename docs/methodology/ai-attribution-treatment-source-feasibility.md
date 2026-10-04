# AI-attribution treatment-source feasibility screen

## Question

Can any currently identified, publicly available Canadian source authorize a
quarterly regional measure of realized AI or data-centre construction?

For the 2026-09-01 source vintage, the answer is **no**. This is a source
capability finding, not evidence that construction activity is zero.

The machine-readable contract is
`data/model/ai_attribution_treatment_source_feasibility_contract_v0.1.json`;
the deterministic result is
`data/model-runs/ai_attribution_treatment_source_feasibility_v0.1.json`.

## Locked authorizing gates

A source must pass all seven gates before it can enter the treatment panel:

1. AI or data-centre specific;
2. construction-activity specific;
3. realized rather than intended or forecast;
4. linkable to a project or region;
5. quarterly or finer;
6. publicly retrievable; and
7. accompanied by revision provenance.

Passing some gates does not permit a composite proxy. Each missing
characteristic changes what the measure means.

## Candidate findings

Eight plausible sources are assessed. Alberta Major Projects and Edmonton
permits identify project activity but publish estimates or permits rather than
realized dose. Statistics Canada information-sector capex contains actual and
revised annual values, but NAICS 51 is broad and the geography is provincial.
Monthly building investment has useful regional resolution but aggregates
building types. Building permits are leading indicators of intended work.

The 2024 Survey of Commercial and Institutional Energy Use is important for the
wider observatory: its instrument collects data-centre type, computer-room
floor area, critical IT load, design load, cooling and annual energy use. The
public release, however, exposes aggregated operating-building energy results
rather than building-level construction spend or labour hours. It is therefore
operating-stock and power context, not construction treatment. Annual CMA
industry employment is likewise labour context, not data-centre construction
labour input.

## Decision boundary

The screen identifies zero authorizing candidates. Treatment onset and dose
remain unavailable; causal estimation remains closed; AI-attributable cost and
schedule fields remain null. The next qualifying evidence must identify
data-centre construction, record realized spend or labour hours, support a
project or regional linkage and quarterly vintages, and preserve revisions.

The search boundary is public Canadian federal, provincial, municipal,
regulator, utility, audit and issuer disclosure. Confidential respondent
microdata and inferred allocations of announced capex are excluded.

## Reproduction

```bash
npm run attribution:treatment-sources
PYTHONPATH=research/src python3 -m unittest research/tests/test_treatment_source_feasibility.py -v
npm run attribution:preflight
npm run program:audit
```
