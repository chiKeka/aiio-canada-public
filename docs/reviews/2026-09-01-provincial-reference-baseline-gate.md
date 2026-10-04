# BC, Ontario and Quebec reference-baseline gate

## Scope

This gate applies the locked AIIO reference-class calibration protocol to the
province-level Statistics Canada BCPI series for British Columbia, Ontario and
Quebec. It does not assess provincial AI attribution, power systems, project
inventories or graph parameters.

## Inputs

- Source: Statistics Canada table 18-10-0289-01.
- Locked raw vintage SHA-256:
  `d0d11fda82bf37c3720d159c1d441bc1f15abd73ba9b7d9e750f4b1929b26612`.
- Normalized reference extract:
  `data/processed/bcpi_reference_bc_on_qc.csv`.
- Normalized extract SHA-256:
  `8d6f2bce624176f736d68ac40f87fc5a3e78aec68d7ad0493ee26b3cfba60a5e`.
- Model artifact:
  `data/model-runs/bc_on_qc_bcpi_reference_baseline_v0.1.json`.
- Model artifact SHA-256:
  `866b7f7aca6cf12e6184a5417048036ded318a369c53f039e815e5c99c4aac0b`.

## Coverage

- Three province-level geographies: `PR_24`, `PR_35`, `PR_59`.
- Four reference classes: institutional buildings, schools, office buildings,
  and bus depots with maintenance and repair facilities.
- Twelve province/reference-class series.
- Thirty-eight quarterly observations per series, from 2017 Q1 through 2026
  Q2.
- Five forecast horizons per series, producing 60 horizon checks.

## Gate result

All 60 horizon checks are `not_assessed`. The available rolling origins range
from 15 for the one-year horizon to zero for the five-year horizon. After the
predeclared earlier-half/later-half split, none can meet the minimum 15
calibration and 10 validation origins.

All projected indexes, projected cumulative changes and empirical error bands
remain null. Public projection authorization is false. No Calgary or Edmonton
model selection, coefficient or forecast error is transferred to another
province.

## Verification

- The normalized extract reproduces byte-for-byte from the locked raw ZIP.
- The model artifact reproduces from the normalized extract and declared
  provincial configuration.
- The full research suite passes 79 tests.
- Independent methodological review remains pending; no public Decision Mode
  output is authorized.

## Disposition

Retain the observed provincial series as a common evidence spine and continue
quarterly ingestion. A shorter-history method may be proposed only through a
new preregistered protocol and must not be selected after inspecting these
failed results. Until then, provincial project-cost forecasts remain withheld.
