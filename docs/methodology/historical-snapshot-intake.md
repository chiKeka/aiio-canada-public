# Historical source snapshot intake

The subsequent [historical evidence acquisition](historical-evidence-acquisition.md)
downloaded eight dated BCPI releases and reviewed CAL-3 and all six permits.
Those partial sources are not accepted full historical snapshots; the readiness
gap below remains open.

The intake stores immutable normalized source snapshots and selects the latest
whole snapshot available by a specified date. It turns the vintage audit into
an operational acquisition workflow. It does not fill missing historical data,
replay the model, or authorize a forecast.

## Current registered captures

| Snapshot | Normalized records | Conservative availability (UTC) |
| --- | ---: | --- |
| `AB_PROJECTS_CAPTURE_20260831` | 22 | 2026-08-31 13:10:54 |
| `EDM_PERMITS_CAPTURE_20260901` | 85 | 2026-09-01 04:32:51 |
| `BCPI_CAPTURE_20260831` | 29,424 | 2026-08-31 13:06:36 |

These are existing captures, not newly acquired historical releases. The project
snapshot contains the existing AI-relevance screen, not the entire Alberta
project register. The permit snapshot includes the existing broad keyword screen,
not only the six permits used by the proxy. The BCPI snapshot preserves the
existing Alberta extract, including older reference quarters.

An observation dated 1981, a permit issued in 2018, or a project start year of
2024 does not move a 2026 capture's availability backward. None of the three
captures was archived before any of the eight benchmark forecast origins.
The generated queue therefore contains **24 missing source/origin pairs** and
zero origins with all three source snapshots available. Those 24 requirements do
not necessarily require 24 different files: a suitable release may cover several
origins, subject to later row-level coverage checks.

## Commands

Register a prepared intake descriptor:

```sh
npm run planning:snapshot-register -- data/vintages/intake/AB_PROJECTS_CAPTURE_20260831.json
```

Identical registration returns `already_registered`. Revised data or publication
evidence requires a new snapshot ID; an existing snapshot cannot be overwritten.
Registration verifies the capture manifest and actual raw bytes, hashes the
normalized CSV, checks source IDs and unique record IDs, and copies the CSV into
`data/vintages/artifacts/`. Subsequent source refreshes do not rewrite that copy.
The preserved snapshot and catalog both record hashes.

Select a source snapshot at an exact timestamp:

```sh
npm run planning:snapshot-select -- STATCAN_BCPI_18100289 --as-of 2024-03-31T23:59:59Z
npm run planning:snapshot-select -- STATCAN_BCPI_18100289 --as-of 2026-09-05T00:00:00Z
```

The first returns `missing` with null snapshot, artifact and record count. The
second selects the registered BCPI capture. It returns a verified file reference,
not a modeled value. Removed rows are not silently restored from older releases;
the selected artifact is always a whole snapshot. Different contents claiming
the same latest availability time cause an ambiguity error instead of arbitrary
selection. Identical-content ties are resolved deterministically by snapshot ID.

Build all benchmark selections and the acquisition queue:

```sh
npm run planning:snapshot-readiness
```

The report is `data/model-runs/historical_snapshot_readiness_current.json`.
It lists source selections for the UTC end of the quarter before each target
quarter. Its acquisition queue records the required source, forecast target and
latest acceptable availability date.

## Preparing a new capture

Use the existing descriptors in `data/vintages/intake/` as templates. A descriptor
requires schema `AIIO_SNAPSHOT_INTAKE_1.0`, a new uppercase snapshot ID, source ID,
capture-manifest path/hash, normalized-artifact path/hash and `publication`.
All referenced paths must remain inside the repository.

The capture manifest must record a successful retrieval, matching source ID,
timezone-aware retrieval timestamp, raw archive path and content hash. A missing
raw cache cannot pass intake verification. `raw_copy_path` may identify another
local copy only if its bytes match the capture's content hash exactly. Raw files
are verified locally; intake does not copy raw archives into the public site.

Supported normalized CSV identifiers are:

| Source | Unique record field |
| --- | --- |
| `ALBERTA_MAJOR_PROJECTS` | `project_id` |
| `EDMONTON_GENERAL_BUILDING_PERMITS` | `permit_proxy_id` |
| `STATCAN_BCPI_18100289` | `observation_id` |

Every normalized row must have the matching `source_id`. Raw-file verification,
CSV shape and record identity do not prove that the normalization is correct.
Source-specific parser reconciliation and domain coverage remain separate work.

## Publication dates earlier than capture

Set `publication` to null unless there is evidence supporting an earlier public
release of the **exact captured contents**. Null means the capture timestamp is
used conservatively. A filename, reference period or general announcement is not
sufficient evidence of that content's publication time.

To register an earlier date, supply:

- `published_at`: a timezone-aware timestamp no later than capture;
- `evidence`: repository path and SHA-256 of the archived release evidence;
- `review_receipt`: repository path and SHA-256 of the matching review receipt.

The review receipt must contain:

```json
{
  "schema_version": "AIIO_PUBLICATION_DATE_REVIEW_1.0",
  "decision": "accept_snapshot_publication_date",
  "scope": "source_publication_date_only",
  "source_id": "the matching registered source ID",
  "raw_content_sha256": "sha256 of the exact captured contents",
  "published_at": "the exact claimed timestamp",
  "evidence_sha256": "sha256 of the archived release evidence",
  "reviewer": "the actual reviewer",
  "reviewed_at": "a timezone-aware timestamp at or after capture"
}
```

This is a schema illustration, not an accepted receipt. No historical publication
receipt has been created for the registered captures. The reviewer must assess
whether the evidence binds that date to those raw contents, not merely to a
related project or dataset. The loader rechecks this binding and both file hashes
whenever snapshots are selected.

A receipt records a reviewer assertion; its hash is not authentication of the
reviewer, a digital signature, or proof of source publication. Acceptance applies
only to source availability. Predictive and causal authorization remain false.

## Verification and next work

Tests cover future-release exclusion, preservation after source CSV edits,
immutable IDs, publication/content mismatches, malformed rows, missing raw bytes,
hash drift, path containment, conflicting versions and whole-snapshot selection.
The readiness report also reproduces without requiring ignored raw caches after
the snapshots have been registered.

Next, acquire dated earlier project, permit and BCPI releases, normalize them
with source-specific checks, and register supported publication dates. A full
model replay must then verify market/asset coverage, training periods, required
fields and period-specific data availability. Even all three source snapshots
being selected would not establish those conditions automatically.

The frozen v0.1/v0.2 experiments, live application and public calibration gates
remain unchanged.
