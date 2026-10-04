# Quebec milestone longitudinal panel

## Purpose

This module measures selection and continuity in Quebec's official public-infrastructure dashboard before AIIO treats its authorized-revision histories as a reference candidate. It uses publisher-stable project IDs across archived dashboard snapshots. It does not infer why a project entered, disappeared or reappeared, and it does not convert authorized cost or completion plans into final outcomes. The later complete-catalog panel now supersedes this milestone sample for authoritative selection diagnostics; the milestone artifact remains as a documented sampling comparison.

The official Données Québec catalog exposes 69 CSV resources dated from 2020-05-19 through 2026-08-20. AIIO inventories the complete catalog metadata and hash-locks a reproducible ten-vintage milestone sample:

- earliest available snapshot;
- final snapshot before the November 2020 publication-threshold change;
- first snapshot after that change;
- latest schema-valid snapshot in each calendar year; and
- latest available snapshot.

Overlapping rules are deduplicated. The sample is intentionally not described as the complete monthly panel.

## Rebuild sequence

```bash
npm run outcomes:quebec:vintages:fetch
npm run outcomes:quebec:vintages:normalize
npm run outcomes:quebec:review
```

The catalog, every selected CSV and every retrieval manifest carry SHA-256 content hashes. Retrieval validates official Données Québec URLs. Normalization checks the contract and each source manifest before reading a row.

## Fail-closed source handling

The nominal 2024 year-end CSVs dated 2024-11-01 and 2024-12-04 do not expose the declared dashboard schema as ordinary CSV columns. AIIO records both rejections and falls back to the latest earlier schema-valid 2024 resource, dated 2024-10-09. It does not repair or reinterpret malformed publisher exports.

The 2024-10-09 file contains one duplicate `no_projet=555` row whose analytical fields are identical and whose coordinates differ slightly. The normalizer collapses that pair and records the action. Any duplicate with conflicting analytical fields fails validation.

## Current diagnostics

| Diagnostic | Count |
| --- | ---: |
| Official CSV resources inventoried | 69 |
| Selected milestone vintages | 10 |
| Snapshot-project observations | 5,362 |
| Unique stable project IDs | 1,121 |
| Present in latest snapshot | 649 |
| Absent from latest snapshot | 472 |
| Projects with an interval disappearance | 473 |
| Projects with a milestone reentry | 2 |

At the threshold transition, 278 IDs continue from 2020-10-26 to 2020-11-16, 120 are newly observed and two are no longer observed. The newly observed group combines the threshold expansion from CAD 50 million to CAD 20 million with ordinary project entry and cannot be interpreted as a treatment cohort.

Across adjacent selected milestones, the panel contains 4,239 consecutive project observations, including 1,770 pairs with comparable authorized costs and 1,719 with comparable completion months. Those diagnostics locate changes but do not establish final cost or schedule outcomes.

## Parser-review package

The deterministic review package selects 57 current-snapshot projects. It includes every unreconciled cost or schedule chain, asset-class coverage, no-event controls, large increases/decreases, large schedule delays/advances, ambiguous multi-date text, completion markers and available milestone reentries. Each row contains the public source history text, its hash, parsed events and blank reviewer fields.

This is a review instrument, not a completed review. It deliberately oversamples edge cases, supplies no population error estimate and leaves every reviewer and authorization field blank. Independent review must record disagreements and disposition rather than silently editing source evidence.

## Publication boundary

```text
complete longitudinal panel: not authorized
project exit or completion outcome: not authorized
parser for decision use: not authorized
public-project cost outcome panel: not authorized
public-project schedule outcome panel: not authorized
AI-attributable effect: not authorized
```

The complete 69-date panel is now implemented in `docs/methodology/quebec-full-archive-longitudinal-panel.md`. It shows that milestone sampling captured all but one unique ID but understated reentry projects (2 versus 36). The remaining evidence step is independent parser and extraction review.
