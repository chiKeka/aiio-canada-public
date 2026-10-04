# Grok release red-team: Alberta pilot

Date: 2026-08-31  
Reviewer: Grok CLI 0.2.87  
Gate: model and research-prototype release  
Verdict: **HOLD**

This review was requested as an independent challenge to the Alberta pilot before publication. The reviewer assessed the graph engine, scenario assumptions, release metadata, power calculations, communication layer, and tests. The review is advisory: each finding is reproduced here as a concise project record, while the AIIO team remains responsible for verification and disposition.

## Findings and dispositions

| ID | Severity | Finding | Required disposition |
|---|---|---|---|
| GR-01 | Blocker | Resource and queue states behaved as one-year pulses. Pressures disappeared unless a new shock arrived, so the engine could not support timing claims. | Add explicit node retention with low, central, and high values. Propagate retained state through subsequent periods and test the decay path. |
| GR-02 | Blocker | The three displayed cases varied only graph weights even though denominators, absorption, local capture, and persistence dominate the scale uncertainty. | Label structural cases as diagnostic cases, not uncertainty intervals. Add one-at-a-time and joint sensitivity runs for denominators, absorption, capture, and retention. Limit displayed precision. |
| GR-03 | Blocker | The release was not reproducible: the repository was dirty, the commit was not pinned, and run artifacts lacked engine hashes, parameter-set identifiers, node validity dates, and edge assumption metadata. | Build from a clean pinned source commit; record full commit and file hashes; add node validity fields plus edge author, version, and assumption IDs; retain explicit structural-test banners for unsourced assumptions. |
| GR-04 | High | CAD construction shocks and MW power quantities were mixed. A CAD shock drove a grid queue, and PUE was used as a peak multiplier. | Remove the CAD-to-grid-queue path. Publish an independent MW-based power overlay with a commissioning profile, energy PUE, and a separate peak-to-IT factor. |
| GR-05 | High | Electrical pressure could reach schedules directly and again through the cost node; grid and building electrical equipment were merged; the cost node pooled too many unnormalised inflows. | Split building and grid electrical materials, remove cost-to-schedule edges, use direct capacity paths for schedule pressure, and constrain the effective incoming cost weights. |
| GR-06 | High | The public layer could be read as a forecast: scenario periods were zero-based, outcomes lacked a delay-pressure qualifier, reported CAD precision was excessive, and the excluded 54% of capex was not prominent. | Rename the exercise as a counterfactual uncalibrated diagnostic; include calendar years; use `*_DELAY_PRESSURE` outcome IDs; round public values; state that pressure scores are not delay percentages and that 54% of capex is outside the graph. |
| GR-07 | High | The PSPE test suite lacked identity, cycle, mass-bound, absorption sensitivity, additivity, signed-path accounting, self-loop, and golden-run tests. | Add the missing invariants and a committed golden run before reopening the gate. |

## Release rule

The HOLD remains in force until all seven findings are implemented and verified. A public research prototype may reopen only with a clean source commit, reproducible artifacts, passed validation, and a conspicuous “structural diagnostic, not an empirical finding or forecast” surface. Calibrated policy claims remain out of scope until observed denominators and response parameters are defensibly estimated.

