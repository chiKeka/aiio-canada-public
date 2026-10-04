# Province-linked BCPI historical backcast

Status: research display only; public projection and project-cost translation withheld.

## Question

Can AIIO extend the short official British Columbia, Ontario and Quebec building-price histories for model validation without mislabelling city-market observations as official provincial data?

## Public source and rationale

Statistics Canada table [18-10-0289-01](https://www150.statcan.gc.ca/t1/tbl1/en/tv.action?pid=1810028901) publishes quarterly Building Construction Price Index values by model building and construction division. Statistics Canada's release notes state that provincial-level indexes are calculated from the movements of the respective census metropolitan areas.

The locked AIIO vintage contains official provincial observations from 2017 Q1 and long Montréal, Toronto and Vancouver series beginning in 1981 Q1 for the institutional, school and office reference classes. This permits a transparent historical bridge, but not an official provincial reconstruction.

## Locked method

For each province and reference class, AIIO names one long-history reference market:

| Province output | Historical reference market |
|---|---|
| Quebec | Montréal CMA |
| Ontario | Toronto CMA |
| British Columbia | Vancouver CMA |

Let `P_anchor` be the first official provincial index and `C_anchor` the reference CMA index in the same quarter, 2017 Q1. For every earlier quarter `t`:

`P_linked,t = C_t × (P_anchor / C_anchor)`

The pipeline uses the linked value only before the anchor. It preserves every official provincial value without modification from 2017 Q1 onward. The municipal-operations proxy begins in 2017 and is not backcast.

Every inferred row is labelled `inferred` and carries the flags `province_linked_cma_backcast` and `not_official_provincial_observation`. Its source DGUID remains the reference CMA DGUID rather than a provincial DGUID.

## Overlap screen

Before emitting an artifact, the pipeline applies the same single anchor to the entire official overlap and compares the linked CMA level with the official province level. The predeclared maximum mean absolute percentage error is 3%. All 12 province/reference-class diagnostics pass in the current vintage; maximum observed overlap MAPE is below 0.3% and maximum absolute overlap error is below 1.1%.

This screen answers only whether a scaled reference CMA tracks the published provincial index during the overlap. It does not prove that the CMA represented the whole province before 2017.

## Forecast validation

The combined history is passed through the unchanged locked rolling-origin reference-cost protocol. The resulting 12 reference series produce 60 horizon assessments:

- 9 internally gate-passing horizons;
- 36 gate-failed horizons; and
- 15 not-assessed horizons.

All nine internal passes are British Columbia-linked results. Ontario and Quebec do not pass the forecast gates, and all municipal-operations horizons remain not assessed because no pre-2017 history exists.

An internal gate pass does not authorize publication. Independent review must assess the splice, overlap diagnostic, reference-market choice, forecast protocol and claim boundary before any individual horizon can be used in Decision Mode.

## Outputs

- `data/processed/bcpi_province_linked_history_bc_on_qc.csv`
- `data/model-runs/bc_on_qc_province_linked_reference_baseline_v0.1.json`
- `research/src/aiio/provincial_backcast.py`
- `research/tests/test_provincial_backcast.py`

Rebuild with:

```bash
npm run cost:backcast:provinces
npm run cost:review:province-bridge
```

The second command produces a ten-criterion, hash-locked independent-review
packet and a reviewer prompt. The packet is non-authorizing: a separately
validated verdict is required, and even a pass may recommend research display
only.

## Prohibited interpretations

The backcast is not:

- an official provincial BCPI observation before 2017;
- evidence that one CMA fully represents a province;
- a public-project cost forecast;
- a schedule model;
- an AI-infrastructure treatment or effect; or
- authority to publish a gate-passing horizon.
