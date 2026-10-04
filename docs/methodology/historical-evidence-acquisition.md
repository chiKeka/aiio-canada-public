# Historical evidence acquisition and review

Completed 5 September 2026. This work acquired public source material, reconciled
the data attachments, assembled a CAL-3 timeline, and reviewed all six included
Edmonton permits. The evidence is insufficient for a historical model replay.
No frozen experiment or production application was changed.

## BCPI releases acquired

Eight Daily releases, eight attached HTML tables, eight CSV attachments and the
archived table 18-10-0276 ZIP were downloaded directly from Statistics Canada.
The capture manifest records retrieval timestamps, URLs, status, byte counts and
SHA-256 hashes. Acquisition in 2026 is separate from the release dates below.

| Forecast origin | Reference quarter | Dated release |
| --- | --- | --- |
| 2024-03-31 | 2023 Q4 | [2024-02-01](https://www150.statcan.gc.ca/n1/daily-quotidien/240201/dq240201a-eng.htm) |
| 2024-06-30 | 2024 Q1 | [2024-05-02](https://www150.statcan.gc.ca/n1/daily-quotidien/240502/dq240502c-eng.htm) |
| 2024-09-30 | 2024 Q2 | [2024-07-30](https://www150.statcan.gc.ca/n1/daily-quotidien/240730/dq240730d-eng.htm) |
| 2024-12-31 | 2024 Q3 | [2024-11-05](https://www150.statcan.gc.ca/n1/daily-quotidien/241105/dq241105c-eng.htm) |
| 2025-03-31 | 2024 Q4 | [2025-02-04](https://www150.statcan.gc.ca/n1/daily-quotidien/250204/dq250204b-eng.htm) |
| 2025-06-30 | 2025 Q1 | [2025-04-25](https://www150.statcan.gc.ca/n1/daily-quotidien/250425/dq250425b-eng.htm) |
| 2025-09-30 | 2025 Q2 | [2025-07-24](https://www150.statcan.gc.ca/n1/daily-quotidien/250724/dq250724d-eng.htm) |
| 2025-12-31 | 2025 Q3 | [2025-11-04](https://www150.statcan.gc.ca/n1/daily-quotidien/251104/dq251104b-eng.htm) |

The CSV and HTML values match for all 32 Calgary/Edmonton rows: two cities,
residential and non-residential aggregates, eight releases. The derived CSV keeps
the three published index levels, quarterly and annual changes, base year, source
URL and source hash separately for each release. Published percentage changes are
preserved rather than recomputed from rounded levels.

These aggregates do **not** contain the office, institutional and school detail
used by the frozen benchmark. Substituting non-residential totals would change
the research question. The predecessor ZIP yields 180 relevant city/type/quarter
observations for 2017 Q1–2024 Q2, but represents one terminal archived dataset.
It cannot establish every value as known at all eight forecast origins.

The November 2024 release introduced the 2023 base and added four cities. Its
notes say changes from 2023 onward may differ because weights were updated.
It also says prior-quarter data may be revised. The captured November 2024 and
November 2025 article footers show modification dates after their release dates;
their metadata still shows the original dates. Exact historical content review
therefore remains pending even for dated pages. This is not proof that the
attached numeric tables changed on those footer dates.

The original intake queue requests table 18-10-0289 at every origin. A later
replay contract must explicitly support predecessor 18-10-0276 before the series
transition, document the mapping and preserve each base/vintage. The archived
predecessor has not been mislabeled as the current table or registered under its
source ID.

## CAL-3 cost, status and schedule timeline

The [English announcement](https://www.estruxture.com/press-releases/estruxture-announces-albertas-largest-data-center-introducing-the-groundbreaking-cal-3-facility)
has an October 29, 2024 dateline but a November 15 page date. It describes a 90 MW
facility planned for the second half of 2026. The corresponding
[French announcement](https://www.estruxture.com/fr/communiques-de-presse/estruxture-annonce-un-investissement-de-750-millions-de-dollars-dans-le-plus-grand-centre-de-donn%C3%A9es-de-lalberta-cal-3)
states CAD 750 million in its headline/features and more than that amount in its
body, with an autumn 2026 opening target. The captured English text omits the
investment amount. These current page versions do not establish exact contents
at either 2024 date; November 15 is only a conservative candidate pending review.

A [July 29, 2025 company article](https://www.estruxture.com/blog/why-alberta-estruxtures-vision-for-powering-canadas-digital-future-from-calgary)
retains the autumn 2026 target without adding a quantified project cost. The
[May 14, 2026 announcement](https://www.estruxture.com/press-releases/estruxture-announces-coreweave-as-anchor-tenant-for-cal-3-its-landmark-ai-ready-facility-in-alberta)
names CoreWeave as anchor tenant for part of Phase 1 and retains a second-half
2026 opening target. Its reference to over CAD 1 billion of investment in Alberta
does not provide a sufficiently clear comparable project budget to overwrite
the CAD 750 million estimate.

The existing August 31, 2026 Alberta register capture gives CAD 750 million,
2024–2026 and Under Construction. It does not prove when those fields first
became public. No dated construction-start certificate, quarterly expenditure,
completion evidence, or AI share of construction spending was acquired. The
2026 tenant announcement postdates all eight benchmark origins.

## All six permit reviews

The six descriptions were checked against the original municipal capture using
the adapter's whitespace-normalized hashes. Amounts are reported construction
values, not realized spending. The v0.1 review and all model inputs are preserved;
v0.2 records the completed analyst review with independent review still pending.

| Permit | Work scope | Class | Reported CAD |
| --- | --- | --- | ---: |
| 0-292502657 | Rogers fire-alarm alteration | Maintenance | 180,000 |
| 0-309784686 | PowerHouse data-room construction | Fitout | 35,000 |
| 1-356648187 | Rogers DC2 halls 7 and 8 in empty warehouse | Expansion | 4,000,000 |
| 1-461055944 | Wolfpaw server-room enlargement | Fitout | 150,000 |
| 1-429959179 | Cross Cancer Institute cooling replacement | Maintenance | 658,000 |
| 1-634601931 | Enbridge like-for-like suppression panel replacement | Maintenance | 25,000 |

Maintenance totals CAD 863,000 of CAD 5,048,000. An expansion-oriented sensitivity
could exclude that amount, leaving CAD 4,185,000 across the expansion and fitouts.
That change has not been applied to an experiment. None of these permit texts
establishes AI-specific spending.

The two Rogers records are distinct scopes and dates. Their shared operator and
neighbourhood support a facility candidate but do not establish a confirmed
match or duplicate event. [Qu's current Edmonton page](https://qudatacentres.com/locations/edmonton-data-centre)
describes two facilities; present-day capacity and AI marketing do not establish
historic permit scope. [Wolfpaw's fibre-ring page](https://www.wolfpaw.com/wolfpaw-data-centres-inc/fibre-ring/)
lists Rice Howard Place as a network location, which supports a location
association but not property ownership or construction identity.
[PowerHouse Group](https://www.powerhousegroup.com/home) supplies design and
construction services; its name in a permit alone does not establish who owns
the facility. No independent ownership or parcel-level linkage was confirmed.
Addresses and coordinates were not added to the published review.

## Replay decision and deliverables

**Do not rerun the frozen benchmark using these partial historical inputs.**
The existing intake still has zero complete origins and 24 missing source/origin
pairs. Acquired release evidence is recorded separately from accepted full
snapshots. Missing exposure evidence remains missing, not zero.

The remaining acquisition requirements are concrete:

1. Full detailed BCPI vintages, including training history and revision notes,
   for the eight release dates above, using the correct predecessor/current table.
2. Historical Alberta register snapshots with publication evidence for project
   costs, status and schedule; CAL-3 announcements are supplemental evidence.
3. Historical municipal permit snapshots or record-level publication histories,
   plus independent review of proposed facility matches and scope exclusions.

If these are unavailable publicly, the next step is an archive enquiry to the
source owners. No message has been sent. A new model replay should be specified
only after the detailed coverage and publication evidence are verified.

Tracked artifacts:

- `data/reviews/historical_bcpi_capture_manifest_v0.1.json`
- `data/reviews/historical_web_capture_sources_v0.1.json`
- `data/reviews/cal3_publication_timeline_v0.1.json`
- `data/reviews/edmonton_included_permit_review_v0.2.json`
- `data/processed/bcpi_daily_alberta_release_observations_v0.1.csv`
- `data/processed/bcpi_predecessor_alberta_asset_extract_v0.1.csv`
- `data/model-runs/historical_evidence_acquisition_v0.1.json`

Original web/ZIP captures stay in the ignored local evidence directory. The
review builder verifies raw and extracted-content hashes, links between releases
and attachments, all 32 table rows, six description hashes and scope totals:

```sh
python3 scripts/build-historical-evidence-review.py
npm run planning:snapshot-readiness
```

The builder requires the local captures; the versioned artifacts and manifests
remain reviewable without them. Reacquiring a URL can produce different bytes and
does not recreate a historic vintage automatically.

Validation: the evidence builder passed and reproduced identical derived files;
timeline references resolved; all 249 research tests and lint passed. The
readiness check reproduced zero complete origins and 24 missing source/origin
pairs. These checks establish consistency, not historical publication acceptance
or independent review.
