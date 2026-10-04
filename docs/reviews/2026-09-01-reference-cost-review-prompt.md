# Independent review prompt — Alberta reference-cost baseline

Act as an independent modelling reviewer. Perform a read-only review; do not edit files, alter gates, authorize publication directly or supply replacement parameters. Verify the exact packet and input hashes before reviewing.

Packet: `data/model-runs/alberta_reference_cost_review_package_v0.1.json`
Packet SHA-256: `sha256:24df8d2263f0c6875a981eeed1dda2bf5576b0870531a2e88cf11572e25b5935`

## Locked inputs

- `data/processed/bcpi_alberta.csv` — `sha256:4ea07e72d839df3e66b81f5e9b213932c153e39020af7bc96cc0ce6cdb2f36c1`
- `data/model-runs/alberta_bcpi_reference_baseline_v0.1.json` — `sha256:9909c2d10a6c67f9699d98cd16dead6e619635b3a16b535c389ae9efa518bd40`
- `research/src/aiio/calibration.py` — `sha256:e1f727c620c556ae40150824cab11afae49cd26cafe5e568d5438265185c413d`
- `research/src/aiio/model_review.py` — `sha256:3e340792421d3799ffc289c3b787626e48be43e3714b690c0b962bd10e50f7d6`
- `research/tests/test_calibration.py` — `sha256:4a692c14a2c17e7abb2ffaac883714ee07ef06fd2ab1dcebac24e87b5fa9af64`
- `research/tests/test_calibration_artifact.py` — `sha256:6d9763e886b80e9c64ab560ea1f404e0ef85f9269bcab128eadaf8e5063310c2`
- `docs/methodology/calibration-protocol.md` — `sha256:5fe2e7fc1f00b8c1010d288213db1cceeaadf50848ed15f5e2578956ae6c44be`
- `docs/methodology/reference-cost-independent-review.md` — `sha256:1b4931e58c332473062c27b444d4019121db8797af5063032d94142277f203fc`
- `docs/methodology/pspe-integration-audit.md` — `sha256:6a6a32647d53982ccc7745eead29b067823410cf9cb94d59c25e2740b78cca03`
- `docs/product/decision-mode.md` — `sha256:44c1a177a67249c229a4f76d6d65bf4e9a3e2b0a063061f5965453caffb68a8d`

## Required criteria

1. `estimand_boundary` — Does the artifact consistently describe a BCPI model-building reference-index path rather than a project-cost or AI-effect forecast?
2. `temporal_integrity` — Are every candidate selection, error-band estimate and validation decision based only on information available at each rolling origin?
3. `predeclared_model_selection` — Are candidates, lookback, tie rule, horizons, partitioning and gates fixed in code without post-outcome tuning?
4. `validation_adequacy` — Are the locked origin counts, error gates and flat-benchmark comparison appropriate for the narrow baseline-only claim?
5. `interval_semantics` — Are the p10/p90 bands correctly constructed and described as empirical historical error ranges, not confidence or probability intervals?
6. `fail_closed_outputs` — Do failed or unassessed horizons remain null everywhere downstream, including project-cost translation and the public surface?
7. `reference_class_mapping` — Are the four building reference mappings and Calgary/Edmonton geographic limits defensible and sufficiently disclosed?
8. `graph_unit_separation` — Is the dimensionless PSPE-informed graph kept separate from BCPI percentages and project dollars?
9. `reproducibility` — Do locked inputs, implementation hash, deterministic artifact and tests provide enough evidence to reproduce the exact run?
10. `public_claim_boundary` — Would authorization remain limited to individual gate-passing E1 horizons, with no E2, province-wide, long-horizon health/school or project-budget claim?

Run the packet's declared tests where possible. Return only one JSON object matching `verdict_contract`. A pass is prohibited if any required criterion is conditional or failed, or if any critical/high finding remains open. Even a pass may recommend only the single listed gate-passing E1 horizon; every E2, project-budget, graph monetization, long-horizon health/school and province-wide claim remains withheld.
