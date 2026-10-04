# Independent review prompt — province-linked BCPI bridge

Act as an independent modelling reviewer. Work read-only: do not edit artifacts, alter governance gates or authorize publication directly. Verify the exact packet and every manifest hash before reviewing.

Packet: `data/model-runs/bc_on_qc_province_linked_review_package_v0.1.json`
Packet SHA-256: `sha256:dfa6ba151c27226b3d83732326a8e5137a82157ce2b3fe1ab31136c4ef54a534`

## Locked inputs

- `data/processed/bcpi_reference_bc_on_qc.csv` — `sha256:8d6f2bce624176f736d68ac40f87fc5a3e78aec68d7ad0493ee26b3cfba60a5e`
- `data/processed/bcpi_reference_van_tor_mtl.csv` — `sha256:ac7f0603d84460c8049f335042d2ebc305671f1dab97174fdea159cfdbea1d4c`
- `data/processed/bcpi_province_linked_history_bc_on_qc.csv` — `sha256:be1fb4655cf4a3625cad0e96dd304a5e0a1d4ee932be8d42d80d7965cc0f2f0f`
- `data/model-runs/bc_on_qc_province_linked_reference_baseline_v0.1.json` — `sha256:4a9a19269a889db967b1c170173ce017722161eeb335122e89ee1730147c5d0b`
- `research/src/aiio/provincial_backcast.py` — `sha256:353b72c3df83dc8a1cdb66c023687da3dce4dffc19e33c17754ced6c6c0b8cca`
- `research/src/aiio/calibration.py` — `sha256:e1f727c620c556ae40150824cab11afae49cd26cafe5e568d5438265185c413d`
- `research/src/aiio/provincial_backcast_review.py` — `sha256:545c8418fc4e79c7405c794cca6ef75f68e04aba8d3ba3856b72d68703db9112`
- `research/tests/test_provincial_backcast.py` — `sha256:ba7067449692ebcbcf20876e5d4683e83484370e48d20427b33d8b52b66c6409`
- `docs/methodology/province-linked-bcpi-backcast.md` — `sha256:72fbf6fa45b153175417498d3d2d5c4714c0b34faa838bcc35b77643caf5f6fe`
- `docs/product/decision-mode.md` — `sha256:44c1a177a67249c229a4f76d6d65bf4e9a3e2b0a063061f5965453caffb68a8d`

## Required criteria

1. `source_lineage` — Do both normalized inputs reconcile to the locked Statistics Canada BCPI source and retain their distinct province/CMA geographies?
2. `evidence_status_boundary` — Are official provincial observations preserved and every pre-2017 bridge value unambiguously labelled inferred and not official?
3. `anchor_formula` — Is the single-anchor scaling formula implemented deterministically without using future provincial values to alter pre-anchor growth?
4. `reference_market_choice` — Are Montréal, Toronto and Vancouver defensible, sufficiently disclosed historical reference markets for the narrow research-validation use?
5. `overlap_diagnostic` — Is the predeclared 3% overlap MAPE screen correctly calculated, interpreted and insufficient on its own to establish historical representativeness?
6. `splice_integrity` — Are quarter continuity, anchor continuity, units, index base, source IDs and DGUID lineage preserved across the inferred/observed splice?
7. `forecast_validation` — Does the unchanged rolling-origin protocol remain temporally valid when applied to the mixed inferred/observed history?
8. `fail_closed_outputs` — Do failed and unassessed horizons remain null and do all internal passes remain withheld from project-cost translation?
9. `reproducibility` — Do the hashes, deterministic artifacts and tests reproduce all 1,752 observations, 12 diagnostics and 60 horizon dispositions?
10. `public_claim_boundary` — Would any authorization remain limited to research display of the bridge, with no official-history, project-cost, AI-effect or province-wide representativeness claim?

Run the declared tests where possible and return only one JSON object matching `verdict_contract`. A pass is prohibited when any criterion is conditional or failed or an unresolved critical/high finding exists. Even a pass may recommend research display only; official pre-2017 province history, public projections, project-cost translation and AI attribution remain prohibited.
