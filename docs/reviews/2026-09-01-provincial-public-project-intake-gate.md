# Provincial public-project intake gate — 2026-09-01

## Decision

**Passed for source-preserving research intake. Not authorized for pooled exposure, cost totals, causal inference, schedule-delay estimates, or AI-attributable project escalation.**

The pipeline now normalizes official British Columbia, Ontario, and Quebec project records into one Canada-ready schema while keeping their incompatible source scopes visible.

## Locked inputs

| Source | Vintage | Raw records | SHA-256 |
| --- | --- | ---: | --- |
| `BC_MAJOR_PROJECTS_INVENTORY` | Feature attributes dated 2024-12-01 | 648 | `8ff579493b29400183e5664a3fad55e8eb40792549f2722efdf91d7b05fb4f5e` |
| `ONTARIO_BUILDS_PROJECTS` | CSV dated 2026-06-12 | 5,935 | `acd5e57a1989517aaae269b5836f7d1e56b22b2f948d0254500b8c3b54b5bae4` |
| `QUEBEC_PQI_PROJECT_DASHBOARD` | CSV dated 2026-08-20 | 649 | `a437f7ba9a749f33b130ec5a1a724821134b1b91bc7a2970bcf2597e8ff5877b` |

Retrieval manifests record the effective URL, UTC retrieval time, content type, byte length, archive path, and full content hash.

## Transformation contract

The adapter emits 33 fields covering identity, geography, original publisher taxonomy, inferred AIIO asset class, stage, schedule, cost status, public-funding signal, organizations, coordinates, provenance, vintage, and row-level quality flags.

Key rules:

1. Publisher categories and status text are never overwritten; canonical fields sit beside them.
2. British Columbia and Quebec cost values are multiplied by one million because the sources publish millions of Canadian dollars.
3. Ontario budget values of zero become null with `zero_budget_treated_as_missing`; they do not enter totals as zero-cost projects.
4. Ontario’s missing publisher identifier is replaced by a deterministic full-row vintage hash, explicitly flagged as derived.
5. Exact duplicate Ontario source rows are collapsed deterministically; one duplicate row was removed in this vintage.
6. Original schedule text is retained. Parsed years are limited to explicit four-digit years plus the two documented Ontario month/year patterns. Unparsed periods remain flagged.
7. Asset classification is inferred from publisher category, type, subtype, project name, description, and BC clean-energy signal. `unclassified` is a valid output, not an error.
8. Public funding is a source signal, not a legal ownership determination. BC `FALSE` is represented as `public_funding_not_reported`, not private ownership.

## Coverage result

The combined artifact contains 7,231 normalized records across three provinces:

| Geography | Normalized records | Reported cost | Complete schedule | End year | Coordinates |
| --- | ---: | ---: | ---: | ---: | ---: |
| British Columbia | 648 | 604 | 280 | 308 | 648 |
| Ontario | 5,934 | 3,929 | 0 | 5,704 | 5,499 |
| Quebec | 649 | 351 | 0 | 343 | 0 |

The lack of comparable start periods in Ontario and Quebec is decisive: a national overlap or annualized expenditure screen would currently manufacture comparability. The gate therefore fails closed.

## Locked outputs

| Artifact | SHA-256 |
| --- | --- |
| `data/processed/public_projects_bc_on_qc.csv` | `aecba64233970132e94950067dc0ada365a324393a0cf3adb3165539bc7d5f8a` |
| `data/model-runs/public_projects_bc_on_qc_intake_v0.1.json` | `f518be27e58e7df2e83ec72b53c8ef1b43c2787a2319c82a455bd96e72421acd` |

The report sets `publication_boundary.status` to `research_evidence_only` and `public_project_exposure_authorized` to `false`.

## Required next gate

Before provincial records can feed an executive exposure result, AIIO needs source-specific rules for active-project selection, start-period reconstruction or explicit omission, Ontario sample coverage, BC vintage retirement, and Quebec threshold continuity. Those rules must be tested against archived vintages and independently reviewed.

## Independent review status

Independent review remains pending; no independent verdict is claimed. Evidence intake does not authorize model or decision-output promotion.
