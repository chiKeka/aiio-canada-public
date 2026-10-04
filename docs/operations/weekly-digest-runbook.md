# Weekly evidence digest operating runbook

## Operating objective

Maintain a dated, source-registered intake journal of newly published or newly
transformed public evidence relevant to AI infrastructure, public-project cost
and delivery, labour, materials, power and regional macro conditions. The
weekly operation feeds research review; it does not silently update a model or
public release.

## Weekly sequence

The scheduled GitHub workflow runs each Monday at 15:00 UTC and may also be
started manually. It retrieves the registered municipal permit proxies from
their official APIs, rebuilds the comparison artifacts and public research
surface, creates a dated digest intake, and runs the full research and web
quality gates. When evidence changes, it pushes an `automation/weekly-evidence-*`
branch and opens a pull request. It never merges that pull request.

1. Read the latest dated intake and manifest to establish the evidence cutoff.
2. Check the official public sources already registered for the monitored
   channels and identify material releases or revisions since that cutoff.
3. Reconcile every candidate source ID and canonical URL against
   `data/registry/sources.json`. A newly discovered source requires a separate,
   reviewable registry change before it can enter an edition.
4. Draft only evidence-backed items. Each item must distinguish the observed or
   inferred change from its possible model implication and must set
   `automatic_model_change` to `false`.
5. Do not create an empty edition merely to satisfy cadence. If no qualifying
   public evidence was found, report the sources checked and leave the latest
   immutable edition unchanged.
6. Build the newest dated intake with `npm run digest:build`, then run
   `npm run digest:audit`, the digest tests, the full research tests and the
   program-readiness audit.
7. Review the generated Markdown and hash manifest. Commit a new edition only
   when the intake is substantive and every gate passes.

The same process can be reproduced locally with
`npm run evidence:refresh-weekly`. Direct official APIs are the reproducible
acquisition path. Firecrawl can be used to discover or monitor candidate public
sources, but a discovered source must be registered and reviewed before it can
feed the automated model surface.

## Promotion boundary

- `no_change` records evidence without proposing model work.
- `review_candidate` opens a research question; it does not change a parameter.
- `promote_after_release` still requires the relevant schema, modelling,
  independent-review and versioned-release gates.
- The weekly operation never deploys, publishes, authorizes a withheld output,
  edits a frozen release, or turns a scenario into evidence.
- Production updates only after a reviewer merges the generated pull request;
  the existing Vercel Git integration then builds the reviewed `main` commit.

## Failure handling

Stop the edition when a source is unregistered, a URL differs from its registry
record, a date disagrees with its filename, a source is inaccessible, evidence
status is ambiguous, or a deterministic rebuild changes an older edition.
Record the gap rather than filling it with an assumption.

## Availability, receipt checks and frozen vintage

`/api/availability` measures application liveness. `/api/health` reports artifact
integrity and separate evidence readiness reasons. A stale digest or overdue
source verification degrades readiness while the last-good evidence remains
available and visibly dated. The production monitor logs the exact route and
HTTP status and retains machine-readable diagnostics; overdue evidence appears
as a warning rather than a claim that the whole website is unavailable.

`public/data/source-freshness.json` retains the frozen review vintage.
`public/data/source-receipts.json` records current operational verification,
which status and health age against the request clock. A successful unchanged
fetch advances verification, never an observation date. A failed attempt retains
the previous success and last-good values. Unknown publication dates remain
unknown. Retrieval timestamps use the actual UTC check date, independently of
an optional digest edition date.

For an offline, read-only receipt check, run:

```sh
python3 research/scripts/weekly_evidence_refresh.py --root . --check-receipts
PYTHONPATH=research/src python3 -m unittest research/tests/test_weekly_refresh.py research/tests/test_source_freshness.py
python3 -m unittest discover -s tests -p test_construction_refresh.py
```

The receipt check reads local registry and archived receipts, prints the source
IDs whose cadence is overdue, and performs no fetch or file write. Fixtures
verify success, unchanged verification, failed attempts, and retained values.
These checks do not establish that remote sources or GitHub-hosted runners will
succeed. The live weekly workflow remains review gated; its diagnostic artifacts
are retained even when source refresh fails. An edition passing local fixture
checks has not been published, dispatched, merged, or deployed.

## September 28 runner failure: unresolved

The September 28, 2026 refresh run
[36483370891]([historical source-record reference withheld])
reported failure with an empty recorded step list for job `109134212289`.
There are no executed refresh steps or source-fetch diagnostics establishing a
pipeline or source failure. Its runner/infrastructure cause remains unresolved;
the receipt and monitoring changes do not claim to repair that incident. A
future authorized run with recorded steps is needed to diagnose any recurrence.

The October 3 production monitor run
[37149353943]([historical source-record reference withheld])
failed its public-route loop on a 503 without printing the route. The old health
implementation intentionally returned 503 for overdue evidence. That incident
supports correcting the availability/readiness contract and diagnostic logging;
it does not establish a whole-site outage or failure of every official source.
