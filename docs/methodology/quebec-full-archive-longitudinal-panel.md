# Quebec complete-catalog longitudinal panel

## Purpose

This module represents every official CSV snapshot date exposed by the Québec infrastructure-dashboard catalog. It replaces the ten-vintage milestone sample as AIIO's authoritative selection and continuity diagnostic. It does not turn dashboard entry, disappearance, authorized cost or planned completion into a final audited outcome.

The source contract covers 69 unique dates from 2020-05-19 through 2026-08-20. Rebuild the artifacts with:

```bash
npm run outcomes:quebec:archive:fetch
npm run outcomes:quebec:archive:normalize
```

Every source file and manifest is content-hashed. A rerun verifies existing resource IDs, URLs and hashes before reuse.

## Source-representation contract

The archive contains three publisher representations:

| Representation | Snapshot dates | Treatment |
| --- | ---: | --- |
| Canonical CSV schema | 67 | Parsed directly |
| Valid legacy header aliases | 1 | Mapped to canonical names; values retained |
| Structurally unusable wrapped CSV | 1 | Raw CSV retained; official paired XLSX for the same date supplies the rows |

The exception is 2024-12-04. Its CSV stores the intended comma-separated content inside a malformed semicolon-wrapped representation and does not parse into reliable project rows. The paired official XLSX contains 700 projects on one 17-column sheet. AIIO verified that workbook with an independent spreadsheet reader and a narrow Open XML extraction. The report therefore sets `all_snapshots_parsed_directly_from_csv` to `false` even though all 69 catalog dates are represented.

Two publisher duplicate anomalies are retained in the audit trail and collapsed only when analytical fields are identical:

- 151 exact duplicate rows in 2025-01-30; and
- one exact duplicate row in 2025-09-04.

The earlier 2024-10-09 coordinate-only duplicate remains governed by the same rule. Conflicting duplicate project IDs fail normalization.

## Full-panel diagnostics

| Diagnostic | Full 69-date panel | Ten milestones |
| --- | ---: | ---: |
| Snapshot-project observations | 43,044 | 5,362 |
| Unique stable project IDs | 1,122 | 1,121 |
| Absent from latest snapshot | 473 | 472 |
| Projects with a reentry | 36 | 2 |

The milestone design captured nearly every distinct ID, but substantially understated temporary disappearance and reentry. The full sequence is therefore required for transition analysis.

Across the 68 adjacent snapshot transitions, the complete panel observes 510 disappearance events. For 291, the project's final prior history contains both a publisher-declared complete-service marker and an explicit statement that the project will be removed from the dashboard. The remaining 219 disappearance events are unclassified. The publisher statement improves source-level interpretation but is not an independently audited actual-completion outcome.

The full panel also exposes 41,885 adjacent stable-ID observation pairs, including 19,774 comparable authorized-cost pairs and 17,739 comparable completion-month pairs. These are change diagnostics, not causal AI effects or outturn distributions.

## Threshold and outcome boundaries

The publication threshold changed from CAD 50 million to CAD 20 million in November 2020. Entry around that date combines threshold expansion and ordinary project entry. It is not a treatment cohort.

A disappearance may still represent cancellation, renaming, merger, scope change or another publication event unless the source explicitly states complete service and planned retirement. Even an explicit retirement statement does not supply an audited final cost, exact actual completion date or estimate price-basis date.

```text
catalog snapshot coverage: complete
all snapshots parsed directly from CSV: no
publisher retirement marker as final outcome: not authorized
project exit outcome: not authorized
public-project cost outcome panel: not authorized
public-project schedule outcome panel: not authorized
AI-attributable effect: not authorized
```

The next research step is to complete independent parser and extraction review, then determine whether the 291 publisher-declared retirement transitions can support a preregistered, source-specific schedule-retirement endpoint without overstating final completion.
