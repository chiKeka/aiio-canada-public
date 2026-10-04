# CanadaBuys construction procurement outcome-feasibility intake

## Purpose

This intake tests whether public federal procurement files can supply the
project-outcome fields required by the AI-attribution contract. It is an
evidence feasibility screen, not an estimate of public-project cost escalation,
schedule delay, procurement competition or an AI-attributable effect.

The machine outputs are:

- `data/processed/canadabuys_construction_outcome_feasibility.csv`; and
- `data/model-runs/canadabuys_construction_outcome_feasibility_v0.1.json`.

## Locked public sources

The 2026-2027 fiscal-year tender, award and contract-history files are registered
separately so each retrieved byte stream has its own source ID, retrieval time,
hash and raw manifest. The parent [CanadaBuys procurement and contracting data
catalogue](https://canadabuys.canada.ca/en/procurement-and-contracting-data)
states that the downloadable files cover tender notices, award notices and
PSPC contract history. The associated Open Government records and CanadaBuys
data dictionary define the file scopes and fields.

| Source ID | File role | Registered as-of |
| --- | --- | --- |
| `CANADABUYS_TENDER_NOTICES_FY2026_2027` | Tender publication, closing date, category and delivery-region labels | 2026-08-31 |
| `CANADABUYS_AWARD_NOTICES_FY2026_2027` | Award date and reported contract-value fields | 2026-08-31 |
| `CANADABUYS_CONTRACT_HISTORY_FY2026_2027` | PSPC contract and amendment rows, instrument dates and reported total value | 2026-08-28 |

The three raw CSV caches are intentionally git-ignored because they total about
29 MB and are reproducible from their registered public URLs. Their compact
retrieval manifests remain versioned.

## Transformation contract

1. Validate every required source header and fail on schema drift.
2. Read the multiline CSVs with the standard CSV parser rather than spreadsheet
   row assumptions.
3. Select any linkage key with a published construction category (`CNST`).
4. Link tender, award and contract-history rows through the published
   solicitation number. A generated linkage ID is explicitly not a physical
   project identifier.
5. Preserve only analytical fields. Contact names, emails, phone numbers,
   supplier addresses and long free-text descriptions are excluded from the
   processed output.
6. Infer a province only when one unambiguous published delivery-region label is
   present. National, multi-region, National Capital Region and unmapped values
   remain distinct; no CMA is fabricated.
7. Treat zero or missing reported contract values as unavailable. Contract dates
   remain procurement-instrument dates and are never relabelled as physical
   construction dates.
8. Publish nulls for every absent authorizing outcome field and retain a
   fail-closed publication boundary.

## Current feasibility result

The locked current-fiscal-year intake contains 2,391 tender rows, 3,121 award
rows and 1,350 contract-history rows before construction screening. It produces
358 construction linkage records:

- 301 have a tender publication and closing date;
- 146 have an award date and reported contract start/end dates;
- 52 have a positive reported CAD award value;
- 89 link a tender to at least one award row;
- 47 link a tender to at least one contract-history row; and
- 145 have one inferable province or territory, while zero have a published CMA.

Those numbers describe field coverage in one current-fiscal-year federal
snapshot. They are not project totals, market shares or performance rates.

## Identification decision

| Required concept | Public file result | Authorization |
| --- | --- | --- |
| Tender open/close and award dates | Partially available | Descriptive procurement timing only |
| Reported award and contract values | Partially available | Candidate linkage field only |
| Stable physical project ID | Missing | No cost/schedule outcome |
| Independent estimate with price basis | Missing | No estimate-to-award or estimate-to-outturn outcome |
| Complete approved-change history | Missing | No outturn reconciliation |
| Baseline and actual physical schedule | Missing | No physical schedule-delay outcome |
| Compliant bidder count | Missing | No procurement-competition outcome |
| CMA project geography | Missing | No region-quarter-asset-class panel |

The result therefore remains `procurement_feasibility_only`. It improves the
evidence pipeline by proving which fields can be normalized and joined, while
also showing why the causal attribution gate must remain closed.

## Reproduction

```bash
npm run fetch:canadabuys:tenders
npm run fetch:canadabuys:awards
npm run fetch:canadabuys:contracts
npm run procurement:normalize
```

The output report hashes all three raw files, all present retrieval manifests
and the processed CSV. Tests lock the current record counts, output hash and
publication boundary.
