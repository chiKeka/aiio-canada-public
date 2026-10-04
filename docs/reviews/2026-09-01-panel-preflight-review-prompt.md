# Independent review prompt — E2 panel acquisition preflight

Review the following AIIO Canada artifacts as a read-only methodological and reproducibility gate. Do not edit files, supply missing evidence, estimate an effect, or treat a candidate source as authorizing evidence.

## Locked inputs

| Artifact | SHA-256 |
|---|---|
| `data/model/ai_attribution_panel_contract_v0.1.json` | `f8a0f750a0c1f3d225dba3a2fd43c17d5629988bf29daa0fd503cd708f43cca4` |
| `data/model/ai_attribution_panel_acquisition_contract_v0.1.json` | `4af807d9a9973680ba42bf4eb31cb4d71a81dd2928b0168dec67a152cc7d9f63` |
| `data/model-runs/ai_attribution_panel_preflight_v0.1.json` | `fdab0eba6735db0dbe5a2376c6801267610129b9512171459bb6653b82b3ae4a` |
| `research/src/aiio/panel_preflight.py` | `629e5b79c1213b0084a81841a9c6c9c02a3dd49e99ba82d893d51cb20033f211` |
| `research/tests/test_panel_preflight.py` | `6de323e87269fd45a35eebf20d5d11db13807f829f050e68c0b6191a873b7d0d` |

## Required review criteria

1. The acquisition contract is linked to the locked attribution contract and every referenced source ID exists in the registry.
2. Five candidate CMAs, two potential treated regions, three potential controls, and three asset classes are presented as planning scope only—not as eligible observations.
3. All 27 authorizing field instances are assigned exactly to the four declared acquisition tasks; no uncovered field is hidden by a proxy.
4. All ten evidence receipts are hash-locked, assertion-checked, and explicitly non-authorizing or control-only.
5. Announcements, requested or forecast MW, permit values, broad-sector capex, authorized revisions, catalog disappearance, scenario capex, and graph scores cannot authorize treatment or outcomes.
6. S3/PSPE is used only to prioritize missing nodes and ties; it does not fill fields, define treatment dose, create a counterfactual, or identify an effect.
7. Zero treated regions, controls, asset classes, and panel rows are currently eligible; estimator authorization is false and all effect outputs remain null.
8. The preflight is deterministic, reproducible from the locked inputs, and fails closed under source drift, assertion drift, incomplete queue coverage, or premature authorization.

## Required response

Return JSON only:

```json
{
  "verdict": "PASS | PASS_WITH_CONDITIONS | FAIL",
  "artifact_sha256": "fdab0eba6735db0dbe5a2376c6801267610129b9512171459bb6653b82b3ae4a",
  "criteria": [
    {"id": 1, "status": "pass | fail", "finding": "concise evidence-backed finding"}
  ],
  "findings": [
    {"severity": "blocker | high | medium | low", "artifact": "path", "finding": "specific issue"}
  ]
}
```

A reviewer verdict is advisory. It cannot assemble the panel, authorize an estimator, or change publication status automatically.
