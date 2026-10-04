# Historical vintages and project/permit linkage

The local archive does not yet support a point-in-time replay of the eight
planning-benchmark forecast origins. The linkage review also shows that the
six included Edmonton permits should not be treated as six new data-centre
construction projects. This audit preserves the frozen benchmark and proxy.

## Archive findings

| Source | Retrieval manifests | Distinct data contents | Earliest archived retrieval |
| --- | ---: | ---: | --- |
| Alberta major projects | 1 | 1 | 2026-08-31 |
| Edmonton building permits | 3 | 1 | 2026-09-01 |
| Statistics Canada BCPI | 1 | 1 | 2026-08-31 |

The Edmonton downloads dated September 1, 2 and 3 declare identical data hashes.
Different retrieval dates or metadata hashes do not create distinct historical
permit contents. The archived files describe earlier activity, but none of the
pinned retrievals predates a forecast origin in the 2024 Q2–2026 Q1 benchmark.
There are zero complete archived information sets for those eight origins.

This finding concerns the local archive only. It does not establish that older
official releases or public archives are unavailable elsewhere. Retrieval time,
permit issue date, project start year and source publication time are separate
fields. The report never treats an early activity date as proof that today's
record was available then, or missing historical exposure as zero exposure.

Local raw verification reconciled three unique data blobs to their manifests
and all six reviewed descriptions to the normalized description hashes. Where
a repeated download's named cache file is absent, an existing copy with the
identical content hash can verify the data bytes. This does not verify that the
missing retrieval occurred or establish a historical publication date.

## Draft permit review

The raw descriptions were inspected locally. The review artifact keeps controlled
work labels, source IDs and description hashes; it does not republish free text,
addresses, neighbourhoods or coordinates. Labels remain analyst proposals pending
independent review.

| Work class | Records | Reported permit value |
| --- | ---: | ---: |
| Data-centre expansion | 1 | CAD 4,000,000 |
| Data/server-room fit-out or alteration | 2 | CAD 185,000 |
| Maintenance or equipment replacement | 3 | CAD 863,000 |

These are permit estimates, not realized spend. The maintenance group includes
fire-alarm work, a fire-suppression-panel replacement and cooling replacement
in a health institution. An explicit data-centre phrase is insufficient to
classify such work as new AI infrastructure construction. The draft does not
automatically exclude any record from the frozen model.

Two Rogers descriptions identify the same operator and neighbourhood, creating
one candidate facility group. One permit covers fire-alarm work and the other
warehouse expansion. Those clues do not prove a common building, duplicated
scope, duplicated cost or a single independent construction event. Five proposed
facility groups therefore remain five candidates, not five confirmed facilities.
No permits are deduplicated and no project/permit linkage is confirmed.

## Overlap and timing

The current dollar-valued project component is in Calgary; the included permits
are in Edmonton. There are **zero simultaneously positive project/permit
market-quarter cells** in the frozen reconstruction. Same-cell overlap between
those two components is therefore not the immediate explanation for the failed
benchmark. This is conditional on the current records and CMA mapping; it does
not resolve within-permit overlap or future additions.

The audit found a separate schedule denominator issue. The CAL-3 project reports
a 2024–2026 schedule, or 12 quarters. The frozen proxy ends in 2026 Q2 and
normalizes its construction weights over the 10 quarters inside that data window.
Consequently, it allocates the full CAD 750 million reported project value by
June 2026. Normalizing the same assumed profile over all 12 scheduled quarters
would allocate CAD 652,739,251.04 through June and retain the remaining allocation
for the final two quarters. These figures precede the assumed realization ratios.

This is a reconstruction arithmetic issue, not evidence of actual spending.
The original proxy, panel, benchmark contract and benchmark results are preserved.
A correction must be a new version with a full-schedule denominator, followed by
reconciliation and a newly frozen comparison protocol. Do not overwrite the
unsuccessful primary benchmark or select a revised model based on its results.

Follow-up: the separately versioned correction and comparisons are now available
in [proxy v0.2](full-schedule-proxy-comparison.md). This audit and the original
benchmark remain preserved as the evidence that motivated the correction.

## Next evidence and implementation steps

1. Acquire dated archived project cost, stage and schedule records, plus historical
   BCPI releases, for the relevant forecast origins. Record publication date and
   retrieval timestamp separately and reconcile any source revisions.
2. Acquire permit publication/update evidence or archived releases. The current
   issue dates do not establish when the archived field values became available.
3. Independently review the six scope labels and the Rogers candidate pair using
   stable facility/work-package identifiers. Preserve separate maintenance and
   expansion scopes unless evidence establishes duplication.
4. Implement the full-schedule denominator in a separate reconstruction version.
   Freeze project-only, permit-only and reviewed-scope ablations before refitting.

## Reproduction and boundaries

Run `npm run planning:vintage-linkage` for the portable, manifest-based audit.
Use `npm run planning:vintage-linkage -- --verify-raw` to additionally require
local raw bytes and verify the six description hashes. Missing raw files without
an identical-content copy cause that optional verification to fail.

The contract pins the source manifests, reviewed records, existing proxy and
benchmark. Tests check repeatability, identical-download handling, complete
review coverage, hash drift, path containment, missing raw bytes and rejection
of attempted authorization. All validated-estimate, causal, automatic-model-change
and confirmed-linkage flags remain false.

Artifacts:

- `data/model/vintage_linkage_audit_contract_v0.1.json`
- `data/model-runs/vintage_linkage_audit_v0.1.json`
- `data/reviews/edmonton_included_permit_review_v0.1.json`
