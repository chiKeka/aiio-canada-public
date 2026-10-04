# Provincial power-planning intake gate - 2026-09-01

## Decision

**Passed for source-preserving research intake. Not authorized for public provincial comparison, scenario calibration, spare-capacity claims or transmission requirements.**

The intake binds five official Ontario, B.C. and Quebec source artifacts, extracts 47 decision-oriented metrics and retains four B.C. transmission actions. It fails closed because independent extraction review is pending and the provinces publish materially different quantities.

## Locked sources

| Source | Artifact SHA-256 |
| --- | --- |
| IESO 2026 APO data tables | `987448021f1db08bf7c815f453fa9f73057a2507f25992e110aca0abc3666526` |
| IESO 2026 demand module | `dce737fb9061fafed2c0d2371681f2de0860c8511aec47cb95e19196e912f597` |
| BC Hydro 2025 IRP summary | `48943e3c868100ee8da1676f94a20400f8070ee7302a9b5945e0908d3a8073ab` |
| Quebec 2025 supply-plan progress report | `88d382a1b9f8cca86d7cebacdac3ee3bc13077f3c34f631d11ddbc7758a2f7f1` |
| Hydro-Quebec 2026 data-centre announcement | `2f5beed48b1be4ad62e20729c6f4ef36eada08e28a4903ad9595e3cd64e7a921` |

Retrieval manifests retain the effective URL, UTC retrieval time, content type, byte length, archive path and full content hash.

## Coverage

| Province | Metrics | Evidence currently represented |
| --- | ---: | --- |
| Ontario | 32 | System energy scenarios, seasonal peaks, remaining needs after in-flight actions, data-centre energy endpoints |
| Quebec | 11 | Regular sales, winter system peak, data-centre winter peak, current/outlook announcement |
| British Columbia | 4 | Selected energy acquisitions and generation additions, plus four named transmission actions |

The selected records are a source profile rather than a complete extraction of every published series.

## Reproducibility controls

1. Every source file is verified against the content hash in the manual extract.
2. Every Ontario workbook metric is checked against its exact worksheet and cell locator.
3. Quantity types enforce allowed units and source/geography contracts.
4. Metrics retain quantity status so published forecasts and plan actions cannot masquerade as observations.
5. The output explicitly prohibits pooling incompatible data-centre energy and peak metrics.
6. Scenario calibration and transmission requirements remain false regardless of source-profile review status.

## Locked outputs

| Artifact | SHA-256 |
| --- | --- |
| `data/manual/provincial_power_planning_extract_2026_09.json` | `7981705fc82e2fee6d08e3a336c9731d41cd6b2b7f77d7ad9a148e194fcfcf07` |
| `data/model-runs/provincial_power_planning_contract_v0.1.json` | `137ac23f574ec9d9d3b1661c1ca99087487704edc2dc58ebbff61bae08c26cc3` |
| `data/processed/provincial_power_planning_metrics.csv` | `c0770af42e51dea7845ba2c8a593eb585825213965ffd3286c7ac1b67bedb691` |

## Independent review status

Independent review remains pending; the artifact is not authorized for Decision Mode or model calibration.
